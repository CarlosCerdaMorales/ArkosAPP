from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .forms import AppointmentForm
from .models import Service, Worker, Availability, Appointment, StatusChoices
from datetime import datetime, timedelta
from django.http import JsonResponse



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
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            
            appointment.user = request.user
            appointment.datetime = form.cleaned_data['datetime_actual']
            
            worker_id = form.cleaned_data['worker_id']
            appointment.worker = get_object_or_404(Worker, id=worker_id)
            
            appointment.save()
            
            return redirect('appointment_success', pk=appointment.id)
    else:
        form = AppointmentForm()

    context = {
        'form': form,
        'services': Service.objects.all()
    }
    return render(request, 'appointments/create.html', context)

@login_required
def appointment_success_view(request, pk):
    appointment = get_object_or_404(Appointment, id=pk, user=request.user)
    
    return render(request, 'appointments/success.html', {'appointment': appointment})

def get_available_slots(request):
    """
    Esta función recibe: ?service_id=X&date=YYYY-MM-DD
    Devuelve JSON: { 'slots': [ {'time': '09:00', 'worker_id': 1}, ... ] }
    """
    service_id = request.GET.get('service_id')
    date_str = request.GET.get('date')

    if not service_id or not date_str:
        return JsonResponse({'error': 'Faltan datos'}, status=400)

    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        service = Service.objects.get(id=service_id)
        day_of_week = target_date.weekday()
    except (ValueError, Service.DoesNotExist):
        return JsonResponse({'slots': []})

    
    workers = Worker.objects.filter(specialties__name=service.name)

    available_slots = []

    for worker in workers:
        availabilities = Availability.objects.filter(
            worker=worker, 
            day_of_week=day_of_week
        )

        for rule in availabilities:
            current_time = datetime.combine(target_date, rule.start_time)
            end_time = datetime.combine(target_date, rule.end_time)
            
            while current_time + timedelta(minutes=service.duration) <= end_time:
                slot_start = current_time.time()
                
                is_taken = Appointment.objects.filter(
                    worker=worker,
                    datetime=current_time,
                    status__in=['PENDIENTE', 'CONFIRMADA']
                ).exists()

                if not is_taken:
                    available_slots.append({
                        'time_display': slot_start.strftime('%H:%M'),
                        'time_value': slot_start.strftime('%H:%M'),
                        'worker_id': worker.id,
                        'worker_name': worker.name,
                    })

                current_time += timedelta(minutes=service.duration)

    available_slots.sort(key=lambda x: x['time_value'])

    return JsonResponse({'slots': available_slots})