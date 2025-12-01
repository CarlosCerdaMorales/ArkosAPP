from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client
import threading

def send_appointment_notifications(appointment):
    email_thread = threading.Thread(target=_send_email, args=(appointment,))
    sms_thread = threading.Thread(target=_send_sms, args=(appointment,))
    
    email_thread.start()
    sms_thread.start()

def _get_contact_info(appointment):
    if appointment.user:
        return appointment.user.email, appointment.user.phone_number, appointment.user.first_name
    else:
        return appointment.guest_email, appointment.guest_phone, appointment.guest_first_name

def _send_email(appointment):
    email, _, name = _get_contact_info(appointment)
    
    if not email: return

    subject = 'Confirmación de Cita - NATURSUR'
    message = f"""
    Hola {name},

    Tu cita ha sido confirmada con éxito.

    Detalles:
    - Servicio: {appointment.service.get_name_display()}
    - Especialista: {appointment.worker.name}
    - Fecha: {appointment.datetime.strftime('%d/%m/%Y')}
    - Hora: {appointment.datetime.strftime('%H:%M')}

    Si necesitas cancelar, recuerda hacerlo con al menos 12 horas de antelación.

    ¡Te esperamos!
    Equipo NATURSUR
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"❌ Error enviando email: {e}")

def _send_sms(appointment):
    _, phone, name = _get_contact_info(appointment)
    
    if not phone: return
    body = f"NATURSUR: Hola {name}, cita confirmada para el {appointment.datetime.strftime('%d/%m a las %H:%M')} con {appointment.worker.name}."

    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone
        )
    except Exception as e:
        print(f"❌ Error enviando SMS: {e}")