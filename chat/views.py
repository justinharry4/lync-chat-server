from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser, AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound

from .permissions import (
    IsAssociatedUser, IsGroupChatAdmin, IsGroupChatCreator,
    IsGroupChatMember, IsPrivateChatMember
)
from .viewsets import (
    ReadOnlyModelViewSet, NoUpdateModelViewSet,
    CustomWriteModelViewSet, CustomWriteNoUpdateModelViewSet
)
from .models import (
    Message, Profile, ProfilePhoto, PrivateChat, PrivateChatParticipant,
    Chat, GroupChat, GroupChatParticipant, GroupChatAdmin
)
from .serializers import (
    CreateGroupChatSerializer, GroupChatAdminSerializer,
    GroupChatParticipantSerializer, GroupChatSerializer,
    ChatSerializer, CreatePrivateChatSerializer, MessageSerializer,
    UpdateGroupChatAdminSerializer, UpdateMessageSerializer,
    UpdateProfileSerializer, UpdateStatusProfileSerializer,
    PrivateChatParticipantSerializer, PrivateChatSerializer,
    ProfilePhotoSerializer, ProfileSerializer
)
from .exceptions import ResourceLocked
from .pagination import MessagePagination


class ProfileViewSet(CustomWriteModelViewSet):
    queryset = Profile.objects.prefetch_related('photo').all()
    http_method_names = ['get', 'post', 'patch', 'delete']
    retrieve_serializer_class = ProfileSerializer

    def get_permissions(self):
        if self.action == 'retrieve':
            perms = [IsAuthenticated()]
        elif self.action == 'create':
            perms = [AllowAny()]
        elif self.action == 'partial_update':
            perms = [IsAssociatedUser(self.kwargs['pk'])]
        else:
            perms = [IsAdminUser()]
        
        return perms

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return UpdateProfileSerializer
        elif self.action == 'update_active_status':
            return UpdateStatusProfileSerializer
        return ProfileSerializer

    @action(detail=True, url_path='status', methods=['PATCH'])
    def update_active_status(self, request, pk):
        profile = get_object_or_404(Profile, pk=pk)
        serializer = UpdateStatusProfileSerializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        mod_profile = serializer.save()

        ret_serializer = ProfileSerializer(mod_profile)
        return Response(ret_serializer.data, status=status.HTTP_200_OK)


class ProfilePhotoViewSet(NoUpdateModelViewSet):
    serializer_class = ProfilePhotoSerializer
    child = True
    parent_models = [Profile]
    parent_url_lookups = ['profile_pk']

    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            profile_id = self.kwargs[self.parent_url_lookups[0]]
            perms = [IsAssociatedUser(profile_id, Profile)]
        else:
            perms = [IsAuthenticated()]
 
        return perms

    def get_queryset(self):
        profile_id = self.kwargs[self.parent_url_lookups[0]]
        return ProfilePhoto.objects.filter(profile_id=profile_id)
        
    def get_serializer_context(self):
        return {'profile_id': self.kwargs[self.parent_url_lookups[0]]}


class PrivateChatViewSet(CustomWriteNoUpdateModelViewSet):
    retrieve_serializer_class = PrivateChatSerializer

    def get_permissions(self):
        if self.action == 'retrieve':
            id = self.kwargs['pk']
            perms = [IsPrivateChatMember(id)]
        elif self.action == 'destroy':
            perms = [IsAdminUser()]
        else:
            perms = [IsAuthenticated()]

        return perms

    def get_queryset(self):
        return self.request.user.private_chats.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePrivateChatSerializer
        return PrivateChatSerializer
    
    def get_serializer_context(self):
        return {'user': self.request.user}
    

class PrivateChatParticipantViewSet(ReadOnlyModelViewSet):
    serializer_class = PrivateChatParticipantSerializer
    child = True
    parent_models = [PrivateChat]
    parent_url_lookups = ['private_chat_pk']

    def get_permissions(self):
        private_chat_id = self.kwargs[self.parent_url_lookups[0]]
        return [IsPrivateChatMember(private_chat_id)]

    def get_queryset(self):
        private_chat_pk = self.kwargs[self.parent_url_lookups[0]]
        return PrivateChatParticipant.objects.filter(private_chat_id=private_chat_pk)
    

class GroupChatViewSet(CustomWriteNoUpdateModelViewSet):
    retrieve_serializer_class = GroupChatSerializer

    def get_permissions(self):
        if self.action == 'retrieve':
            group_chat_id = self.kwargs['pk']
            perms = [IsGroupChatMember(group_chat_id)]
        elif self.action == 'destroy':
            perms = [IsAdminUser()]
        else:
            perms = [IsAuthenticated()]
        
        return perms

    def get_queryset(self):   
        return self.request.user.group_chats.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateGroupChatSerializer
        return GroupChatSerializer
    
    def get_serializer_context(self):
        return {'user': self.request.user}
    

class GroupChatParticipantViewSet(NoUpdateModelViewSet):
    serializer_class = GroupChatParticipantSerializer
    child = True
    parent_models = [GroupChat]
    parent_url_lookups = ['group_chat_pk']

    def get_permissions(self):
        group_chat_id = self.kwargs[self.parent_url_lookups[0]]

        if self.action == 'create':
            perms = [IsGroupChatAdmin(group_chat_id)]
        elif self.action == 'destroy':
            is_participant_user = (
                IsGroupChatMember(group_chat_id) &
                IsAssociatedUser(self.kwargs['pk'])
            )
            perms = [
                is_participant_user |
                IsGroupChatAdmin(group_chat_id)
            ]
        else:
            perms = [IsGroupChatMember(group_chat_id)]

        return perms

    def get_queryset(self):
        group_chat_id = self.kwargs[self.parent_url_lookups[0]]
        return GroupChatParticipant.objects.filter(group_chat_id=group_chat_id)
    
    def get_serializer_context(self):
        context = {'group_chat_id': self.kwargs[self.parent_url_lookups[0]]}
        return context
    

class GroupChatAdminViewSet(CustomWriteModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    retrieve_serializer_class = GroupChatAdminSerializer
    child = True
    parent_models = [GroupChat]
    parent_url_lookups = ['group_chat_pk']

    def get_permissions(self):
        group_chat_id = self.kwargs[self.parent_url_lookups[0]]

        if self.action in ['list', 'retrieve']:
            perms = [IsGroupChatMember(group_chat_id)]
        else:
            perms = [IsGroupChatCreator(group_chat_id)]

        return perms

    def get_queryset(self):
        group_chat_id = self.kwargs[self.parent_url_lookups[0]]
        return GroupChatAdmin.objects.filter(group_chat_id=group_chat_id)

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return UpdateGroupChatAdminSerializer
        return GroupChatAdminSerializer
    
    def get_serializer_context(self):
        context = {'group_chat_id': self.kwargs[self.parent_url_lookups[0]]}
        return context
    

class BaseChatViewSet(CustomWriteModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    serializer_class = ChatSerializer
    retrieve_serializer_class = ChatSerializer
    child = True

    def get_permissions(self):
        parent_info = self.get_parent_info()
        parent_chat_perm = parent_info['parent_chat_perm']
        parent_chat_id = self.kwargs[self.parent_url_lookups[0]]

        perms = [parent_chat_perm(parent_chat_id)]

        if self.action in ['retrieve', 'partial_update']:
            perms.append(IsAssociatedUser(self.kwargs['pk']))
        elif self.action == 'destroy':
            perms = [IsAdminUser()]

        return perms
    
    def get_queryset(self):
        parent_info = self.get_parent_info()
        parent_chat_type = parent_info['parent_chat_type']
        parent_chat_id = self.kwargs[self.parent_url_lookups[0]]
        
        return Chat.objects.filter(
            user=self.request.user,
            object_id=parent_chat_id,
            parent_chat_type=parent_chat_type
        )
    
    def get_serializer_context(self):
        parent_info = self.get_parent_info()

        return {
            'user': self.request.user,
            'parent_chat_model': self.parent_models[0],
            'parent_chat_type': parent_info['parent_chat_type'],
            'parent_chat_id': self.kwargs[self.parent_url_lookups[0]]
        }

    @action(detail=False, url_path='current', methods=['GET'])
    def get_current_chat(self, request, private_chat_pk):
        queryset = self.get_queryset()
        current_chat = queryset.filter(terminated_at=None).first()
        serializer = ChatSerializer(current_chat)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
    

class PCChatViewSet(BaseChatViewSet):
    parent_models = [PrivateChat]
    parent_url_lookups = ['private_chat_pk']
    
    def get_parent_info(self):
        return {
            'parent_chat_type': 'PC',
            'parent_chat_perm': IsPrivateChatMember
        }


class GCChatViewSet(BaseChatViewSet):
    parent_models = [GroupChat]
    parent_url_lookups = ['group_chat_pk']

    def get_parent_info(self):
        return {
            'parent_chat_type': 'GC',
            'parent_chat_perm': IsGroupChatMember
        }


class BaseMessageViewSet(ReadOnlyModelViewSet):
    child = True
    # retrieve_serializer_class = MessageSerializer
    # http_method_names = ['get', 'post', 'patch', 'delete']
    pagination_class = MessagePagination

    def get_permissions(self):
        parent_info = self.get_parent_info()
        parent_chat_perm = parent_info['parent_chat_perm']
        parent_chat_id = self.kwargs[self.parent_url_lookups[0]]
        chat_id = self.kwargs[self.parent_url_lookups[1]]

        return [
            parent_chat_perm(parent_chat_id),
            IsAssociatedUser(chat_id, Chat)
        ]

    def get_queryset(self):
        parent_info = self.get_parent_info()
        parent_chat_type = parent_info['parent_chat_type']
        parent_id = self.kwargs[self.parent_url_lookups[0]]
        chat_id = self.kwargs[self.parent_url_lookups[1]]

        # if not Chat.objects.filter(
        #     pk=chat_id,
        #     object_id=parent_id,
        #     parent_chat_type=parent_chat_type
        # ).exists():
        #     parent_model = self.parent_models[0]

        #     raise NotFound(
        #         f'{parent_model.__name__} of id `{parent_id}` '
        #         f'has no child Chat of id `{chat_id}`'
        #     )

        chat = Chat.objects.get(pk=chat_id)
        
        if not (chat.object_id == int(parent_id) and 
            chat.parent_chat_type == parent_chat_type
        ):
            parent_model = self.parent_models[0]

            raise NotFound(
                f'{parent_model.__name__} of id `{parent_id}` '
                f'has no child Chat of id `{chat_id}`'
            )
        
        # debug code
        # query_dict = {
        #     'parent_id': parent_id,
        #     'parent_chat_type': parent_chat_type,
        #     'time_stamp__gte': chat.created_at,
        #     'deleted_at': None
        # }

        if chat.terminated_at is not None:
            # debug code
            # query_dict['time_stamp__lte'] = chat.terminated_at

            # dev code
            raise ResourceLocked(
                'The referenced Chat has been terminated'
            )

        # debug code
        # return Message.objects.filter(**query_dict)

        allowed_statuses = [
            Message.STATUS_SENT,
            Message.STATUS_DELIVERED,
            Message.STATUS_VIEWED
        ]

        # dev code
        return Message.objects.filter(
            parent_id=parent_id,
            parent_chat_type=parent_chat_type,
            time_stamp__gte=chat.created_at,
            delivery_status__in=allowed_statuses,
            deleted_at=None,
        )
    
    def get_serializer_class(self):
        # if self.action == 'partial_update':
        #     return UpdateMessageSerializer
        return MessageSerializer

    def get_serializer_context(self):
        parent_info = self.get_parent_info()

        return {
            'user': self.request.user,
            'parent_chat_model': self.parent_models[0],
            'parent_chat_type': parent_info['parent_chat_type']
        }
    

class PrivateChatMessageViewSet(BaseMessageViewSet):
    parent_models = [PrivateChat, Chat]
    parent_url_lookups = ['private_chat_pk', 'chat_pk']

    def get_parent_info(self):
        return {
            'parent_chat_type': 'PC',
            'parent_chat_perm': IsPrivateChatMember
        }
    

class GroupChatMessageViewSet(BaseMessageViewSet):
    parent_models = [GroupChat, Chat]
    parent_url_lookups = ['group_chat_pk', 'chat_pk']

    def get_parent_info(self):
        return {
            'parent_chat_type': 'GC',
            'parent_chat_perm': IsGroupChatMember
        }