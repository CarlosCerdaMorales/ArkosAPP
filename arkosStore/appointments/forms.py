from django import forms
from .models import Appointment
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from django.utils import timezone
from workers.models import Worker

class AppointmentForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'hidden-input'}),
        label="Fecha"
    )
    time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'hidden-input'}),
        label="Hora"
    )
    
    worker_id = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        model = Appointment
        fields = ['service'] 
        widgets = {
            'service': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        """
        This method combines the separate date and time fields into a single datetime object
        """
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        time_data = cleaned_data.get('time')
        service = cleaned_data.get('service')
        worker_id = cleaned_data.get('worker_id')

        if date and time_data and service and worker_id:
            naive_combined_datetime = datetime.combine(date, time_data)
            
            combined_datetime = timezone.make_aware(naive_combined_datetime)
            
            if combined_datetime < timezone.now():
                raise ValidationError("No puedes reservar en el pasado.")
            
            cleaned_data['datetime_actual'] = combined_datetime
            
            if not Worker.objects.filter(id=worker_id).exists():
                raise ValidationError("El trabajador seleccionado no es válido.")

            end_time = combined_datetime + timedelta(minutes=service.duration)
            
            overlapping_appointments = Appointment.get_overlapping_appointments(
                start_time=combined_datetime, 
                end_time=end_time
            ).exists()

            if overlapping_appointments:
                raise ValidationError(
                    "Esta franja horaria ya está reservada o se solapa con otra cita existente. Por favor, selecciona otro horario."
                )

        return cleaned_data