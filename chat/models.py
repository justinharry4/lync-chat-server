from django.db import models
from django.conf import settings


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_online = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_photo_removed = models.BooleanField(default=True)


class ProfilePhoto(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='chat/images')
    uploaded_at = models.DateTimeField(auto_now=True)

