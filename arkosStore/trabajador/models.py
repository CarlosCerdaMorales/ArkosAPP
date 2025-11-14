from django.db import models

# Create your models here.

class Trabajador(models.Model):
    nombre = models.CharField(max_length=120)
    especialidad = models.CharField(max_length=120)

    def __str__(self):
        return f"{self.nombre} — {self.especialidad}"