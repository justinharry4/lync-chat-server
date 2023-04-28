from django.urls import path
# from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import DefaultRouter, NestedDefaultRouter
from .views import ProfilePhotoViewSet, ProfileViewSet


base_router = DefaultRouter()
base_router.register('profiles', ProfileViewSet)

profiles_router = NestedDefaultRouter(base_router, 'profiles', lookup='profile')
profiles_router.register('photos', ProfilePhotoViewSet, basename='profile-photos')

urlpatterns = base_router.urls
urlpatterns += profiles_router.urls

# urlpatterns = [
#     path('profiles/', ProfileList.as_view(), name='profile-list'),
#     path('profiles/<int:id>/', ProfileDetail.as_view(), name='profile-detail'),
#     path('profiles/<int:id>/status/', ProfileDetail.modify_active_status, name='profile-active-status'),
#     path('profiles/<int:profile_id>/photos/', ProfilePhotoList.as_view(), name='profile-photo-list'),
#     path('profiles/<int:profile_id>/photos/<int:id>/', ProfilePhotoDetail.as_view(), name='profile-photo-detail'),
# ]