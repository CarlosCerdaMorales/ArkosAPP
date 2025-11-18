from django.db import models

from accounts.models import User
from workers.models import Worker, TypeChoices

# Create your models here.

class StatusChoices(models.TextChoices):
        PENDING = 'PENDIENTE', 'Pendiente'
        CONFIRMED = 'CONFIRMADA', 'Confirmada'
        COMPLETED = 'COMPLETADA', 'Completada'
        CANCELLED = 'CANCELADA', 'Cancelada'


class Appointment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_appointments')
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='worker_appointments')
    datetime = models.DateTimeField()
    status = models.CharField(max_length=10, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    appointment_type = models.CharField(max_length=30, choices=TypeChoices.choices, default=TypeChoices.OSTEOPATHY_MASSAGE)

    def __str__(self):
        return f"Cita de {self.user.username} con {self.worker} el {self.datetime.strftime('%Y-%m-%d %H:%M')}"

