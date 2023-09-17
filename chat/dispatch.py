from rest_framework.serializers import ValidationError

from .frames import TextFrame, FrameParser
from .exceptions import InvalidMessageData


class Dispatcher():
    def __init__(self, consumer):
        self.consumer = consumer
        consumer_class_dict = consumer.__class__.__dict__

        self.handlers = [
            value for value in consumer_class_dict.values()
            if isinstance(value, MessageHandler)
        ]

    def dispatch(self, message):
        header = message['header']
        status_code = header['status_code']

        for handler in self.handlers:
            if status_code in handler.allowed_codes:
                try:
                    handler.handler_fn(
                        self.consumer,
                        key=header['key'],
                        status_code=status_code,
                        message_body=message['body']
                    )
                    break
                except ValidationError as exc:
                    raise InvalidMessageData(exc.detail)


class MessageHandler():
    def __init__(self, func, allowed_codes):
        self.handler_fn = func
        self.allowed_codes = allowed_codes

    def __call__(self, consumer, key, status_code, message_body):
        self.handler_fn(consumer, key, status_code, message_body)

    def __repr__(self):
        codes_str = str(self.allowed_codes)
        return f'<MessageHandler allowed_codes={codes_str}>'
