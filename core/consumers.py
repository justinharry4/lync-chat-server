import uuid
from asgiref.sync import async_to_sync

from dispatcher.consumers import BaseConsumer
from dispatcher.frames import TextFrame
from dispatcher.models import Client
from chat.models import PrivateChat, Message
from .handlers import PrivateChatMessageHandlerSet, PrivateChatAckHandlerSet
from .authentication import JWTAuthentication
from . import status


class PrivateChatConsumer(BaseConsumer):
    authentication_class = JWTAuthentication
    chat_model = PrivateChat
    chat_type = 'PC'
    receiver_type = 'recieve.channel.layer.event'
    handler_set_classes = [
        PrivateChatMessageHandlerSet,
        PrivateChatAckHandlerSet,
    ]

    def send_acknowledgement(self, key, client_code, **kwargs):
        data = {'client_code': client_code, **kwargs}
        frame = TextFrame(key, status.SERVER_ACKNOWLEDGMENT, data)

        self.send(bytes_data=frame.data)

    def channel_layer_send(self, channel_name, data):
        async_to_sync(self.channel_layer.send)(channel_name, data)  

    def recieve_channel_layer_event(self, event):
        event_data = event['data']
        content_format = event_data.get('content_format')
        status = event_data.get('delivery_status')

        if content_format:
            if content_format == Message.FORMAT_TEXT:
                self.send_text_data(event_data)
            else:
                pass
        elif status:
            self.send_delivery_status_data(event_data)

    def forward_text_data(self, message):
        private_chat_id = message.parent_id
        private_chat = self.chat_model.objects \
            .prefetch_related('participant_users') \
            .get(pk=private_chat_id)
        
        sender = self.scope['user']
        queryset = private_chat.participant_users.exclude(pk=sender.id)
        recipient = queryset[0]
        clients = Client.objects.filter(user=recipient)

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
            channel_name = client.channel_name
            self.channel_layer_send(channel_name, channel_data)

    def send_text_data(self, message_data):
        key = str(uuid.uuid4())
        data = {'chat_type': self.chat_type, **message_data}
        frame = TextFrame(key, status.SERVER_TEXT_DATA, data)

        entry = {'message_id': message_data['message_id']}
        self.registry.setdefault(key, entry)

        self.send(bytes_data=frame.data)

    def send_delivery_status_data(self, status_data):
        key = str(uuid.uuid4())
        data = {'chat_type': self.chat_type, **status_data}
        frame = TextFrame(key, status.SERVER_MESSAGE_STATUS, data)

        self.send(bytes_data=frame.data)