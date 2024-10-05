from django.contrib.auth import get_user_model

from rest_framework import permissions

from .models import GroupChat, PrivateChat


def silence_not_found_error(view, model, pk):
    if not hasattr(view, 'missing_objects'):
        view.missing_objects = []

    view.missing_objects.append((model, pk))


class CustomBasePermission(permissions.BasePermission):
    def is_authenticated(self, request):
        return request.user and request.user.is_authenticated
    
    def __or__(self, other_perm):
        return OrPermission(self, other_perm)
    
    def __and__(self, other_perm):
        return AndPermission(self, other_perm)
    

class OrPermission(CustomBasePermission):
    def __init__(self, perm1, perm2):
        self.perm1 = perm1
        self.perm2 = perm2

    def has_permission(self, request, view):
        return (
            self.perm1.has_permission(request, view) or
            self.perm2.has_permission(request, view)
        )
    

class AndPermission(CustomBasePermission):
    def __init__(self, perm1, perm2):
        self.perm1 = perm1
        self.perm2 = perm2

    def has_permission(self, request, view):
        return (
            self.perm1.has_permission(request, view) and
            self.perm2.has_permission(request, view)
        )


class IsPrivateChatMember(CustomBasePermission):
    message = 'user is not a participant in the referenced private chat'

    def __init__(self, private_chat_id):
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
    def __init__(self, object_id, model=None, user_field='user'):
        self.id = object_id
        self.model = model
        self.user_field = user_field

    def has_permission(self, request, view):        
        if not self.is_authenticated(request):
            return False
        
        if not self.model:
            self.model = view.get_queryset().model

        self.message = (
            f'user is not associated with the referenced {self.model.__name__}'
        )

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

