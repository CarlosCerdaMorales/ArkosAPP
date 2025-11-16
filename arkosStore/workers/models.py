from django.db import models

# Create your models here.

class Worker(models.Model):
    class AppointmentType(models.TextChoices):
        MASAJE = 'Masaje', 'Osteopatía y Masaje Holístico'
        PAR = 'ParBiomagnético', 'Par Biomagnético Equilibrado'
        EMOCIONES = 'TécnicasEmocionales', 'Técnicas Emocionales Adaptadas'
        NUTRICION = 'AsesoramientoNutricional', 'Asesoramiento Nutricional'
        OTRO = 'Otro', 'Otro'
    
    name = models.CharField(max_length=120)
    specialty = models.CharField(max_length=50, choices=AppointmentType.choices, default=AppointmentType.OTRO)

    def __str__(self):
        return f"{self.name} — {self.get_specialty_display()}"