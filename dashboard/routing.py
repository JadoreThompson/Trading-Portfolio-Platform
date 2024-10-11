from .consumers import OrderConsumer
from django.urls import re_path

websocket_urlpatterns = [
    re_path(r"ws/(?P<email>[\w.@+-]+)/orders$", OrderConsumer.as_asgi()),
]
