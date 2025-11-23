from django import forms

from accounts.models import User
from .models import Appointment, Service, StatusChoices
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
            'service': forms.Select(attrs={'class': 'hidden-input'}),
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
            
            max_future_datetime = timezone.now() + timedelta(days=30)

            if combined_datetime > max_future_datetime:
                raise ValidationError("Las reservas solo están permitidas con un máximo de 30 días de antelación.")
                
            cleaned_data['datetime_actual'] = combined_datetime
            
            if not Worker.objects.filter(id=worker_id).exists():
                raise ValidationError("El trabajador seleccionado no es válido.")

            end_time = combined_datetime + timedelta(minutes=service.duration)
            
            overlapping_candidates = Appointment.objects.filter(
                datetime__lt=end_time,
                datetime__date=combined_datetime.date(),
                status__in=[StatusChoices.PENDING, StatusChoices.CONFIRMED]
            ).select_related('service') 

            is_overlapping = False
            for existing_app in overlapping_candidates:
                if existing_app.calculated_end_time > combined_datetime:
                    is_overlapping = True
                    break

            if is_overlapping:
                raise ValidationError(
                    "Esta franja horaria ya está reservada o se solapa con otra cita existente. Por favor, selecciona otro horario."
                )

        return cleaned_data
    
class AdminAppointmentForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(role='REG'),
        label="Cliente",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    service = forms.ModelChoiceField(
        queryset=Service.objects.all(),
        label="Servicio",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    worker = forms.ModelChoiceField(
        queryset=Worker.objects.all(),
        label="Especialista",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date = forms.DateField(
        label="Fecha",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    time = forms.TimeField(
        label="Hora",
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )

    class Meta:
        model = Appointment
        fields = ['user', 'service', 'worker'] 

    def clean(self):
        cleaned_data = super(forms.ModelForm, self).clean()
        
        date = cleaned_data.get('date')
        time_data = cleaned_data.get('time')

        if date and time_data:
            try:
                naive_combined = datetime.combine(date, time_data)
                combined_datetime = timezone.make_aware(naive_combined)
                cleaned_data['datetime_actual'] = combined_datetime
            except Exception as e:
                self.add_error('time', "Hora inválida")
        
        return cleaned_data