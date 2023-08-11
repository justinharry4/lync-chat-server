from django.urls import path

from rest_framework_nested.routers import DefaultRouter, NestedDefaultRouter

from .views import (
    GroupChatAdminViewSet, GroupChatParticipantViewSet, ProfilePhotoViewSet,
    ProfileViewSet, PrivateChatViewSet, PrivateChatParticipantViewSet,
    GroupChatViewSet, PCChatViewSet, GCChatViewSet
)


base_router = DefaultRouter()
base_router.register('profiles', ProfileViewSet)
base_router.register('privatechats', PrivateChatViewSet, 'private-chats')
base_router.register('groupchats', GroupChatViewSet, 'group-chats')

profiles_router = NestedDefaultRouter(base_router, 'profiles',
                                      lookup='profile')
profiles_router.register('photo', ProfilePhotoViewSet, 
                         basename='profile-photos')

private_chat_router = NestedDefaultRouter(base_router, 'privatechats',
                                          lookup='private_chat')
private_chat_router.register('participants', PrivateChatParticipantViewSet,
                             basename='privatechat-participants')
private_chat_router.register('chats', PCChatViewSet,
                             basename='private-childchats')

group_chat_router = NestedDefaultRouter(base_router, 'groupchats',
                                        lookup='group_chat')
group_chat_router.register('participants', GroupChatParticipantViewSet,
                           basename='groupchat-participants')
group_chat_router.register('chats', GCChatViewSet,
                           basename='group-childchats')
group_chat_router.register('admins', GroupChatAdminViewSet,
                           basename='groupchat-admins')

urlpatterns = base_router.urls
urlpatterns += profiles_router.urls
urlpatterns += private_chat_router.urls
urlpatterns += group_chat_router.urls

