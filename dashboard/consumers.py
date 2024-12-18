import json
import uuid
from datetime import datetime

# Django
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from channels.generic.websocket import AsyncWebsocketConsumer

# Local
from .tasks import send_email
from .price_updater import redis_client, close_position, fetch_price
from .models import Orders


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

    async def disconnect(self, code):
        """
        Called when the WebSocket connection is closed.

        Discards the channel from the group and logs the disconnection.
        """
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        """
        Called when a message is received from the WebSocket.

        Parses the incoming message, processes order creation or closing
        requests, and sends relevant confirmations back to the client.
        """
        data = json.loads(text_data)
        if not isinstance(data.get('dollar_amount', None), str):
            data['dollar_amount'] = float(data['dollar_amount'])

        if data.get('action', None) == 'open':
            await self.create_order(data)
        if data.get('action', None) == 'close':
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
            """Creating the order"""
            try:
                data['open_price'] = float(redis_client.get(data['ticker']).decode())
            except AttributeError:
                data['open_price'] = fetch_price(tick=data['ticker'])

            data['is_active'] = True

            return Orders.objects.create(**{
                key: value for
                key, value in data.items()
                if key not in ['action', 'csrfmiddlewaretoken']
            })

        def func2(data):
            # Check if the user has enough balance to create the order.
            user = User.objects.get(email=data['user_id'])
            if user.balance < data['dollar_amount']:
                return None
            user.balance -= data['dollar_amount']
            user.save()
            return user.balance

        valid = await sync_to_async(func2)(data)
        if valid:
            order = await sync_to_async(func)(data)
            order_dict = {
                key: (v if not isinstance(v, (uuid.UUID, datetime, bytes)) else str(v))
                for key, v in vars(order).items()
                if key != '_state'
            }
            order_dict.update({'topic': 'order_created', 'balance': valid})
            await self.send(json.dumps(order_dict))
            send_email.delay('Order Created', 'A new order was created', data['user_id'])
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
