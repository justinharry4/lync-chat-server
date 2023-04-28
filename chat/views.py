from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import mixins
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.decorators import action

from .models import Profile, ProfilePhoto
from .serializers import (ModifyProfileStatusSerializer,
                          ProfilePhotoSerializer,
                          ProfileSerializer)


class ProfileViewSet(ModelViewSet):
    queryset = Profile.objects.prefetch_related('photos').all()
    serializer_class = ProfileSerializer

    def get_serializer_class(self):
        if self.action == 'modify_active_status':
            return ModifyProfileStatusSerializer
        else: 
            return ProfileSerializer

    def get_permissions(self):
        if self.action in ['list', 'destroy', 'modify_active_status']:
            return [IsAdminUser()]
        else: 
            return [AllowAny()]

    @action(detail=True, url_path='status', methods=['PATCH'])
    def modify_active_status(self, request, pk):
        profile = get_object_or_404(Profile, pk=pk)
        # serializer_class = self.get_serializer_class()
        serializer = self.get_serializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        mod_profile = serializer.save()

        ret_serializer = ProfileSerializer(mod_profile)
        return Response(ret_serializer.data)


class ProfilePhotoViewSet(mixins.CreateModelMixin,
                          mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.DestroyModelMixin,
                          GenericViewSet):
    serializer_class = ProfilePhotoSerializer

    def get_queryset(self):
        profile_id = self.kwargs['profile_pk']
        return ProfilePhoto.objects.filter(profile_id=profile_id).select_related('profile')
    
    def get_permissions(self):
        if self.action in ['list']:
            return [IsAdminUser()]
        elif self.action == 'retrieve':
            photo_id = self.kwargs['pk']
            latest_photo = self.get_latest_photo()

            if latest_photo and str(latest_photo.id) != photo_id:
                return [IsAdminUser()]
            else:
                return [AllowAny()]
        else:
            return [AllowAny()]
        
    def get_serializer_context(self):
        return {'profile_id': self.kwargs['profile_pk']}
        
    def get_latest_photo(self):
        profile_id = self.kwargs['profile_pk']

        latest_photo = ProfilePhoto.objects \
            .filter(profile_id=profile_id) \
            .order_by('uploaded_at') \
            .reverse() \
            .first()
        
        return latest_photo

    def perform_create(self, serializer: ProfilePhotoSerializer):
        profile_id = self.kwargs['profile_pk']
        profile = get_object_or_404(Profile, pk=profile_id)
        
        if profile.is_photo_removed:
            profile.is_photo_removed = False
            profile.save()

        serializer.save()

    def perform_destroy(self, instance: ProfilePhoto):
        latest_photo = self.get_latest_photo()

        if latest_photo.id == instance.id:
            instance.profile.is_photo_removed = True
            instance.profile.save()
        
        instance.delete()

