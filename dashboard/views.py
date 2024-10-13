import json
from datetime import datetime, timedelta

from .forms import CreateOrderForm
from .models import Orders

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    td = datetime.now()
    yd = datetime.now() - timedelta(days=1)

    open_positions = Orders.objects.filter(user=request.user, is_active=True)
    closed_positions = Orders.objects.filter(user=request.user, is_active=False)

    # Generating a tuple of (ticker, percentage, cumulative amount) for each ticker the user has in open positions
    allocs = open_positions.values('ticker').annotate(amount=Sum('unrealised_pnl'))
    total_alloc = sum(item['amount'] for item in allocs)

    asset_allocation = {
        item['ticker']: {
            'amount': item['amount'],
            'percentage': (item['amount'] / total_alloc) * 100
        } for item in allocs
    }

    return render(request, "dashboard/dashboard.html", {
        'create_order_form': CreateOrderForm(),
        'email': request.user.email,
        'balance': float("{:.2f}".format(request.user.balance)),
        'open_positions': open_positions,
        'closed_positions': closed_positions,
        'day_change':  sum(
            order.realised_pnl for order in closed_positions if order.closed_at.year == td.year and order.closed_at.month == td.month and order.closed_at.day == td.day
        ) - sum(order.realised_pnl for order in closed_positions if order.closed_at.year == yd.year and order.closed_at.month == yd.month and order.closed_at.day == yd.day),
        'asset_allocation': json.dumps(asset_allocation)
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
