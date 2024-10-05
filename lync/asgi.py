import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lync.settings')

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter
from core.asgi import get_websocket_asgi_application

core_asgi_app = get_websocket_asgi_application()

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': core_asgi_app
})