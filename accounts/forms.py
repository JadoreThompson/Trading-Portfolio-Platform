import re
from django import forms
from django.core.exceptions import ValidationError


# Functions
def validate_special_chars(value):
    special_characters = re.findall(r'[!@#$%^&*(),.?":{}|<>]', value)
    if len(special_characters) < 2:
        raise ValidationError('Password must contain at least 2 special characters.')


def validate_username(var):
    allowed_characters = re.compile(r'^[a-zA-Z0-9!@#$%^&*(),.?":{}|<>]*$')
    if not allowed_characters.match(var):
        raise ValidationError(
            'Username contains invalid characters. Only alphanumeric and common special characters are allowed.')


# Forms
class LoginForm(forms.Form):
    email = forms.EmailField(label='Email', max_length=255, widget=forms.EmailInput)
    password = forms.CharField(label='Password', max_length=20, min_length=8, widget=forms.PasswordInput(),
                               validators=[validate_special_chars])


class RegisterForm(forms.Form):
    username = forms.CharField(label='Username', max_length=20, min_length=3)
    email = forms.EmailField(label='Email', max_length=255, widget=forms.EmailInput)
    password = forms.CharField(label='Password', max_length=20, min_length=8, widget=forms.PasswordInput(),
                               validators=[validate_username])
