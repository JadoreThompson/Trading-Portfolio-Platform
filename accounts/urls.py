from .views import LoginView, RegisterView, EmailConfirmationView
from django.urls import path


urlpatterns = [
    path('login', LoginView.as_view(), name='login'),
    path('register', RegisterView.as_view(), name='register'),
    path('confirm-email', EmailConfirmationView.as_view(), name='confirm_email'),
]
