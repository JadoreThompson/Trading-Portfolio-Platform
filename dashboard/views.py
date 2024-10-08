import json

from .forms import AccountBalanceForm, CreateOrderForm
from .models import Orders

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse
from django.shortcuts import render, redirect


class InsufficientError(Exception):
    pass


@login_required
def dashboard(request):
    no_balance = request.user.balance == None
    return render(request, 'dashboard/dashboard.html', {
        'no_balance': no_balance,
        'balance_form': AccountBalanceForm,
        'create_order_form': CreateOrderForm,
        'email': request.user.email
    })


def create_balance(request):
    try:
        if request.method == 'POST':
            request.user.balance = request.POST.dict()['balance']
            request.user.save()
            messages.success(request, 'Balance Created')
            return redirect('dashboard')
    except Exception as e:
        print("Error: ", type(e), str(e))
        return redirect('dashboard')


def create_order(request):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            body = {k: v for k, v in data.items() if k != 'csrfmiddlewaretoken' and v}
            body['dollar_amount'] = float(body['dollar_amount'])

            # Creating new order
            if request.user.balance < body['dollar_amount']:
                raise InsufficientError("You don't have enough money")
            Orders.objects.create(user=request.user, **body)

            # Saving new balance
            request.user.balance = request.user.balance - body['dollar_amount']
            request.user.save()
            return JsonResponse(status=200, data={'message': 'Successfully created order'})
    except InsufficientError as e:
        return JsonResponse(status=401, data={'error': str(e)})
    except Exception as e:
        print(type(e), str(e))
        return JsonResponse(status=500, data={"error": str(e)})
