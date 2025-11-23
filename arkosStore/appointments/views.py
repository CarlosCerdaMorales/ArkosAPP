from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .forms import AdminAppointmentForm, AppointmentForm
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

@login_required
def cancel_appointment_view(request, pk):
    appointment = get_object_or_404(Appointment, id=pk, user=request.user)

    limit_time = timezone.now() + timedelta(hours=12)

    if appointment.datetime > limit_time:
        appointment.delete()
        messages.success(request, "Cita cancelada correctamente.")
    else:
        messages.error(request, "No es posible cancelar con menos de 12 horas de antelación.")

    return redirect('upcoming_appointments')

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
        service_duration = service.duration
        service_duration_delta = timedelta(minutes=service_duration)

        max_date = timezone.now().date() + timedelta(days=30)

        if target_date < timezone.now().date():
            return JsonResponse({'slots': []})
        
        if target_date > max_date:
            return JsonResponse({'slots': []})
        
    except (ValueError, Service.DoesNotExist):
        return JsonResponse({'slots': []})

    
    workers = Worker.objects.filter(specialties__name=service.name)

    available_slots = []
    
    existing_appointments_qs = Appointment.objects.filter(
        datetime__date=target_date,
        status__in=[StatusChoices.PENDING, StatusChoices.CONFIRMED]
    ).select_related('service')


    for worker in workers:
        availabilities = Availability.objects.filter(
            worker=worker, 
            day_of_week=day_of_week
        )


        for rule in availabilities:
            naive_start = datetime.combine(target_date, rule.start_time)
            current_time = timezone.make_aware(naive_start)
            
            naive_end = datetime.combine(target_date, rule.end_time)
            end_time = timezone.make_aware(naive_end)
            
            if target_date == timezone.now().date():
                if current_time < timezone.now():
                    minutes_past_hour = timezone.now().minute
                    minutes_to_add = (service_duration - (minutes_past_hour % service_duration)) % service_duration
                    current_time = (timezone.now() + timedelta(minutes=minutes_to_add)).replace(second=0, microsecond=0)

                if (current_time >= end_time):
                    continue

            while current_time + service_duration_delta <= end_time:
                slot_start = current_time.time()
                slot_end_time = current_time + service_duration_delta
                
                is_overlapping = False
                for app in existing_appointments_qs:
                    if not app.service:
                        continue 
                        
                    app_end_time = app.calculated_end_time

                    if current_time < app_end_time and app.datetime < slot_end_time:
                        is_overlapping = True
                        break

                if not is_overlapping:
                    available_slots.append({
                        'time_display': slot_start.strftime('%H:%M'),
                        'time_value': slot_start.strftime('%H:%M'),
                        'worker_id': worker.id,
                        'worker_name': worker.name,
                    })

                current_time += service_duration_delta

    available_slots.sort(key=lambda x: x['time_value'])

    return JsonResponse({'slots': available_slots})


def modify_appointment_view(request, pk):
    appointment = get_object_or_404(Appointment, id=pk)
    
    if request.method == 'POST':
        form = AdminAppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.datetime = form.cleaned_data['datetime_actual']
            appointment.save()
            return redirect('custom_admin')
    else:
        initial_data = {
            'date': appointment.datetime.date(),
            'time': appointment.datetime.time()
        }
        form = AdminAppointmentForm(instance=appointment, initial=initial_data)

    return render(request, 'appointments/admin.html', {
        'form': form, 
        'title': f'Modificar Cita #{pk}' 
    })

def admin_cancel_appointment(request, pk):
    appointment = get_object_or_404(Appointment, id=pk)
    
    appointment.delete()
    
    return redirect('custom_admin')
