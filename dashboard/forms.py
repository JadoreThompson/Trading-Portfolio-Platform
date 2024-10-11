from django import forms


class CreateOrderForm(forms.Form):
    TICKER_CHOICES = [
        ('BTC/USDT', "BTCUSDT")
    ]

    ticker = forms.CharField(label='Select an option', max_length=10)
    dollar_amount = forms.FloatField(min_value=50)
