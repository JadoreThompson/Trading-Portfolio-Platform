# Generated by Django 5.1.1 on 2024-10-21 10:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_emailconfirmtokens_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailconfirmtokens',
            name='created_at',
            field=models.IntegerField(default=1729506471),
        ),
    ]
