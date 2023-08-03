from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.conf import settings


def get_user_model():
    app_name, user_model_name = settings.AUTH_USER_MODEL.split('.')
    content_type = ContentType.objects.get(app_label=app_name, model=user_model_name)
    user_model = content_type.model_class()

    return user_model

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_online = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)


class ProfilePhoto(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='photo')
    image = models.ImageField(upload_to='chat/images')
    uploaded_at = models.DateTimeField(auto_now=True)


class Chat(models.Model):
    PARENT_CHAT_PRIVATE = 'PC'
    PARENT_CHAT_GROUP = 'GC'
    PARENT_CHAT_CHOICES = [
        (PARENT_CHAT_PRIVATE, 'PRIVATE CHAT'),
        (PARENT_CHAT_GROUP, 'GROUP CHAT')
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    terminated_at = models.DateTimeField(null=True)
    parent_chat_type = models.CharField(max_length=2, choices=PARENT_CHAT_CHOICES)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    parent_chat = GenericForeignKey()
    

class PrivateChat(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    chats = GenericRelation(Chat, related_query_name='private_chat')
    participant_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='PrivateChatParticipant',
        related_name='private_chats'
    )


class PrivateChatParticipant(models.Model):
    private_chat = models.ForeignKey(
        PrivateChat,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='private_chat_memberships'
    )
    

class GroupChat(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_groups'
    )
    chats = GenericRelation(Chat, related_query_name='group_chat')
    participant_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='GroupChatParticipant',
        related_name='group_chats'
    )
    admin_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='GroupChatAdmin',
    )

class GroupChatParticipant(models.Model):
    group_chat = models.ForeignKey(
        GroupChat,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='group_chat_memberships'
    )
    date_joined = models.DateTimeField(auto_now_add=True)


class GroupChatAdmin(models.Model):
    group_chat = models.ForeignKey(
        GroupChat,
        on_delete=models.CASCADE,
        related_name='admins'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    is_active = models.BooleanField(default=True)
    is_creator = models.BooleanField(default=False)


