from uuid import uuid4
from enum import Enum
from toolbox.settings import AUTH_USER_MODEL
from django.db import models
from django.utils.translation import gettext_lazy as _


class TradeType(str, Enum):
    BUY = 'BUY'
    SELL = 'SELL'


class OrderStatus(str, Enum):
    OPEN = 'OPEN'
    CLOSED = 'CLOSED'


class TradeTypeField(models.TextChoices):
    BUY = TradeType.BUY.value, _('buy')
    SELL = TradeType.SELL.value, _('sell')


class OrderStatusField(models.TextChoices):
    OPEN = OrderStatus.OPEN.value, _('open') # Allows for translation - wider audience
    CLOSED = OrderStatus.CLOSED.value, _('closed')


class Orders(models.Model):
    order_id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE) # Deletes all records when user is deleted
    ticker = models.CharField(editable=False, max_length=10)
    dollar_amount = models.FloatField(null=True, blank=True, default=0.0)
    unit_amount = models.FloatField(null=True, blank=True, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    trade_type = models.CharField(max_length=5, choices=TradeTypeField)
    order_status = models.CharField(max_length=6, choices=OrderStatusField, default=OrderStatus.OPEN)

    def __str__(self):
        return f"Order {self.order_id} - Status: {self.order_status} - User: {self.user}"
