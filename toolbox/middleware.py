from django.contrib import auth
from django.contrib import messages


class ClearMessagesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        messages.get_messages(request)
        return self.get_response(request)
