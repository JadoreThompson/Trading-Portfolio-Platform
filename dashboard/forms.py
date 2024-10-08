from django import forms


class AccountBalanceForm(forms.Form):
    CHOICES = [
        (100000, '100,000'),
        (250000, '250,000'),
        (500000, '500,000'),
    ]
    balance = forms.ChoiceField(choices=CHOICES, label='Choose a balance')


class CreateOrderForm(forms.Form):
    CHOICES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]

    ticker = forms.CharField()
    dollar_amount = forms.DecimalField(decimal_places=2, required=False)
    unit_amount = forms.IntegerField(required=False)
    trade_type = forms.ChoiceField(choices=CHOICES)
