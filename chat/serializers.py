from django.db import transaction
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from .models import (
    GroupChat, GroupChatAdmin, GroupChatParticipant, Profile, ProfilePhoto,
    PrivateChat, PrivateChatParticipant, Chat, get_user_model
)
from .exceptions import ResourceLocked

class StrictUpdateModelSerializer(serializers.ModelSerializer):
    def is_model_field(self, field):
        model = self.Meta.model
        field_names = [f.name for f in model._meta.get_fields() if f.name != 'id']

        return field in field_names
        

    def check_allowed_fields(self):
        errors = {}
        for field in self.initial_data:
            if field not in self.validated_data and self.is_model_field(field):
                errors[field] = 'field update is not allowed'
        
        self.strict_update_errors = errors
    
    def update(self, instance, validated_data):
        if len(self.validated_data) == 0:
            raise serializers.ValidationError(
                'at least one valid update field must be included'
            )
        
        self.check_allowed_fields()

        if self.strict_update_errors:
            raise serializers.ValidationError(self.strict_update_errors)

        return super().update(instance, validated_data)

    
# profile photo serializer
class ProfilePhotoSerializer(serializers.ModelSerializer):
    profile = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ProfilePhoto
        fields = ['id', 'image', 'profile', 'uploaded_at']

    def create(self, validated_data):
        profile_id = self.context['profile_id']

        profile = Profile.objects.get(pk=profile_id)
        if hasattr(profile, 'photo'):
            profile.photo.delete()

        return ProfilePhoto.objects.create(profile_id=profile_id, **validated_data)

# profile serializers
class ProfileSerializer(serializers.ModelSerializer):
    last_seen = serializers.ReadOnlyField()
    is_online = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    photo = ProfilePhotoSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = [
            'id',
            'user',
            'last_seen',
            'is_online',
            'is_active',
            'photo'
        ]

class UpdateProfileSerializer(StrictUpdateModelSerializer):
    class Meta:
        model = Profile
        fields = ['last_seen', 'is_online']

class UpdateStatusProfileSerializer(StrictUpdateModelSerializer):
    class Meta:
        model = Profile
        fields = ['is_active']


# private chat participant serializer
class PrivateChatParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivateChatParticipant
        fields = ['id', 'private_chat', 'user']


# private chat serializers
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
        
        return sorted(user_ids)
    
    def create(self, validated_data):
        user_ids = validated_data['participant_user_ids']
        users_tag = PrivateChat.generate_participants_tag(user_ids)

        with transaction.atomic():
            if PrivateChat.objects.filter(participant_users_tag=users_tag).exists():
                raise serializers.ValidationError(
                    'a private chat with the given participants already exists'
                )

            private_chat = PrivateChat.objects.create()
            
            participants = [
                PrivateChatParticipant(
                    private_chat=private_chat,
                    user_id=user_id
                ) for user_id in user_ids
            ]
            PrivateChatParticipant.objects.bulk_create(participants)

            private_chat.save()

        return private_chat


# chat serializers
class ChatSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    terminated_at = serializers.ReadOnlyField()
    parent_chat_type = serializers.ReadOnlyField()
    parent_chat = serializers.PrimaryKeyRelatedField(read_only=True)

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
    
    def get_parent_chat_model(self):
        parent_chat_type = self.context['parent_chat_type']

        if parent_chat_type == 'PC':
            return PrivateChat
        elif parent_chat_type == 'GC':
            return GroupChat

class UpdateChatSerializer(StrictUpdateModelSerializer):
    class Meta:
        model = Chat
        fields = ['terminated_at']

    def update(self, instance, validated_data):
        if instance.terminated_at is not None:
            raise ResourceLocked('terminated_at field cannot be updated')

        return super().update(instance, validated_data)


# group chat participant serializer
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


# group chat admin serilaizers
class GroupChatAdminSerializer(serializers.ModelSerializer):
    group_chat = serializers.PrimaryKeyRelatedField(read_only=True)
    is_active = serializers.ReadOnlyField()
    is_creator = serializers.ReadOnlyField()
    
    class Meta:
        model = GroupChatAdmin
        fields = ['id', 'group_chat', 'user', 'is_active', 'is_creator']

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
    
class UpdateGroupChatAdminSerializer(StrictUpdateModelSerializer):
    class Meta:
        model = GroupChatAdmin
        fields = ['is_active']

    
# group chat serializers
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
