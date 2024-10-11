import asyncio
import json

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model

from .price_updater import redis_client, close_position, fetch_price
from .models import Orders

from channels.generic.websocket import AsyncWebsocketConsumer


User = get_user_model()
comment = "[WEBSOCKET][{topic}] >>> {message}"


class OrderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.user = self.scope['url_route']['kwargs']['email']
        self.room_group_name = f"orders-{self.user.split('@')[0]}"

        # Adding this specific channel to a group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        print(comment.format(topic='CONNECTED', message=f'Successfully connected to client, Group: {self.room_group_name}'))

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print(comment.format(topic='DISCONNECT', message=f"Disconnected from client with code: {code}"))

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        if 'dollar_amount' in data: data['dollar_amount'] = float(data['dollar_amount'])
        print(comment.format(topic='MESSAGE', message=f'Received message from client: {json.dumps(data)}'))

        if data['action'] == 'open':
            await self.create_order(data)
            print(comment.format(topic='SUCCESS', message='Successfully sent order creation confirmation'))
        if data['action'] == 'close':
            await self.close_user_position(data)
            await self.send(json.dumps({'type': 'close_order_confirmation'}))

    async def create_order(self, data):
        def func(data):
            data.pop('csrfmiddlewaretoken', None)
            data['open_price'] = redis_client.get(data['ticker']) if redis_client.get(data['ticker']) else fetch_price(tick=data['ticker'])
            data['is_active'] = True
            return Orders.objects.create(**{key: value for key, value in data.items() if key != 'action'})

        def func2(data):
            user = User.objects.get(email=data['user_id'])
            if user.balance < data['dollar_amount']:
                return None
            user.balance -= data['dollar_amount']
            user.save()
            return 1

        if await sync_to_async(func2)(data):
            return await sync_to_async(func)(data)
        await self.send(json.dumps({'type': 'insufficient_balance', 'message': 'Insufficient funds'}))
        return None

    async def position_closed(self, event):
        await self.send(json.dumps(event['message']))

    async def position_update(self, event):
        await self.send(json.dumps(event['message']))

    async def close_user_position(self, data):
        def func(data):
            order_id = data['order_id']
            order = Orders.objects.get(order_id=order_id)
            current_price = redis_client.get(order.ticker).decode()
            return order, current_price

        order, current_price = await sync_to_async(func)(data)
        await close_position(order, current_price, data['dollar_amount'], 'user requested close')
