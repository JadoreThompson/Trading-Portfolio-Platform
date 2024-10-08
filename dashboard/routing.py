from django.urls import path

from . import consumers


websocket_urlpatterns = [
    path('ws/trade', consumers.TradeConsumer.as_asgi(), name='trade_socket')
]
