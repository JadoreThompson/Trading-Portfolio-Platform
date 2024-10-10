from django import forms


class CreateOrderForm(forms.Form):
    TICKER_CHOICES = [
        ('BTC/USDT', "BTCUSDT")
    ]
    ticker = forms.ChoiceField(choices=TICKER_CHOICES)
    dollar_amount = forms.FloatField(min_value=50)
