import secrets

from registrations.models import RegistrationRequest
from users.models import Asociado, User


class RegistrationServiceError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def approve_request(request: RegistrationRequest) -> User:
    if request.status != RegistrationRequest.Status.PENDING:
        raise RegistrationServiceError(
            code="REGISTRATION_NOT_PENDING",
            message="Solo se pueden aprobar solicitudes en estado pendiente.",
        )

    user, created = User.objects.get_or_create(
        email=request.email,
        defaults={
            "first_name": request.first_name,
            "last_name": request.last_name,
            "identification": f"REG-{request.id}",
            "city": "",
            "role": User.Role.ASSOCIATE,
        },
    )

    if created:
        user.set_password(secrets.token_urlsafe(12))
        user.save()

    if not hasattr(user, "asociado_profile"):
        Asociado.objects.create(user=user)

    request.status = RegistrationRequest.Status.APPROVED
    request.save()

    return user


def reject_request(request: RegistrationRequest) -> None:
    if request.status != RegistrationRequest.Status.PENDING:
        raise RegistrationServiceError(
            code="REGISTRATION_NOT_PENDING",
            message="Solo se pueden rechazar solicitudes en estado pendiente.",
        )

    request.status = RegistrationRequest.Status.REJECTED
    request.save()
