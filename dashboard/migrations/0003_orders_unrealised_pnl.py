# Generated by Django 5.1.1 on 2024-10-11 20:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_alter_orders_open_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='orders',
            name='unrealised_pnl',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
