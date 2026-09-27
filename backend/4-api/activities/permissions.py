from django.utils import timezone
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from activities.models import Activity
from users.models import User


class IsAdmin(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Role.ADMIN)


class ActivityPermission(BasePermission):
    """
    - Admin: acceso total.
    - Asociado: puede modificar/eliminar solo actividades presentes/futuras donde está relacionado.
    - Otros: solo lectura de sus propias actividades.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view: APIView, obj: Activity) -> bool:
        user: User = request.user

        if user.role == User.Role.ADMIN:
            return True

        # Solo lectura no requiere validación adicional de objeto
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True

        # El creador siempre puede modificar sus propias actividades
        if obj.creator == user:
            return True

        # Verificar que el asociado esté relacionado con la actividad
        try:
            asociado = user.asociado_profile
        except Exception:
            return False

        if obj.asociado != asociado:
            return False

        # Actividades pasadas son de solo lectura para asociados
        if obj.start_datetime < timezone.now():
            return False

        return True
