from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username=models.CharField(max_length=30,unique=True)
    id=models.AutoField(primary_key=True)
    email=models.EmailField(unique=True)
    first_name=models.CharField(max_length=30)
    last_name=models.CharField(max_length=30)