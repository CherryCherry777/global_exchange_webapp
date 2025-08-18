from django.contrib.auth.models import AbstractUser
from django.db import models

#Las clases van aqui
#Los tipos de usuarios heredan AbstractUser
class usuario(AbstractUser):
    estado = models.BooleanField(default=True)
