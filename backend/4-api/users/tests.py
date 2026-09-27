from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from users.models import Asociado, User


class UserModelTest(TestCase):
    def test_create_user(self) -> None:
        user = User.objects.create_user(
            email="associate@example.com",
            password="pass1234",
            identification="123456",
            first_name="Juan",
            last_name="Perez",
            city="Bogota",
        )
        self.assertEqual(user.email, "associate@example.com")
        self.assertEqual(user.role, User.Role.ASSOCIATE)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password("pass1234"))

    def test_create_superuser(self) -> None:
        admin = User.objects.create_superuser(
            email="admin@example.com",
            password="admin1234",
            identification="999999",
            first_name="Admin",
            last_name="User",
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertEqual(admin.role, User.Role.ADMIN)

    def test_create_user_without_email_raises(self) -> None:
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="pass1234")

    def test_create_asociado(self) -> None:
        user = User.objects.create_user(
            email="asociado@example.com",
            password="pass1234",
            identification="777777",
            first_name="Maria",
            last_name="Lopez",
            city="Cali",
        )
        asociado = Asociado.objects.create(user=user)
        self.assertEqual(asociado.user, user)
        self.assertEqual(str(asociado), "Maria Lopez (asociado@example.com)")

    def test_asociado_is_one_to_one_with_user(self) -> None:
        user = User.objects.create_user(
            email="unique@example.com",
            password="pass1234",
            identification="888888",
            first_name="Carlos",
            last_name="Gomez",
            city="Bogota",
        )
        Asociado.objects.create(user=user)
        with self.assertRaises(Exception):
            Asociado.objects.create(user=user)


class AuthTokenTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="user@example.com",
            password="testpass123",
            identification="111111",
            first_name="Test",
            last_name="User",
            city="Medellin",
        )
        self.token_url = reverse("token_obtain_pair")
        self.refresh_url = reverse("token_refresh")

    def test_login_with_valid_credentials(self) -> None:
        response = self.client.post(
            self.token_url,
            {"email": "user@example.com", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_with_invalid_credentials(self) -> None:
        response = self.client.post(
            self.token_url,
            {"email": "user@example.com", "password": "wrongpass"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_refresh_token(self) -> None:
        login = self.client.post(
            self.token_url,
            {"email": "user@example.com", "password": "testpass123"},
            format="json",
        )
        refresh = login.data["refresh"]
        response = self.client.post(
            self.refresh_url,
            {"refresh": refresh},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
