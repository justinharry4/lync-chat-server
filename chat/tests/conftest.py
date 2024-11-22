from rest_framework.test import APIClient
from pytest import fixture
from model_bakery import baker

from core.models import User
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
def authenticate_as_any(authenticate):
    def do_auth():
        user = baker.make(User)
        authenticate(user)
        return user
    return do_auth

@fixture
def authenticate_as_pc_member(authenticate, create_private_chat):
    def do_auth():
        users = baker.make(User, _quantity=2)
        private_chat = create_private_chat(users)
        authenticate(users[0])

        return (users[0], private_chat)
    return do_auth

@fixture
def authenticate_as_non_pc_member(authenticate, create_private_chat):
    def do_auth():
        users = baker.make(User, _quantity=3)
        private_chat = create_private_chat(users[:2])
        authenticate(users[2])

        return (users[2], private_chat)
    return do_auth

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