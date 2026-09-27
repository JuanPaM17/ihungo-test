from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.models import Asociado, User


def make_user(email: str, identification: str, **kwargs) -> User:
    return User.objects.create_user(
        email=email,
        password="pass1234",
        identification=identification,
        first_name="Test",
        last_name="User",
        city="Bogota",
        **kwargs,
    )


class UserModelTest(TestCase):
    def test_create_user(self) -> None:
        user = make_user("associate@example.com", "123456")
        self.assertEqual(user.email, "associate@example.com")
        self.assertEqual(user.role, User.Role.ASSOCIATE)
        self.assertFalse(user.is_staff)
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
        user = make_user("asociado@example.com", "777777")
        asociado = Asociado.objects.create(user=user)
        self.assertEqual(asociado.user, user)

    def test_asociado_is_one_to_one_with_user(self) -> None:
        user = make_user("unique@example.com", "888888")
        Asociado.objects.create(user=user)
        with self.assertRaises(Exception):
            Asociado.objects.create(user=user)


class AuthTokenTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = make_user("user@example.com", "111111")
        self.token_url = reverse("token_obtain_pair")
        self.refresh_url = reverse("token_refresh")

    def test_login_with_valid_credentials(self) -> None:
        response = self.client.post(
            self.token_url,
            {"email": "user@example.com", "password": "pass1234"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_with_invalid_credentials(self) -> None:
        response = self.client.post(
            self.token_url,
            {"email": "user@example.com", "password": "wrongpass"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token(self) -> None:
        login = self.client.post(
            self.token_url,
            {"email": "user@example.com", "password": "pass1234"},
            format="json",
        )
        response = self.client.post(
            self.refresh_url,
            {"refresh": login.data["refresh"]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)


class AsociadoAPITest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = make_user("admin@example.com", "000001", role=User.Role.ADMIN)
        self.associate_user = make_user("assoc@example.com", "000002")
        self.asociado = Asociado.objects.create(user=self.associate_user)
        self.list_url = reverse("asociado-list")

    def _auth(self) -> None:
        response = self.client.post(
            reverse("token_obtain_pair"),
            {"email": "admin@example.com", "password": "pass1234"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_list_asociados_authenticated(self) -> None:
        self._auth()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_asociado_authenticated(self) -> None:
        self._auth()
        new_user = make_user("new@example.com", "000003")
        response = self.client.post(self.list_url, {"user": new_user.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_reject_unauthenticated(self) -> None:
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
