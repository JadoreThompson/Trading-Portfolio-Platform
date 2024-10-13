import json
from datetime import datetime, timedelta

from django.db.models.functions import ExtractMonth, ExtractDay

from .forms import CreateOrderForm
from .models import Orders
from .formulas import sharpe_ratio, sortino_ratio, sharpe_std
from .price_updater import redis_client

from django.http import JsonResponse
from django.db.models import Sum
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    td = datetime.now()
    yd = datetime.now() - timedelta(days=1)

    open_positions = Orders.objects.filter(user=request.user, is_active=True)
    closed_positions = Orders.objects.filter(user=request.user, is_active=False)

    # Asset Allocation
    allocs = open_positions.values('ticker').annotate(amount=Sum('unrealised_pnl'))
    total_alloc = sum(item['amount'] for item in allocs)
    asset_allocation = {item['ticker']: { 'amount': item['amount'], 'percentage': (item['amount'] / total_alloc) * 100} for item in allocs}

    # Get distinct months from closed positions
    months = closed_positions.annotate(month=ExtractMonth('created_at')).values_list('month', flat=True).distinct()

    # Aggregate monthly returns for each distinct month
    monthly_positions = closed_positions.annotate(month=ExtractMonth('created_at')).values('month').annotate(
        monthly_returns=Sum('realised_pnl'))
    monthly_positions = closed_positions.values('created_at').annotate(months=ExtractMonth('created_at')).annotate(monthly_returns=Sum('months'))
    months = []
    for item in monthly_positions:
        if item['created_at'].month in months: pass
        else:
            months.append(item['created_at'].month)

    # Statistics Table
    total_returns = sum(months)
    std = sharpe_std(months)
    sharpe = sharpe_ratio(total_returns, months)
    sortino = sortino_ratio(total_returns, months)
    average_daily_return = closed_positions.annotate(day=ExtractDay('closed_at')).annotate(total_returns=Sum('realised_pnl'))
    print(average_daily_return)

    return render(request, "dashboard/dashboard.html", {
        'create_order_form': CreateOrderForm(),
        'email': request.user.email,
        'balance': float("{:.2f}".format(request.user.balance)),
        'open_positions': open_positions,
        'closed_positions': closed_positions,
        'day_change':  sum(
            order.realised_pnl for order in closed_positions if order.closed_at.year == td.year and order.closed_at.month == td.month and order.closed_at.day == td.day
        ) - sum(order.realised_pnl for order in closed_positions if order.closed_at.year == yd.year and order.closed_at.month == yd.month and order.closed_at.day == yd.day),
        'asset_allocation': json.dumps(asset_allocation),
        'sharpe': None
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
    tickers = ['BTC/USDT']
    if request.method == 'GET':
        q = request.GET.get('q', '').upper()
        similars = [item for item in tickers if item.startswith(q)]
        return JsonResponse(status=200, data=similars, safe=False)
    return JsonResponse(status=400, data={'error': 'Invalid request'})
