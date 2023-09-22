from django.db import transaction

from .models import Message, TextMessage
from .serializers import MessageSerializer
from .dispatch import HandlerSet
from .decorators import message_handler, ack_handler
from .exceptions import InvalidData
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


class PrivateChatMessageHandlerSet(HandlerSet):
    @message_handler(allowed_codes=head_text_codes)
    def handle_text_data(self, key, status_code, message_body):
        cons = self.consumer
        content_format = message_body['content_format']

        if content_format != Message.FORMAT_TEXT:
            raise InvalidData(
                f'Invalid content format {content_format} '
                'for text message'
            )

        chat_id = message_body['parent_id']
        text = message_body['content']

        message_context = {
            'user': cons.user,
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
            # message = serializer.save()

            if status_code == status.CLIENT_HEAD_TEXT_EOC:
                # TextMessage.objects.create(
                #     text=text,
                #     message=message
                # )
                pass
            elif status_code == status.CLIENT_HEAD_TEXT_MCE:
                # entry = {'model_object': message, 'text_str': text}
                # cons.registry.setdefault(key, entry)
                pass
        
        cons.send_acknowledgement(key, status_code)
        # print(message, serializer.data, getattr(message, 'content'))
        