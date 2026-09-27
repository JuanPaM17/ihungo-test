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
