from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta, time
import random

from workers.models import Worker, Specialty, TypeChoices
from appointments.models import Service, Availability, Appointment, StatusChoices
from reviews.models import Review

User = get_user_model()

class Command(BaseCommand):
    help = 'Carga datos iniciales con servicios dobles y valoraciones'

    def handle(self, *args, **kwargs):
        self.stdout.write('Limpiando base de datos...')
        Review.objects.all().delete()
        Appointment.objects.all().delete()
        Availability.objects.all().delete()
        Service.objects.all().delete()
        Worker.objects.all().delete()
        Specialty.objects.all().delete()
        User.objects.exclude(username='admin').delete()

        # 1. ESPECIALIDADES
        self.stdout.write('Creando Especialidades...')
        specialties_objs = {}
        for code, label in TypeChoices.choices:
            obj, _ = Specialty.objects.get_or_create(name=code)
            specialties_objs[code] = obj

        # 2. USUARIOS
        self.stdout.write('Creando Usuarios...')
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin', phone_number='+34 600000000', role='ADMIN')
        
        user1 = User.objects.create_user('user1', 'u1@test.com', 'user1234', phone_number='+34 611111111', role='REG', first_name="Juan", last_name="Cliente")
        user2 = User.objects.create_user('user2', 'u2@test.com', 'user1234', phone_number='+34 622222222', role='REG', first_name="Ana", last_name="Clienta")

        # 3. SERVICIOS (2 Variaciones por tipo)
        self.stdout.write('Creando Servicios (30min y 60min)...')
        services_db = [] 
        
        for code, label in TypeChoices.choices:
            s30 = Service.objects.create(name=code, duration=30)
            services_db.append(s30)
            s60 = Service.objects.create(name=code, duration=60)
            services_db.append(s60)

        # 4. TRABAJADORES
        self.stdout.write('Creando Trabajadores...')
        workers_conf = [
            ("Elena Osteo", [TypeChoices.OSTEOPATHY_MASSAGE]),
            ("David Mag", [TypeChoices.PAR_MAGNETIC]),
            ("Laura Emo", [TypeChoices.EMOTIONAL_TECH]),
            ("Manuel Nutri", [TypeChoices.NUTRITIONAL_ADVICE]),
            ("Sofía General", [TypeChoices.OTHER]),
            ("Carlos Pro", [TypeChoices.OSTEOPATHY_MASSAGE, TypeChoices.PAR_MAGNETIC]),
            ("Marta Expert", [TypeChoices.NUTRITIONAL_ADVICE, TypeChoices.EMOTIONAL_TECH, TypeChoices.OTHER])
        ]

        workers_db = []
        for name, specs in workers_conf:
            w = Worker.objects.create(name=name)
            for s in specs:
                w.specialties.add(specialties_objs[s])
            workers_db.append(w)
            
            for day in range(5):
                Availability.objects.create(worker=w, day_of_week=day, start_time=time(9,0), end_time=time(17,0))

        # 5. CITAS Y VALORACIONES
        self.stdout.write('Generando Citas y Valoraciones...')

        def create_appt(user, worker_idx, service_idx, days_offset, hour, status):
            dt = timezone.now() + timedelta(days=days_offset)
            while dt.weekday() >= 5: dt += timedelta(days=1)
            dt = dt.replace(hour=hour, minute=0, second=0, microsecond=0)

            appt = Appointment.objects.create(
                user=user,
                worker=workers_db[worker_idx],
                service=services_db[service_idx],
                datetime=dt,
                status=status
            )

            if status == StatusChoices.COMPLETED:
                comments = ["Increíble servicio", "Muy profesional", "Me sentí muy bien", "Volveré seguro", "Correcto"]
                Review.objects.create(
                    appointment=appt,
                    rating=random.randint(4, 5),
                    comment=random.choice(comments)
                )

        create_appt(user1, 0, 0, -10, 10, StatusChoices.COMPLETED) 
        create_appt(user1, 5, 2, -5, 11, StatusChoices.COMPLETED)
        
        create_appt(user1, 1, 3, 2, 9, StatusChoices.CONFIRMED)  
        create_appt(user1, 2, 4, 3, 12, StatusChoices.PENDING)   
        create_appt(user1, 6, 6, 5, 16, StatusChoices.PENDING)   

        create_appt(user2, 3, 6, -20, 9, StatusChoices.COMPLETED) 
        create_appt(user2, 4, 8, -15, 10, StatusChoices.COMPLETED) 
        create_appt(user2, 0, 1, -2, 14, StatusChoices.COMPLETED)  
        
        create_appt(user2, 5, 0, 1, 10, StatusChoices.CONFIRMED)
        create_appt(user2, 6, 8, 4, 11, StatusChoices.CONFIRMED)

        self.stdout.write(self.style.SUCCESS('¡Datos cargados: Usuarios, Servicios Dobles y Valoraciones creadas!'))