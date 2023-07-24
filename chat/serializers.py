from django.db import transaction
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from .models import Profile, ProfilePhoto, PrivateChat, PrivateChatParticipant, Chat


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

    class Meta:
        model = PrivateChat
        fields = ['id', 'created_at', 'participants']


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
        
        app_name, user_model_name = settings.AUTH_USER_MODEL.split('.')
        content_type = ContentType.objects.get(app_label=app_name, model=user_model_name)
        user_model = content_type.model_class()

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


class ChatSerializer(serializers.ModelSerializer):
    termination_date = serializers.ReadOnlyField()
    last_active = serializers.ReadOnlyField()
    parent_chat = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = [
            'id',
            'created_at',
            'termination_date',
            'last_active',
            'parent_chat_type',
            'parent_chat',
        ]

    # def validate_parent_chat_id(self, parent_chat_id):
    #     model = self.get_parent_chat_model()
    #     print(model.objects.all())
    #     if not model.objects.filter(pk=parent_chat_id).exists():
    #         raise serializers.ValidationError(
    #             f'A {model.__name__} object with id `{parent_chat_id}` does not exist'
    #         )
        
    #     return parent_chat_id

    def create(self, validated_data):
        parent_chat_id = self.context['parent_chat_id']
        model = self.get_parent_chat_model()
        content_type = ContentType.objects.get_for_model(model)

        if not model.objects.filter(pk=parent_chat_id).exists():
            raise serializers.ValidationError(
                f'A {model.__name__} object with id `{parent_chat_id}` does not exist'
            )

        return Chat.objects.create(
            content_type=content_type,
            object_id=parent_chat_id,
            **validated_data
        )
    
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

