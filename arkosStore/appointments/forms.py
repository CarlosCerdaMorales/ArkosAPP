from django import forms
from .models import Appointment, Service
from django.core.exceptions import ValidationError
from datetime import datetime

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

        if date and time_data:
            combined_datetime = datetime.combine(date, time_data)
            if combined_datetime < datetime.now():
                raise ValidationError("No puedes reservar en el pasado.")
            
            cleaned_data['datetime_actual'] = combined_datetime
            
        return cleaned_data