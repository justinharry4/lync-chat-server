from django.db import transaction

from channels.generic.websocket import WebsocketConsumer

from .frames import FrameParser, TextFrame
from .dispatch import Dispatcher
from .models import PrivateChat, Message, TextMessage, get_user_model
from .serializers import MessageSerializer
from .exceptions import ProtocolError, InvalidMessageData
from .decorators import message_handler
from . import status

head_text_codes = [
    status.CLIENT_HEAD_TEXT_EOC,
    status.CLIENT_HEAD_TEXT_MCE
]
extra_text_codes = [
    status.CLIENT_MORE_TEXT_EOC,
    status.CLIENT_MORE_TEXT_MCE
]
head_file_codes = [
    status.CLIENT_HEAD_FILE_EOC,
    status.CLIENT_HEAD_FILE_MCE,
]
extra_file_codes = [
    status.CLIENT_MORE_FILE_EOC,
    status.CLIENT_MORE_FILE_MCE
]


class BaseChatConsumer(WebsocketConsumer):
    def connect(self):
        self.registry = {}
        self.dispatcher = Dispatcher(self)
        
        user_model = get_user_model()
        self.user = user_model.objects.get(pk=3)

        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        try:
            parser = FrameParser(bytes_data)

            message = parser.parse()
            # print(message)

            self.dispatcher.dispatch(message)
        except ProtocolError as exc:
            print('Exception\n', exc)

    def send_acknowledgement(self, key, client_code):
        data = {'client_code': client_code}
        frame = TextFrame(key, status.SERVER_ACKNOWLEDGMENT, data)

        self.send(bytes_data=frame.data)


class PrivateChatConsumer(BaseChatConsumer):
    chat_model = PrivateChat
    chat_type = 'PC'

    @message_handler(allowed_codes=head_text_codes)
    def handle_text_data(self, key, status_code, message_body):
        content_format = message_body['content_format']

        if content_format != Message.FORMAT_TEXT:
            raise InvalidMessageData(
                f'Invalid content format {content_format} '
                'for text message'
            )

        chat_id = message_body['parent_id']
        text = message_body['content']

        message_context = {
            'user': self.user,
            'parent_chat_model': self.chat_model,
            'parent_chat_type': self.chat_type,
        }
        message_data = {
            'parent_id': chat_id,
            'content_format': content_format,
        }

        with transaction.atomic():
            serializer = MessageSerializer(
                data=message_data,
                context=message_context
            )
            serializer.is_valid(raise_exception=True)
            # message = serializer.save()

            if status_code == status.CLIENT_HEAD_TEXT_EOC:
                # TextMessage.objects.create(
                #     text=text,
                #     message=message
                # )
                pass
            elif status_code == status.CLIENT_HEAD_TEXT_MCE:
                # entry = {'model_object': message, 'text_str': text}
                # self.registry.setdefault(key, entry)
                pass
        
        self.send_acknowledgement(key, status_code)
        # print(message, serializer.data, getattr(message, 'content'))
        