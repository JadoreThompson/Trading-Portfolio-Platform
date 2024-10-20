# Local
import json
from datetime import datetime

from .forms import LoginForm, RegisterForm
from .models import CustomUser, EmailConfirmTokens
from dashboard.tasks import schedule_weekly_pdf
from .tasks import send_confirm_email_token, generate_token

# Django
from django.contrib import messages
from django.contrib.auth import get_user_model, authenticate, login
from django.shortcuts import render, redirect
from django.views import View
from django.db.utils import IntegrityError
from django.http import JsonResponse, HttpResponse



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

            messages.error(request, "Invalid credentials")
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
            data = {k: v for k, v in request.POST.dict().items() if k != 'csrfmiddlewaretoken'}
            if User.objects.filter(email=data['email']):
                raise IntegrityError('Account already exists')

            new_user = User.objects.create_user(**data)
            new_user.is_active = False
            new_user.save()

            new_token = EmailConfirmTokens.objects.create(user=new_user, token=generate_token())

            send_confirm_email_token.delay(new_user.email, new_token.token)
            schedule_weekly_pdf(new_user.email)
            return JsonResponse(status=200, data={'message': 'registration successful'})
        except IntegrityError as e:
            return JsonResponse(status=409, data={'error': str(e)})
        except Exception as e:
            return JsonResponse(status=500, data={'error': str(e)})


class EmailConfirmationView(View):
    _TOKEN_EXPIRY = 300

    def post(self, request):
        data = {k: v for k, v in request.POST.dict().items() if k != 'csrfmiddlewaretoken'}
        token_row = EmailConfirmTokens.objects.get(token=data['token'])

        if not token_row:
            return JsonResponse(status=404, data={'error': 'Incorrect Token'})
        if (int(datetime.now().timestamp()) - self._TOKEN_EXPIRY) > token_row.created_at:
            return JsonResponse(status=409, data={'error': 'Token Expired'})

        user = CustomUser.objects.get(email=token_row.user_id)
        user.is_active = True
        user.save()

        token_row.delete()
        login(request, user)
        return JsonResponse(    status=200, data={'message': 'Successfully confimed email'})
