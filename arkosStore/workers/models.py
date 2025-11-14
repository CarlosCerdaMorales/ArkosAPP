from django.db import models

# Create your models here.

class Worker(models.Model):
    class AppointmentType(models.TextChoices):
        TYPE1 = 'TYPE1', 'T1'
        TYPE2 = 'TYPE2', 'T2'
        TYPE3 = 'TYPE3', 'T3'
    
    name = models.CharField(max_length=120)
    specialty = models.CharField(max_length=20, choices=AppointmentType.choices, default=AppointmentType.TYPE1)

    def __str__(self):
        return f"{self.name} — {self.specialty}"