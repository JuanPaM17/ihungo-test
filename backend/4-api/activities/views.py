from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from activities.filters import filter_by_date_range
from activities.models import Activity
from activities.permissions import ActivityPermission
from activities.serializers import ActivityReadSerializer, ActivityWriteSerializer
from activities.services import ActivityValidationError, check_availability
from users.models import User


class ActivityViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [ActivityPermission]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        user: User = self.request.user
        queryset = Activity.objects.select_related("asociado__user", "creator").all()

        # Para detalle (retrieve, update, delete) devolvemos todo para que
        # has_object_permission pueda evaluar y responder 403 en lugar de 404.
        if self.action not in ("list",):
            return queryset

        if user.role != User.Role.ADMIN:
            try:
                asociado = user.asociado_profile
                queryset = queryset.filter(
                    asociado=asociado
                ) | queryset.filter(creator=user)
                queryset = queryset.distinct()
            except Exception:
                queryset = queryset.filter(creator=user)

        return filter_by_date_range(
            queryset,
            desde=self.request.query_params.get("desde"),
            hasta=self.request.query_params.get("hasta"),
        )

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return ActivityWriteSerializer
        return ActivityReadSerializer

    def _error_response(self, code: str, message: str, http_status: int) -> Response:
        return Response(
            {"error": {"code": code, "message": message}},
            status=http_status,
        )

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
        except ActivityValidationError as exc:
            if exc.code == "ACTIVITY_OVERLAP":
                return self._error_response(exc.code, exc.message, status.HTTP_409_CONFLICT)
            return self._error_response(exc.code, exc.message, status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
        except ActivityValidationError as exc:
            if exc.code == "ACTIVITY_OVERLAP":
                return self._error_response(exc.code, exc.message, status.HTTP_409_CONFLICT)
            return self._error_response(exc.code, exc.message, status.HTTP_400_BAD_REQUEST)
        return Response(ActivityReadSerializer(instance, context={"request": request}).data)

    @action(detail=False, methods=["get"], url_path="disponibilidad")
    def disponibilidad(self, request: Request) -> Response:
        """
        Consulta la disponibilidad de asociados en un rango de tiempo.

        Query params:
          - fecha_inicio (requerido): ISO 8601. Ejemplo: 2025-03-15T09:00:00Z
          - fecha_fin    (requerido): ISO 8601. Ejemplo: 2025-03-15T11:00:00Z
          - asociado_id  (opcional): ID numérico del asociado específico.

        Respuesta:
          {
            "rango": { "inicio": ..., "fin": ... },
            "resumen": { "libres": N, "ocupados": N },
            "asociados": [
              {
                "id": 1,
                "nombre": "Juan Pérez",
                "email": "juan@example.com",
                "estado": "libre" | "ocupado",
                "actividades_bloqueantes": [ { id, activity_type, start_datetime, end_datetime, description } ]
              }
            ]
          }
        """
        fecha_inicio = request.query_params.get("fecha_inicio")
        fecha_fin = request.query_params.get("fecha_fin")

        if not fecha_inicio or not fecha_fin:
            return Response(
                {"error": {"code": "MISSING_PARAMS", "message": "fecha_inicio y fecha_fin son requeridos."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        asociado_id = request.query_params.get("asociado_id")

        try:
            result = check_availability(
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                asociado_id=int(asociado_id) if asociado_id else None,
                user=request.user,
            )
        except (ValueError, TypeError):
            return Response(
                {"error": {"code": "INVALID_PARAMS", "message": "Parámetros inválidos."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result)
