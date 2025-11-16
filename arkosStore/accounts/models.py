from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

# Create your models here.

class User(AbstractUser):
    class Role(models.TextChoices):
        NO_REGISTRADO = 'NO_REG', 'No registrado'
        REGISTRADO = 'REG', 'Registrado'
        ADMIN = 'ADMIN', 'Administrador'

    phone_regex = RegexValidator(
        regex=r'^\+\d{1,5} \d{1,15}$',
        message="El formato del teléfono debe ser: '+[código país] [número]'. Ej: +34 123456789012345"
    )

    email= models.EmailField(unique=True, blank=False, null=False)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.REGISTRADO)
    phone_number = models.CharField(
        validators=[phone_regex], 
        max_length=22,
        blank=False,
        null=False,
        unique=True
    )
    address = models.CharField(max_length=255, blank=False)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"