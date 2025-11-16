from django.db import models

# Create your models here.

class TypeChoices(models.TextChoices):
        OSTEOPATHY_MASSAGE = 'OSTEOPATIA_MASAJE', 'Osteopatía y Masaje Holístico'
        PAR_MAGNETIC = 'PAR_MAGNETICO', 'Par Biomagnético Equilibrado'
        EMOTIONAL_TECH = 'TECNICAS_EMOCIONALES', 'Técnicas Emocionales Adaptadas'
        NUTRITIONAL_ADVICE = 'ASESORAMIENTO_NUTRICIONAL', 'Asesoramiento Nutricional'
        OTHER = 'OTRO', 'Otro'

class Worker(models.Model):
    name = models.CharField(max_length=120)
    specialty = models.CharField(max_length=50, choices=TypeChoices.choices, default=TypeChoices.OTHER)

    def __str__(self):
        return f"{self.name} — {self.get_specialty_display()}"