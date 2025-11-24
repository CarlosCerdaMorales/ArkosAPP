from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from appointments.models import Appointment, Availability, Service, StatusChoices
from workers.models import TypeChoices, Worker

User = get_user_model()


class AppointmentLogicTest(TestCase):

    def setUp(self):
        """
        Initial setup for tests.
        We create a user, a worker, and two services with different durations.
        """
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
            phone_number="+34 600111222",
        )

        self.worker = Worker.objects.create(name="Worker Test")

        self.service_60 = Service.objects.create(
            name=TypeChoices.OSTEOPATHY_MASSAGE, duration=60
        )

        self.service_30 = Service.objects.create(
            name=TypeChoices.NUTRITIONAL_ADVICE, duration=30
        )

    def test_calculated_end_time(self):
        """
        Test that calculated_end_time returns the correct end time based on service duration.
        1. For a 60-minute service, the end time should be start time + 60 minutes.
        2. For a 30-minute service, the end time should be start time + 30 minutes.
        """
        start_time = timezone.now()

        appointment_1 = Appointment.objects.create(
            user=self.user,
            worker=self.worker,
            service=self.service_60,
            datetime=start_time,
        )

        expected_end_1 = start_time + timedelta(minutes=60)
        self.assertEqual(appointment_1.calculated_end_time, expected_end_1)

        appointment_2 = Appointment.objects.create(
            user=self.user,
            worker=self.worker,
            service=self.service_30,
            datetime=start_time,
        )

        expected_end_2 = start_time + timedelta(minutes=30)
        self.assertEqual(appointment_2.calculated_end_time, expected_end_2)

    def test_can_be_cancelled_true(self):
        """
        Test that can_be_cancelled returns True if there are more than 12 hours left.
        """
        future_date = timezone.now() + timedelta(hours=24)

        appointment = Appointment.objects.create(
            user=self.user,
            worker=self.worker,
            service=self.service_60,
            datetime=future_date,
        )
        self.assertTrue(appointment.can_be_cancelled)

    def test_can_be_cancelled_false_too_soon(self):
        """
        Test that can_be_cancelled returns False if there are less than 12 hours left.
        """
        soon_date = timezone.now() + timedelta(hours=2)

        appointment = Appointment.objects.create(
            user=self.user,
            worker=self.worker,
            service=self.service_60,
            datetime=soon_date,
        )

        self.assertFalse(appointment.can_be_cancelled)

    def test_can_be_cancelled_false_in_past(self):
        """
        Test that can_be_cancelled returns False for past appointments.
        """
        past_date = timezone.now() - timedelta(days=1)

        appointment = Appointment.objects.create(
            user=self.user,
            worker=self.worker,
            service=self.service_60,
            datetime=past_date,
        )

        self.assertFalse(appointment.can_be_cancelled)


class AppointmentViewsTest(TestCase):

    def setUp(self):
        """
        Initial setup for view tests.
        """
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            password="password",
            email="test@example.com",
            phone_number="+34 600111222",
        )
        self.other_user = User.objects.create_user(
            username="other",
            password="password",
            email="other@example.com",
            phone_number="+34 600333444",
        )

        self.worker = Worker.objects.create(name="Worker Test")
        self.service = Service.objects.create(
            name=TypeChoices.OSTEOPATHY_MASSAGE, duration=60
        )

        self.client.login(username="testuser", password="password")

    def test_history_view_logic(self):
        """
        Should only show PAST and COMPLETED appointments of the logged-in user.
        """
        past_date = timezone.now() - timedelta(days=1)

        app1 = Appointment.objects.create(
            user=self.user,
            worker=self.worker,
            service=self.service,
            datetime=past_date,
            status=StatusChoices.COMPLETED,
        )

        Appointment.objects.create(
            user=self.user,
            worker=self.worker,
            service=self.service,
            datetime=timezone.now() + timedelta(days=1),
            status=StatusChoices.CONFIRMED,
        )

        Appointment.objects.create(
            user=self.other_user,
            worker=self.worker,
            service=self.service,
            datetime=past_date,
            status=StatusChoices.COMPLETED,
        )

        response = self.client.get(reverse("appointment_history"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, app1.service.get_name_display())
        self.assertEqual(len(response.context["appointments"]), 1)

    def test_upcoming_view_logic(self):
        """
        Should only show FUTURE and CONFIRMED appointments of the logged-in user.
        """
        future_date = timezone.now() + timedelta(days=1)

        app1 = Appointment.objects.create(
            user=self.user,
            worker=self.worker,
            service=self.service,
            datetime=future_date,
            status=StatusChoices.CONFIRMED,
        )

        Appointment.objects.create(
            user=self.user,
            worker=self.worker,
            service=self.service,
            datetime=timezone.now() - timedelta(days=1),
            status=StatusChoices.COMPLETED,
        )

        response = self.client.get(reverse("upcoming_appointments"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["appointments"]), 1)

    def test_create_appointment_success(self):
        """
        Should create an appointment successfully.
        """
        future_date = timezone.now() + timedelta(days=2)
        data = {
            "service": self.service.id,
            "date": future_date.date(),
            "time": time(10, 0),
            "worker_id": self.worker.id,
        }

        response = self.client.post(reverse("create_appointment"), data)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Appointment.objects.filter(user=self.user, datetime__hour=10).exists()
        )

    def test_create_appointment_fail_past_date(self):
        """Should not allow booking in the past."""
        past_date = timezone.now() - timedelta(days=1)
        data = {
            "service": self.service.id,
            "date": past_date.date(),
            "time": time(10, 0),
            "worker_id": self.worker.id,
        }

        response = self.client.post(reverse("create_appointment"), data)
        self.assertEqual(response.status_code, 200)

        form = response.context["form"]

        self.assertFalse(form.is_valid())

        self.assertIn("No puedes reservar en el pasado.", form.non_field_errors())

    def test_create_appointment_fail_overlap(self):
        """Should not allow booking overlapping appointments."""
        future_date = timezone.now() + timedelta(days=3)
        Appointment.objects.create(
            user=self.other_user,
            worker=self.worker,
            service=self.service,
            datetime=future_date.replace(hour=10, minute=0),
            status=StatusChoices.CONFIRMED,
        )

        data = {
            "service": self.service.id,
            "date": future_date.date(),
            "time": time(10, 30),
            "worker_id": self.worker.id,
        }

        response = self.client.post(reverse("create_appointment"), data)
        self.assertEqual(response.status_code, 200)

        form = response.context["form"]
        self.assertFalse(form.is_valid())

        expected_error = "Esta franja horaria ya está reservada o se solapa con otra cita existente. Por favor, selecciona otro horario."
        self.assertIn(expected_error, form.non_field_errors())

    def test_cancel_valid(self):
        """
        Cancelling with >12h deletes the appointment.
        """
        future_date = timezone.now() + timedelta(hours=24)
        app = Appointment.objects.create(
            user=self.user,
            worker=self.worker,
            service=self.service,
            datetime=future_date,
        )

        response = self.client.get(reverse("cancel_appointment", args=[app.id]))

        self.assertRedirects(response, reverse("upcoming_appointments"))
        self.assertFalse(Appointment.objects.filter(id=app.id).exists())

    def test_cancel_invalid_too_late(self):
        """
        Cancalling with <12h does not delete the appointment.
        """
        soon_date = timezone.now() + timedelta(hours=2)
        app = Appointment.objects.create(
            user=self.user, worker=self.worker, service=self.service, datetime=soon_date
        )

        response = self.client.get(reverse("cancel_appointment", args=[app.id]))

        self.assertTrue(Appointment.objects.filter(id=app.id).exists())

    def test_cancel_other_user_appointment(self):
        """
        Trying to cancel another user's appointment returns 404.
        """
        future_date = timezone.now() + timedelta(hours=24)
        app_other = Appointment.objects.create(
            user=self.other_user,
            worker=self.worker,
            service=self.service,
            datetime=future_date,
        )

        response = self.client.get(reverse("cancel_appointment", args=[app_other.id]))
        self.assertEqual(response.status_code, 404)

    def test_api_get_slots(self):
        """
        Basic test for the get_available_slots API endpoint.
        """
        today = timezone.now().date()
        next_monday = today + timedelta(days=(7 - today.weekday()))

        Availability.objects.create(
            worker=self.worker,
            day_of_week=0,
            start_time=time(9, 0),
            end_time=time(11, 0),
        )

        url = reverse("get_available_slots")
        response = self.client.get(
            url, {"service_id": self.service.id, "date": next_monday}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("slots", data)
