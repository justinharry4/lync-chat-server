from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from core.models import User
from chat.models import Profile, ProfilePhoto, PrivateChat, PrivateChatParticipant, Chat


USER1_USERNAME = 'Henry'
USER1_EMAIL = 'user1@lync.com'
USER1_PASSWORD = 'user1pass'
USER1_PHOTO = 'jay.png'

USER2_USERNAME = 'Rebecca'
USER2_EMAIL = 'user2@lync.com'
USER2_PASSWORD = 'user2pass'
USER2_PHOTO = 'mel.png'


class Command(BaseCommand):
    """
    This command creates the minimal set of objects that make up 
    a complete private chat context. These objects include a pair 
    of users, profiles, profile photos, chats and private chat participants, 
    and the related private chat. This command is typically run to 
    initialize the database before testing the application with the
    UI client.
    """

    def handle(self, *args, **options):
        self.stdout.write('Creating private chat context...')

        credentials_list = [
            (USER1_USERNAME, USER1_EMAIL, USER1_PASSWORD),
            (USER2_USERNAME, USER2_EMAIL, USER2_PASSWORD),
        ]
        photos_dir = settings.BASE_DIR / 'media' / 'chat' / 'images'
        photo_paths = [
            photos_dir / USER1_PHOTO,
            photos_dir / USER2_PHOTO,
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
            
            participants, chats = [], []
            for user in users:
                participants.append(
                    PrivateChatParticipant(private_chat=private_chat,
                                           user=user)
                )
                chats.append(
                    Chat(user=user,
                         parent_chat_type=Chat.PARENT_CHAT_PRIVATE,
                         content_type=ContentType.objects.get_for_model(PrivateChat),
                         object_id=private_chat.id)
                )

            PrivateChatParticipant.objects.bulk_create(participants)
            Chat.objects.bulk_create(chats)

            self.stdout.write('Private chat context successfully created!')
        except Exception as exc:
            raise CommandError(
                'Context creation failed.'
            ) from exc
            




