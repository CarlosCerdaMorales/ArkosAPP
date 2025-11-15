from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.test import TestCase
from django.urls import reverse

CustomUser = get_user_model()


class UserModelTest(TestCase):
    def test_user_creation_defaults(self):
        """
        Tests creation of a standard user with required, valid custom fields.
        """
        valid_email = "user@example.com"
        valid_phone = "+1 123456789012345"

        user = CustomUser.objects.create_user(
            username="user_test",
            email=valid_email,
            password="testpassword",
            phone_number=valid_phone,
        )

        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.email, valid_email)

        self.assertEqual(user.role, CustomUser.Role.REGISTRADO)

        self.assertEqual(user.phone_number, valid_phone)
        self.assertEqual(user.address, "")

    def test_superuser_creation(self):
        """
        Tests creation of a superuser with required, valid custom fields.
        """
        admin_user = CustomUser.objects.create_superuser(
            username="admin_test",
            email="admin@example.com",
            password="adminpassword",
            phone_number="+1 987654321098765",
        )
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)

    def test_str_method_output(self):
        """
        Tests the __str__ method (now with required fields).
        """
        user = CustomUser.objects.create_user(
            username="john_doe",
            email="john@example.com",
            password="testpassword",
            phone_number="+1 111111111111111",
        )
        self.assertEqual(str(user), "john_doe (Registrado)")

        admin = CustomUser.objects.create_user(
            username="site_admin",
            email="site@admin.com",
            password="p",
            role=CustomUser.Role.ADMIN,
            phone_number="+1 222222222222222",
        )
        self.assertEqual(str(admin), "site_admin (Administrador)")

    def test_email_uniqueness_enforced(self):
        """
        Tests that the unique=True constraint on email is enforced by the DB.
        """
        CustomUser.objects.create_user(
            username="user1",
            email="unique@example.com",
            password="p",
            phone_number="+1 333333333333333",
        )

        with self.assertRaises(IntegrityError):
            CustomUser.objects.create_user(
                username="user2",
                email="unique@example.com",
                password="p",
                phone_number="+1 444444444444444",
            )

    def test_phone_uniqueness_enforced(self):
        """
        Tests that the unique=True constraint on phone_number is enforced by the DB.
        """
        CustomUser.objects.create_user(
            username="user_A",
            email="A@example.com",
            password="p",
            phone_number="+1 555555555555555",
        )

        with self.assertRaises(IntegrityError):
            CustomUser.objects.create_user(
                username="user_B",
                email="B@example.com",
                password="p",
                phone_number="+1 555555555555555",
            )


class RegistrationViewTest(TestCase):
    def test_successful_registration(self):
        """
        Tests that a user can be created successfully through the register view
        with all new required and valid fields.
        """
        user_count_before = CustomUser.objects.count()

        valid_data = {
            "username": "new_user",
            "first_name": "Test",
            "last_name": "User",
            "email": "new_user@example.com",
            "phone_number": "+1 555555555555555",
            "address": "123 Test St",
            "password1": "StrongPass123",
            "password2": "StrongPass123",
        }

        response = self.client.post(reverse("register"), valid_data)

        self.assertEqual(CustomUser.objects.count(), user_count_before + 1)

        self.assertRedirects(response, reverse("login"))

        created_user = CustomUser.objects.get(username="new_user")
        self.assertEqual(created_user.email, valid_data["email"])
        self.assertEqual(created_user.phone_number, valid_data["phone_number"])

    def test_registration_invalid_phone_format(self):
        """
        Tests that registration fails with an invalid phone number format.
        """
        user_count_before = CustomUser.objects.count()

        invalid_data = {
            "username": "badphone",
            "email": "badphone@example.com",
            "phone_number": "ESTO NO ES UN NUMERO",
            "password1": "StrongPass123",
            "password2": "StrongPass123",
        }

        response = self.client.post(reverse("register"), invalid_data)

        self.assertEqual(CustomUser.objects.count(), user_count_before)

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "El formato del teléfono debe ser:")

    def test_registration_fails_with_existing_email(self):
        """
        Tests that registration fails if the email already exists in the database.
        """
        CustomUser.objects.create_user(
            username="user1",
            email="test@example.com",
            password="password123",
            phone_number="+1 111111111111111",
        )

        user_count_before = CustomUser.objects.count()

        response = self.client.post(
            reverse("register"),
            {
                "username": "user2",
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
                "phone_number": "+1 222222222222222",
                "address": "123 Fake St",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
            },
        )

        self.assertEqual(CustomUser.objects.count(), user_count_before)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Ya existe Usuario con este Email.")

    def test_registration_fails_with_mismatched_passwords(self):
        """
        Tests that registration fails if password1 and password2 are different.
        """
        user_count_before = CustomUser.objects.count()

        response = self.client.post(
            reverse("register"),
            {
                "username": "mismatch",
                "first_name": "Test",
                "last_name": "User",
                "email": "mismatch@example.com",
                "phone_number": "+1 333333333333333",
                "address": "123 Fake St",
                "password1": "StrongPass123",
                "password2": "DIFFERENT_Pass456",
            },
        )

        self.assertEqual(CustomUser.objects.count(), user_count_before)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Los dos campos de contraseña no coinciden.")

    def test_registration_fails_with_existing_username(self):
        """
        Tests that registration fails if the username already exists.
        """
        CustomUser.objects.create_user(
            username="existing_user",
            email="test1@example.com",
            password="password123",
            phone_number="+1 444444444444444",
        )

        user_count_before = CustomUser.objects.count()

        response = self.client.post(
            reverse("register"),
            {
                "username": "existing_user",
                "first_name": "Test",
                "last_name": "User",
                "email": "test2@example.com",
                "phone_number": "+1 555555555555555",
                "address": "123 Fake St",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
            },
        )

        self.assertEqual(CustomUser.objects.count(), user_count_before)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Ya existe un usuario con este nombre.")
