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
    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
        related_name='photo'
    )
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
    participant_users_tag = models.CharField(max_length=100, null=True)
    messages = GenericRelation('Message', related_query_name='private_chat')

    @classmethod
    def generate_participants_tag(cls, user_ids):
        str_ids = [str(user_id) for user_id in user_ids]
        return ' '.join(str_ids)
    
    def save(self, force_insert=False, force_update=False, using =None, update_fields=None):
        if self.id and self.participant_users.count() > 0:
            users = self.participant_users.all().order_by('id')
            user_ids = [user.id for user in users]
            tag = PrivateChat.generate_participants_tag(user_ids)

            self.participant_users_tag = tag

        return super().save(force_insert, force_update, using, update_fields)


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
    messages = GenericRelation('Message', related_query_name='group_chat')

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


class Message(models.Model):    
    PARENT_CHAT_PRIVATE = 'PC'
    PARENT_CHAT_GROUP = 'GC'

    FORMAT_TEXT = 'TXT'
    FORMAT_IMAGE = 'IMG'
    FORMAT_AUDIO = 'AUD'
    FORMAT_VIDEO = 'VID'

    STATUS_IN_PROGRESS = 'P'
    STATUS_SENT = 'S'
    STATUS_DELIVERED = 'D'
    STATUS_VIEWED = 'V'

    PARENT_CHAT_CHOICES = [
        (PARENT_CHAT_PRIVATE, 'PRIVATE CHAT'),
        (PARENT_CHAT_GROUP, 'GROUP CHAT')
    ]

    FORMAT_CHOICES = [
        (FORMAT_TEXT, 'TEXT'),
        (FORMAT_IMAGE, 'IMAGE'),
        (FORMAT_AUDIO, 'AUDIO'),
        (FORMAT_VIDEO, 'VIDEO')
    ]

    STATUS_CHOICES = [
        (STATUS_IN_PROGRESS, 'IN_PROGRESS'),
        (STATUS_SENT, 'SENT'),
        (STATUS_DELIVERED, 'DELIVERED'),
        (STATUS_VIEWED, 'VIEWED')
    ]

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    parent_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE
    )
    parent_id = models.PositiveIntegerField()
    parent_chat = GenericForeignKey('parent_content_type', 'parent_id')
    parent_chat_type = models.CharField(max_length=2, choices=PARENT_CHAT_CHOICES)
    content_format = models.CharField(max_length=3, choices=FORMAT_CHOICES)
    time_tag = models.DateTimeField(null=True)
    deleted_at = models.DateTimeField(null=True)
    delivery_status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default=STATUS_IN_PROGRESS
    )


class TextMessage(models.Model):
    text = models.TextField()
    message = models.OneToOneField(
        Message,
        on_delete=models.CASCADE,
        related_name='content'
    )