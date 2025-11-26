import os
import random
from datetime import time, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils import timezone

from appointments.models import Appointment, Availability, Service, StatusChoices
from reviews.models import Review
from workers.models import Specialty, TypeChoices, Worker

User = get_user_model()


class Command(BaseCommand):
    help = "Carga datos iniciales"

    def handle(self, *args, **kwargs):
        self.stdout.write("Limpiando base de datos...")
        Review.objects.all().delete()
        Appointment.objects.all().delete()
        Availability.objects.all().delete()
        Service.objects.all().delete()
        Worker.objects.all().delete()
        Specialty.objects.all().delete()
        User.objects.exclude(username="admin").delete()

        IMAGES_SOURCE_DIR = os.path.join(
            settings.BASE_DIR, "workers", "fixtures", "images"
        )

        if not os.path.exists(IMAGES_SOURCE_DIR):
            self.stdout.write(
                self.style.WARNING(f"No existe la carpeta {IMAGES_SOURCE_DIR}")
            )

        self.stdout.write("Creando Especialidades...")
        specialties_objs = {}
        for code, label in TypeChoices.choices:
            obj, _ = Specialty.objects.get_or_create(name=code)
            specialties_objs[code] = obj

        self.stdout.write("Creando Usuarios...")
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                "admin",
                "admin@example.com",
                "admin",
                phone_number="+34 600000000",
                role="ADMIN",
            )

        user1 = User.objects.create_user(
            "user1",
            "u1@test.com",
            "user1234",
            phone_number="+34 611111111",
            role="REG",
            first_name="Juan",
            last_name="Cliente",
        )
        user2 = User.objects.create_user(
            "user2",
            "u2@test.com",
            "user1234",
            phone_number="+34 622222222",
            role="REG",
            first_name="Ana",
            last_name="Clienta",
        )

        self.stdout.write("Creando Servicios...")
        services_db = []
        for code, label in TypeChoices.choices:
            services_db.append(Service.objects.create(name=code, duration=30))
            services_db.append(Service.objects.create(name=code, duration=60))

        self.stdout.write("Creando Trabajadores...")

        workers_conf = [
            (
                "Elena Osteo",
                [TypeChoices.OSTEOPATHY_MASSAGE],
                "elena.jpg",
                "Especialista en osteopatía estructural con más de 15 años de experiencia aliviando dolores de espalda y corrigiendo posturas.",
            ),
            (
                "Jesús Navas",
                [TypeChoices.PAR_MAGNETIC],
                "jesus.jpg",
                "El 'Duende de Los Palacios'. Leyenda viva con una resistencia inagotable. Aplica su velocidad y constancia para equilibrar tu pH con una precisión de campeón del mundo.",
            ),
            (
                "Laura Emo",
                [TypeChoices.EMOTIONAL_TECH],
                "laura.jpg",
                "Terapeuta holística experta en desbloquear tensiones emocionales. Su enfoque suave te ayudará a reconectar contigo mismo.",
            ),
            (
                "Nemanja Gudelj",
                [TypeChoices.NUTRITIONAL_ADVICE],
                "gud.jpg",
                "El comodín incombustible. Un líder nato dentro y fuera del campo que destaca por su enorme polivalencia, rindiendo tanto de mediocentro como de central.",
            ),
            (
                "Sofía General",
                [TypeChoices.OTHER],
                "sofia.jpg",
                "Nuestra experta todoterreno. Combina diversas técnicas orientales y occidentales para ofrecer un tratamiento integral y personalizado.",
            ),
            (
                "Ivan Rakitic",
                [TypeChoices.OSTEOPATHY_MASSAGE, TypeChoices.PAR_MAGNETIC],
                "ivan.jpg",
                "El arquitecto croata. Capitán y líder que levantó la copa en Turín. Aporta clase, visión y una precisión milimétrica en cada tratamiento.",
            ),
            (
                "Yassine Bounou",
                [
                    TypeChoices.NUTRITIONAL_ADVICE,
                    TypeChoices.EMOTIONAL_TECH,
                    TypeChoices.OTHER,
                ],
                "bono.jpg",
                "Nuestro guardián y Premio Zamora. Héroe de Budapest. Su tranquilidad bajo palos se traduce en una paz mental absoluta para sus pacientes.",
            ),
        ]

        workers_db = []
        for name, specs, img_filename, bio_text in workers_conf:

            w = Worker.objects.create(name=name, bio=bio_text)

            for s in specs:
                w.specialties.add(specialties_objs[s])

            if img_filename:
                img_path = os.path.join(IMAGES_SOURCE_DIR, img_filename)
                if os.path.exists(img_path):
                    with open(img_path, "rb") as img_file:
                        w.image.save(img_filename, File(img_file), save=True)
                else:
                    self.stdout.write(self.style.WARNING(f"Falta foto: {img_filename}"))

            workers_db.append(w)

            for day in range(5):
                Availability.objects.create(
                    worker=w,
                    day_of_week=day,
                    start_time=time(9, 0),
                    end_time=time(17, 0),
                )

        self.stdout.write("Generando Citas y Valoraciones...")

        def create_appt(user, worker_idx, service_idx, days_offset, hour, status):
            dt = timezone.now() + timedelta(days=days_offset)
            while dt.weekday() >= 5:
                dt += timedelta(days=1)
            dt = dt.replace(hour=hour, minute=0, second=0, microsecond=0)

            appt = Appointment.objects.create(
                user=user,
                worker=workers_db[worker_idx],
                service=services_db[service_idx],
                datetime=dt,
                status=status,
            )

            if status == StatusChoices.COMPLETED and user != user1:
                comments = [
                    "Increíble servicio",
                    "Muy profesional",
                    "Me sentí muy bien",
                    "Volveré seguro",
                    "Correcto",
                ]
                Review.objects.create(
                    appointment=appt,
                    rating=random.randint(4, 5),
                    comment=random.choice(comments),
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

        self.stdout.write(self.style.SUCCESS("Datos cargados exitosamente"))
