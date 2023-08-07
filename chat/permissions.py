from django.shortcuts import get_object_or_404
from django.http.response import Http404

from rest_framework import permissions
from rest_framework.exceptions import NotFound

from .models import PrivateChat


def silence_not_found_error(view, model, pk):
    if not hasattr(view, 'missing_objects'):
        view.missing_objects = []

    view.missing_objects.append((model, pk))


class CustomBasePermission(permissions.BasePermission):
    def is_authenticated(self, request):
        return request.user and request.user.is_authenticated


class IsPrivateChatMember(CustomBasePermission):
    message = 'user is not a participant in the referenced private chat'

    def __init__(self, private_chat_id=None):
        self.id = private_chat_id

    def has_permission(self, request, view):
        if self.is_authenticated(request): 
            try:
                private_chat = PrivateChat.objects.get(pk=self.id)
            except PrivateChat.DoesNotExist:
                silence_not_found_error(view, PrivateChat, self.id)
                return True

            participant_users = private_chat.participant_users
            
            return participant_users.filter(pk=request.user.id).exists()
        
        return False
    

class IsGroupChatMember(CustomBasePermission):
    message = 'user is not a participant in the referenced private chat'

    def __init__(self, group_chat_id):
        self.id = group_chat_id

    def has_permission(self, request, view):
        pass