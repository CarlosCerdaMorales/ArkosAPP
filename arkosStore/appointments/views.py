from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import AppointmentForm, AdminAppointmentForm, ServiceForm
from accounts.models import User
from .models import Service, Worker, Availability, Appointment, StatusChoices, TypeChoices
from datetime import datetime, timedelta
from django.http import JsonResponse
from .services import send_appointment_notifications



@login_required
def appointment_history_view(request):
    appointments = Appointment.objects.filter(
        user=request.user, status=StatusChoices.COMPLETED, datetime__lt=timezone.now()
    ).order_by("-datetime")
    return render(request, "appointments/history.html", {"appointments": appointments})


@login_required
def upcoming_appointments_view(request):
    appointments = Appointment.objects.filter(
        user=request.user,
        status__in=[StatusChoices.PENDING, StatusChoices.CONFIRMED],
        datetime__gte=timezone.now(),
    ).order_by("datetime")
    return render(request, "appointments/upcoming.html", {"appointments": appointments})


def create_appointment_view(request):
    is_guest_mode = request.GET.get('mode') == 'guest'
    form_user = None if is_guest_mode else request.user

    if request.method == "POST":
        form = AppointmentForm(request.POST, user=form_user)

        if form.is_valid():
            appointment = form.save(commit=False)

            if request.user.is_authenticated:
                appointment.user = request.user
                if is_guest_mode:
                    appointment.user = None
                    appointment.guest_first_name = request.POST.get('guest_first_name')
                    appointment.guest_last_name = request.POST.get('guest_last_name')
                    appointment.guest_email = request.POST.get('guest_email')
                    appointment.guest_phone = request.POST.get('guest_phone')
                    appointment.status = StatusChoices.CONFIRMED
            else:
                appointment.user = None


            appointment.datetime = form.cleaned_data["datetime_actual"]
            worker_id = form.cleaned_data["worker_id"]
            appointment.worker = get_object_or_404(Worker, id=worker_id)

            appointment.save()

            send_appointment_notifications(appointment)

            return redirect("appointment_success", pk=appointment.id)
    else:
        form = AppointmentForm(user=request.user)

    context = {"form": form, "services": Service.objects.all(), 'force_guest': is_guest_mode  }
    return render(request, "appointments/create.html", context)


def appointment_success_view(request, pk):
    appointment = get_object_or_404(Appointment, id=pk)

    if appointment.user and appointment.user != request.user:
        raise Http404("No tienes permiso para ver esta reserva.")

    return render(request, "appointments/success.html", {"appointment": appointment})


@login_required
def cancel_appointment_view(request, pk):
    appointment = get_object_or_404(Appointment, id=pk, user=request.user)

    limit_time = timezone.now() + timedelta(hours=12)

    if appointment.datetime > limit_time:
        appointment.delete()
        messages.success(request, "Cita cancelada correctamente.")
    else:
        messages.error(
            request, "No es posible cancelar con menos de 12 horas de antelación."
        )

    return redirect("upcoming_appointments")


def get_available_slots(request):
    """
    Esta función recibe: ?service_id=X&date=YYYY-MM-DD
    Devuelve JSON: { 'slots': [ {'time': '09:00', 'worker_id': 1}, ... ] }
    """
    service_id = request.GET.get("service_id")
    date_str = request.GET.get("date")

    if not service_id or not date_str:
        return JsonResponse({"error": "Faltan datos"}, status=400)

    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        service = Service.objects.get(id=service_id)
        day_of_week = target_date.weekday()
        service_duration = service.duration
        service_duration_delta = timedelta(minutes=service_duration)

        max_date = timezone.now().date() + timedelta(days=30)

        if target_date < timezone.now().date():
            return JsonResponse({"slots": []})

        if target_date > max_date:
            return JsonResponse({"slots": []})

    except (ValueError, Service.DoesNotExist):
        return JsonResponse({"slots": []})

    workers = Worker.objects.filter(specialties__name=service.name)

    available_slots = []

    existing_appointments_qs = Appointment.objects.filter(
        datetime__date=target_date,
        status__in=[StatusChoices.PENDING, StatusChoices.CONFIRMED],
    ).select_related("service")

    for worker in workers:
        availabilities = Availability.objects.filter(
            worker=worker, day_of_week=day_of_week
        )

        for rule in availabilities:
            naive_start = datetime.combine(target_date, rule.start_time)
            current_time = timezone.make_aware(naive_start)

            naive_end = datetime.combine(target_date, rule.end_time)
            end_time = timezone.make_aware(naive_end)

            if target_date == timezone.now().date():
                if current_time < timezone.now():
                    minutes_past_hour = timezone.now().minute
                    minutes_to_add = (
                        service_duration - (minutes_past_hour % service_duration)
                    ) % service_duration
                    current_time = (
                        timezone.now() + timedelta(minutes=minutes_to_add)
                    ).replace(second=0, microsecond=0)

                if current_time >= end_time:
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
                    available_slots.append(
                        {
                            "time_display": slot_start.strftime("%H:%M"),
                            "time_value": slot_start.strftime("%H:%M"),
                            "worker_id": worker.id,
                            "worker_name": worker.name,
                        }
                    )

                current_time += service_duration_delta

    available_slots.sort(key=lambda x: x["time_value"])

    return JsonResponse({"slots": available_slots})


def services_list_view(request):
    static_data = {
        TypeChoices.OSTEOPATHY_MASSAGE: {
            "title": "Osteopatía y Masaje Holístico",
            "desc": "El cuerpo es un sistema en constante ajuste. El dolor, la tensión o la falta de movilidad son señales de que algo "
            "no está funcionando bien. A través de técnicas de masaje y osteopatía, trabajamos para liberar restricciones, mejorar la "
            "postura y restaurar la armonía de tu organismo. Mi objetivo es ayudarte a moverte sin dolor y con mayor libertad, respetando "
            "siempre la estructura natural de tu cuerpo.",
            "image": "img/services/osteo.jpg",
        },
        TypeChoices.PAR_MAGNETIC: {
            "title": "Par Biomagnético",
            "desc": "Nuestro organismo está lleno de campos energéticos que, en ocasiones, se ven alterados por virus, bacterias o desequilibrios internos. "
            "El Par Biomagnético es una técnica que utiliza imanes para restaurar el balance natural del cuerpo, favoreciendo la capacidad de recuperación del "
            "organismo. Si buscas una terapia complementaria para mejorar tu bienestar, esta puede ser una excelente opción.",
            "image": "img/services/par.jpg",
        },
        TypeChoices.EMOTIONAL_TECH: {
            "title": "Técnicas Emocionales",
            "desc": "Las emociones no solo afectan nuestra mente, también pueden dejar huella en nuestro cuerpo. Muchas tensiones musculares, bloqueos o "
            "molestias físicas tienen un origen emocional. Utilizo diversas técnicas para ayudarte a liberar esas cargas y sentirte más ligero y equilibrado.",
            "image": "img/services/emo.jpg",
        },
        TypeChoices.NUTRITIONAL_ADVICE: {
            "title": "Asesoramiento Nutricional",
            "desc": "La alimentación es la base de nuestra energía y bienestar. No se trata solo de perder peso, sino de aprender a nutrir "
            "el cuerpo de forma adecuada. A través de un enfoque basado en la naturopatía, te ayudo a mejorar tu alimentación y a crear hábitos "
            "saludables que realmente funcionen para ti.",
            "image": "img/services/nutri.jpg",
        },
        TypeChoices.OTHER: {
            "title": "Otras Terapias",
            "desc": "Consultas personalizadas para tratamientos específicos o combinados según las necesidades únicas de tu cuerpo.",
            "image": "img/services/otro.jpg",
        },
    }

    existing_codes = Service.objects.values_list("name", flat=True).distinct()

    services_to_show = []
    for code in existing_codes:
        if code in static_data:
            services_to_show.append(static_data[code])

    durations = (
        Service.objects.values_list("duration", flat=True)
        .distinct()
        .order_by("duration")
    )

    return render(
        request,
        "appointments/services_list.html",
        {"services": services_to_show, "durations": durations},
    )

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
            'time': appointment.datetime.time(),
            'guest_first_name': appointment.guest_first_name,
            'guest_last_name': appointment.guest_last_name,
            'guest_email': appointment.guest_email,
            'guest_phone': appointment.guest_phone,
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

def is_admin(user):
    return user.is_authenticated and user.role == User.Role.ADMIN

@user_passes_test(is_admin)
def admin_create_service(request):
    if request.method == "POST":
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("custom_admin")
    else:
        form = ServiceForm()
    return render(request, "appointments/admin_create_service.html", {"form": form})
