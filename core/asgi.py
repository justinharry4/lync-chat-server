from django.conf import settings

from channels.routing import URLRouter
from channels.security.websocket import OriginValidator

from lync.urls.websocket import urlpatterns

def get_websocket_asgi_application():
    routed_app = URLRouter(urlpatterns)

    secured_app = OriginValidator(routed_app, settings.CORS_ALLOWED_ORIGINS)
    
    return secured_app