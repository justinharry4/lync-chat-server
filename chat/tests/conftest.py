from rest_framework.test import APIClient
from pytest import fixture
from model_bakery import baker

from chat.models import PrivateChat, PrivateChatParticipant


class Constants:
    INVALID_ID = 1000

@fixture
def test_data():
    return Constants()

@fixture
def api_client():
    return APIClient()

@fixture
def authenticate(api_client):
    def do_authenticate(user):
        api_client.force_authenticate(user=user)
    return do_authenticate

@fixture
def create_private_chat():
    def do_create_private_chat(users):
        private_chat = baker.make(PrivateChat)
        baker.make(
            PrivateChatParticipant,
            _quantity=2,
            user=iter(users),
            private_chat=private_chat,
        )
        return private_chat
    return do_create_private_chat

@fixture
def create_private_chats_for_user(create_private_chat):
    def do_create_private_chats(user, other_users):
        private_chats = []
        for u in other_users:
            private_chat = create_private_chat([user, u])
            private_chats.append(private_chat)
        return private_chats
    return do_create_private_chats