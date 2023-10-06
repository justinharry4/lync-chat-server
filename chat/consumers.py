import uuid

from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

from .frames import FrameParser, TextFrame, AuthFrameParser
from .dispatch import Dispatcher
from .handlers import PrivateChatMessageHandlerSet
from .models import PrivateChat, Message, TextMessage, ChatClient
from .authentication import JWTAuthentication
from .exceptions import ProtocolError, NotAuthenticated
from . import status


class BaseChatConsumer(WebsocketConsumer):
    authentication_class = JWTAuthentication

    def connect(self):
        self.is_authenticated = False

        self.registry = {}
        self.dispatcher = Dispatcher(self, *self.handler_set_classes)

        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        if not self.is_authenticated:
            try:
                parser = AuthFrameParser(bytes_data)
                auth_data = parser.parse()

                self.authenticate_client(auth_data)
            except NotAuthenticated as exc:
                self.close()
                print(exc.__class__.__name__, '\n', exc)
        else:
            try:
                parser = FrameParser(bytes_data)
                message = parser.parse()

                self.dispatcher.dispatch(message)
            except ProtocolError as exc:
                print(exc.__class__.__name__, '\n', exc)

    def authenticate_client(self, auth_data):
        auth = self.authentication_class()
        user = auth.authenticate(auth_data)

        self.scope['user'] = user
        self.client = ChatClient.objects.create(
            user=user,
            chat_type=self.chat_type,
            channel_name=self.channel_name,
        )

        self.is_authenticated = True

    def send_acknowledgement(self, key, client_code, **kwargs):
        data = {'client_code': client_code, **kwargs}
        frame = TextFrame(key, status.SERVER_ACKNOWLEDGMENT, data)

        self.send(bytes_data=frame.data)


class PrivateChatConsumer(BaseChatConsumer):
    chat_model = PrivateChat
    chat_type = 'PC'
    handler_set_classes = [PrivateChatMessageHandlerSet]
    receiver_type = 'recieve.channel.layer.event'

    def recieve_channel_layer_event(self, event):
        print('channel event recieved')

        event_data = event['data']

        if event_data['content_format'] == Message.FORMAT_TEXT:
            self.send_text_data(event_data)
        else:
            pass

    def forward_text_data(self, message):
        private_chat_id = message.parent_id
        private_chat = self.chat_model.objects \
            .prefetch_related('participant_users') \
            .get(pk=private_chat_id)
        
        sender = self.scope['user']
        queryset = private_chat.participant_users.exclude(pk=sender.id)
        recipient = queryset[0]
        clients = ChatClient.objects.filter(user=recipient)

        channel_data = {
            'type': self.receiver_type,
            'data': {
                'chat_id': private_chat_id,
                'message_id': message.id,
                'content': message.content.text,
                'content_format': Message.FORMAT_TEXT,
                'time_stamp': message.time_stamp.isoformat(),
            }
        }

        for client in clients:
            # print('chat_client', client, client.user)
            channel_name = client.channel_name
            async_to_sync(self.channel_layer.send)(channel_name, channel_data)  

    def send_text_data(self, message_data):
        key = str(uuid.uuid4())

        data = {'chat_type': self.chat_type, **message_data}

        frame = TextFrame(key, status.SERVER_HEAD_TEXT_EOC, data)

        self.send(bytes_data=frame.data)
