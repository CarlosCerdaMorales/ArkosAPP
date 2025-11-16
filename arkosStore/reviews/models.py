from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from appointments.models import Appointment

# Create your models here.

class Review(models.Model):
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, null=True)
    date = models.DateField(auto_now_add=True)
    
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='review'
    )

    def __str__(self):
        try:
            return f"Review ({self.rating}/5) de {self.appointment.user.username} para la cita {self.appointment.id}"
        except:
            return f"Review ({self.rating}/5)"
