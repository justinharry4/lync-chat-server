from dispatcher.exceptions import CodeNotAllowed
from dispatcher.dispatch import MessageHandler
from .status import CLIENT_ACKNOWLEDGMENT


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
        
        handler = MessageHandler(wrapped_func, [CLIENT_ACKNOWLEDGMENT])
        return handler
    
    return decorator
