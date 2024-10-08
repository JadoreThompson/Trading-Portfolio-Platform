from .forms import LoginForm, RegisterForm

from django.shortcuts import render
from django.views import View


class LoginView(View):
    def get(self, request):
        return render(request, 'accounts/login.html', {'form': LoginForm})

    def post(self, request):
        pass


class RegisterView(View):
    def get(self, request):
        return render(request, 'accounts/register.html', {'form': RegisterForm})

    def post(self, request):
        data = request.POST.dict()

        return self.get(request)
