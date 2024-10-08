from .forms import LoginForm, RegisterForm

from django.contrib import messages
from django.contrib.auth import get_user_model, authenticate, authenticate, login, logout
from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.views import View


User = get_user_model()


class LoginView(View):
    def get(self, request):
        return render(request, 'accounts/login.html', {'form': LoginForm})

    def post(self, request):
        pass


class RegisterView(View):
    def get(self, request):
        return render(request, 'accounts/register.html', {'form': RegisterForm})

    def post(self, request):
        try:
            data = {key: value for key, value in request.POST.dict().items() if key != 'csrfmiddlewaretoken'}
            user = User.objects.create(**data)
            login(request, user)
            messages.success(request, 'Logging you in')
            return redirect('dashboard')
        except IntegrityError:
            messages.error(request, 'User already exists')
            return render(request, 'accounts/register.html', {'form': RegisterForm})


