import json

from django.http import JsonResponse

from .forms import CreateOrderForm
from .models import Orders

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    return render(request, "dashboard/dashboard.html", {
        'create_order_form': CreateOrderForm(),
        'email': request.user.email,
        'balance': request.user.balance,
        'open_positions': Orders.objects.filter(user=request.user, is_active=True)
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

