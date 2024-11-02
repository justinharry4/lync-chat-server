from rest_framework.test import APIClient
from pytest import fixture
from model_bakery import baker

from core.models import User
from chat.models import PrivateChat, PrivateChatParticipant


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