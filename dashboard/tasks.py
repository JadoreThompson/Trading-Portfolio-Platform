import os
import base64
import json
from uuid import uuid4
from datetime import datetime, timedelta
import jinja2
import pdfkit

from celery import shared_task
from django.conf import settings
from django_celery_beat.models import CrontabSchedule, PeriodicTask

# Local
from toolbox.celery import app
from .models import Orders

# Google
from email.message import EmailMessage
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


template_loader = jinja2.FileSystemLoader('templates/')
template_env = jinja2.Environment(loader=template_loader)
template = template_env.get_template('weekly_breakdown_pdf.html')


@shared_task
def send_email(subject, body, recipient, file=None):
    creds, _ = google.auth.default()

    try:
        service = build("gmail", "v1", credentials=creds)

        message = EmailMessage()
        message.set_content(body)
        message["To"] = recipient
        message["From"] = settings.SENDER_EMAIL
        message["Subject"] = subject

        if file:
            with open(file, 'rb') as f:
                pdf_data = f.read()
                message.add_attachment(pdf_data, maintype='application', subtype='pdf', filename=file)


        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {"raw": encoded_message}
        # pylint: disable=E1101
        send_message = (
            service.users()
            .messages()
            .send(userId="me", body=create_message)
            .execute()
        )
        print(f'Message Id: {send_message["id"]}')
        os.remove(file)
    except HttpError as error:
        print(f"An error occurred: {error}")


@shared_task
def weekly_pdf(user):
    all_closed_orders = Orders.objects \
        .filter(user=user, created_at__gt=datetime.now().date() - timedelta(days=7), is_active=False) \
        .values(
            'ticker', 'dollar_amount', 'realised_pnl', 'open_price', 'close_price',
            'created_at', 'closed_at', 'user_id'
        )

    all_open_orders = Orders.objects \
        .filter(user=user, created_at__gt=datetime.now().date() - timedelta(days=7), is_active=True) \
        .values(
            'ticker', 'dollar_amount', 'realised_pnl', 'open_price', 'created_at', 'user_id'
        )

    if all_open_orders or all_closed_orders:
        closed_trades = [order for order in all_closed_orders]
        open_trades = [order for order in all_open_orders]

        context = {
            'user': user,
            'date': datetime.now().date(),
            'closed_trades': closed_trades,
            'open_trades': open_trades
        }

        output_text = template.render(context)

        config = pdfkit.configuration(wkhtmltopdf='C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe')
        file_name = f'{uuid4()}.pdf'
        pdfkit.from_string(output_text, file_name, configuration=config)

        send_email('weekly breakdown', 'this is this weeks breakdown', user, file=file_name)


def schedule_weekly_pdf(user):
    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute='30',
        hour='16',
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
    )

    PeriodicTask.objects.create(
        crontab=schedule,
        name=uuid4(),
        task='dashboard.tasks.weekly_pdf',
        args=json.dumps([user]),
        enabled=True,
        one_off=True,
    )
