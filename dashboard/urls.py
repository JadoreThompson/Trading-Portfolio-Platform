from .views import dashboard, create_balance, create_order
from django.views.decorators.csrf import csrf_exempt
from django.urls import path

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('create_balance', create_balance, name='create_balance'),
    path('create_order', csrf_exempt(create_order), name='create_order'),
]
