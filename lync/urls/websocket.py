from django.urls import path

from channels.routing import URLRouter

from chat.urls.websocket import urlpatterns

urlpatterns = [
    path('chat/', URLRouter(urlpatterns))
]
