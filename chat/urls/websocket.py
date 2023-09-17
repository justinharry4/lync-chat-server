from django.urls import path

from ..consumers import PrivateChatConsumer

urlpatterns = [
    path('privatechats/', PrivateChatConsumer.as_asgi())
]