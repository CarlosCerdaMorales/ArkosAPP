from django.db import models

from accounts.models import User
from workers.models import Worker



# Create your models here.

class Appointment(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDIENTE', 'Pendiente'
        CONFIRMED = 'CONFIRMADA', 'Confirmada'
        COMPLETED = 'COMPLETADA', 'Completada'
        CANCELLED = 'CANCELADA', 'Cancelada'

    class TypeChoices(models.TextChoices):
        OSTEOPATHY_MASSAGE = 'OSTEOPATIA_MASAJE', 'Osteopatía y Masaje Holístico'
        PAR_MAGNETIC = 'PAR_MAGNETICO', 'Par Biomagnético Equilibrado'
        EMOTIONAL_TECH = 'TECNICAS_EMOCIONALES', 'Técnicas Emocionales Adaptadas'
        NUTRITIONAL_ADVICE = 'ASESORAMIENTO_NUTRICIONAL', 'Asesoramiento Nutricional'


    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='client_appointments'
    )

    trabajador = models.ForeignKey(
        Worker,
        on_delete=models.CASCADE,
        related_name='worker_appointments'
    )

    fecha = models.DateTimeField()
    estado = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING)
    
    tipo = models.CharField(
        max_length=30,
        choices=TypeChoices.choices,
        default=TypeChoices.OSTEOPATHY_MASSAGE
    )

    def __str__(self):
        return f"Cita de {self.usuario.username} con {self.trabajador} el {self.fecha.strftime('%Y-%m-%d %H:%M')}"

