from django.urls import path
from rest_framework_nested.routers import DefaultRouter, NestedDefaultRouter
from .views import (ProfilePhotoViewSet,
                    ProfileViewSet,
                    ChatViewSet,
                    PrivateChatViewSet,
                    PrivateChatParticipantViewSet)


base_router = DefaultRouter()
base_router.register('profiles', ProfileViewSet)
base_router.register('privatechats', PrivateChatViewSet, 'private-chats')
base_router.register('privatechat-participants', PrivateChatParticipantViewSet)

profiles_router = NestedDefaultRouter(base_router, 'profiles', lookup='profile')
profiles_router.register('photos', ProfilePhotoViewSet, basename='profile-photos')

private_chat_router = NestedDefaultRouter(base_router, 'privatechats', lookup='private_chat')
private_chat_router.register('chats', ChatViewSet, basename='private-childchats')

urlpatterns = base_router.urls
urlpatterns += profiles_router.urls
urlpatterns += private_chat_router.urls

