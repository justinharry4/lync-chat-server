import datetime

from django.db import transaction
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from .models import (
    GroupChat, GroupChatAdmin, GroupChatParticipant, Message, Profile, ProfilePhoto,
    PrivateChat, PrivateChatParticipant, Chat, TextMessage, get_user_model
)
from .exceptions import ResourceLocked

class StrictUpdateModelSerializer(serializers.ModelSerializer):
    def is_model_field(self, field):
        model = self.Meta.model
        field_names = [
            f.name for f in model._meta.get_fields() if f.name != 'id'
        ]

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
    participants = PrivateChatParticipantSerializer(many=True, read_only=True)
    chats = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = PrivateChat
        fields = ['id', 'created_at', 'participants', 'chats']

class CreatePrivateChatSerializer(serializers.Serializer):
    participant_user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        min_length=1,
        max_length=2
    )

    def validate_participant_user_ids(self, user_ids):
        current_user = self.context['user']

        if len(user_ids) == 1:
            user_ids.append(current_user.id)

        if user_ids[0] == user_ids[1]:
            raise serializers.ValidationError(
                'a private chat must have 2 different participants.'
            )
        
        if current_user.id not in user_ids:
            raise serializers.ValidationError(
                'current user must be included as one of the '
                'participants for a two-item list'
            )
        
        user_model = get_user_model()
        other_id, = [id for id in user_ids if id != current_user.id]

        if not user_model.objects.filter(pk=other_id).exists():
            raise serializers.ValidationError(
                f'a user with id `{other_id}` was not found.'
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
    parent_id = serializers.ReadOnlyField(source='object_id')

    class Meta:
        model = Chat
        fields = [
            'id',
            'user',
            'created_at',
            'terminated_at',
            'parent_chat_type',
            'parent_id',
        ]

    def create(self, validated_data):
        user = self.context['user']
        model = self.context['parent_chat_model']
        parent_chat_id = self.context['parent_chat_id']
        parent_chat_type = self.context['parent_chat_type']
        content_type = ContentType.objects.get_for_model(model)

        queryset = Chat.objects.filter(
            user=user,
            terminated_at=None, 
            object_id=parent_chat_id,
            parent_chat_type=parent_chat_type,
        )
        
        if queryset.count() != 0:
            raise serializers.ValidationError(
                'an open chat belonging to the current user exists'
            )

        return Chat.objects.create(
            user=user,
            parent_chat_type=parent_chat_type,
            content_type=content_type,
            object_id=parent_chat_id,
            **validated_data
        )
    
    def update(self, instance, validated_data):
        if instance.terminated_at is not None:
            raise ResourceLocked(
                'The referenced chat has already been terminated'
            )
        
        instance.terminated_at = datetime.datetime.now()
        instance.save()

        return instance
    

# class UpdateChatSerializer(StrictUpdateModelSerializer):
#     class Meta:
#         model = Chat
#         fields = ['terminated_at']

#     def update(self, instance, validated_data):
#         if instance.terminated_at is not None:
#             raise ResourceLocked(
#                 '`terminated_at` field can only be updated once'
#             )
        
#         instance.terminated_at = datetime.datetime.now()
#         instance.save()

#         return instance


# group chat participant serializer
class GroupChatParticipantSerializer(serializers.ModelSerializer):
    group_chat = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = GroupChatParticipant
        fields = ['id', 'group_chat', 'user', 'date_joined']

    def create(self, validated_data):
        user = validated_data['user']
        group_chat_id = self.context['group_chat_id']
        group_chat = GroupChat.objects.get(pk=group_chat_id)

        if group_chat.participant_users.filter(id=user.id).exists():
            raise serializers.ValidationError(
                'the given user is already a participant in this group chat'
            )

        participant = GroupChatParticipant.objects.create(
            group_chat=group_chat,
            user=user
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
        user = validated_data['user']
        group_chat_id = self.context['group_chat_id']
        group_chat = GroupChat.objects.get(pk=group_chat_id)

        if not group_chat.participant_users.filter(id=user.id).exists():
            raise serializers.ValidationError(
                'the given user is not a participant in this group chat'
            )

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


class CreateGroupChatSerializer(serializers.Serializer):
    participant_user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        min_length=2,
        max_length=100
    )

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
        creator = self.context['user']
        user_ids = validated_data['participant_user_ids']
        
        try:
            user_ids.index(creator.id)
        except ValueError:
            user_ids.insert(0, creator.id)

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


# message serializers
class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.PrimaryKeyRelatedField(read_only=True)
    parent_chat_type = serializers.ReadOnlyField()
    delivery_status = serializers.ReadOnlyField()
    time_stamp = serializers.ReadOnlyField()
    deleted_at = serializers.ReadOnlyField()
    content = serializers.SerializerMethodField(method_name='get_content')

    class Meta:
        model = Message
        fields = [
            'id',
            'sender',
            'parent_id',
            'parent_chat_type',
            'content_format',
            'delivery_status',
            'time_stamp',
            'deleted_at',
            'content',
        ]

    def get_content(self, message: Message):
        if message.content_format == Message.FORMAT_TEXT:
            serializer_class = TextMessageSerializer
        
        content_object = message.content
        serializer = serializer_class(content_object)

        return serializer.data

    def create(self, validated_data):
        user = self.context['user']
        parent_model = self.context['parent_chat_model']
        parent_chat_type = self.context['parent_chat_type']

        content_type = ContentType.objects.get_for_model(parent_model)

        return Message.objects.create(
            sender=user,
            parent_content_type=content_type,
            parent_chat_type=parent_chat_type,
            **validated_data
        )
    

class UpdateMessageSerializer(StrictUpdateModelSerializer):
    class Meta:
        model = Message
        fields = ['delivery_status', 'time_stamp', 'deleted_at']

    def update(self, instance, validated_data):
        status_order = {'P': 0, 'S': 1, 'D': 2, 'V': 3}
        errors = {}

        status = validated_data.get('delivery_status')
        if status:
            current_status = instance.delivery_status
            # if status_order[current_status] > status_order[status]:
            if status_order[status] != (status_order[current_status] + 1):
                errors['delivery_status'] = 'invalid status update sequence'
        
        single_update_fields = ['time_stamp', 'deleted_at']

        for field in single_update_fields:
            if field in validated_data and getattr(instance, field):
                errors[field] = 'field can only be updated once'

        if errors:
            raise serializers.ValidationError(errors)

        return super().update(instance, validated_data)


class TextMessageSerializer(serializers.ModelSerializer):
    # message = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = TextMessage
        fields = ['id', 'text']