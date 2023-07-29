from django.db import transaction
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from .models import GroupChat, GroupChatAdmin, GroupChatParticipant, get_user_model, Profile, ProfilePhoto, PrivateChat, PrivateChatParticipant, Chat


class StrictUpdateModelSerializer(serializers.ModelSerializer):
    class CustomMeta:
        pass

    def get_update_fields(self):
        try:
            fields = self.CustomMeta.update_fields
            if not len(fields) > 0:
                raise ValueError(
                    'CustomMeta.update_fields must be a non-empty list'
                )
        except AttributeError:
            raise ValueError(
                'update_fields attribute on CustomMeta must be provided '
                'as a non-empty list.'
            )
        
        return fields
    
    def update(self, instance, validated_data):
        update_fields = self.get_update_fields()

        for attr in validated_data:
            if attr not in update_fields:
                raise serializers.ValidationError(
                    f'`{attr}` field update is not allowed.'
                )

        return super().update(instance, validated_data)

    

class ProfilePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfilePhoto
        fields = ['id', 'image', 'uploaded_at']

    def create(self, validated_data):
        profile_id = self.context['profile_id']
        photo = ProfilePhoto.objects.create(profile_id=profile_id, **validated_data)

        return photo


class ProfileSerializer(serializers.ModelSerializer):
    photos = ProfilePhotoSerializer(many=True, read_only=True)
    is_active = serializers.ReadOnlyField()
    latest_photo = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'id',
            'user',
            'last_seen',
            'is_online',
            'is_active',
            'is_photo_removed',
            'photos',
            'latest_photo'
        ]

    def get_latest_photo(self, profile):
        sort_key = lambda p: p.uploaded_at
        sorted_photos = sorted(profile.photos.all(), key=sort_key, reverse=True)

        if len(sorted_photos) > 0:
            return sorted_photos[0].id
        

class ModifyProfileStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['is_active']


class PrivateChatParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivateChatParticipant
        fields = ['id', 'private_chat', 'user']


class PrivateChatSerializer(serializers.ModelSerializer):
    participants = PrivateChatParticipantSerializer(many=True)
    chats = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = PrivateChat
        fields = ['id', 'created_at', 'participants', 'chats']


class CreatePrivateChatSerializer(serializers.Serializer):
    participant_user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        min_length=2,
        max_length=2
    )

    def validate_participant_user_ids(self, user_ids):
        id1, id2 = user_ids

        if id1 == id2:
            raise serializers.ValidationError(
                'a private chat must have 2 different participants.'
            )
        
        user_model = get_user_model()

        for user_id in user_ids:
            if not user_model.objects.filter(pk=user_id).exists():
                raise serializers.ValidationError(
                    f'a user with id `{user_id}` was not found.'
                )
        
        return user_ids
    
    def create(self, validated_data):
        with transaction.atomic():
            print(validated_data)
            user_ids = validated_data['participant_user_ids']

            private_chat = PrivateChat.objects.create()
            
            for user_id in user_ids:
                PrivateChatParticipant.objects.create(
                    private_chat=private_chat,
                    user_id=user_id
                )

        return private_chat


class ChatSerializer(StrictUpdateModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    parent_chat_type = serializers.ReadOnlyField()
    parent_chat = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = [
            'id',
            'user',
            'created_at',
            'terminated_at',
            'parent_chat_type',
            'parent_chat',
        ]

    class CustomMeta:
        update_fields = ['terminated_at']

    def create(self, validated_data):
        user = self.validate_user(self.context['user'])

        parent_chat_id = self.context['parent_chat_id']
        model = self.get_parent_chat_model()
        content_type = ContentType.objects.get_for_model(model)

        if not model.objects.filter(pk=parent_chat_id).exists():
            raise serializers.ValidationError(
                f'A {model.__name__} object with id `{parent_chat_id}` does not exist'
            )

        return Chat.objects.create(
            user=user,
            parent_chat_type=self.context['parent_chat_type'],
            content_type=content_type,
            object_id=parent_chat_id,
            **validated_data
        )

    def validate_user(self, user):
        parent_model = self.get_parent_chat_model()
        parent_chat_id = self.context['parent_chat_id']
        parent_chat = parent_model.objects.get(pk=parent_chat_id)

        if not parent_chat.participant_users.filter(pk=user.id).exists():
            raise serializers.ValidationError(
                f'{parent_model.__name__} object with id `{parent_chat_id}` '
                f'does not have the current user as one of its participants'
            )
        
        return user
    
    def get_parent_chat(self, chat):
        if self.context['parent_chat_type'] == 'PC':
            parent_chat_serializer = PrivateChatSerializer(chat.parent_chat)
            return parent_chat_serializer.data
        else: pass
    
    def get_parent_chat_model(self):
        parent_chat_type = self.context['parent_chat_type']

        if parent_chat_type == 'PC':
            return PrivateChat
        elif parent_chat_type == 'GC':
            return 'GroupChat'
        

class GroupChatParticipantSerializer(serializers.ModelSerializer):
    group_chat = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = GroupChatParticipant
        fields = ['id', 'group_chat', 'user', 'date_joined']

    def create(self, validated_data):
        group_chat_id = self.context['group_chat_id']
        user = validated_data['user']
        group_chat = GroupChat.objects.get(pk=group_chat_id)

        if group_chat.participant_users.filter(id=user.id).exists():
            raise serializers.ValidationError(
                'the given user is already a participant in this group chat'
            )

        participant = GroupChatParticipant.objects.create(
            group_chat=group_chat,
            user=validated_data['user']
        )

        return participant


class GroupChatAdminSerializer(StrictUpdateModelSerializer):
    group_chat = serializers.PrimaryKeyRelatedField(read_only=True)
    is_creator = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = GroupChatAdmin
        fields = ['id', 'group_chat', 'user', 'is_active', 'is_creator']
    
    class CustomMeta:
        update_fields = ['is_active']

    def create(self, validated_data):
        group_chat_id = self.context['group_chat_id']
        user = validated_data['user']
        group_chat = GroupChat.objects.get(pk=group_chat_id)

        if group_chat.admin_users.filter(id=user.id).exists():
            raise serializers.ValidationError(
                'the given user is already an admin in this group chat'
            )
        
        admin = GroupChatAdmin.objects.create(
            group_chat=group_chat,
            user=user
        )

        return admin
    

class GroupChatSerializer(serializers.ModelSerializer):
    participants = GroupChatParticipantSerializer(many=True, read_only=True)
    admins = GroupChatAdminSerializer(many=True, read_only=True)
    chats = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = GroupChat
        fields = ['id', 'created_at', 'creator', 'participants', 'admins', 'chats']


class CreateGroupChatSerializer(serializers.ModelSerializer):
    participant_user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        min_length=2,
        max_length=100
    )

    class Meta:
        model = GroupChat
        fields = ['creator', 'participant_user_ids']

    def validate_participant_user_ids(self, user_ids):
        unique_ids = set(user_ids)
        
        if len(user_ids) != len(unique_ids):
            raise serializers.ValidationError(
                'a group chat must have unique paricipants'
            )
        
        user_model = get_user_model()

        queryset = user_model.objects.filter(pk__in=unique_ids)
        if queryset.count() != len(unique_ids):
            raise serializers.ValidationError(
                'id list contains id(s) of non-existent user(s)'
            )

        return list(unique_ids)
    
    def create(self, validated_data):
        user_ids = validated_data['participant_user_ids']
        creator = validated_data['creator']
        
        try:
            creator_id = creator.id
            user_ids.index(creator_id)
        except ValueError:
            user_ids.insert(0, creator_id)

        with transaction.atomic():
            group_chat = GroupChat.objects.create(creator=creator)
            participants = [
                GroupChatParticipant(
                    group_chat=group_chat,
                    user_id=user_id
                ) for user_id in user_ids
            ]
            GroupChatParticipant.objects.bulk_create(participants)

            GroupChatAdmin.objects.create(
                group_chat=group_chat,
                user=creator,
                is_creator=True
            )

        return group_chat
