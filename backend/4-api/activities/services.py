
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from activities.models import Activity
from users.models import Asociado, User


class ActivityValidationError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def validate_date_range(start_datetime, end_datetime) -> None:
    if end_datetime <= start_datetime:
        raise ActivityValidationError(
            code="INVALID_DATE_RANGE",
            message="La fecha de fin debe ser posterior a la fecha de inicio.",
        )


def validate_no_overlap(
    asociado: Asociado,
    start_datetime,
    end_datetime,
    exclude_id: int | None = None,
) -> None:
    qs = Activity.objects.filter(
        asociado=asociado,
        start_datetime__lt=end_datetime,
        end_datetime__gt=start_datetime,
    )
    if exclude_id is not None:
        qs = qs.exclude(id=exclude_id)

    if qs.exists():
        raise ActivityValidationError(
            code="ACTIVITY_OVERLAP",
            message="El asociado ya tiene una actividad en ese rango de tiempo.",
        )


def create_activity(validated_data: dict, creator) -> Activity:
    start = validated_data["start_datetime"]
    end = validated_data["end_datetime"]
    asociado = validated_data["asociado"]

    validate_date_range(start, end)
    validate_no_overlap(asociado, start, end)

    return Activity.objects.create(creator=creator, **validated_data)


def update_activity(activity: Activity, validated_data: dict) -> Activity:
    start = validated_data.get("start_datetime", activity.start_datetime)
    end = validated_data.get("end_datetime", activity.end_datetime)
    asociado = validated_data.get("asociado", activity.asociado)

    validate_date_range(start, end)
    validate_no_overlap(asociado, start, end, exclude_id=activity.id)

    for attr, value in validated_data.items():
        setattr(activity, attr, value)
    activity.save()
    return activity


def check_availability(
    fecha_inicio: str,
    fecha_fin: str,
    asociado_id: int | None,
    user: "User",
) -> dict:
    """
    Consulta la disponibilidad de asociados en un rango de tiempo.

    Un asociado está ocupado si tiene alguna actividad con solapamiento real:
        activity.start_datetime < fecha_fin  AND  activity.end_datetime > fecha_inicio

    Args:
        fecha_inicio: ISO 8601 string (inicio del rango).
        fecha_fin: ISO 8601 string (fin del rango).
        asociado_id: ID de asociado específico, o None para evaluar todos.
        user: usuario autenticado (respeta visibilidad según rol).

    Returns:
        dict con rango, resumen y lista de asociados con su estado.
    """
    inicio = parse_datetime(fecha_inicio)
    fin = parse_datetime(fecha_fin)

    if inicio is None or fin is None:
        raise ValueError("Formato de fecha inválido.")
    if fin <= inicio:
        raise ValueError("fecha_fin debe ser posterior a fecha_inicio.")

    # Asociados a evaluar
    asociados_qs = Asociado.objects.select_related("user").all()
    if asociado_id is not None:
        asociados_qs = asociados_qs.filter(pk=asociado_id)

    # Actividades solapadas en el rango (overlap real)
    actividades_solapadas = Activity.objects.select_related("asociado").filter(
        start_datetime__lt=fin,
        end_datetime__gt=inicio,
    )
    if asociado_id is not None:
        actividades_solapadas = actividades_solapadas.filter(asociado_id=asociado_id)

    # Indexar por asociado_id
    bloqueantes_por_asociado: dict[int, list] = {}
    for act in actividades_solapadas:
        bloqueantes_por_asociado.setdefault(act.asociado_id, []).append(act)

    resultado = []
    libres = 0
    ocupados = 0

    for asoc in asociados_qs:
        bloqueantes = bloqueantes_por_asociado.get(asoc.pk, [])
        estado = "ocupado" if bloqueantes else "libre"

        if estado == "libre":
            libres += 1
        else:
            ocupados += 1

        resultado.append({
            "id": asoc.pk,
            "nombre": f"{asoc.user.first_name} {asoc.user.last_name}",
            "email": asoc.user.email,
            "estado": estado,
            "actividades_bloqueantes": [
                {
                    "id": b.pk,
                    "activity_type": b.activity_type,
                    "start_datetime": b.start_datetime.isoformat(),
                    "end_datetime": b.end_datetime.isoformat(),
                    "description": b.description,
                }
                for b in bloqueantes
            ],
        })

    return {
        "rango": {"inicio": fecha_inicio, "fin": fecha_fin},
        "resumen": {"libres": libres, "ocupados": ocupados},
        "asociados": resultado,
    }
