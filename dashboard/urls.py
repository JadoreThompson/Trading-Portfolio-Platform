from .views import dashboard, create_order, get_tickers
from django.urls import path


urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('create_order', create_order, name='create_order'),
    path('tickers/', get_tickers, name='get_tickers'),
]
