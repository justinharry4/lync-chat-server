from collections import OrderedDict

from django.db.models.query import QuerySet

from rest_framework.pagination import CursorPagination, BasePagination
from rest_framework.response import Response

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

    def paginate_queryset(self, queryset, request, view=None):
        category = self.get_category(request)
        size = self.get_size(request)
        self.initial_queryset = queryset
        ordered_queryset = queryset.order_by('time_stamp')

        if category == 'initial':
            self.paginated_set = self.get_initial_messages(ordered_queryset, request)
        
        return self.paginated_set
        
    def get_paginated_response(self, data):
        return Response(data=OrderedDict([
            ('result_count', len(data)),
            ('unread_count', self.count_set(self.target_start_set)),
            # ('next', self.get_next_link())
            # ('previous', self.get_previous_link())
            ('total_count', self.count_set(self.initial_queryset)),
            ('results', data),
        ]))

    def get_category(self, request):
        valid_categories = ['initial', 'older', 'newer', 'unread']
        category = request.query_params.get(
            self.category_param,
            self.default_category
        )

        if category not in valid_categories:
            return self.default_category
        return category

    def get_size(self, request):
        size = request.query_params.get(
            self.size_param,
            self.default_size
        )

        try:
            if int(size) > self.max_size:
                return self.max_size
        except (ValueError, TypeError):
            return self.default_size

    def get_initial_messages(self, queryset, request):
        middle_idx = self.get_first_new_message_index(queryset, request)

        count = self.count_set(self.target_end_set)
        if middle_idx is None:
            old_msg_count = count
        else:
            old_msg_count = count - 1

        new_msg_count = self.count_set(self.target_start_set)

        if old_msg_count < self.default_size:
            start_idx = 0
        else:
            start_idx = old_msg_count - self.default_size # or: middle_idx - self.default_size - 1

        if new_msg_count < self.default_size:
            end_idx = None
        else:
            end_idx = middle_idx + self.default_size

        return list(queryset[start_idx:end_idx])
    
    def get_unread_messages(self, queryset, request):
        target_index = self.get_first_new_message_index(queryset, request)

        if target_index is None:
            return []
        
        new_msg_count = self.count_set(self.target_start_set)

        if new_msg_count < self.default_size:
            pass

    def get_first_new_message_index(self, queryset, request):
        new_message_statuses = [
            Message.STATUS_SENT,
            Message.STATUS_DELIVERED
        ]

        target_message = queryset \
            .filter(delivery_status__in=new_message_statuses) \
            .exclude(sender=request.user) \
            .first()
        
        if target_message is None:
            self.target_end_set = queryset
            self.target_start_set = []

            return None
        
        self.target_end_set = queryset.filter(
            time_stamp__lte=target_message.time_stamp
        )
        self.target_start_set = queryset.filter(
            time_stamp__gte=target_message.time_stamp
        )

        count = self.count_set(self.target_end_set)
        return count - 1

        # if target_message:
        #     self.target_end_set = queryset.filter(
        #         time_stamp__lte=target_message.time_stamp
        #     )
        #     self.target_start_set = queryset.filter(
        #         time_stamp__gte=target_message.time_stamp
        #     )
        # else:
        #     self.target_end_set = queryset
        #     self.target_start_set = []
        
        # count = self.count_set(self.target_end_set)
        # if target_message is None:
        #     return None 
        
        # return count - 1

    def count_set(self, iterable):
        if isinstance(iterable, QuerySet):
            return iterable.count()
        return len(iterable)