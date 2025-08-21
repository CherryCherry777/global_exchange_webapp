from django.contrib.auth.models import AbstractUser
from django.db import models

#Las clases van aqui
#Los usuarios heredan AbstractUser
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username
