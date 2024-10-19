import asyncio
import json
import uuid

import ccxt
import redis
from datetime import datetime

# Local
from .tasks import send_order_email
from dashboard.models import Orders

# Django
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer


Users = get_user_model()
redis_client = redis.Redis(host='localhost', port=6379, db=0)


async def retrieve_order():
    """
    Retrieves all active orders from the Orders model.
    This function runs synchronously in the database context,
    wrapped with `sync_to_async` for asynchronous compatibility.

    :return: A queryset of active Orders.
    """

    def func():
        orders = Orders.objects.filter(is_active=True)
        return list(set(orders))

    return await sync_to_async(func)()


async def save_unrealised_pl(order: Orders, new_equity: int | float):
    """
    Updates the unrealized profit/loss (PnL) for an order and saves it.

    :param order: The order instance to update.
    :param new_equity: The calculated new equity value.
    """
    def func():
        order.unrealised_pnl = new_equity
        order.save()

    await sync_to_async(func)()


async def close(order, close_price, amount):
    """
    Closes the order, updates the user's balance, and saves the order details
    such as close price, realized PnL, and close time.

    :param order: The order instance to close.
    :param close_price: The price at which the order is closed.
    :param amount: The amount of realized PnL to apply to the user.
    """
    def func(order, close_price: int | float, amount: int | float):
        if order.is_active and not order.closed_at:
            user = Users.objects.get(email=order.user_id)
            user.balance += (order.dollar_amount + amount)
            user.save()

            order.is_active = not order.is_active
            order.close_price = close_price
            order.closed_at = datetime.now()
            order.realised_pnl = float("{:.2f}".format(order.dollar_amount - (order.dollar_amount - amount)))
            order.unrealised_pnl = 0.0
            order.save()
            return user.balance
        else:
            return None

    balance = await sync_to_async(func)(order, close_price, amount)
    if balance:
        return balance
    return None


def fetch_price(order=None, tick=None):
    """
    Fetches the most recent price of the specified ticker using the Binance API.
    Checks Redis for stored price and updates if a new price is available.

    :param order: The order instance containing the ticker (optional).
    :param tick: The ticker string (optional).
    :return: The fetched price, or None if no update is needed or an error occurs.
    """
    exchange = ccxt.binance()
    exchange.load_markets()
    ticker = order.ticker if order else tick

    try:
        price = exchange.fetch_last_prices([ticker]).get(ticker, {}).get('price', None)
        if price:
            stored_price = redis_client.get(ticker)
            if stored_price:
                if price == float(stored_price.decode()):
                    return None
            redis_client.set(ticker, price)
            return price
    except Exception as e:
        return None


async def start_order_updater():
    """
    Continuously retrieves active orders and starts tracking their price updates.
    Processes each order based on the latest price fetched from the market.

    This function should run in the background.
    """
    while True:
        active_orders = await retrieve_order()
        for order in active_orders:
            price = fetch_price(order)
            if isinstance(price, int | float):
                await process_order(price, order)
            else:
                continue


async def process_order(current_ticker_price, order: Orders):
    """
    Processes each order by calculating the price change and updating
    unrealized PnL or closing the position if necessary.

    :param current_ticker_price: The latest price for the ticker.
    :param order: The order instance being processed.
    """
    price_change = (current_ticker_price - order.open_price) / order.open_price
    new_equity = float("{:.2f}".format(order.dollar_amount - (order.dollar_amount * (1 + price_change))))
    if new_equity == -1 * order.dollar_amount:
        await close_position(order, current_ticker_price, new_equity)
    else:
        await save_unrealised_pl(order, new_equity)
        await send_position_update(order, current_ticker_price, new_equity)


async def close_position(order: Orders, close_price: int | float, amount, reason='liquidated'):
    """
    Closes an order and sends a message via WebSocket to notify the client.

    :param order: The order instance to close.
    :param close_price: The price at which the order is closed.
    :param amount: The realized PnL.
    :param reason: The reason for closing (e.g., liquidation), defaults to 'liquidated'.
    """
    def func():
        message = {
            'topic': 'closed',
            'reason': reason,
            'ticker': order.ticker,
            'amount': amount,
           'close_price': close_price
        }
        message.update(vars(order))

        for k, v in list(message.items()):
            if isinstance(v, (uuid.UUID, datetime)): message[k] = str(v)
            if k == '_state': del message[k]
        return message

    # Close and send to user
    balance = await close(order, close_price, amount)
    if balance:
        message = await sync_to_async(func)()
        message['balance'] = balance
        send_order_email.delay('order_created', 'a new order was created', order.user_id)
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f"orders-{order.user_id.split('@')[0]}",
            {
                'type': 'position_closed',
                'message': message
            }
        )


async def send_position_update(order, current_price: int | float, amount):
    """
    Sends a position update message via WebSocket to notify the client of changes.

    :param order: The order instance being updated.
    :param current_price: The latest price for the ticker.
    :param amount: The updated amount (equity) of the position.
    """
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f"orders-{order.user_id.split('@')[0]}",
        {
            'type': 'position_update',
            'message': {
                'topic': 'position_update',
                'ticker': order.ticker,
                'current_price': current_price,
                'amount': amount,
                'order_id': str(order.order_id)
            }
        }
    )
