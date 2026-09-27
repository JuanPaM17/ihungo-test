from django.test import TestCase
from django.utils import timezone

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
        self.assertEqual(activity.description, "Taller de prueba")

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
