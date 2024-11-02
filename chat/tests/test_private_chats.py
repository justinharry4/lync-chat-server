from rest_framework import status
from model_bakery import baker
import pytest

from core.models import User
from chat.models import PrivateChatParticipant, PrivateChat


@pytest.fixture
def call_create_pc_endpoint(api_client):
    def make_api_call(data):
        return api_client.post('/chat/privatechats/', data)
    return make_api_call

@pytest.fixture
def call_retrieve_pc_endpoint(api_client):
    def make_api_call(pk):
        return api_client.get(f'/chat/privatechats/{pk}/')
    return make_api_call


@pytest.mark.django_db
class TestCreatePrivateChat():
    def test_if_user_is_anonymous_returns_401(self, call_create_pc_endpoint):
        response = call_create_pc_endpoint({'participant_user_ids': [1, 2]})
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_repeated_id_in_ids_list_returns_400(self,
                                                    authenticate,
                                                    call_create_pc_endpoint):
        user = baker.make(User)
        authenticate(user)

        response = call_create_pc_endpoint({'participant_user_ids': [user.id, user.id]})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['participant_user_ids'] is not None

    def test_if_user_id_not_in_ids_list_returns_400(self,
                                                    authenticate,
                                                    call_create_pc_endpoint):
        user1, user2, user3 = baker.make(User, _quantity=3)
        authenticate(user1)

        response = call_create_pc_endpoint({'participant_user_ids': [user2.id, user3.id]})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['participant_user_ids'] is not None

    def test_if_invalid_ids_returns_400(self, authenticate, call_create_pc_endpoint):
        user = baker.make(User)
        authenticate(user)

        response = call_create_pc_endpoint({'participant_user_ids': [user.id, 1000]})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['participant_user_ids'] is not None

    def test_if_existing_chat_with_given_ids_returns_400(self,
                                                         authenticate,
                                                         call_create_pc_endpoint,
                                                         create_private_chat):
        user1, user2 = baker.make(User, _quantity=2)
        create_private_chat([user1, user2])
        authenticate(user1)

        response = call_create_pc_endpoint({'participant_user_ids': [user1.id, user2.id]})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_if_new_valid_id_pair_returns_201(self, authenticate, call_create_pc_endpoint):
        user1, user2 = baker.make(User, _quantity=2)
        authenticate(user1)

        response = call_create_pc_endpoint({'participant_user_ids': [user1.id, user2.id]})
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['id'] > 0


class TestRetrievePrivateChat():
    def test_if_user_is_anonymous_returns_401(self, call_retrieve_pc_endpoint):
        response = call_retrieve_pc_endpoint(1)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
