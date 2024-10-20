import json
from celery import shared_task
import random
import string
from datetime import datetime

# Local
from .models import EmailConfirmTokens
from dashboard.tasks import send_email


def generate_token(length=10):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))


@shared_task
def send_confirm_email_token(user, token):
    send_email.delay('Confirm Email', token, user)
