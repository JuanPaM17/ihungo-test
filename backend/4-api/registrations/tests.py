from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from registrations.models import RegistrationRequest
from users.models import Asociado, User

REGISTRO_URL = "/api/registro/"


def make_admin() -> User:
    return User.objects.create_user(
        email="admin@example.com",
        password="pass1234",
        identification="000001",
        first_name="Admin",
        last_name="User",
        city="Bogota",
        role=User.Role.ADMIN,
        is_staff=True,
    )


class RegistrationRequestPublicAPITest(TestCase):
    """Tests del endpoint público POST /api/registro/"""

    def setUp(self) -> None:
        self.client = APIClient()
        self.valid_data = {
            "first_name": "Ana",
            "last_name": "Torres",
            "email": "ana@example.com",
        }

    def test_create_registration_without_auth(self) -> None:
        # Caso 1: endpoint público, no requiere JWT
        response = self.client.post(REGISTRO_URL, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_new_request_is_pending(self) -> None:
        # Caso 2: estado inicial = pendiente
        self.client.post(REGISTRO_URL, self.valid_data, format="json")
        req = RegistrationRequest.objects.get(email="ana@example.com")
        self.assertEqual(req.status, RegistrationRequest.Status.PENDING)

    def test_requested_at_is_set_automatically(self) -> None:
        # Caso 3: fecha_solicitud automática
        self.client.post(REGISTRO_URL, self.valid_data, format="json")
        req = RegistrationRequest.objects.get(email="ana@example.com")
        self.assertIsNotNone(req.requested_at)

    def test_reject_invalid_email(self) -> None:
        # Caso 4: email inválido
        data = {**self.valid_data, "email": "not-an-email"}
        response = self.client.post(REGISTRO_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_empty_first_name(self) -> None:
        # Caso 5: nombre vacío
        data = {**self.valid_data, "first_name": ""}
        response = self.client.post(REGISTRO_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_duplicate_pending_request(self) -> None:
        # Caso 6: no permitir dos solicitudes pendientes para el mismo email
        self.client.post(REGISTRO_URL, self.valid_data, format="json")
        response = self.client.post(REGISTRO_URL, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "REGISTRATION_ALREADY_PENDING")

    def test_reject_if_user_already_exists(self) -> None:
        # Caso 7: email ya pertenece a un usuario activo
        User.objects.create_user(
            email="ana@example.com",
            password="pass1234",
            identification="111111",
            first_name="Ana",
            last_name="Torres",
            city="Bogota",
        )
        response = self.client.post(REGISTRO_URL, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "USER_ALREADY_EXISTS")


class RegistrationApprovalServiceTest(TestCase):
    """Tests de la lógica de aprobación/rechazo."""

    def setUp(self) -> None:
        self.admin = make_admin()
        self.pending = RegistrationRequest.objects.create(
            first_name="Carlos",
            last_name="Gomez",
            email="carlos@example.com",
        )

    def test_admin_can_approve_pending_request(self) -> None:
        # Caso 8: admin puede aprobar solicitud pendiente
        from registrations.services import approve_request
        approve_request(self.pending)
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, RegistrationRequest.Status.APPROVED)

    def test_approve_creates_user_and_asociado(self) -> None:
        # Caso 9: aprobar crea usuario y asociado
        from registrations.services import approve_request
        approve_request(self.pending)
        self.assertTrue(User.objects.filter(email="carlos@example.com").exists())
        user = User.objects.get(email="carlos@example.com")
        self.assertTrue(Asociado.objects.filter(user=user).exists())

    def test_approve_sets_status_to_approved(self) -> None:
        # Caso 10: solicitud queda en estado aprobada
        from registrations.services import approve_request
        approve_request(self.pending)
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, RegistrationRequest.Status.APPROVED)

    def test_cannot_approve_already_approved_request(self) -> None:
        # Caso 11: no se puede aprobar dos veces
        from registrations.services import RegistrationServiceError, approve_request
        approve_request(self.pending)
        self.pending.refresh_from_db()
        with self.assertRaises(RegistrationServiceError):
            approve_request(self.pending)

    def test_cannot_approve_rejected_request(self) -> None:
        # Caso 12: no se puede aprobar una rechazada
        from registrations.services import RegistrationServiceError, approve_request
        self.pending.status = RegistrationRequest.Status.REJECTED
        self.pending.save()
        with self.assertRaises(RegistrationServiceError):
            approve_request(self.pending)

    def test_admin_can_reject_pending_request(self) -> None:
        # Caso 13: admin puede rechazar solicitud pendiente
        from registrations.services import reject_request
        reject_request(self.pending)
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, RegistrationRequest.Status.REJECTED)

    def test_reject_does_not_create_user(self) -> None:
        # Caso 14: rechazar no crea usuario
        from registrations.services import reject_request
        reject_request(self.pending)
        self.assertFalse(User.objects.filter(email="carlos@example.com").exists())

    def test_reject_sets_status_to_rejected(self) -> None:
        # Caso 15: solicitud queda en estado rechazada
        from registrations.services import reject_request
        reject_request(self.pending)
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, RegistrationRequest.Status.REJECTED)
