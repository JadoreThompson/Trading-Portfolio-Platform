import json
import uuid
from datetime import datetime

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model

from .price_updater import redis_client, close_position, fetch_price
from .models import Orders

from channels.generic.websocket import AsyncWebsocketConsumer


User = get_user_model()
comment = "[WEBSOCKET][{topic}] >>> {message}"


class OrderConsumer(AsyncWebsocketConsumer):
    """
    A WebSocket consumer that handles order-related events for users.

    This consumer connects to a WebSocket, listens for order creation
    and closing events, and communicates with the Redis price updater
    for real-time price fetching.
    """

    async def connect(self):
        """
        Called when the WebSocket connection is established.

        Accepts the connection and adds the channel to a specific group
        based on the user's email. This allows broadcasting messages to
        all connected clients of the same user.
        """
        await self.accept()
        self.user = self.scope['url_route']['kwargs']['email']
        self.room_group_name = f"orders-{self.user.split('@')[0]}"

        # Adding this specific channel to a group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        print(comment.format(topic='CONNECTED', message=f'Successfully connected to client, Group: {self.room_group_name}'))

    async def disconnect(self, code):
        """
        Called when the WebSocket connection is closed.

        Discards the channel from the group and logs the disconnection.
        """
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print(comment.format(topic='DISCONNECT', message=f"Disconnected from client with code: {code}"))

    async def receive(self, text_data=None, bytes_data=None):
        """
        Called when a message is received from the WebSocket.

        Parses the incoming message, processes order creation or closing
        requests, and sends relevant confirmations back to the client.
        """
        data = json.loads(text_data)
        if 'dollar_amount' in data:
            data['dollar_amount'] = float(data['dollar_amount'])
        print(comment.format(topic='MESSAGE', message=f'Received message from client: {json.dumps(data)}'))

        if data['action'] == 'open':
            await self.create_order(data)
            print(comment.format(topic='SUCCESS', message='Successfully sent order creation confirmation'))
        if data['action'] == 'close':
            order = await self.close_user_position(data)
            # await self.send(json.dumps({'type': 'close_order_confirmation'}.update(vars(order))))

    async def create_order(self, data):
        """
        Creates a new order based on the received data.

        Validates the user's balance before creating the order. If the
        user has sufficient funds, the order is created and the user's
        balance is updated. Otherwise, an insufficient funds message is sent.

        Args:
            data (dict): The order data received from the client.
        """

        def func(data):
            # Remove CSRF token and fetch current price for the ticker.
            data.pop('csrfmiddlewaretoken', None)
            data['open_price'] = float(redis_client.get(data['ticker']).decode()) if float(redis_client.get(data['ticker']).decode()) else fetch_price(tick=data['ticker'])
            data['is_active'] = True

            return Orders.objects.create(**{key: value for key, value in data.items() if key != 'action'})

        def func2(data):
            # Check if the user has enough balance to create the order.
            user = User.objects.get(email=data['user_id'])
            if user.balance < data['dollar_amount']:
                return None
            user.balance -= data['dollar_amount']
            user.save()
            return 1

        if await sync_to_async(func2)(data):
            order = await sync_to_async(func)(data)
            order_dict = {key: value for key, value in vars(order).items() if key != '_state'}
            for k, v in order_dict.items():
                if isinstance(v, (uuid.UUID, datetime, bytes)):
                    order_dict[k] = str(v)

            json_dict = {'topic': 'order_created'}
            json_dict.update(order_dict)
            await self.send(json.dumps(json_dict))
            return None
        else:
            await self.send(json.dumps({'type': 'insufficient_balance', 'message': 'Insufficient funds'}))
            return None

    async def position_closed(self, event):
        """
        Handles the event when a position is closed.

        Sends a message to the client confirming the closure of a position.

        Args:
            event (dict): The event data containing the message.
        """
        await self.send(json.dumps(event['message']))

    async def position_update(self, event):
        """
        Handles position updates and sends the updated message to the client.

        Args:
            event (dict): The event data containing the updated message.
        """
        await self.send(json.dumps(event['message']))

    async def close_user_position(self, data):
        """
        Closes a user's position based on the provided order data.

        Retrieves the order by its ID, fetches the current price, and
        calls the close_position function to handle the closure.

        Args:
            data (dict): The data containing the order ID and dollar amount.
        """
        def func(data):
            order = Orders.objects.get(order_id=data['order_id'])
            return order, redis_client.get(order.ticker).decode()

        order, current_price = await sync_to_async(func)(data)
        await close_position(order, current_price, data['dollar_amount'], 'user requested close')
        return order
