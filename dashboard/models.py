from datetime import datetime
from uuid import uuid4
from django.db import models
from django.conf import settings


class Orders(models.Model):
    ORDER_TYPES = [
        ('long', 'Long'),
        ('short', 'Short'),
    ]
    order_id = models.UUIDField(default=uuid4, primary_key=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ticker = models.CharField()
    dollar_amount = models.FloatField(default=0.0)
    realised_pnl = models.FloatField(null=True, blank=True)
    unrealised_pnl = models.FloatField(null=True, blank=True)
    open_price = models.FloatField(default=0.0, null=True, blank=True)
    close_price = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField()
    order_type = models.CharField(choices=ORDER_TYPES, default='null')


class Watchlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ticker = models.CharField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'ticker'], name='unique_user_ticker')
        ]

    def __str__(self):
        return f'{self.user.email} - {self.ticker}'

