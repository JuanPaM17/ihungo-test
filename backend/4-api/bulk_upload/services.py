from __future__ import annotations

from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string

from activities.services import ActivityValidationError, validate_date_range, validate_no_overlap
from activities.models import Activity
from users.models import Asociado, User


ASSOCIATE_REQUIRED = {"identificacion", "nombre", "apellidos", "email", "ciudad"}
ACTIVITY_REQUIRED = {"tipo_actividad", "descripcion", "fecha_inicio", "fecha_fin", "asociado_email"}


# ---------------------------------------------------------------------------
# Bulk upload de asociados
# ---------------------------------------------------------------------------

def bulk_upload_asociados(rows, fieldnames: list[str]) -> dict:
    if not ASSOCIATE_REQUIRED.issubset(set(fieldnames)):
        raise ValueError("Missing required columns")

    created = 0
    failed = 0
    errors = []

    for idx, row in enumerate(rows, start=2):
        email = (row.get("email") or "").strip().lower()
        identificacion = (row.get("identificacion") or "").strip()
        nombre = (row.get("nombre") or "").strip()
        apellidos = (row.get("apellidos") or "").strip()
        ciudad = (row.get("ciudad") or "").strip()

        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            failed += 1
            errors.append({"row": idx, "code": "INVALID_EMAIL", "detail": f"Email inválido: {email}"})
            continue

        if not nombre:
            failed += 1
            errors.append({"row": idx, "code": "INVALID_DATA", "detail": "El nombre es requerido"})
            continue

        # Duplicate email
        if User.objects.filter(email=email).exists():
            failed += 1
            errors.append({"row": idx, "code": "DUPLICATE_EMAIL", "detail": f"Email duplicado: {email}"})
            continue

        # Duplicate identification
        if User.objects.filter(identification=identificacion).exists():
            failed += 1
            errors.append({"row": idx, "code": "DUPLICATE_IDENTIFICATION", "detail": f"Identificación duplicada: {identificacion}"})
            continue

        user = User.objects.create_user(
            email=email,
            password=get_random_string(20),
            identification=identificacion,
            first_name=nombre,
            last_name=apellidos,
            city=ciudad,
            role=User.Role.ASSOCIATE,
        )
        Asociado.objects.create(user=user)
        created += 1

    return {"created": created, "failed": failed, "errors": errors}


# ---------------------------------------------------------------------------
# Bulk upload de actividades
# ---------------------------------------------------------------------------

_ACTIVITY_TYPE_MAP = {
    "workshop": Activity.Type.WORKSHOP,
    "seminar": Activity.Type.SEMINAR,
    "meeting": Activity.Type.MEETING,
    "training": Activity.Type.TRAINING,
    "other": Activity.Type.OTHER,
}


def bulk_upload_actividades(rows, fieldnames: list[str], creator) -> dict:
    if not ACTIVITY_REQUIRED.issubset(set(fieldnames)):
        raise ValueError("Missing required columns")

    from django.utils.dateparse import parse_datetime

    created = 0
    failed = 0
    errors = []

    for idx, row in enumerate(rows, start=2):
        asociado_email = (row.get("asociado_email") or "").strip().lower()
        tipo = (row.get("tipo_actividad") or "").strip().lower()
        descripcion = (row.get("descripcion") or "").strip()
        fecha_inicio_str = (row.get("fecha_inicio") or "").strip()
        fecha_fin_str = (row.get("fecha_fin") or "").strip()

        # Resolve asociado
        try:
            user = User.objects.get(email=asociado_email)
            asociado = user.asociado_profile
        except (User.DoesNotExist, Asociado.DoesNotExist):
            failed += 1
            errors.append({"row": idx, "code": "ASOCIADO_NOT_FOUND", "detail": f"Asociado no encontrado: {asociado_email}"})
            continue

        # Parse dates
        start = parse_datetime(fecha_inicio_str)
        end = parse_datetime(fecha_fin_str)
        if start is None or end is None:
            failed += 1
            errors.append({"row": idx, "code": "INVALID_DATE", "detail": "Fecha inválida"})
            continue

        # Make aware if needed
        from django.utils import timezone as tz
        if tz.is_naive(start):
            start = tz.make_aware(start)
        if tz.is_naive(end):
            end = tz.make_aware(end)

        try:
            validate_date_range(start, end)
            validate_no_overlap(asociado, start, end)
        except ActivityValidationError as exc:
            failed += 1
            errors.append({"row": idx, "code": exc.code, "detail": exc.message})
            continue

        activity_type = _ACTIVITY_TYPE_MAP.get(tipo, tipo)
        Activity.objects.create(
            activity_type=activity_type,
            description=descripcion,
            start_datetime=start,
            end_datetime=end,
            asociado=asociado,
            creator=creator,
        )
        created += 1

    return {"created": created, "failed": failed, "errors": errors}
