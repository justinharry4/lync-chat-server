from django.db import models
from django.conf import settings


class Client(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    channel_name = models.CharField(max_length=255)
    connection_time = models.DateTimeField(auto_now_add=True)
