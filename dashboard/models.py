from uuid import uuid4
from django.db import models
from django.conf import settings


class Orders(models.Model):
    order_id = models.UUIDField(default=uuid4, primary_key=True, editable=False)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
