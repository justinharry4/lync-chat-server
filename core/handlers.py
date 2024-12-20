import datetime

from django.db import transaction

from chat.models import Chat, Message, TextMessage
from chat.serializers import ChatSerializer, MessageSerializer, UpdateMessageSerializer
from dispatcher.models import Client
from dispatcher.dispatch import HandlerSet
from dispatcher.decorators import message_handler
from dispatcher.exceptions import InvalidData
from .decorators import ack_handler
from . import status


head_file_codes = [
    status.CLIENT_HEAD_FILE_EOC,
    status.CLIENT_HEAD_FILE_MCE,
]
extra_file_codes = [
    status.CLIENT_MORE_FILE_EOC,
    status.CLIENT_MORE_FILE_MCE
]

def get_term_chat_users(parent_chat, parent_chat_type):
    participant_users = parent_chat.participant_users.all()

    open_chats = Chat.objects \
        .select_related('user') \
        .filter(
            user__in=participant_users,
            object_id=parent_chat.id,
            parent_chat_type=parent_chat_type,
            terminated_at=None,
        )
    
    participant_user_ids = [user.id for user in participant_users]
    open_chat_user_ids = [chat.user.id for chat in open_chats]
    term_chat_user_ids = set(participant_user_ids) - set(open_chat_user_ids)

    term_chat_users = [
        user for user in participant_users
        if user.id in term_chat_user_ids
    ]
    
    return term_chat_users


class PrivateChatMessageHandlerSet(HandlerSet):
    @message_handler(allowed_codes=[status.CLIENT_TEXT_DATA])
    def handle_text_data(self, key, status_code, message_body):
        cons = self.consumer
        content_format = message_body['content_format']

        if content_format != Message.FORMAT_TEXT:
            raise InvalidData(
                f'Invalid content format {content_format} '
                'for text message'
            )

        chat_id = message_body['chat_id']
        text = message_body['content']

        private_chat = cons.chat_model.objects \
            .prefetch_related('participant_users') \
            .get(pk=chat_id)
        
        term_chat_users = get_term_chat_users(
            parent_chat=private_chat,
            parent_chat_type=cons.chat_type
        )

        if len(term_chat_users) > 0:
            chat_context = {
                'parent_chat_model': cons.chat_model,
                'parent_chat_type': cons.chat_type,
                'parent_chat_id': private_chat.id,
            }

            for user in term_chat_users:
                chat_context['user'] = user

                chat_serializer = ChatSerializer(
                    data={},
                    context=chat_context,
                )
                chat_serializer.is_valid(raise_exception=True)
                chat_serializer.save()

        message_context = {
            'user': cons.scope['user'],
            'parent_chat_model': cons.chat_model,
            'parent_chat_type': cons.chat_type,
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
            message = serializer.save()

            TextMessage.objects.create(
                text=text,
                message=message
            )

            update_data = {
                'delivery_status': Message.STATUS_SENT,
                'time_stamp': datetime.datetime.utcnow(),
            }
            update_serializer = UpdateMessageSerializer(
                message,
                data=update_data,
            )
            update_serializer.is_valid(raise_exception=True)
            update_serializer.save()

        ack_data = {
            'message_id': message.id,
            'time_stamp': message.time_stamp.isoformat(),
        }
        
        cons.send_acknowledgement(key, status_code, **ack_data)
        cons.forward_text_data(message)

    @message_handler(allowed_codes=[status.CLIENT_MESSAGE_STATUS])
    def handle_delivery_status_data(self, key, status_code, message_body):
        cons = self.consumer
        chat_id = message_body['chat_id']
        delivery_status = message_body['delivery_status']
        user = cons.scope['user']

        if delivery_status == Message.STATUS_DELIVERED:
            query_dict = {'delivery_status': Message.STATUS_SENT}
        elif delivery_status == Message.STATUS_VIEWED:
            query_dict = {
                'delivery_status__in': [Message.STATUS_SENT, Message.STATUS_DELIVERED]
            }

        target_messages = Message.objects \
            .exclude(sender=user) \
            .filter(
                parent_id=chat_id,
                parent_chat_type=cons.chat_type,
                **query_dict,
            )

        update_data = {'delivery_status': delivery_status}
        update_serializer = UpdateMessageSerializer(
            target_messages,
            data=[update_data],
            many=True,
            static=True,
        )

        update_serializer.is_valid(raise_exception=True)
        update_serializer.save()


class PrivateChatAckHandlerSet(HandlerSet):
    @ack_handler(allowed_server_codes=[status.SERVER_TEXT_DATA])
    def ack_text_data_send(self, key, status_code, message_body):
        cons = self.consumer
        entry = cons.registry.get(key)

        message_id = entry['message_id']
        delivery_status = message_body['delivery_status']
        message = Message.objects.select_related('sender').get(pk=message_id)

        update_data = {'delivery_status': delivery_status}
        update_serializer = UpdateMessageSerializer(message, update_data)
        update_serializer.is_valid(raise_exception=True)
        update_serializer.save()

        cons.registry.pop(key)

        sender = message.sender
        clients = Client.objects.filter(user=sender)

        channel_data = {
            'type': cons.receiver_type,
            'data': {
                'chat_id': message.parent_id,
                'message_id': message.id,
                'delivery_status': message.delivery_status,
            }
        }

        for client in clients:
            channel_name = client.channel_name
            cons.channel_layer_send(channel_name, channel_data)

