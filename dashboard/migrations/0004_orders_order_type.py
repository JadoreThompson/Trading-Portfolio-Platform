# Generated by Django 5.1.1 on 2024-10-21 10:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0003_watchlist_unique_user_ticker'),
    ]

    operations = [
        migrations.AddField(
            model_name='orders',
            name='order_type',
            field=models.CharField(choices=[('long', 'LONG'), ('short', 'SHORT')], default='null'),
        ),
    ]
