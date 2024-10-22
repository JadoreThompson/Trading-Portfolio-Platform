import json
import os
import uuid
from datetime import datetime, timedelta

import django.db.utils
import requests
from urllib.parse import quote

# Local
from .forms import CreateOrderForm
from .models import Orders, Watchlist
from .formulas import sharpe_ratio, sortino_ratio, sharpe_std

# Django
from django.db.models import Case, When, Count, Avg
from django.db.models.functions import ExtractMonth, ExtractWeekDay, Trunc
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db.models import Sum
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


CC_HEADER = {
    'Authorization': f'Bearer: {os.getenv('CC_DATA_API_KEY')}'
}


# ---------------------------------------------------------------
# ALL THE DASHBOARD RELATED FUNCTIONS AND ENDPOINTS
# ---------------------------------------------------------------
@login_required
def dashboard(request):
    td = datetime.now()

    open_positions = Orders.objects.filter(user=request.user, is_active=True)
    closed_positions = Orders.objects.filter(user=request.user, is_active=False)

    # Asset Allocation
    allocs = open_positions.values('ticker').annotate(amount=Sum('unrealised_pnl'))
    total_alloc = sum(item['amount'] for item in allocs if item['amount'])
    asset_allocation = {item['ticker']: {'amount': item['amount'], 'percentage': (item['amount'] / total_alloc) * 100}
                        for item in allocs if item.get('amount', None)}

    # Get distinct months from closed positions
    months = closed_positions.annotate(month=ExtractMonth('created_at')).values_list('month', flat=True).distinct()

    # Aggregate monthly returns for each distinct month
    monthly_positions = closed_positions.annotate(month=ExtractMonth('created_at')).values('month').annotate(
        monthly_returns=Sum('realised_pnl'))
    monthly_positions = closed_positions.values('created_at').annotate(months=ExtractMonth('created_at')).annotate(
        monthly_returns=Sum('months'))
    months = []
    for item in monthly_positions:
        if item['created_at'].month in months:
            pass
        else:
            months.append(item['created_at'].month)

    # Statistics Table
    total_returns = sum(months)
    std = sharpe_std(months)
    sharpe = sharpe_ratio(total_returns, months)
    sortino = sortino_ratio(total_returns, months)
    average_daily_return = closed_positions.aggregate(Avg('realised_pnl'))
    win_rate = closed_positions.aggregate(
        total_wins=Sum(Case(When(realised_pnl__gt=0, then=1))),
        total_trades=Count('order_id')
    )
    try:
        win_rate = win_rate['total_wins'] / win_rate['total_trades']
    except (ZeroDivisionError, TypeError):
        win_rate = 0

    daily_pnl = closed_positions \
        .annotate(weekday=ExtractWeekDay('created_at')) \
        .values('weekday') \
        .annotate(total_return=Sum('realised_pnl'))

    wkday_map = {
        1: 'Sunday', 2: 'Monday', 3: 'Tuesday', 4: 'Wednesday',
        5: 'Thursday', 6: 'Friday', 7: 'Saturday', 8: 'Sunday'
    }

    daily_wins = {wkday_map.get(item['weekday'], 'Unknown'): round(item['total_return']) for item in
                  daily_pnl}

    balance_growth = {str((td - timedelta(days=item['weekday'])).date()): item['total_return'] for item in daily_pnl}
    balance_growth['starting_balance'] = round(request.user.balance + sum(daily_wins[key] for key in daily_wins), 2)

    open_pos = [
        {
            k: (v if not isinstance(v, (uuid.UUID, datetime)) else str(v))
            for k, v in order.items() if k != '_state'
        }
        for order in [vars(order) for order in open_positions]
    ]

    print(Watchlist.objects.filter(user=request.user))

    return render(request, "dashboard/dashboard.html", {
        'create_order_form': CreateOrderForm(),
        'email': request.user.email,
        'balance': round(request.user.balance, 2),
        'open_positions': open_pos,
        'open_js': json.dumps(open_pos),
        'closed_positions': closed_positions,
        'day_change': round(sum(
            order.realised_pnl for order in closed_positions if
            order.closed_at.year == td.year
            and order.closed_at.month == td.month
            and order.closed_at.day == td.day
        ), 2),
        'unrealised_gain': round(sum(order.unrealised_pnl for order in open_positions if order.unrealised_pnl), 2),
        'realised_gain': round(sum(order.realised_pnl for order in closed_positions), 2),
        'asset_allocation': json.dumps(asset_allocation),
        'sharpe': sharpe,
        'sortino': sortino,
        'average_daily_return': round(average_daily_return['realised_pnl__avg'], 2)
        if average_daily_return['realised_pnl__avg'] else 0,
        'win_rate': round(win_rate, 2),
        'volume': sum(order.dollar_amount for order in closed_positions),
        'daily_wins': daily_wins,
        'balance_growth': json.dumps(balance_growth),
        'watchlist': Watchlist.objects.filter(user=request.user)
    })


def create_order(request):
    if request.method == "POST":
        try:
            data = {key: value for key, value in request.POST.dict().items() if key != 'csrfmiddlewaretoken'}

            data['user'] = request.user
            request.user.balance -= float(data['dollar_amount'])
            request.user.save()

            order = Orders.objects.create(**data)
            return JsonResponse(status=200, data={"message": "Order created", "order_id": order.order_id})
        except Exception as e:
            print({"error": f"{str(e)}", "type": f"{type(e)}"})
            return JsonResponse(status=500, data={"error": f"{str(e)}", "type": f"{type(e)}"})
    else:
        return JsonResponse(status=403, data={"error": "Invalid request"})


def get_tickers(request):
    """
    Returns the ticker that starts with the input
    :param request:
    :return:
    """
    tickers = [
        'BTC/USDT', 'ETH/USDT', 'LTC/USDT', 'SOL/USDT'
    ]
    if request.method == 'GET':
        q = request.GET.get('q', '').upper()
        similars = [item for item in tickers if item.startswith(q)]
        return JsonResponse(status=200, data=similars, safe=False)
    return JsonResponse(status=400, data={'error': 'Invalid request'})


def get_growth(request):
    if request.method == 'GET':
        interval = request.GET.get('interval')
        if interval not in ['week', 'month', 'year']:
            return JsonResponse(status=405, data={'error': 'Invalid interval. Must be week, month, year'})

        positions = Orders.objects.filter(user=request.user, is_active=False)
        if interval == 'week':
            target_interval = 'day'
            trades = positions.filter(closed_at__gt=datetime.now() - timedelta(days=7))\
                .annotate(day=Trunc('closed_at', 'day'))\
                .values('day')\
                .annotate(total_return=Sum('realised_pnl'))\
                .order_by('day')
        if interval == 'month':
            target_interval = 'week'
            trades = positions.filter(closed_at__gt=datetime.now() - timedelta(days=30))\
                .annotate(week=Trunc('closed_at', 'week'))\
                .values('week')\
                .annotate(total_return=Sum('realised_pnl'))\
                .order_by('week')
        if interval == 'year':
            target_interval = 'month'
            trades = positions.filter(closed_at__gt=datetime.now() - timedelta(days=365))\
                .annotate(month=Trunc('closed_at', 'month'))\
                .values('month')\
                .annotate(total_return=Sum('realised_pnl'))\
                .order_by('month')

        data = {
            str(item[target_interval].date()): float("{:.2f}".format(item['total_return']))
            for item in trades
        }
        data['starting_balance'] = request.user.balance + sum(data[key] for key in data)
        return JsonResponse(status=200, data=data)
    return JsonResponse(status=400, data={'error': 'bad request'})


# ---------------------------------------------------------------
#                                   ALL WATCHLIST RELATED
# ---------------------------------------------------------------
def get_currency_stats(symbol):
    """
    Returns a dictionary of data points for the symbol. This is not a view function
    :param symbol:
    :return:
    """
    r = requests.get(
        f'https://data-api.cryptocompare.com/index/cc/v1/latest/tick?market=cadli&instruments={symbol}&apply_mapping=true',
        headers=CC_HEADER
    )
    cols = [
        'CURRENT_DAY_QUOTE_VOLUME', 'CURRENT_DAY_OPEN', 'CURRENT_DAY_HIGH',
        'CURRENT_DAY_LOW', 'CURRENT_WEEK_LOW', 'CURRENT_WEEK_OPEN', 'CURRENT_WEEK_HIGH',
        'CURRENT_WEEK_QUOTE_VOLUME'
    ]
    return {key.lower(): round(value, 2) for key, value in r.json()['Data'][symbol].items() if key in cols}


@login_required
def get_watchlist(request):
    try:
        BASE_URL = 'https://newsapi.org/v2'
        API_KEY = os.getenv('NEWS_API_KEY')
        currency = request.GET.get('q')
        currency_statistics = get_currency_stats(currency)

        r = requests.get(
            BASE_URL + f"/everything?"
                       f"q={currency}"
                       f"&apiKey={quote(API_KEY)}"
                       f"&from={datetime.now().date() - timedelta(days=2)}"
                       f"&language=en"
                       f"&pageSize=12"
                       "&sortBy=pubishedAt"
        )
        articles = [
            {
                'source': item.get('source', {}).get('name', None),
                'title': item.get('title', None),
                'image': item.get('urlToImage', None),
                'description': item.get('description', None)
            } for item in r.json()['articles'][:10]
        ]
        return render(request, 'dashboard/watchlist.html', {
            'symbol': currency,
            'email': request.user.email,
            'cc_data': currency_statistics,
            'articles': articles,
            'watchlist': Watchlist.objects.filter(user=request.user)
        })
    except Exception as e:
        print(type(e), str(e), end=f"\n{"-" * 10}\n")


def get_currency_data(request):
    if request.method == 'GET':
        data = get_currency_stats(request.GET.get('q'))
        return JsonResponse(status=200, data=data)
    else:
        return JsonResponse(status=400, data={'error': 'Invalid request type'})


@csrf_exempt
def add_to_watchlist(request):
    if request.method != 'POST':
        return JsonResponse(status=400, data={'error': 'Invalid request type'})

    try:
        body = json.loads(request.body)
        Watchlist.objects.create(user=request.user, ticker=body['ticker'].replace("/", "-"))
        return JsonResponse(status=200, data={'message': 'Successfully added to watchlist'})
    except django.db.utils.IntegrityError:
        return JsonResponse(status=200, data={'message': 'Item already in watchlist'})
    except Exception as e:
        print(type(e), str(e))
        return JsonResponse(status=500, data={'error': 'Something went wrong'})


@csrf_exempt
def remove_from_watchlist(request):
    if request.method != 'POST':
        return JsonResponse(status=400, data={'error': 'Invalid request type'})

    try:
        Watchlist.objects.get(user=request.user, ticker=json.loads(request.body).get('ticker').replace("/", "-")).delete()
        return JsonResponse(status=200, data={'message': 'Item deleted from watchlist'})
    except Watchlist.DoesNotExist:
        return JsonResponse(status=404, data={'error': "Item doesn't exist"})
    except Exception as e:
        print(type(e), str(e))
        return JsonResponse(status=500, data={'error': 'Something went wrong'})
