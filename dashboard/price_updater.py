import ccxt
import redis
from asgiref.sync import sync_to_async

from channels.layers import get_channel_layer

from dashboard.models import Orders

redis_client = redis.Redis(host='localhost', port=6379, db=0)


async def retrieve_order():
    def func():
        orders = Orders.objects.filter(is_active=True)
        return orders
    return await sync_to_async(func)()


async def save_unrealised_pl(order: Orders, new_equity: int | float):
    def func():
        order.unrealised_pnl = float("{:.2f}".format(new_equity))
        order.save()
    await sync_to_async(func)()


async def close(order, close_price, amount):
    def func(order, close_price: int | float, amount: int | float):
        order.is_active = False
        order.close_price = close_price
        order.realised_pnl = amount
        order.unrealised_pnl = 0.0
        order.save()
    await sync_to_async(func)(order, close_price, amount)


def fetch_price(order=None, tick=None):
    """
    Fetches most recent price and assigns value to redis
    :param order:
    :return:
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
    Retrieves all active orders and starts tracking them
    :return:
    """
    while True:
        active_orders = await retrieve_order()
        async for order in active_orders:
            price = fetch_price(order)
            if isinstance(price, int | float):
                await process_order(price, order)


async def process_order(current_ticker_price, order: Orders):
    price_change = (current_ticker_price - order.open_price) / order.open_price
    new_equity = order.dollar_amount * (1 + price_change)
    if new_equity == -1 * order.dollar_amount:
        await close_position(order, current_ticker_price, new_equity)
    else:
        await save_unrealised_pl(order, new_equity)
        await send_position_update(order, current_ticker_price, new_equity)


async def close_position(order: Orders, close_price: int | float, amount, reason=None):
    await close(order, close_price, amount)

    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f"orders-{order.user_id.split('@')[0]}",
        {
            'type': 'position_closed',
            'message': {
                'reason': reason if reason else 'liquidated',
                'ticker': order.ticker,
                'amount': amount,
                'close_price': close_price
            }
        }
    )


async def send_position_update(order, current_price: int | float, amount):
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f"orders-{order.user_id.split('@')[0]}",
        {
            'type': 'position_update',
            'message': {
                'ticker': order.ticker,
                'current_price': current_price,
                'amount': amount,
                'order_id': str(order.order_id)
            }
        }
    )
