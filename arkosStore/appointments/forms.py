from datetime import datetime, timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from workers.models import Worker

from .models import Appointment, StatusChoices


class AppointmentForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "hidden-input"}),
        label="Fecha",
    )
    time = forms.TimeField(
        widget=forms.TimeInput(attrs={"type": "time", "class": "hidden-input"}),
        label="Hora",
    )
    worker_id = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        model = Appointment
        fields = [
            "service",
            "guest_first_name",
            "guest_last_name",
            "guest_email",
            "guest_phone",
        ]
        widgets = {
            "service": forms.Select(attrs={"class": "hidden-input"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        if not self.user or not self.user.is_authenticated:
            guest_first_name = cleaned_data.get("guest_first_name")
            guest_email = cleaned_data.get("guest_email")
            guest_phone = cleaned_data.get("guest_phone")

            if not guest_first_name:
                self.add_error("guest_first_name", "El nombre es obligatorio.")
            if not guest_email:
                self.add_error("guest_email", "El email es obligatorio.")
            if not guest_phone:
                self.add_error("guest_phone", "El teléfono es obligatorio.")

        date = cleaned_data.get("date")
        time_data = cleaned_data.get("time")
        service = cleaned_data.get("service")
        worker_id = cleaned_data.get("worker_id")

        if date and time_data and service and worker_id:
            naive_combined_datetime = datetime.combine(date, time_data)
            combined_datetime = timezone.make_aware(naive_combined_datetime)

            if combined_datetime < timezone.now():
                raise ValidationError("No puedes reservar en el pasado.")

            max_future_datetime = timezone.now() + timedelta(days=30)
            if combined_datetime > max_future_datetime:
                raise ValidationError(
                    "Las reservas solo están permitidas con un máximo de 30 días de antelación."
                )

            cleaned_data["datetime_actual"] = combined_datetime

            if not Worker.objects.filter(id=worker_id).exists():
                raise ValidationError("El trabajador seleccionado no es válido.")

            end_time = combined_datetime + timedelta(minutes=service.duration)

            overlapping_candidates = Appointment.objects.filter(
                datetime__lt=end_time,
                datetime__date=combined_datetime.date(),
                status__in=[StatusChoices.PENDING, StatusChoices.CONFIRMED],
                worker_id=worker_id,
            ).select_related("service")

            is_overlapping = False
            for existing_app in overlapping_candidates:
                if existing_app.calculated_end_time > combined_datetime:
                    is_overlapping = True
                    break

            if is_overlapping:
                raise ValidationError(
                    "Esta franja horaria ya está reservada o se solapa con otra cita existente."
                )

        return cleaned_data
