
from activities.models import Activity
from users.models import Asociado


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
