import csv
import io

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.models import Asociado, User

ASOCIADOS_URL = "/api/carga-masiva/asociados/"
ACTIVIDADES_URL = "/api/carga-masiva/actividades/"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_admin() -> User:
    return User.objects.create_user(
        email="admin@example.com",
        password="pass1234",
        identification="ADM001",
        first_name="Admin",
        last_name="User",
        city="Bogota",
        role=User.Role.ADMIN,
        is_staff=True,
    )


def make_associate(email: str, identification: str) -> tuple[User, Asociado]:
    user = User.objects.create_user(
        email=email,
        password="pass1234",
        identification=identification,
        first_name="Test",
        last_name="User",
        city="Bogota",
        role=User.Role.ASSOCIATE,
    )
    asociado = Asociado.objects.create(user=user)
    return user, asociado


def csv_file(rows: list[dict], fieldnames: list[str]) -> io.BytesIO:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return io.BytesIO(buf.getvalue().encode())


def xlsx_file(rows: list[dict], fieldnames: list[str]) -> io.BytesIO:
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(fieldnames)
    for row in rows:
        ws.append([row.get(f, "") for f in fieldnames])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


ASSOCIATE_FIELDS = ["identificacion", "nombre", "apellidos", "email", "ciudad"]
ACTIVITY_FIELDS = ["tipo_actividad", "descripcion", "fecha_inicio", "fecha_fin", "asociado_email"]


# ---------------------------------------------------------------------------
# Fase 7 — Carga masiva de asociados
# ---------------------------------------------------------------------------

class BulkUploadAsociadosTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.admin = make_admin()
        token = self.client.post(
            reverse("token_obtain_pair"),
            {"email": "admin@example.com", "password": "pass1234"},
            format="json",
        ).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        self.valid_row = {
            "identificacion": "123456",
            "nombre": "Juan",
            "apellidos": "Perez",
            "email": "juan@example.com",
            "ciudad": "Bogota",
        }

    def test_admin_can_upload_valid_csv(self) -> None:
        # Caso 1
        f = csv_file([self.valid_row], ASSOCIATE_FIELDS)
        response = self.client.post(ASOCIADOS_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["created"], 1)
        self.assertEqual(response.data["failed"], 0)

    def test_admin_can_upload_valid_xlsx(self) -> None:
        # Caso 2
        f = xlsx_file([self.valid_row], ASSOCIATE_FIELDS)
        f.name = "asociados.xlsx"
        response = self.client.post(ASOCIADOS_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["created"], 1)

    def test_multiple_valid_rows_created(self) -> None:
        # Caso 3
        rows = [
            {"identificacion": "111", "nombre": "A", "apellidos": "B", "email": "a@example.com", "ciudad": "X"},
            {"identificacion": "222", "nombre": "C", "apellidos": "D", "email": "c@example.com", "ciudad": "Y"},
        ]
        f = csv_file(rows, ASSOCIATE_FIELDS)
        response = self.client.post(ASOCIADOS_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["created"], 2)
        self.assertEqual(response.data["failed"], 0)

    def test_invalid_row_does_not_block_valid_rows(self) -> None:
        # Caso 4
        rows = [
            {"identificacion": "333", "nombre": "Valid", "apellidos": "User", "email": "valid@example.com", "ciudad": "Z"},
            {"identificacion": "444", "nombre": "", "apellidos": "User", "email": "invalid-email", "ciudad": "Z"},
        ]
        f = csv_file(rows, ASSOCIATE_FIELDS)
        response = self.client.post(ASOCIADOS_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["created"], 1)
        self.assertEqual(response.data["failed"], 1)

    def test_invalid_email_reported_per_row(self) -> None:
        # Caso 5
        row = {**self.valid_row, "email": "not-an-email"}
        f = csv_file([row], ASSOCIATE_FIELDS)
        response = self.client.post(ASOCIADOS_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["failed"], 1)
        self.assertEqual(response.data["errors"][0]["row"], 2)
        self.assertEqual(response.data["errors"][0]["code"], "INVALID_EMAIL")

    def test_duplicate_email_reported_per_row(self) -> None:
        # Caso 6
        User.objects.create_user(
            email="juan@example.com",
            password="pass",
            identification="999999",
            first_name="Juan",
            last_name="Perez",
            city="Bogota",
        )
        f = csv_file([self.valid_row], ASSOCIATE_FIELDS)
        response = self.client.post(ASOCIADOS_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["failed"], 1)
        self.assertEqual(response.data["errors"][0]["code"], "DUPLICATE_EMAIL")

    def test_duplicate_identification_reported_per_row(self) -> None:
        # Caso 7
        User.objects.create_user(
            email="other@example.com",
            password="pass",
            identification="123456",
            first_name="Other",
            last_name="User",
            city="Bogota",
        )
        f = csv_file([self.valid_row], ASSOCIATE_FIELDS)
        response = self.client.post(ASOCIADOS_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["failed"], 1)
        self.assertEqual(response.data["errors"][0]["code"], "DUPLICATE_IDENTIFICATION")

    def test_missing_required_columns_returns_400(self) -> None:
        # Caso 8
        f = csv_file([{"nombre": "Juan"}], ["nombre"])
        response = self.client.post(ASOCIADOS_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_format_returns_400(self) -> None:
        # Caso 9
        f = io.BytesIO(b"not a valid file")
        f.name = "file.txt"
        response = self.client.post(ASOCIADOS_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_associate_receives_403(self) -> None:
        # Caso 10
        _, _ = make_associate("assoc@example.com", "ASC001")
        token = self.client.post(
            reverse("token_obtain_pair"),
            {"email": "assoc@example.com", "password": "pass1234"},
            format="json",
        ).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        f = csv_file([self.valid_row], ASSOCIATE_FIELDS)
        response = self.client.post(ASOCIADOS_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_receives_401(self) -> None:
        # Caso 11
        self.client.credentials()
        f = csv_file([self.valid_row], ASSOCIATE_FIELDS)
        response = self.client.post(ASOCIADOS_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Fase 7 — Carga masiva de actividades
# ---------------------------------------------------------------------------

class BulkUploadActividadesTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.admin = make_admin()
        token = self.client.post(
            reverse("token_obtain_pair"),
            {"email": "admin@example.com", "password": "pass1234"},
            format="json",
        ).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        _, self.asociado = make_associate("assoc@example.com", "ASC001")

        self.valid_row = {
            "tipo_actividad": "workshop",
            "descripcion": "Taller",
            "fecha_inicio": "2027-01-01T09:00:00Z",
            "fecha_fin": "2027-01-01T11:00:00Z",
            "asociado_email": "assoc@example.com",
        }

    def test_admin_can_upload_valid_csv(self) -> None:
        # Caso 12
        f = csv_file([self.valid_row], ACTIVITY_FIELDS)
        response = self.client.post(ACTIVIDADES_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["created"], 1)
        self.assertEqual(response.data["failed"], 0)

    def test_admin_can_upload_valid_xlsx(self) -> None:
        # Caso 13
        f = xlsx_file([self.valid_row], ACTIVITY_FIELDS)
        f.name = "actividades.xlsx"
        response = self.client.post(ACTIVIDADES_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["created"], 1)

    def test_creator_is_request_user(self) -> None:
        # Caso 14
        from activities.models import Activity
        f = csv_file([self.valid_row], ACTIVITY_FIELDS)
        self.client.post(ACTIVIDADES_URL, {"file": f}, format="multipart")
        activity = Activity.objects.first()
        self.assertEqual(activity.creator, self.admin)

    def test_nonexistent_asociado_reported_per_row(self) -> None:
        # Caso 15
        row = {**self.valid_row, "asociado_email": "noexiste@example.com"}
        f = csv_file([row], ACTIVITY_FIELDS)
        response = self.client.post(ACTIVIDADES_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["failed"], 1)
        self.assertEqual(response.data["errors"][0]["code"], "ASOCIADO_NOT_FOUND")

    def test_invalid_date_range_reported_per_row(self) -> None:
        # Caso 16
        row = {**self.valid_row, "fecha_fin": "2027-01-01T08:00:00Z"}
        f = csv_file([row], ACTIVITY_FIELDS)
        response = self.client.post(ACTIVIDADES_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["failed"], 1)
        self.assertEqual(response.data["errors"][0]["code"], "INVALID_DATE_RANGE")

    def test_overlap_reported_per_row(self) -> None:
        # Caso 17
        from activities.models import Activity
        Activity.objects.create(
            activity_type="workshop",
            start_datetime="2027-01-01T09:00:00Z",
            end_datetime="2027-01-01T11:00:00Z",
            asociado=self.asociado,
            creator=self.admin,
        )
        f = csv_file([self.valid_row], ACTIVITY_FIELDS)
        response = self.client.post(ACTIVIDADES_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["failed"], 1)
        self.assertEqual(response.data["errors"][0]["code"], "ACTIVITY_OVERLAP")

    def test_invalid_row_does_not_block_valid_rows(self) -> None:
        # Caso 18
        rows = [
            self.valid_row,
            {**self.valid_row, "fecha_fin": "2027-01-01T08:00:00Z", "fecha_inicio": "2027-01-01T09:00:00Z"},
        ]
        f = csv_file(rows, ACTIVITY_FIELDS)
        response = self.client.post(ACTIVIDADES_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["created"], 1)
        self.assertEqual(response.data["failed"], 1)

    def test_multiple_valid_activities_created(self) -> None:
        # Caso 19
        rows = [
            {**self.valid_row, "fecha_inicio": "2027-02-01T09:00:00Z", "fecha_fin": "2027-02-01T11:00:00Z"},
            {**self.valid_row, "fecha_inicio": "2027-03-01T09:00:00Z", "fecha_fin": "2027-03-01T11:00:00Z"},
        ]
        f = csv_file(rows, ACTIVITY_FIELDS)
        response = self.client.post(ACTIVIDADES_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["created"], 2)
        self.assertEqual(response.data["failed"], 0)

    def test_associate_receives_403(self) -> None:
        # Caso 20
        token = self.client.post(
            reverse("token_obtain_pair"),
            {"email": "assoc@example.com", "password": "pass1234"},
            format="json",
        ).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        f = csv_file([self.valid_row], ACTIVITY_FIELDS)
        response = self.client.post(ACTIVIDADES_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_receives_401(self) -> None:
        # Caso 21
        self.client.credentials()
        f = csv_file([self.valid_row], ACTIVITY_FIELDS)
        response = self.client.post(ACTIVIDADES_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
