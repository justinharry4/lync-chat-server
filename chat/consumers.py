from channels.generic.websocket import WebsocketConsumer

from .frames import FrameParser, TextFrame, AuthFrameParser
from .dispatch import Dispatcher
from .handlers import PrivateChatMessageHandlerSet
from .models import PrivateChat, Message, TextMessage
from .authentication import JWTAuthentication
from .exceptions import ProtocolError, NotAuthenticated
from . import status


class BaseChatConsumer(WebsocketConsumer):
    authentication_class = JWTAuthentication

    def connect(self):
        self.is_authenticated = False

        self.registry = {}
        self.dispatcher = Dispatcher(self, *self.handler_sets)

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

    def send_acknowledgement(self, key, client_code):
        data = {'client_code': client_code}
        frame = TextFrame(key, status.SERVER_ACKNOWLEDGMENT, data)

        self.send(bytes_data=frame.data)


class PrivateChatConsumer(BaseChatConsumer):
    chat_model = PrivateChat
    chat_type = 'PC'
    handler_sets = [PrivateChatMessageHandlerSet]

    def forward_text_data(self, message:Message):
        private_chat = message.parent_chat

        pass