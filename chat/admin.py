from django.contrib import admin

from . import models


@admin.register(models.Profile)
class ProfileAdmin(admin.ModelAdmin):
    pass

@admin.register(models.ProfilePhoto)
class ProfilePhotoAdmin(admin.ModelAdmin):
    pass

@admin.register(models.PrivateChat)
class PrivateChatAdmin(admin.ModelAdmin):
    pass

@admin.register(models.PrivateChatParticipant)
class PrivateChatParticipantAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Chat)
class ChatAdmin(admin.ModelAdmin):
    pass