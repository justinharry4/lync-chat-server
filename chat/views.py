from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework import mixins
from rest_framework.permissions import IsAdminUser, AllowAny, IsAuthenticated
from rest_framework.decorators import action

from .viewsets import CustomWriteModelViewSet, CustomWriteNoUpdateModelViewSet, NoUpdateModelViewSet
from .models import (Profile,
                     ProfilePhoto,
                     PrivateChat,
                     PrivateChatParticipant,
                     Chat,
                     GroupChat,
                     GroupChatParticipant,
                     GroupChatAdmin)
from .serializers import (CreateGroupChatSerializer, GroupChatAdminSerializer, GroupChatParticipantSerializer, GroupChatSerializer,
                          ChatSerializer,
                          CreatePrivateChatSerializer,
                          UpdateStatusProfileSerializer,
                          PrivateChatParticipantSerializer,
                          PrivateChatSerializer,
                          ProfilePhotoSerializer,
                          ProfileSerializer)
from . import serializers as ser


class ProfileViewSet(CustomWriteModelViewSet):
    queryset = Profile.objects.prefetch_related('photos').all()
    http_method_names = ['get', 'post', 'patch', 'delete']
    retrieve_serializer_class = ser.ProfileSerializer

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return ser.UpdateProfileSerializer
        elif self.action == 'update_active_status':
            return ser.UpdateStatusProfileSerializer
        return ser.ProfileSerializer

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

        ret_serializer = ser.ProfileSerializer(mod_profile)
        return Response(ret_serializer.data, status=status.HTTP_200_OK)
    



class ProfilePhotoViewSet(NoUpdateModelViewSet):
    serializer_class = ProfilePhotoSerializer

    def get_queryset(self):
        profile_id = self.kwargs['profile_pk']
        return ProfilePhoto.objects.filter(profile_id=profile_id).select_related('profile')
    
    def get_permissions(self):
        if self.action in ['list']:
            return [IsAdminUser()]
        elif self.action == 'retrieve':
            photo_id = self.kwargs['pk']
            latest_photo = self.get_latest_photo()

            if latest_photo and str(latest_photo.id) != photo_id:
                return [IsAdminUser()]
            else:
                return [AllowAny()]
        else:
            return [AllowAny()]
        
    def get_serializer_context(self):
        return {'profile_id': self.kwargs['profile_pk']}
        
    def get_latest_photo(self):
        profile_id = self.kwargs['profile_pk']

        latest_photo = ProfilePhoto.objects \
            .filter(profile_id=profile_id) \
            .order_by('uploaded_at') \
            .reverse() \
            .first()
        
        return latest_photo

    def perform_create(self, serializer: ProfilePhotoSerializer):
        profile_id = self.kwargs['profile_pk']
        profile = get_object_or_404(Profile, pk=profile_id)
        
        if profile.is_photo_removed:
            profile.is_photo_removed = False
            profile.save()

        serializer.save()

    def perform_destroy(self, instance: ProfilePhoto):
        latest_photo = self.get_latest_photo()

        if latest_photo.id == instance.id:
            instance.profile.is_photo_removed = True
            instance.profile.save()
        
        instance.delete()


class PrivateChatViewSet(NoUpdateModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # from core.models import User
        # user = User.objects.get(pk=2)
        user = self.request.user
        if user.is_staff:
            return PrivateChat.objects.all()

        return user.private_chats.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePrivateChatSerializer
        return PrivateChatSerializer
    
    def create(self, request, *args, **kwargs):
        create_serializer = CreatePrivateChatSerializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        private_chat = create_serializer.save()

        return_serializer = PrivateChatSerializer(private_chat)
        return Response(return_serializer.data, status=status.HTTP_201_CREATED)
    

class PrivateChatParticipantViewSet(ReadOnlyModelViewSet):
    serializer_class = PrivateChatParticipantSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        private_chat_pk = self.kwargs['private_chat_pk']
        return PrivateChatParticipant.objects.filter(private_chat_id=private_chat_pk)


class ChatViewSet(ModelViewSet):
    serializer_class = ChatSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        parent_type = self.get_serializer_context()['parent_chat_type']
        parent_chat_pk = self.get_serializer_context()['parent_chat_id']
        
        return Chat.objects.filter(
            object_id=parent_chat_pk,
            parent_chat_type=parent_type
        )

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


class GroupChatViewSet(NoUpdateModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # from core.models import User
        # user = User.objects.get(pk=2)
        user = self.request.user
        if user.is_staff:
            return GroupChat.objects.all()

        return user.group_chats.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateGroupChatSerializer
        return GroupChatSerializer
    
    def create(self, request, *args, **kwargs):
        create_serializer = CreateGroupChatSerializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        group_chat = create_serializer.save()

        return_serializer = GroupChatSerializer(group_chat)
        return Response(return_serializer.data, status=status.HTTP_201_CREATED)
    

class GroupChatParticipantViewSet(NoUpdateModelViewSet):
    serializer_class = GroupChatParticipantSerializer

    def get_queryset(self):
        group_chat_id = self.kwargs['group_chat_pk']
        return GroupChatParticipant.objects.filter(group_chat_id=group_chat_id)
    
    def get_serializer_context(self):
        context = {'group_chat_id': self.kwargs['group_chat_pk']}
        return context
    

class GroupChatAdminViewSet(ModelViewSet):
    serializer_class = GroupChatAdminSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        group_chat_id = self.kwargs['group_chat_pk']
        return GroupChatAdmin.objects.filter(group_chat_id=group_chat_id)
    
    def get_serializer_context(self):
        context = {'group_chat_id': self.kwargs['group_chat_pk']}
        return context

    