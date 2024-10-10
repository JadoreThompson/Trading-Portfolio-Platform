from .forms import LoginForm, RegisterForm

from django.contrib import messages
from django.contrib.auth import get_user_model, authenticate, login
from django.shortcuts import render, redirect
from django.views import View


User = get_user_model()


class LoginView(View):
    def get(self, request):
        return render(request, 'accounts/login.html', {'form': LoginForm()})


    def post(self, request):
        try:
            data = request.POST.dict()
            del data['csrfmiddlewaretoken']

            user = authenticate(email=data['email'], password=data['password'])
            if user:
                login(request,user)
                messages.success(request, 'Logged in successfully')
                return redirect('dashboard')
            messages.error(request, "Invalid credentials")
            return render(request, 'accounts/login.html')
        except Exception as e:
            print(f"[LOGIN][ERROR] -> {type(e)} - {str(e)}")


class RegisterView(View):
    def get(self, request):
        return render(request, 'accounts/register.html', {'form': LoginForm()})


    def post(self, request):
        try:
            data = request.POST.dict()
            del data['csrfmiddlewaretoken']

            if User.objects.filter(email=data['email']):
                messages.error(request, 'Account already exists')

            new_user = User.objects.create(**data)
            login(request, new_user)
            messages.success(request, 'User crested successfully')
            return redirect('dashboard')
        except Exception as e:
            print(f"[REGISTER][ERROR] -> {type(e)} - {str(e)}")
