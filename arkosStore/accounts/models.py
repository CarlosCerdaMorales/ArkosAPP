from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    class Role(models.TextChoices):
        NO_REGISTRADO = 'NO_REG', 'No registrado'
        REGISTRADO = 'REG', 'Registrado'
        ADMIN = 'ADMIN', 'Administrador'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.REGISTRADO)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"