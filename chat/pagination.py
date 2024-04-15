from collections import OrderedDict

from django.db.models.query import QuerySet

from rest_framework.pagination import BasePagination
from rest_framework.response import Response
from rest_framework.utils.urls import remove_query_param, replace_query_param

from .models import Message

class MessagePagination(BasePagination):
    """
    Custom pagination class which provides hooks for
    returning various kinds of message lists based on
    request query parameter values `category`, `reference`
    and `size`.
    """

    category_param = 'category'
    ref_param = 'reference'
    size_param = 'size'

    default_size = 5
    default_category = 'initial'
    max_size = 30

    is_redirected = False

    def paginate_queryset(self, queryset, request, view=None):
        self.request = request
        self.category = self.get_category()
        self.queryset = queryset.order_by('time_stamp')

        if self.category == 'initial':
            self.paginated_set = self.get_initial_messages()
        elif self.category == 'unread':
            self.paginated_set = self.get_unread_messages()
        else:
            params = {
                'ref_id': self.get_reference_id(),
                'size': self.get_size(),
            }
        
            if self.category == 'older':
                self.paginated_set = self.get_older_messages(params)
            elif self.category == 'newer':
                self.paginated_set = self.get_newer_messages(params)
        
        return self.paginated_set
        
    def get_paginated_response(self, data):
        response_data = OrderedDict()
        
        response_data.update([
            ('redirected', self.is_redirected)
        ])

        if self.category in ['initial', 'older', 'newer']:
            response_data.update([
                ('next', self.get_next_link(data)),
                ('previous', self.get_previous_link(data))
            ])

        if self.category in ['initial', 'unread']:
            response_data.update([
                ('unread_count', self.count_set(self.target_start_set)
            )])

        response_data.update([
            ('result_count', len(data)),
            ('total_count', self.count_set(self.queryset)), #debug
            ('results', data),
        ])

        return Response(data=response_data)

    def get_category(self):
        valid_categories = ['initial', 'older', 'newer', 'unread']
        category = self.request.query_params.get(
            self.category_param,
            self.default_category
        )

        if category not in valid_categories:
            return self.default_category
        return category

    def get_size(self):
        size = self.request.query_params.get(
            self.size_param,
            self.default_size
        )

        try:
            if int(size) > self.max_size:
                return self.max_size
        except (ValueError, TypeError):
            size = self.default_size
        
        return int(size)
        
    def get_reference_id(self):
        param = self.request.query_params.get(self.ref_param)

        try:
            int_id = int(param)
            ref_message = self.queryset.get(pk=int_id)
            ref_id = ref_message.id
        except (ValueError, TypeError, Message.DoesNotExist):
            return None
        
        return ref_id

    def get_initial_messages(self):
        middle_idx = self.get_first_new_message_index()

        count = self.count_set(self.target_end_set)
        if middle_idx is None:
            old_msg_count = count
        else:
            old_msg_count = count - 1

        new_msg_count = self.count_set(self.target_start_set)

        if old_msg_count <= self.default_size:
            start_idx = 0
            self.has_previous = False
        else:
            start_idx = old_msg_count - self.default_size 
            self.has_previous = True

        if new_msg_count <= self.default_size:
            end_idx = None
            self.has_next = False
        else:
            end_idx = middle_idx + self.default_size
            self.has_next = True

        return list(self.queryset[start_idx:end_idx])
    
    def get_unread_messages(self):
        target_idx = self.get_first_new_message_index()

        if target_idx is None:
            return []
        
        new_msg_count = self.count_set(self.target_start_set)

        if new_msg_count < self.default_size:
            start_idx = 0
        else:
            start_idx = new_msg_count - self.default_size

        return list(self.target_start_set[start_idx:])

    def get_older_messages(self, params):
        ref_id = params['ref_id']
        size = params['size']
       
        if not ref_id:
            return self.redirect()

        ref_message_idx = self.get_message_index(ref_id, is_oldest=False)
        older_msg_count = self.target_end_set.count() - 1

        if older_msg_count <= size:
            start_idx = 0
            self.has_previous = False
        else:
            start_idx = older_msg_count - size
            self.has_previous = True

        return list(self.queryset[start_idx:ref_message_idx])

    def get_newer_messages(self, params):
        ref_id = params['ref_id']
        size = params['size']

        if not ref_id:
            return self.redirect()

        ref_message_idx = self.get_message_index(ref_id, is_oldest=True)
        newer_msg_count = self.target_start_set.count() - 1
        start_idx = ref_message_idx + 1

        if newer_msg_count <= size:
            end_idx = None
            self.has_next = False
        else:
            end_idx = start_idx + size
            self.has_next = True

        newer_messages = list(self.queryset[start_idx:end_idx])

        return newer_messages
        
    def get_message_index(self, message_id, is_oldest):
        target_message = self.queryset.get(pk=message_id)

        self.target_end_set = self.queryset.filter(
            time_stamp__lte=target_message.time_stamp,
        )

        if is_oldest:
            self.target_start_set = self.queryset.filter(
                time_stamp__gte=target_message.time_stamp,
            )

        return self.target_end_set.count() - 1

    def get_first_new_message_index(self):
        new_message_statuses = [
            Message.STATUS_SENT,
            Message.STATUS_DELIVERED
        ]

        target_message = self.queryset \
            .filter(delivery_status__in=new_message_statuses) \
            .exclude(sender=self.request.user) \
            .first()
        
        if target_message is None:
            self.target_end_set = self.queryset
            self.target_start_set = []

            return None
        
        self.target_end_set = self.queryset.filter(
            time_stamp__lte=target_message.time_stamp
        )
        self.target_start_set = self.queryset.filter(
            time_stamp__gte=target_message.time_stamp
        )

        count = self.count_set(self.target_end_set)
        return count - 1

    def count_set(self, iterable):
        if isinstance(iterable, QuerySet):
            return iterable.count()
        return len(iterable)
    
    def get_next_link(self, data):
        if not getattr(self, 'has_next', False):
            return None

        latest_message_data = data[-1]
        ref_id = latest_message_data['id']

        next_url = self.modify_query_params('newer', ref_id)
        return next_url
    
    def get_previous_link(self, data):
        if not getattr(self, 'has_previous', False):
            return None
        
        oldest_message_data = data[0]
        ref_id = oldest_message_data['id']
        
        previous_url = self.modify_query_params('older', ref_id)
        return previous_url

    def modify_query_params(self, category, ref_id):
        url = self.request.build_absolute_uri()

        size = self.request.query_params.get(self.size_param, None)
        if size is not None:
            url = remove_query_param(url, self.size_param)

        modified_url = url
        query_dict = {self.category_param: category, self.ref_param: ref_id}

        for key, value in query_dict.items():
            modified_url = replace_query_param(modified_url, key, value)

        return modified_url
    
    def redirect(self):
        self.category = self.default_category
        self.is_redirected = True

        return self.get_initial_messages()