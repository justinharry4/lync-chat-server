from django.shortcuts import get_object_or_404
from django.http.response import Http404

from rest_framework import permissions
from rest_framework.exceptions import NotFound

from .models import GroupChat, PrivateChat, get_user_model


def silence_not_found_error(view, model, pk):
    if not hasattr(view, 'missing_objects'):
        view.missing_objects = []

    view.missing_objects.append((model, pk))


def one_of(*args):
    class CompositeOrPermission(CustomBasePermission):
        perms = args

        def has_permission(self, request, view):
            for perm in self.perms:
                if perm.has_permission(request, view):
                    return True

            return False

    return CompositeOrPermission()

def all_of(*args):
    class CompositeAndPermission(CustomBasePermission):
        perms = args

        def has_permission(self, request, view):
            for perm in self.perms:
                if not perm.has_permission(request, view):
                    return False
                
            return True
        
    return CompositeAndPermission()


class CustomBasePermission(permissions.BasePermission):
    def is_authenticated(self, request):
        return request.user and request.user.is_authenticated


class IsPrivateChatMember(CustomBasePermission):
    message = 'user is not a participant in the referenced private chat'

    def __init__(self, private_chat_id=None):
        self.id = private_chat_id

    def has_permission(self, request, view):
        if not self.is_authenticated(request):
            return False
        
        try:
            private_chat = PrivateChat.objects.get(pk=self.id)
        except PrivateChat.DoesNotExist:
            silence_not_found_error(view, PrivateChat, self.id)
            return True
        
        participant_users = private_chat.participant_users
        return participant_users.filter(pk=request.user.id).exists()
    

class IsGroupChatMember(CustomBasePermission):
    message = 'user is not a participant in the referenced group chat'

    def __init__(self, group_chat_id):
        self.id = group_chat_id

    def has_permission(self, request, view):
        if not self.is_authenticated(request):
            False

        try:
            group_chat = GroupChat.objects.get(pk=self.id)
        except GroupChat.DoesNotExist:
            silence_not_found_error(view, GroupChat, self.id)
            return True
        
        participant_users = group_chat.participant_users
        return participant_users.filter(pk=request.user.id).exists()
        

class IsGroupChatAdmin(CustomBasePermission):
    message = 'user is not an admin in the referenced group chat'

    def __init__(self, group_chat_id):
        self.id = group_chat_id

    def has_permission(self, request, view):
        if not self.is_authenticated(request):
            return False
        
        try:
            group_chat = GroupChat.objects.get(pk=self.id)
        except GroupChat.DoesNotExist:
            silence_not_found_error(view, GroupChat, self.id)
            return True
        
        return group_chat.admin_users.filter(pk=request.user.id).exists()
    

class IsGroupChatCreator(CustomBasePermission):
    message = 'user is not the creator of the referenced group chat'
    
    def __init__(self, group_chat_id):
        self.id = group_chat_id

    def has_permission(self, request, view):
        if not self.is_authenticated(request):
            return False
        
        try:
            group_chat = GroupChat.objects.get(pk=self.id)
        except GroupChat.DoesNotExist:
            silence_not_found_error(view, GroupChat, self.id)
            return True
        
        return group_chat.creator == request.user


class IsAssociatedUser(CustomBasePermission):
    def __init__(self, model, id, user_field='user'):
        self.model = model
        self.id = id
        self.user_field = user_field
        self.message = f'user is not associated with the referenced {model.__name__}'

    def has_permission(self, request, view):
        if not self.is_authenticated(request):
            return False
        
        id = self.id
        model = self.model
        user_field = self.user_field

        try:
            instance = model.objects.get(pk=id)
        except model.DoesNotExist:
            silence_not_found_error(view, model, id)
            return True

        user_model = get_user_model()
        instance_user = getattr(instance, user_field)
       
        if not isinstance(instance_user, user_model):
            raise TypeError(
                f'`{user_field}` attribute on {model.__name__} '
                f'object is not an instance of {user_model.__name__}'
            )
    
        return instance_user == request.user

    