from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .models import Appointment, StatusChoices


@login_required
def appointment_history_view(request):
    appointments = Appointment.objects.filter(
        user=request.user,
        status=StatusChoices.COMPLETED,
        datetime__lt=timezone.now()
    ).order_by('-datetime')
    return render(request, 'appointments/history.html', {'appointments': appointments})


@login_required
def upcoming_appointments_view(request):
    appointments = Appointment.objects.filter(
        user=request.user,
        status__in=[StatusChoices.PENDING, StatusChoices.CONFIRMED],
        datetime__gte=timezone.now()
    ).order_by('datetime')
    return render(request, 'appointments/upcoming.html', {'appointments': appointments})

@login_required
def create_appointment_view(request):
    return render(request, 'appointments/create.html')
