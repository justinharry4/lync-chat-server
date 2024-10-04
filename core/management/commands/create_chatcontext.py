from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from django.conf import settings

from core.models import User
from chat.models import Profile, ProfilePhoto, PrivateChat, PrivateChatParticipant


class Command(BaseCommand):
    """
    This command creates the minimal set of objects that make up 
    a complete private chat context. These objects include a pair 
    of users, profiles, profile photos and private chat participants, 
    and the related private chat. This command is typically run to 
    initialize the database before testing the application with the
    UI client.
    """

    def handle(self, *args, **options):
        self.stdout.write('Creating private chat context...')

        credentials_list = [
            ('Henry', 'user1@lync.com', 'user1pass'),
            ('Rebecca', 'user2@lync.com', 'user2pass'),
        ]
        photos_dir = settings.BASE_DIR / 'media' / 'chat' / 'images'
        photo_paths = [
            photos_dir / 'jay.png',
            photos_dir / 'mel.png',
        ]   

        try:
            users = []

            for credentials, photo_path in zip(credentials_list, photo_paths):
                try:
                    existing_user = User.objects.get(username=credentials[0])
                    existing_user.delete()
                except User.DoesNotExist:
                    pass

                user = User.objects.create_user(*credentials) 
                profile = Profile.objects.create(user=user)

                with photo_path.open(mode='rb') as f:
                    ProfilePhoto.objects.create(
                        profile=profile,
                        image=File(f, name=photo_path.name)
                    )

                users.append(user)

            private_chat = PrivateChat.objects.create()
            participants = [
                PrivateChatParticipant(
                    private_chat=private_chat,
                    user=user
                ) for user in users
            ]
            PrivateChatParticipant.objects.bulk_create(participants)

            self.stdout.write('Private chat context successfully created!')
        except Exception as exc:
            raise CommandError(
                'Context creation failed.'
            ) from exc
            




