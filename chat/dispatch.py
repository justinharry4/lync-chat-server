from rest_framework.serializers import ValidationError

from .exceptions import InvalidData, CodeNotAllowed


class Dispatcher():
    def __init__(self, consumer, *handler_set_classes):
        self.consumer = consumer
        self.handler_pairs = []
        handler_sets = [cls(consumer) for cls in handler_set_classes]

        for handler_set in handler_sets:
            handlers = handler_set.get_handlers()
            pairs = [(handler, handler_set) for handler in handlers]

            self.handler_pairs.extend(pairs)

    def dispatch(self, message):
        header = message['header']
        status_code = header['status_code']

        for handler, handler_set in self.handler_pairs:
            if status_code in handler.allowed_codes:
                try:
                    handler(
                        handler_set,
                        key=header['key'],
                        status_code=status_code,
                        message_body=message['body']
                    )
                    break
                except CodeNotAllowed:
                    continue
                except ValidationError as exc:
                    raise InvalidData(exc.detail)


class MessageHandler():
    def __init__(self, func, allowed_codes):
        self.handler_fn = func
        self.allowed_codes = allowed_codes

    def __call__(self, consumer, key, status_code, message_body):
        self.handler_fn(
            consumer,
            key=key,
            status_code=status_code,
            message_body=message_body
        )

    def __repr__(self):
        codes_str = str(self.allowed_codes)
        return f'<MessageHandler allowed_codes={codes_str}>'


class HandlerSet():
    def __init__(self, consumer):
        self.consumer = consumer

    def get_handlers(self):
        class_dict = self.__class__.__dict__

        handlers = [
            value for value in class_dict.values()
            if isinstance(value, MessageHandler)
        ]

        return handlers


