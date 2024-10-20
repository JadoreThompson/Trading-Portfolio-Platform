from django.contrib import messages


class CustomMessagesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        messages.get_messages(request).used = True
        response = self.get_response(request)
        return response
