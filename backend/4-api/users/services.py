from django.db import transaction
from django.db.models import ProtectedError

from users.models import Asociado, User


class AsociadoValidationError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


@transaction.atomic
def create_asociado(validated_data: dict) -> Asociado:
    password = validated_data.pop("password")
    user = User.objects.create_user(
        role=User.Role.ASSOCIATE,
        **validated_data,
        password=password,
    )
    return Asociado.objects.create(user=user)


@transaction.atomic
def update_asociado(asociado: Asociado, validated_data: dict) -> Asociado:
    user = asociado.user
    for field in ("email", "identification", "first_name", "last_name", "city"):
        if field in validated_data:
            setattr(user, field, validated_data[field])
    if "password" in validated_data:
        user.set_password(validated_data["password"])
    user.save()
    return asociado


@transaction.atomic
def delete_asociado(asociado: Asociado) -> None:
    try:
        user = asociado.user
        asociado.delete()
        user.delete()
    except ProtectedError:
        raise AsociadoValidationError(
            code="HAS_ACTIVITIES",
            message=(
                "No se puede eliminar el asociado porque tiene actividades asociadas. "
                "Elimina primero las actividades."
            ),
        )
