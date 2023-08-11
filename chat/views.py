from django.shortcuts import get_object_or_404
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from rest_framework.response import Response
from rest_framework import status
from rest_framework import mixins
from rest_framework.permissions import IsAdminUser, AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound

from .permissions import (
    IsAssociatedUser, IsGroupChatAdmin, IsGroupChatCreator,
    IsGroupChatMember, IsPrivateChatMember
)
from .viewsets import (
    ReadOnlyModelViewSet, NoUpdateModelViewSet, CustomWriteModelViewSet, 
    CustomWriteNoUpdateModelViewSet
)
from .models import (
    Profile, ProfilePhoto, PrivateChat, PrivateChatParticipant, Chat, GroupChat,
    GroupChatParticipant, GroupChatAdmin
)
from .serializers import (
    CreateGroupChatSerializer, GroupChatAdminSerializer, GroupChatParticipantSerializer,
    GroupChatSerializer, ChatSerializer, CreatePrivateChatSerializer, UpdateChatSerializer,
    UpdateGroupChatAdminSerializer, UpdateProfileSerializer, UpdateStatusProfileSerializer,
    PrivateChatParticipantSerializer, PrivateChatSerializer, ProfilePhotoSerializer,
    ProfileSerializer
)



def check_parent_existence(parent_model, parent_id_key, kwargs):
    parent_id = kwargs.get(parent_id_key)

    try:
        parent_model.objects.get(pk=parent_id)
    except parent_model.DoesNotExist:
        raise NotFound(
            f'parent {parent_model.__name__} with id `{parent_id}` was not found'
        )


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
    parent_model = Profile
    parent_url_lookup = 'profile_pk'

    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            profile_id = self.kwargs[self.parent_url_lookup]
            perms = [IsAssociatedUser(profile_id, Profile)]
        else:
            perms = [IsAuthenticated()]
 
        return perms

    def get_queryset(self):
        profile_id = self.kwargs[self.parent_url_lookup]
        return ProfilePhoto.objects.filter(profile_id=profile_id)
        
    def get_serializer_context(self):
        return {'profile_id': self.kwargs[self.parent_url_lookup]}


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
    

class PrivateChatParticipantViewSet(ReadOnlyModelViewSet):
    serializer_class = PrivateChatParticipantSerializer
    child = True
    parent_model = PrivateChat
    parent_url_lookup = 'private_chat_pk'

    def get_permissions(self):
        private_chat_id = self.kwargs[self.parent_url_lookup]
        return [IsPrivateChatMember(private_chat_id)]

    def get_queryset(self):
        private_chat_pk = self.kwargs[self.parent_url_lookup]
        return PrivateChatParticipant.objects.filter(private_chat_id=private_chat_pk)


class ChatViewSet(CustomWriteModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    retrieve_serializer_class = ChatSerializer
    child = True

    def get_permissions(self):
        parent_info = self.get_parent_info()

        if parent_info['parent_chat_type'] == 'PC':
            is_parent_chat_member = IsPrivateChatMember
        elif parent_info['parent_chat_type'] == 'GC':
            is_parent_chat_member = IsGroupChatMember

        parent_chat_id = parent_info['parent_chat_id']
        perms = [is_parent_chat_member(parent_chat_id)]

        if self.action in ['retrieve', 'partial_update']:
            perms.append(IsAssociatedUser(self.kwargs['pk']))
        elif self.action == 'destroy':
            perms = [IsAdminUser()]

        return perms

    def get_parent_model(self):
        parent_info = self.get_parent_info()
        return parent_info['parent_chat_model']
    
    def get_parent_url_lookup(self):
        parent_info = self.get_parent_info()
        return parent_info['parent_chat_lookup']

    def get_queryset(self):
        parent_info = self.get_parent_info()
        parent_chat_type = parent_info['parent_chat_type']
        parent_chat_id = parent_info['parent_chat_id']
        
        return Chat.objects.filter(
            user=self.request.user,
            object_id=parent_chat_id,
            parent_chat_type=parent_chat_type
        )

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return UpdateChatSerializer
        return ChatSerializer
    
    def get_serializer_context(self):
        parent_info = self.get_parent_info()
        return {'user': self.request.user, **parent_info}
    
    def get_parent_info(self):
        if hasattr(self, 'parent_info'):
            return self.parent_info

        pc_lookup = 'private_chat_pk'
        gc_lookup = 'group_chat_pk'

        private_chat_id = self.kwargs.get(pc_lookup)
        group_chat_id = self.kwargs.get(gc_lookup)

        if private_chat_id:
            props = (PrivateChat, pc_lookup, 'PC')
        elif group_chat_id:
            props = (GroupChat, gc_lookup, 'GC')

        info_dict = {
            'parent_chat_model': props[0],
            'parent_chat_lookup': props[1],
            'parent_chat_type': props[2]
        }
        
        info_dict['parent_chat_id'] = private_chat_id or group_chat_id
        self.parent_info = info_dict

        return self.parent_info
    

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
    

class GroupChatParticipantViewSet(NoUpdateModelViewSet):
    serializer_class = GroupChatParticipantSerializer
    child = True
    parent_model = GroupChat
    parent_url_lookup = 'group_chat_pk'

    def get_permissions(self):
        group_chat_id = self.kwargs[self.parent_url_lookup]

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
        group_chat_id = self.kwargs[self.parent_url_lookup]
        return GroupChatParticipant.objects.filter(group_chat_id=group_chat_id)
    
    def get_serializer_context(self):
        context = {'group_chat_id': self.kwargs[self.parent_url_lookup]}
        return context
    

class GroupChatAdminViewSet(CustomWriteModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    retrieve_serializer_class = GroupChatAdminSerializer
    child = True
    parent_model = GroupChat
    parent_url_lookup = 'group_chat_pk'

    def get_permissions(self):
        group_chat_id = self.kwargs[self.parent_url_lookup]

        if self.action in ['list', 'retrieve']:
            perms = [IsGroupChatMember(group_chat_id)]
        else:
            perms = [IsGroupChatCreator(group_chat_id)]

        return perms

    def get_queryset(self):
        group_chat_id = self.kwargs['group_chat_pk']
        return GroupChatAdmin.objects.filter(group_chat_id=group_chat_id)

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return UpdateGroupChatAdminSerializer
        return GroupChatAdminSerializer
    
    def get_serializer_context(self):
        context = {'group_chat_id': self.kwargs['group_chat_pk']}
        return context

    