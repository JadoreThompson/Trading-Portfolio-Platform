from .forms import LoginForm, RegisterForm
from .models import CustomUser
from django.contrib import messages
from django.contrib.auth import get_user_model, authenticate, login
from django.shortcuts import render, redirect
from django.views import View
from django.db.utils import IntegrityError


User = get_user_model()
class LoginView(View):
    def get(self, request):
        return render(request, 'accounts/login.html', {'form': LoginForm()})


    def post(self, request):
        try:
            email = request.POST.get('email')
            password = request.POST.get('password')
            user = authenticate(request=request, username=email, password=password)
            if user:
                login(request, user)
                messages.success(request, 'Logged in successfully')
                return redirect('dashboard')

            print(user)
            messages.error(request, "Invalid credentials")
            print("[LOGIN] >>> Invalid credentials")
            return self.get(request)
        except CustomUser.DoesNotExist:
            raise Exception('Invalid Credentials')
        except Exception as e:
            print(f"[LOGIN][ERROR] >>> {type(e)} - {str(e)}")
            messages.error(request, f"Error: {str(e)}")
            return self.get(request)


class RegisterView(View):
    def get(self, request):
        return render(request, 'accounts/register.html', {'form': LoginForm()})


    def post(self, request):
        try:
            data = {k:v for k, v in request.POST.dict().items() if k != 'csrfmiddlewaretoken'}
            if User.objects.filter(email=data['email']):
                messages.error(request, 'Account already exists')

            new_user = User.objects.create_user(**data)
            login(request, new_user)
            messages.success(request, 'User crested successfully')
            return redirect('dashboard')

        except IntegrityError:
            messages.error(request, "Account already exists")
            return render(request, 'accounts/register.html', {'form': RegisterForm()})
        except Exception as e:
            print(f"[ERROR][REGISTER] >>> {type(e)} - {str(e)}")
            messages.error(request, f"Error: {str(e)}")
            return render(request, 'accounts/register.html', {'form': RegisterForm()})
