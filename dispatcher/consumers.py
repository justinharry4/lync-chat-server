from channels.generic.websocket import WebsocketConsumer

from .frames import FrameParser, AuthFrameParser
from .dispatch import Dispatcher
from .models import Client
from .exceptions import ProtocolError, NotAuthenticated


class BaseConsumer(WebsocketConsumer):
    authentication_class = None

    def connect(self):
        self.is_authenticated = False

        self.registry = {}
        self.dispatcher = Dispatcher(self, *self.handler_set_classes)

        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        if self.authentication_class and not self.is_authenticated:
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
        self.client = Client.objects.create(
            user=user,
            channel_name=self.channel_name,
        )

        self.is_authenticated = True
