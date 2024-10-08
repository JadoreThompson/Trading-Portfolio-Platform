from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


class User(AbstractBaseUser):
    email = models.EmailField(unique=True, primary_key=True, max_length=255)
