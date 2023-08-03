from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework import mixins
from rest_framework.permissions import IsAdminUser, AllowAny, IsAuthenticated
from rest_framework.decorators import action

from .viewsets import (
    CustomWriteModelViewSet, CustomWriteNoUpdateModelViewSet, NoUpdateModelViewSet
)
from .models import (
    Profile, ProfilePhoto, PrivateChat, PrivateChatParticipant, Chat, GroupChat,
    GroupChatParticipant, GroupChatAdmin
)
from .serializers import (
    CreateGroupChatSerializer, GroupChatAdminSerializer, GroupChatParticipantSerializer,
    GroupChatSerializer, ChatSerializer, CreatePrivateChatSerializer, UpdateChatSerializer, UpdateGroupChatAdminSerializer, UpdateProfileSerializer,
    UpdateStatusProfileSerializer, PrivateChatParticipantSerializer, PrivateChatSerializer,
    ProfilePhotoSerializer, ProfileSerializer
)
from . import serializers as ser


class ProfileViewSet(CustomWriteModelViewSet):
    queryset = Profile.objects.prefetch_related('photo').all()
    http_method_names = ['get', 'post', 'patch', 'delete']
    retrieve_serializer_class = ProfileSerializer

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return UpdateProfileSerializer
        elif self.action == 'update_active_status':
            return UpdateStatusProfileSerializer
        return ProfileSerializer

    def get_permissions(self):
        if self.action in ['list', 'destroy', 'update_active_status']:
            return [IsAdminUser()]
        else: 
            return [AllowAny()]

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

    def get_queryset(self):
        profile_id = self.kwargs['profile_pk']
        return ProfilePhoto.objects.filter(profile_id=profile_id)
    
    # def get_permissions(self):
        # if self.action in ['list']:
        #     return [IsAdminUser()]
        # elif self.action == 'retrieve':
        #     photo_id = self.kwargs['pk']
        #     latest_photo = self.get_latest_photo()

        #     if latest_photo and str(latest_photo.id) != photo_id:
        #         return [IsAdminUser()]
        #     else:
        #         return [AllowAny()]
        # else:
        #     return [AllowAny()]
        
    def get_serializer_context(self):
        return {'profile_id': self.kwargs['profile_pk']}


class PrivateChatViewSet(CustomWriteNoUpdateModelViewSet):
    permission_classes = [IsAuthenticated]
    retrieve_serializer_class = PrivateChatSerializer
    # print(PrivateChat.objects.filter(participant_users_tag__contains='1'))
    # print(PrivateChat.objects.get(pk=11).get_participants_tag())

    def get_queryset(self):
        # from core.models import User
        # user = User.objects.get(pk=2)
        user = self.request.user
        if user.is_staff:             # private chat list should be private to users
            return PrivateChat.objects.all()

        return user.private_chats.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePrivateChatSerializer
        return PrivateChatSerializer
    

class PrivateChatParticipantViewSet(ReadOnlyModelViewSet):
    serializer_class = PrivateChatParticipantSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        private_chat_pk = self.kwargs['private_chat_pk']
        return PrivateChatParticipant.objects.filter(private_chat_id=private_chat_pk)


class ChatViewSet(CustomWriteModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    retrieve_serializer_class = ChatSerializer

    def get_queryset(self):
        ser_context = self.get_serializer_context()
        parent_type = ser_context['parent_chat_type']
        parent_chat_pk = ser_context['parent_chat_id']
        
        return Chat.objects.filter(
            object_id=parent_chat_pk,
            parent_chat_type=parent_type
        )

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return UpdateChatSerializer
        return ChatSerializer

    def get_serializer_context(self):
        if self.kwargs.get('private_chat_pk'):
            context = {
                'parent_chat_type': 'PC',
                'parent_chat_id': self.kwargs['private_chat_pk']
            }
        elif self.kwargs.get('group_chat_pk'):
            context = {
                'parent_chat_type': 'GC',
                'parent_chat_id': self.kwargs['group_chat_pk']
            }

        context['user'] = self.request.user
        return context


class GroupChatViewSet(CustomWriteNoUpdateModelViewSet):
    permission_classes = [IsAuthenticated]
    retrieve_serializer_class = GroupChatSerializer

    def get_queryset(self):
        # from core.models import User
        # user = User.objects.get(pk=2)
        user = self.request.user            # group chat list should be private to users
        if user.is_staff:
            return GroupChat.objects.all()

        return user.group_chats.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateGroupChatSerializer
        return GroupChatSerializer
    

class GroupChatParticipantViewSet(NoUpdateModelViewSet):
    serializer_class = GroupChatParticipantSerializer

    def get_queryset(self):
        group_chat_id = self.kwargs['group_chat_pk']
        return GroupChatParticipant.objects.filter(group_chat_id=group_chat_id)
    
    def get_serializer_context(self):
        context = {'group_chat_id': self.kwargs['group_chat_pk']}
        return context
    

class GroupChatAdminViewSet(CustomWriteModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    retrieve_serializer_class = GroupChatAdminSerializer

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

    