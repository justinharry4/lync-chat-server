from .exceptions import UnboundDecorator
from .dispatch import MessageHandler

class MessageHandlerDecorator():
    def bind_consumer(self, consumer):
        self.consumer = consumer

    def __call__(self, allowed_codes):
        if not hasattr(self, 'consumer'):
            raise UnboundDecorator(
                f'{self.__class__} object must be bound to a '
                'consumer before being called'
            )
        
        def dec(): pass


def message_handler(allowed_codes):
    def decorator(func):
        handler = MessageHandler(func, allowed_codes)
        return handler

    return decorator