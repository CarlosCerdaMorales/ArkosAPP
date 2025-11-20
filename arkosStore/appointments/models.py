from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import timedelta

from accounts.models import User
from workers.models import Worker, TypeChoices

class StatusChoices(models.TextChoices):
    PENDING = 'PENDIENTE', 'Pendiente'
    CONFIRMED = 'CONFIRMADA', 'Confirmada'
    COMPLETED = 'COMPLETADA', 'Completada'
    CANCELLED = 'CANCELADA', 'Cancelada'

class Service(models.Model):
    name = models.CharField(max_length=100, choices=TypeChoices.choices, verbose_name="Tipo de Servicio")
    duration = models.PositiveIntegerField(default=60, validators=[MinValueValidator(15)], help_text="Duración en minutos")
    
    class Meta:
        unique_together = ('name', 'duration')

    def __str__(self):
        return f"{self.get_name_display()} ({self.duration} min)"

class Availability(models.Model):
    DAY_CHOICES = [
        (0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'), (3, 'Jueves'), 
        (4, 'Viernes'), (5, 'Sábado'), (6, 'Domingo')
    ]

    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='availabilities')
    
    day_of_week = models.IntegerField(choices=DAY_CHOICES, verbose_name="Día")
    start_time = models.TimeField(verbose_name="Hora Inicio")
    end_time = models.TimeField(verbose_name="Hora Fin")

    class Meta:
        verbose_name = "Horario disponible"
        verbose_name_plural = "Horarios disponibles"
       
    def __str__(self):
        return f"{self.worker.name} - {self.get_day_of_week_display()}: {self.start_time} - {self.end_time}"

class Appointment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_appointments')
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='worker_appointments')
    
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='service_appointments',default=None)
    
    datetime = models.DateTimeField()
    status = models.CharField(max_length=10, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    
    def __str__(self):
        return f"Cita de {self.user.username} con {self.worker} el {self.datetime.strftime('%Y-%m-%d %H:%M')}"

    @property
    def calculated_end_time(self):
        """
        If the appointment has a service, returns the end time calculated by adding the service duration to the start time.
        If no service is associated, returns None.
        """
        return self.datetime + timedelta(minutes=self.service.duration)

    @property
    def can_be_cancelled(self):
        """
        Returns True if the appointment can be cancelled (i.e., if it's more than 12 hours away).
        Returns False otherwise.
        """
        limit = timezone.now() + timedelta(hours=12)
        
        return self.datetime > limit