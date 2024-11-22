from rest_framework import status
from model_bakery import baker
import pytest

from core.models import User
from chat.models import PrivateChat


# pc is used as short for private chats

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

@pytest.fixture
def call_list_pcs_endpoint(api_client):
    def make_api_call():
        return api_client.get(f'/chat/privatechats/')
    return make_api_call

@pytest.fixture
def call_delete_pc_endpoint(api_client):
    def make_api_call(pk):
        return api_client.delete(f'/chat/privatechats/{pk}/')
    return make_api_call

@pytest.fixture
def is_member_of_private_chats():
    def check_membership(user, private_chats):
        for private_chat in private_chats:
            target = [p for p in private_chat['participants']
                      if p['user'] == user.id]
            if len(target) == 0:
                return False
        return True
    return check_membership 


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

    def test_if_invalid_ids_returns_400(self,
                                        test_data,
                                        authenticate,
                                        call_create_pc_endpoint):
        user = baker.make(User)
        authenticate(user)

        response = call_create_pc_endpoint({
            'participant_user_ids': [user.id, test_data.INVALID_ID]
        })
        
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


@pytest.mark.django_db
class TestRetrievePrivateChat():
    def test_if_user_is_anonymous_returns_401(self, call_retrieve_pc_endpoint):
        response = call_retrieve_pc_endpoint(1)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_user_is_not_member_returns_403(self,
                                               authenticate,
                                               create_private_chat,
                                               call_retrieve_pc_endpoint):
        users = baker.make(User, _quantity=3)
        private_chat = create_private_chat(users[:2])
        authenticate(users[2])

        response = call_retrieve_pc_endpoint(private_chat.id)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_if_id_does_not_exist_returns_404(self,
                                              authenticate,
                                              test_data,
                                              call_retrieve_pc_endpoint):
        user = baker.make(User)
        authenticate(user)

        response = call_retrieve_pc_endpoint(test_data.INVALID_ID)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_user_is_a_member_returns_200(self,
                                             authenticate,
                                             create_private_chat,
                                             call_retrieve_pc_endpoint):
        users = baker.make(User, _quantity=2)
        private_chat = create_private_chat(users)
        authenticate(users[0])

        response = call_retrieve_pc_endpoint(private_chat.id)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == private_chat.id


@pytest.mark.django_db
class TestListPrivateChats():
    def test_if_user_is_anonymous_returns_401(self, call_list_pcs_endpoint):
        response = call_list_pcs_endpoint()
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_user_is_authenticated_returns_200(self,
                                                  authenticate,
                                                  call_list_pcs_endpoint,
                                                  create_private_chats_for_user,
                                                  is_member_of_private_chats):
        users = baker.make(User, _quantity=10)
        create_private_chats_for_user(users[0], users[1:5])
        create_private_chats_for_user(users[5], users[6:])
        authenticate(users[0])

        response = call_list_pcs_endpoint()
        
        assert response.status_code == status.HTTP_200_OK
        assert is_member_of_private_chats(users[0], response.data)


@pytest.mark.django_db
class TestDeletePrivateChat():
    def test_if_user_is_anonymous_returns_401(self, call_delete_pc_endpoint):
        response = call_delete_pc_endpoint(1)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_user_is_not_admin_returns_403(self,
                                              authenticate,
                                              create_private_chat,
                                              call_delete_pc_endpoint):
        users = baker.make(User, _quantity=2)
        private_chat = create_private_chat(users)
        authenticate(users[0])

        response = call_delete_pc_endpoint(private_chat.id)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_if_user_is_admin_and_id_does_not_exist_returns_404(self,
                                                                test_data,
                                                                authenticate,
                                                                call_delete_pc_endpoint):
        user = baker.make(User, is_staff=True)
        authenticate(user)

        response = call_delete_pc_endpoint(test_data.INVALID_ID)
    
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_if_user_is_admin_and_id_is_valid_returns_204(self,
                                                          authenticate,
                                                          create_private_chat,
                                                          call_delete_pc_endpoint):
        users = baker.make(User, _quantity=3, is_staff=True)
        private_chat = create_private_chat(users[1:])
        authenticate(users[0])

        response = call_delete_pc_endpoint(private_chat.id)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not PrivateChat.objects.filter(pk=private_chat.id).exists()


@pytest.mark.django_db
class TestUpdatePrivateChat():
    def test_if_put_method_returns_405(self, api_client, authenticate):
        user = baker.make(User)
        authenticate(user)

        response = api_client.put('/chat/privatechats/1/', {})
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
    def test_if_patch_method_returns_405(self, api_client, authenticate):
        user = baker.make(User)
        authenticate(user)
        
        response = api_client.patch('/chat/privatechats/1/', {})
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        