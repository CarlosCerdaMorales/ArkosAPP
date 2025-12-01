from django.shortcuts import render
from datetime import datetime
from django.utils import timezone
from appointments.models import Appointment, Service, StatusChoices
from accounts.models import User
from workers.models import Worker
#from django.template import loader
#from django.http import HttpResponse

# Create your views here.

def index(request):
    return render(request, "home/index.html")


def contact(request):
    return render(request, "home/contact.html")

def resources_view(request):
    return render(request, "home/resources.html")

def custom_admin(request):
    date_param = request.GET.get('date')
    if date_param:
        try:
            current_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            current_date = timezone.now().date()
    else:
        current_date = timezone.now().date()
    
    START_HOUR = 9
    END_HOUR = 22
    total_minutes = (END_HOUR - START_HOUR) * 60

    workers = Worker.objects.all()

    temp_appointments = {worker.id: [] for worker in workers}
    
    appointments = Appointment.objects.filter(
        datetime__date=current_date,
        status__in=[StatusChoices.PENDING, StatusChoices.CONFIRMED, StatusChoices.COMPLETED]
    ).select_related('user', 'service', 'worker')

    for app in appointments:
        local_dt = timezone.localtime(app.datetime)
        
        start_minutes = (local_dt.hour * 60 + local_dt.minute) - (START_HOUR * 60)
        duration = app.service.duration

        if start_minutes >= 0: 
            top_pct = (start_minutes / total_minutes) * 100
            height_pct = (duration / total_minutes) * 100
            
            app.css_top = f"{top_pct}%"
            app.css_height = f"{height_pct}%"
            
            if app.worker.id in temp_appointments:
                temp_appointments[app.worker.id].append(app)

    workers_schedule = []
    for worker in workers:
        workers_schedule.append({
            'worker': worker,
            'appointments': temp_appointments.get(worker.id, [])
        })

    hours_axis = range(START_HOUR, END_HOUR)
    
    all_services = Service.objects.all()
    all_clients = User.objects.filter(role='REG')

    context = {
        'current_date': current_date,
        'workers_schedule': workers_schedule, 
        'hours_axis': hours_axis,
        'modal_services': all_services,
        'modal_clients': all_clients,
        'modal_workers': workers,
    }

    return render(request, "home/admin.html", context)

def terms_conditions_view(request):
    return render(request, 'legal/terms.html')