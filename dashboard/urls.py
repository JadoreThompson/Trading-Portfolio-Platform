from .views import (
    dashboard, create_order, get_tickers, get_growth, get_watchlist,
    add_to_watchlist, remove_from_watchlist
)
from django.urls import path


urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('create_order', create_order, name='create_order'),
    path('tickers/', get_tickers, name='get_tickers'),
    path('growth-interval/', get_growth, name='get_growth'),
    path('watchlist/', get_watchlist, name='watchlist'),
    path('add-watchlist', add_to_watchlist, name='add_to_watchlist'),
    path('remove-watchlist', remove_from_watchlist, name='remove_from_watchlist'),
]
