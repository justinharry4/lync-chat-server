from rest_framework import serializers

from .models import Profile, ProfilePhoto


class ProfilePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfilePhoto
        fields = ['id', 'image', 'uploaded_at']

    def create(self, validated_data):
        profile_id = self.context['profile_id']
        photo = ProfilePhoto.objects.create(profile_id=profile_id, **validated_data)

        return photo


class ProfileSerializer(serializers.ModelSerializer):
    photos = ProfilePhotoSerializer(many=True, read_only=True)
    is_active = serializers.ReadOnlyField()
    latest_photo = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'id',
            'user',
            'last_seen',
            'is_online',
            'is_active',
            'is_photo_removed',
            'photos',
            'latest_photo'
        ]

    def get_latest_photo(self, profile):
        sort_key = lambda p: p.uploaded_at
        sorted_photos = sorted(profile.photos.all(), key=sort_key, reverse=True)

        if len(sorted_photos) > 0:
            return sorted_photos[0].id
        

class ModifyProfileStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['is_active']