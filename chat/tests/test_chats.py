from datetime import datetime

from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from model_bakery import baker
import pytest

from core.models import User
from chat.models import PrivateChat, Chat


# pc is used as short for private chats

@pytest.fixture
def call_create_chat_endpoint(api_client):
    def make_api_call(private_chat_pk):
        return api_client.post(f'/chat/privatechats/{private_chat_pk}/chats/')
    return make_api_call

@pytest.fixture
def call_list_chats_endpoint(api_client):
    def make_api_call(private_chat_pk):
        return api_client.get(f'/chat/privatechats/{private_chat_pk}/chats/')
    return make_api_call

@pytest.fixture
def call_retrieve_chat_endpoint(api_client):
    def make_api_call(private_chat_pk, chat_pk):
        return api_client.get(
            f'/chat/privatechats/{private_chat_pk}/chats/{chat_pk}/'
        )
    return make_api_call

@pytest.fixture
def call_update_chat_endpoint(api_client):
    def make_api_call(private_chat_pk, chat_pk, data={}):
        return api_client.patch(
            f'/chat/privatechats/{private_chat_pk}/chats/{chat_pk}/',
            data
        )
    return make_api_call
    
@pytest.fixture
def call_delete_chat_endpoint(api_client):
    def make_api_call(private_chat_pk, chat_pk):
        return api_client.delete(
            f'/chat/privatechats/{private_chat_pk}/chats/{chat_pk}/'
        )
    return make_api_call

@pytest.fixture
def call_current_chat_endpoint(api_client):
    def make_api_call(private_chat_pk):
        return api_client.get(
            f'/chat/privatechats/{private_chat_pk}/chats/current/'
        )
    return make_api_call

@pytest.fixture
def create_chat():
    def do_create(user, private_chat):
        return baker.make(
            Chat,
            user=user,
            object_id=private_chat.id,
            parent_chat_type=Chat.PARENT_CHAT_PRIVATE,
            content_type=ContentType.objects.get_for_model(PrivateChat)
        )
    return do_create

@pytest.fixture
def close_chat():
    def do_close_chat(chat):
        chat.terminated_at = datetime.now()
        chat.save()
    return do_close_chat

@pytest.fixture
def create_chats(create_chat, close_chat):
    def do_create_chats(user, private_chat, quantity):
        chats = []
        while quantity:
            chat = create_chat(user, private_chat)
            if quantity != 1:
                close_chat(chat)

            chats.append(chat)
            quantity -= 1
        return chats
    return do_create_chats

@pytest.fixture
def is_owner_of_chats():
    def check_ownership(user, chats):
        for chat in chats:
            if chat['user'] != user.id:
                return False
        return True 
    return check_ownership

@pytest.fixture
def authenticate_as_chat_owner(authenticate, create_private_chat, create_chat):
    def do_auth():
        users = baker.make(User, _quantity=2)
        private_chat = create_private_chat(users)
        chat = create_chat(users[0], private_chat)
        authenticate(users[0])

        return (users[0], private_chat, chat)
    return do_auth 

@pytest.fixture
def authenticate_as_non_chat_owner(authenticate, create_private_chat, create_chat):
    def do_auth():
        users = baker.make(User, _quantity=2)
        private_chat = create_private_chat(users)
        chat = create_chat(users[1], private_chat)
        authenticate(users[0])

        return (users[0], private_chat, chat)
    return do_auth 


@pytest.mark.django_db
class TestCreateChat():
    def test_if_user_is_anonymous_returns_401(self, call_create_chat_endpoint):
        response = call_create_chat_endpoint(1)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_private_chat_id_doesnt_exist_returns_404(self,
                                                         test_data,
                                                         authenticate,
                                                         authenticate_as_any,
                                                         call_create_chat_endpoint):
        # user = baker.make(User)
        # authenticate(user)
        authenticate_as_any()

        response = call_create_chat_endpoint(test_data.INVALID_ID)
    
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_user_is_not_pc_member_returns_403(self,
                                                  authenticate,
                                                  create_private_chat,
                                                  authenticate_as_non_pc_member,
                                                  call_create_chat_endpoint):
        # users = baker.make(User, _quantity=3)
        # private_chat = create_private_chat(users[:2])
        # authenticate(users[2])
        user, private_chat = authenticate_as_non_pc_member()

        response = call_create_chat_endpoint(private_chat.id)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_if_user_is_pc_member_with_open_chat_returns_400(self,
                                                             authenticate,
                                                             create_private_chat,
                                                             create_chat,
                                                             authenticate_as_pc_member,
                                                             call_create_chat_endpoint):
        # users = baker.make(User, _quantity=2)
        # private_chat = create_private_chat(users)
        # create_chat(users[0], private_chat)
        # authenticate(users[0])
        user, private_chat = authenticate_as_pc_member()
        create_chat(user, private_chat)

        response = call_create_chat_endpoint(private_chat.id)
    
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_if_user_is_pc_member_with_no_chats_returns_201(self,
                                                            authenticate,
                                                            create_private_chat,
                                                            authenticate_as_pc_member,
                                                            call_create_chat_endpoint):
        # users = baker.make(User, _quantity=2)
        # private_chat = create_private_chat(users)
        # authenticate(users[0])
        user, private_chat = authenticate_as_pc_member()

        response = call_create_chat_endpoint(private_chat.id)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert (response.data['id'] > 0 and
                int(response.data['parent_id']) == private_chat.id)
        
    def test_if_user_is_pc_member_with_closed_chats_returns_201(self,
                                                                authenticate,
                                                                create_private_chat,
                                                                create_chat,
                                                                close_chat,
                                                                authenticate_as_pc_member,
                                                                call_create_chat_endpoint):
        # users = baker.make(User, _quantity=2)
        # private_chat = create_private_chat(users)
        # chat = create_chat(users[0], private_chat)
        # close_chat(chat)
        # authenticate(users[0])
        user, private_chat = authenticate_as_pc_member()
        chat = create_chat(user, private_chat)
        close_chat(chat)

        response = call_create_chat_endpoint(private_chat.id)

        assert response.status_code == status.HTTP_201_CREATED
        assert (response.data['id'] > 0 and
                int(response.data['parent_id']) == private_chat.id)
        

@pytest.mark.django_db
class TestListChats():
    def test_if_user_is_anonymous_returns_401(self, call_list_chats_endpoint):
        response = call_list_chats_endpoint(1)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_private_chat_id_doesnt_exist_returns_404(self,
                                                         test_data,
                                                         authenticate,
                                                         authenticate_as_any,
                                                         call_list_chats_endpoint):
        # user = baker.make(User)
        # authenticate(user)
        authenticate_as_any()

        response = call_list_chats_endpoint(test_data.INVALID_ID)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_user_is_not_pc_member_returns_403(self,
                                                  authenticate,
                                                  create_private_chat,
                                                  authenticate_as_non_pc_member,
                                                  call_list_chats_endpoint):
        # users = baker.make(User, _quantity=3)
        # private_chat = create_private_chat(users[:2])
        # authenticate(users[2])
        user, private_chat = authenticate_as_non_pc_member()

        response = call_list_chats_endpoint(private_chat.id)

        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_if_user_is_pc_member_returns_200(self,
                                              authenticate,
                                              create_private_chat,
                                              create_chats,
                                              is_owner_of_chats,
                                              call_list_chats_endpoint):
        users = baker.make(User, _quantity=2)
        private_chat = create_private_chat(users)
        create_chats(users[0], private_chat, 3)
        create_chats(users[1], private_chat, 3)
        authenticate(users[0])

        response = call_list_chats_endpoint(private_chat.id)
    
        assert response.status_code == status.HTTP_200_OK
        assert is_owner_of_chats(users[0], response.data)


@pytest.mark.django_db
class TestRetrieveChat():
    def test_if_user_is_anonymous_returns_401(self, call_retrieve_chat_endpoint):
        response = call_retrieve_chat_endpoint(1, 1)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_pc_does_not_exist_returns_404(self,
                                              test_data,
                                              authenticate,
                                              authenticate_as_any,
                                              call_retrieve_chat_endpoint):
        # user = baker.make(User)
        # authenticate(user)
        authenticate_as_any()

        response = call_retrieve_chat_endpoint(test_data.INVALID_ID, 1)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_user_is_not_pc_member_returns_403(self,
                                                  authenticate_as_non_pc_member,
                                                  call_retrieve_chat_endpoint):
        user, private_chat = authenticate_as_non_pc_member()

        response = call_retrieve_chat_endpoint(private_chat.id, 1)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_if_chat_doesnt_exist_returns_404(self,
                                              test_data,
                                              authenticate_as_pc_member,
                                              call_retrieve_chat_endpoint):
        user, private_chat = authenticate_as_pc_member()

        response = call_retrieve_chat_endpoint(private_chat.id, test_data.INVALID_ID)
    
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_chat_doesnt_belong_to_referenced_pc_returns_404(self,
                                                                authenticate_as_pc_member,
                                                                create_private_chat,
                                                                create_chat,
                                                                call_retrieve_chat_endpoint):
        auth_user, referenced_pc = authenticate_as_pc_member()
        other_user = baker.make(User)
        other_pc = create_private_chat([auth_user, other_user])
        chat = create_chat(auth_user, other_pc)

        response = call_retrieve_chat_endpoint(referenced_pc.id, chat.id)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_if_user_is_not_chat_owner_returns_403(self,
                                                   authenticate_as_non_chat_owner,
                                                   call_retrieve_chat_endpoint):
        user, private_chat, chat = authenticate_as_non_chat_owner()

        response = call_retrieve_chat_endpoint(private_chat.id, chat.id)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_if_user_is_chat_owner_returns_200(self,
                                               authenticate_as_chat_owner,
                                               call_retrieve_chat_endpoint):
        user, private_chat, chat = authenticate_as_chat_owner()

        response = call_retrieve_chat_endpoint(private_chat.id, chat.id)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] ==  chat.id


@pytest.mark.django_db
class TestUpdateChat():
    def test_if_user_is_anonymous_returns_401(self, call_update_chat_endpoint):
        response = call_update_chat_endpoint(1, 1)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_pc_id_doesnt_exists_returns_404(self,
                                             test_data,
                                             authenticate_as_any,
                                             call_update_chat_endpoint):
        authenticate_as_any()

        response = call_update_chat_endpoint(test_data.INVALID_ID, 1)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_user_is_not_pc_member_returns_403(self,
                                                  authenticate_as_non_pc_member,
                                                  call_update_chat_endpoint):
        user, private_chat = authenticate_as_non_pc_member()

        response = call_update_chat_endpoint(private_chat.id, 1)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_if_chat_id_doesnt_exist_returns_404(self,
                                                 test_data,
                                                 authenticate_as_pc_member,
                                                 call_update_chat_endpoint):
        user, private_chat = authenticate_as_pc_member()

        response = call_update_chat_endpoint(private_chat.id, test_data.INVALID_ID)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_chat_id_doesnt_belong_to_referenced_pc(self,
                                                       create_chat,
                                                       create_private_chat,
                                                       authenticate_as_pc_member,
                                                       call_update_chat_endpoint):
        auth_user, referenced_pc = authenticate_as_pc_member()
        other_user = baker.make(User)
        other_pc = create_private_chat([auth_user, other_user])
        chat = create_chat(auth_user, other_pc)

        response = call_update_chat_endpoint(referenced_pc.id, chat.id)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_user_is_not_chat_owner_returns_403(self,
                                       authenticate_as_non_chat_owner,
                                       call_update_chat_endpoint):
        user, private_chat, chat = authenticate_as_non_chat_owner()

        response = call_update_chat_endpoint(private_chat.id, chat.id)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_if_data_is_valid_and_chat_is_closed_returns_423(self,
                                                                  close_chat,
                                                                  authenticate_as_chat_owner,
                                                                  call_update_chat_endpoint):
        user, private_chat, chat = authenticate_as_chat_owner()
        close_chat(chat)

        response = call_update_chat_endpoint(private_chat.id, chat.id)
        
        assert response.status_code == status.HTTP_423_LOCKED

    def test_if_data_is_valid_and_chat_is_open_returns_200(self,
                                                                authenticate_as_chat_owner,
                                                                call_update_chat_endpoint):
        user, private_chat, chat = authenticate_as_chat_owner()
        
        response = call_update_chat_endpoint(private_chat.id, chat.id)
        
        assert response.status_code == status.HTTP_200_OK
        assert (response.data['id'] == chat.id and
                response.data['terminated_at'] is not None)

    def test_if_put_method_returns_405(self, api_client, authenticate_as_chat_owner):
        user, private_chat, chat = authenticate_as_chat_owner()

        response = api_client.put(
            f'/chat/privatechats/{private_chat.id}/chats/{chat.id}/',
            {}
        )
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED