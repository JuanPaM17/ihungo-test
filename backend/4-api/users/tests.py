from datetime import datetime
from datetime import timezone as tz

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from activities.models import Activity
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
        self.admin_user = make_user("admin@example.com", "000001", role=User.Role.ADMIN)
        self.associate_user = make_user("assoc@example.com", "000002")
        self.asociado = Asociado.objects.create(user=self.associate_user)
        self.list_url = reverse("asociado-list")
        self.detail_url = reverse("asociado-detail", args=[self.asociado.pk])

    def _auth_as(self, email: str) -> None:
        response = self.client.post(
            reverse("token_obtain_pair"),
            {"email": email, "password": "pass1234"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def _auth(self) -> None:
        self._auth_as("admin@example.com")

    # ── List ──────────────────────────────────────────────────────────────────

    def test_list_asociados_authenticated(self) -> None:
        self._auth()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_unauthenticated_returns_401(self) -> None:
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── Retrieve ──────────────────────────────────────────────────────────────

    def test_retrieve_asociado_authenticated(self) -> None:
        self._auth()
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "assoc@example.com")

    def test_retrieve_unauthenticated_returns_401(self) -> None:
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_nonexistent_returns_404(self) -> None:
        self._auth()
        response = self.client.get(reverse("asociado-detail", args=[99999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ── Create ────────────────────────────────────────────────────────────────

    def test_create_asociado_as_admin(self) -> None:
        self._auth()
        payload = {
            "email": "nuevo@example.com",
            "password": "segura1234",
            "identification": "000099",
            "first_name": "Nuevo",
            "last_name": "Asociado",
            "city": "Cali",
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], "nuevo@example.com")

    def test_create_asociado_duplicate_email_returns_400(self) -> None:
        self._auth()
        payload = {
            "email": "assoc@example.com",
            "password": "segura1234",
            "identification": "000088",
            "first_name": "Dup",
            "last_name": "Email",
            "city": "Cali",
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_asociado_as_associate_returns_403(self) -> None:
        self._auth_as("assoc@example.com")
        payload = {
            "email": "otro@example.com",
            "password": "segura1234",
            "identification": "000077",
            "first_name": "Otro",
            "last_name": "User",
            "city": "Medellin",
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ── Update ────────────────────────────────────────────────────────────────

    def test_partial_update_as_admin(self) -> None:
        self._auth()
        response = self.client.patch(self.detail_url, {"city": "Medellin"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["city"], "Medellin")

    def test_partial_update_as_associate_returns_403(self) -> None:
        self._auth_as("assoc@example.com")
        response = self.client.patch(self.detail_url, {"city": "Medellin"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ── Delete ────────────────────────────────────────────────────────────────

    def test_delete_asociado_as_admin(self) -> None:
        self._auth()
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Asociado.objects.filter(pk=self.asociado.pk).exists())

    def test_delete_asociado_as_associate_returns_403(self) -> None:
        self._auth_as("assoc@example.com")
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_asociado_with_activities_returns_409(self) -> None:
        self._auth()
        Activity.objects.create(
            asociado=self.asociado,
            creator=self.admin_user,
            activity_type="meeting",
            start_datetime=datetime(2030, 1, 1, 9, 0, tzinfo=tz.utc),
            end_datetime=datetime(2030, 1, 1, 10, 0, tzinfo=tz.utc),
        )
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["code"], "HAS_ACTIVITIES")
