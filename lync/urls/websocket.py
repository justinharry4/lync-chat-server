from django.urls import path

from channels.routing import URLRouter

from core.urls import urlpatterns as core_urlpatterns

urlpatterns = [
    path('chat/', URLRouter(core_urlpatterns))
]
