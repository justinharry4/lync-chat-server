from .dispatch import MessageHandler


def message_handler(allowed_codes):
    def decorator(func):
        handler = MessageHandler(func, allowed_codes)
        return handler

    return decorator