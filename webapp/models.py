from django.contrib.auth.models import AbstractUser, Group
from django.db import models

#Las clases van aqui
#Los usuarios heredan AbstractUser
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username


class Role(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name="role")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.group.name