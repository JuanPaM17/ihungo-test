from django.test import TestCase

from registrations.models import RegistrationRequest


class RegistrationRequestModelTest(TestCase):
    def test_default_status_is_pending(self) -> None:
        req = RegistrationRequest.objects.create(
            first_name="Ana",
            last_name="Torres",
            email="ana@example.com",
        )
        self.assertEqual(req.status, RegistrationRequest.Status.PENDING)

    def test_str_representation(self) -> None:
        req = RegistrationRequest.objects.create(
            first_name="Ana",
            last_name="Torres",
            email="ana2@example.com",
        )
        self.assertIn("Ana", str(req))
        self.assertIn("Pendiente", str(req))
