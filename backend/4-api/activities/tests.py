from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from activities.models import Activity
from users.models import Asociado, User


def make_user(email: str, identification: str) -> User:
    return User.objects.create_user(
        email=email,
        password="pass1234",
        identification=identification,
        first_name="Test",
        last_name="User",
        city="Bogota",
    )


class ActivityModelTest(TestCase):
    def setUp(self) -> None:
        self.creator = make_user("creator@example.com", "111111")
        self.associate_user = make_user("associate@example.com", "222222")
        self.asociado = Asociado.objects.create(user=self.associate_user)

    def test_create_activity(self) -> None:
        activity = Activity.objects.create(
            activity_type=Activity.Type.WORKSHOP,
            description="Taller de prueba",
            start_datetime=timezone.now(),
            end_datetime=timezone.now(),
            asociado=self.asociado,
            creator=self.creator,
        )
        self.assertEqual(activity.activity_type, Activity.Type.WORKSHOP)

    def test_activity_related_to_asociado(self) -> None:
        activity = Activity.objects.create(
            activity_type=Activity.Type.MEETING,
            start_datetime=timezone.now(),
            end_datetime=timezone.now(),
            asociado=self.asociado,
            creator=self.creator,
        )
        self.assertEqual(activity.asociado, self.asociado)

    def test_activity_related_to_creator(self) -> None:
        activity = Activity.objects.create(
            activity_type=Activity.Type.SEMINAR,
            start_datetime=timezone.now(),
            end_datetime=timezone.now(),
            asociado=self.asociado,
            creator=self.creator,
        )
        self.assertEqual(activity.creator, self.creator)

    def test_asociado_activities_reverse_relation(self) -> None:
        Activity.objects.create(
            activity_type=Activity.Type.TRAINING,
            start_datetime=timezone.now(),
            end_datetime=timezone.now(),
            asociado=self.asociado,
            creator=self.creator,
        )
        self.assertEqual(self.asociado.activities.count(), 1)


class ActivityAPITest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.creator = make_user("creator@example.com", "111111")
        associate_user = make_user("associate@example.com", "222222")
        self.asociado = Asociado.objects.create(user=associate_user)
        self.list_url = reverse("actividad-list")

        response = self.client.post(
            reverse("token_obtain_pair"),
            {"email": "creator@example.com", "password": "pass1234"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

        self.activity_data = {
            "activity_type": "workshop",
            "description": "Taller inicial",
            "start_datetime": "2026-10-01T09:00:00Z",
            "end_datetime": "2026-10-01T11:00:00Z",
            "asociado": self.asociado.id,
        }

    def _create_activity(self, **kwargs) -> Activity:
        data = {**self.activity_data, **kwargs}
        return Activity.objects.create(
            activity_type=data.get("activity_type", "workshop"),
            start_datetime=data.get("start_datetime", timezone.now()),
            end_datetime=data.get("end_datetime", timezone.now()),
            asociado=self.asociado,
            creator=self.creator,
        )

    def test_list_activities(self) -> None:
        self._create_activity()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_activity(self) -> None:
        response = self.client.post(self.list_url, self.activity_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_creator_is_request_user(self) -> None:
        response = self.client.post(self.list_url, self.activity_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        activity = Activity.objects.get(id=response.data["id"])
        self.assertEqual(activity.creator, self.creator)

    def test_partial_update_activity(self) -> None:
        activity = self._create_activity()
        url = reverse("actividad-detail", args=[activity.id])
        response = self.client.patch(url, {"description": "Actualizado"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        activity.refresh_from_db()
        self.assertEqual(activity.description, "Actualizado")

    def test_delete_activity(self) -> None:
        activity = self._create_activity()
        url = reverse("actividad-detail", args=[activity.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Activity.objects.filter(id=activity.id).exists())

    def test_filter_by_desde(self) -> None:
        Activity.objects.create(
            activity_type="workshop",
            start_datetime="2026-09-01T09:00:00Z",
            end_datetime="2026-09-01T11:00:00Z",
            asociado=self.asociado,
            creator=self.creator,
        )
        Activity.objects.create(
            activity_type="seminar",
            start_datetime="2026-11-01T09:00:00Z",
            end_datetime="2026-11-01T11:00:00Z",
            asociado=self.asociado,
            creator=self.creator,
        )
        response = self.client.get(self.list_url, {"desde": "2026-10-01"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_hasta(self) -> None:
        Activity.objects.create(
            activity_type="workshop",
            start_datetime="2026-09-01T09:00:00Z",
            end_datetime="2026-09-01T11:00:00Z",
            asociado=self.asociado,
            creator=self.creator,
        )
        Activity.objects.create(
            activity_type="seminar",
            start_datetime="2026-11-01T09:00:00Z",
            end_datetime="2026-11-01T11:00:00Z",
            asociado=self.asociado,
            creator=self.creator,
        )
        response = self.client.get(self.list_url, {"hasta": "2026-10-01"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_range(self) -> None:
        Activity.objects.create(
            activity_type="workshop",
            start_datetime="2026-09-01T09:00:00Z",
            end_datetime="2026-09-01T11:00:00Z",
            asociado=self.asociado,
            creator=self.creator,
        )
        Activity.objects.create(
            activity_type="seminar",
            start_datetime="2026-10-15T09:00:00Z",
            end_datetime="2026-10-15T11:00:00Z",
            asociado=self.asociado,
            creator=self.creator,
        )
        Activity.objects.create(
            activity_type="meeting",
            start_datetime="2026-11-01T09:00:00Z",
            end_datetime="2026-11-01T11:00:00Z",
            asociado=self.asociado,
            creator=self.creator,
        )
        response = self.client.get(self.list_url, {"desde": "2026-10-01", "hasta": "2026-10-31"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_reject_unauthenticated(self) -> None:
        self.client.credentials()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# =============================================================================
# Fase 5 — Validación de fechas
# =============================================================================

class DateValidationTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="pass1234",
            identification="100001",
            first_name="Admin",
            last_name="User",
            city="Bogota",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        associate_user = make_user("assoc@example.com", "100002")
        self.asociado = Asociado.objects.create(user=associate_user)
        self.list_url = reverse("actividad-list")

        response = self.client.post(
            reverse("token_obtain_pair"),
            {"email": "admin@example.com", "password": "pass1234"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

        self.base_data = {
            "activity_type": "workshop",
            "asociado": self.asociado.id,
        }

    def test_reject_end_equal_to_start(self) -> None:
        data = {**self.base_data, "start_datetime": "2026-10-01T10:00:00Z", "end_datetime": "2026-10-01T10:00:00Z"}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "INVALID_DATE_RANGE")

    def test_reject_end_before_start(self) -> None:
        data = {**self.base_data, "start_datetime": "2026-10-01T10:00:00Z", "end_datetime": "2026-10-01T09:00:00Z"}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "INVALID_DATE_RANGE")

    def test_accept_valid_date_range(self) -> None:
        data = {**self.base_data, "start_datetime": "2026-10-01T09:00:00Z", "end_datetime": "2026-10-01T11:00:00Z"}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


# =============================================================================
# Fase 5 — Solapamientos
# =============================================================================

class OverlapValidationTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="pass1234",
            identification="200001",
            first_name="Admin",
            last_name="User",
            city="Bogota",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        associate_user = make_user("assoc@example.com", "200002")
        self.asociado = Asociado.objects.create(user=associate_user)
        self.list_url = reverse("actividad-list")

        response = self.client.post(
            reverse("token_obtain_pair"),
            {"email": "admin@example.com", "password": "pass1234"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

        # Actividad base: 10:00 - 11:00
        self.existing = Activity.objects.create(
            activity_type="workshop",
            start_datetime="2026-10-01T10:00:00Z",
            end_datetime="2026-10-01T11:00:00Z",
            asociado=self.asociado,
            creator=self.admin,
        )
        self.base_data = {"activity_type": "seminar", "asociado": self.asociado.id}

    def test_reject_overlap_at_start(self) -> None:
        # 10:30 - 11:30 solapa al inicio
        data = {**self.base_data, "start_datetime": "2026-10-01T10:30:00Z", "end_datetime": "2026-10-01T11:30:00Z"}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["error"]["code"], "ACTIVITY_OVERLAP")

    def test_reject_overlap_at_end(self) -> None:
        # 09:30 - 10:30 solapa al final
        data = {**self.base_data, "start_datetime": "2026-10-01T09:30:00Z", "end_datetime": "2026-10-01T10:30:00Z"}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["error"]["code"], "ACTIVITY_OVERLAP")

    def test_reject_activity_contained_within(self) -> None:
        # 10:15 - 10:45 contenida dentro
        data = {**self.base_data, "start_datetime": "2026-10-01T10:15:00Z", "end_datetime": "2026-10-01T10:45:00Z"}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["error"]["code"], "ACTIVITY_OVERLAP")

    def test_reject_activity_containing_existing(self) -> None:
        # 09:30 - 11:30 contiene a la existente
        data = {**self.base_data, "start_datetime": "2026-10-01T09:30:00Z", "end_datetime": "2026-10-01T11:30:00Z"}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["error"]["code"], "ACTIVITY_OVERLAP")

    def test_allow_activity_ending_when_other_starts(self) -> None:
        # 09:00 - 10:00 termina justo cuando comienza la existente
        data = {**self.base_data, "start_datetime": "2026-10-01T09:00:00Z", "end_datetime": "2026-10-01T10:00:00Z"}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_allow_activity_starting_when_other_ends(self) -> None:
        # 11:00 - 12:00 comienza justo cuando termina la existente
        data = {**self.base_data, "start_datetime": "2026-10-01T11:00:00Z", "end_datetime": "2026-10-01T12:00:00Z"}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_edit_does_not_conflict_with_itself(self) -> None:
        # Actualizar la misma actividad no debe considerarse solapamiento
        url = reverse("actividad-detail", args=[self.existing.id])
        response = self.client.patch(url, {"description": "Actualizado"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# =============================================================================
# Fase 5 — Permisos y visibilidad
# =============================================================================

class PermissionsAndVisibilityTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

        # Admin
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="pass1234",
            identification="300001",
            first_name="Admin",
            last_name="User",
            city="Bogota",
            role=User.Role.ADMIN,
            is_staff=True,
        )

        # Asociado 1
        self.assoc_user1 = make_user("assoc1@example.com", "300002")
        self.asociado1 = Asociado.objects.create(user=self.assoc_user1)

        # Asociado 2 (no relacionado con las actividades del asociado1)
        self.assoc_user2 = make_user("assoc2@example.com", "300003")
        self.asociado2 = Asociado.objects.create(user=self.assoc_user2)

        self.list_url = reverse("actividad-list")

    def _get_token(self, email: str) -> str:
        response = self.client.post(
            reverse("token_obtain_pair"),
            {"email": email, "password": "pass1234"},
            format="json",
        )
        return response.data["access"]

    def _auth_as(self, email: str) -> None:
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self._get_token(email)}")

    def _make_activity(self, start: str, end: str, asociado=None, creator=None) -> Activity:
        return Activity.objects.create(
            activity_type="workshop",
            start_datetime=start,
            end_datetime=end,
            asociado=asociado or self.asociado1,
            creator=creator or self.admin,
        )

    # --- Admin ---

    def test_admin_can_create_activity(self) -> None:
        self._auth_as("admin@example.com")
        response = self.client.post(self.list_url, {
            "activity_type": "workshop",
            "start_datetime": "2026-10-01T09:00:00Z",
            "end_datetime": "2026-10-01T11:00:00Z",
            "asociado": self.asociado1.id,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_can_update_activity(self) -> None:
        activity = self._make_activity("2026-10-01T09:00:00Z", "2026-10-01T11:00:00Z")
        self._auth_as("admin@example.com")
        url = reverse("actividad-detail", args=[activity.id])
        response = self.client.patch(url, {"description": "Admin update"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_delete_activity(self) -> None:
        activity = self._make_activity("2026-10-01T09:00:00Z", "2026-10-01T11:00:00Z")
        self._auth_as("admin@example.com")
        url = reverse("actividad-detail", args=[activity.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # --- Asociado sobre actividades futuras ---

    def test_asociado_can_update_future_activity(self) -> None:
        activity = self._make_activity("2027-01-01T09:00:00Z", "2027-01-01T11:00:00Z")
        self._auth_as("assoc1@example.com")
        url = reverse("actividad-detail", args=[activity.id])
        response = self.client.patch(url, {"description": "Asociado update"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_asociado_can_delete_future_activity(self) -> None:
        activity = self._make_activity("2027-01-01T09:00:00Z", "2027-01-01T11:00:00Z")
        self._auth_as("assoc1@example.com")
        url = reverse("actividad-detail", args=[activity.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # --- Asociado sobre actividades pasadas ---

    def test_asociado_cannot_update_past_activity(self) -> None:
        activity = self._make_activity("2020-01-01T09:00:00Z", "2020-01-01T11:00:00Z")
        self._auth_as("assoc1@example.com")
        url = reverse("actividad-detail", args=[activity.id])
        response = self.client.patch(url, {"description": "No permitido"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_asociado_cannot_delete_past_activity(self) -> None:
        activity = self._make_activity("2020-01-01T09:00:00Z", "2020-01-01T11:00:00Z")
        self._auth_as("assoc1@example.com")
        url = reverse("actividad-detail", args=[activity.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Visibilidad ---

    def test_user_sees_activity_they_created(self) -> None:
        self._make_activity("2026-10-01T09:00:00Z", "2026-10-01T11:00:00Z", creator=self.assoc_user1)
        self._auth_as("assoc1@example.com")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_asociado_sees_activity_where_related(self) -> None:
        self._make_activity("2026-10-01T09:00:00Z", "2026-10-01T11:00:00Z", asociado=self.asociado1)
        self._auth_as("assoc1@example.com")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_user_cannot_see_unrelated_activities(self) -> None:
        # Actividad del asociado2, creada por admin — assoc1 no debe verla
        self._make_activity("2026-10-01T09:00:00Z", "2026-10-01T11:00:00Z", asociado=self.asociado2, creator=self.admin)
        self._auth_as("assoc1@example.com")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    # --- Acceso sin autenticación ---

    def test_unauthenticated_receives_401(self) -> None:
        self.client.credentials()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Usuario no relacionado no puede modificar ---

    def test_unrelated_user_cannot_modify_activity(self) -> None:
        activity = self._make_activity("2027-01-01T09:00:00Z", "2027-01-01T11:00:00Z", asociado=self.asociado1)
        self._auth_as("assoc2@example.com")
        url = reverse("actividad-detail", args=[activity.id])
        response = self.client.patch(url, {"description": "No permitido"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
