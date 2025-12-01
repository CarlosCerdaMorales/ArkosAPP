from django.shortcuts import render
from datetime import datetime
from django.utils import timezone
from appointments.models import Appointment, Service, StatusChoices
from accounts.models import User
from workers.models import Worker
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

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

@csrf_exempt
def chatbot_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            msg = data.get('message', '').lower()
            
            def check(keywords):
                return any(word in msg for word in keywords)

            hora = datetime.now().hour
            if 6 <= hora < 12:
                saludo_tiempo = "¡Buenos días!"
            elif 12 <= hora < 20:
                saludo_tiempo = "¡Buenas tardes!"
            else:
                saludo_tiempo = "¡Buenas noches!"

            if check(['hola', 'buenas', 'hey', 'qué tal']):
                response = f"{saludo_tiempo} Soy el asistente virtual de Natursur. 🌿<br>¿En qué puedo ayudarte hoy?"

            elif check(['servicio', 'tratamiento', 'masaje', 'fisio', 'osteopatia', 'oferta']):
                url = reverse('services_list')
                response = (
                    "En <b>Natursur</b> cuidamos de ti integralmente.<br>"
                    "Ofrecemos Fisioterapia, Osteopatía, Par Biomagnético y Nutrición.<br><br>"
                    f"👉 <a href='{url}' style='color:#19a463; font-weight:bold;'>Ver catálogo completo y precios</a>"
                )

            elif check(['reserv', 'cita', 'pedir hora', 'calendario']):
                url = reverse('create_appointment')
                response = (
                    "¡Claro! Reservar es muy sencillo y puedes elegir a tu especialista favorito.<br><br>"
                    f"📅 <a href='{url}' class='chat-btn'>Reservar ahora</a>"
                )

            elif check(['registr', 'cuenta', 'sign up', 'crear']):
                url = reverse('register')
                response = "Crear una cuenta te permitirá llevar un historial de tus sesiones.<br>" \
                           f"✍️ <a href='{url}'>Regístrate gratis aquí</a>."

            elif check(['precio', 'cuesta', 'coste', 'tarifas', 'dinero']):
                url = reverse('services_list')
                response = "Nuestras tarifas varían según la duración y el tipo de terapia (desde 30€).<br>" \
                           f"Consulta el listado detallado <a href='{url}'>aquí</a>."

            elif check(['error', 'problema', 'fallo', 'no funciona', 'bug', 'ayuda']):
                email_soporte = "soporte@natursur.com"
                asunto = "Incidencia Web Natursur"
                response = (
                    "Vaya, siento que estés teniendo problemas. 😔<br>"
                    "Por favor, contacta con nuestro equipo técnico directamente:<br><br>"
                    f"📧 <a href='mailto:{email_soporte}?subject={asunto}'>Enviar reporte de incidencia</a><br>"
                    "Te responderemos en menos de 24h."
                )

            elif check(['contact', 'admin', 'telefono', 'llamar', 'ubicacion', 'donde', 'fernando']):
                response = (
                    "📞 <b>Teléfono:</b> +34 600 000 000<br>"
                    "📍 <b>Ubicación:</b> Calle del Bienestar, 12, Sevilla.<br>"
                    "✉️ <b>Email:</b> info@natursur.com<br><br>"
                    "Fernando y el equipo estamos disponibles de Lunes a Viernes de 09:00 a 20:00."
                )

            elif check(['mis citas', 'tengo cita', 'cuando voy', 'historial', 'proxima']):
                if request.user.is_authenticated:
                    url_upcoming = reverse('upcoming_appointments')
                    response = f"Hola {request.user.username}, puedes ver tus próximas sesiones aquí:<br>" \
                               f"📅 <a href='{url_upcoming}'>Ver mis citas programadas</a>"
                else:
                    url_login = reverse('login')
                    response = "Para consultar tus citas privadas necesitas identificarte primero.<br>" \
                               f"🔐 <a href='{url_login}'>Iniciar sesión</a>"

            elif check(['herbalife', 'producto', 'tienda', 'batido', 'suplemento']):
                response = "Trabajamos con la mejor nutrición de Herbalife para complementar tus terapias.<br>" \
                           "Pregunta a nuestros nutricionistas en tu próxima cita."

            elif check(['ofreces', 'haces', 'puedes hacer', 'ayudarme', 'uso', 'instrucciones', 'capaz', 'sirves']):
                response = (
                    "¡Buena pregunta! 🤖 Soy el asistente virtual de Natursur y estoy aquí para agilizar tus gestiones.<br><br>"
                    "<b>Puedo ayudarte a:</b>"
                    "<ul style='margin-left:15px; margin-top:5px; margin-bottom:10px;'>"
                    "<li>ℹ️ Consultar nuestros <b>servicios</b> y precios.</li>"
                    "<li>📅 <b>Reservar</b> cita con tu especialista.</li>"
                    "<li>🔐 Gestionar tu <b>cuenta</b> o registro.</li>"
                    "<li>🆘 Contactar con <b>soporte</b> técnico.</li>"
                    "</ul>"
                    "Simplemente escríbeme algo como: <i>'Quiero reservar'</i> o <i>'Tengo un problema'</i>."
                )

            else:
                response = (
                    "Lo siento, aún estoy aprendiendo y no he entendido eso. 😅<br>"
                    "Prueba a preguntarme: <b>'¿Qué ofreces?'</b> o <b>'Quiero reservar'</b>."
                )
            
            return JsonResponse({'response': response})
            
        except Exception as e:
            print(f"Error chatbot: {e}")
            return JsonResponse({'response': 'Ha ocurrido un error interno.'}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)