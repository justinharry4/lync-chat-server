from .exceptions import UnboundDecorator, CodeNotAllowed
from .dispatch import MessageHandler
from .status import CLIENT_ACKNOWLEDGMENT

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


def ack_handler(allowed_server_codes):
    def decorator(func):
        def wrapped_func(*args, **kwargs):
            server_code = kwargs['message_body']['server_code']

            if server_code not in allowed_server_codes:
                raise CodeNotAllowed(
                    f'server status code `{server_code}` is not '
                    'allowed by the acknowledgement handler'
                )
            
            return func(*args, **kwargs)
        
        handler = MessageHandler(wrapped_func, CLIENT_ACKNOWLEDGMENT)
        return handler
    
    return decorator
