from django.db import models

# Create your models here.

class TypeChoices(models.TextChoices):
        OSTEOPATHY_MASSAGE = 'OSTEOPATIA_MASAJE', 'Osteopatía y Masaje Holístico'
        PAR_MAGNETIC = 'PAR_MAGNETICO', 'Par Biomagnético Equilibrado'
        EMOTIONAL_TECH = 'TECNICAS_EMOCIONALES', 'Técnicas Emocionales Adaptadas'
        NUTRITIONAL_ADVICE = 'ASESORAMIENTO_NUTRICIONAL', 'Asesoramiento Nutricional'
        OTHER = 'OTRO', 'Otro'

class Specialty(models.Model):
    name = models.CharField(
        max_length=50, 
        choices=TypeChoices.choices, 
        unique=True
    )

    def __str__(self):
        return self.get_name_display()

class Worker(models.Model):
    name = models.CharField(max_length=120)
    specialties = models.ManyToManyField(Specialty, related_name='workers', blank=True)

    def __str__(self):
        specialties_list = ", ".join([s.get_name_display() for s in self.specialties.all()])
        return f"{self.name} — {specialties_list}"