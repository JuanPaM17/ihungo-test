from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiResponse
from rest_framework import serializers, status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User

from bulk_upload.parsers import parse_file
from bulk_upload.services import bulk_upload_asociados, bulk_upload_actividades


class IsAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.role == User.Role.ADMIN


_bulk_request = inline_serializer("BulkUploadRequest", {"file": serializers.FileField()})
_bulk_response = inline_serializer(
    "BulkUploadResponse",
    {
        "created": serializers.IntegerField(),
        "failed": serializers.IntegerField(),
        "errors": serializers.ListField(child=serializers.DictField()),
    },
)


@extend_schema(
    tags=["carga-masiva"],
    summary="Carga masiva de asociados",
    description=(
        "Crea asociados en lote desde un archivo CSV o XLSX. "
        "Columnas requeridas: identificacion, nombre, apellidos, email, ciudad. "
        "Las filas inválidas se reportan sin bloquear las válidas."
    ),
    request={"multipart/form-data": _bulk_request},
    responses={
        200: _bulk_response,
        400: OpenApiResponse(description="Formato no soportado o columnas faltantes"),
        401: OpenApiResponse(description="No autenticado"),
        403: OpenApiResponse(description="Se requiere rol administrador"),
    },
)
class BulkUploadAsociadosView(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [IsAdmin]

    def post(self, request: Request) -> Response:
        file = request.FILES.get("file")
        if file is None:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            fieldnames, rows = parse_file(file)
        except Exception:
            return Response({"error": "Unsupported file format"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = bulk_upload_asociados(rows, fieldnames)
        except ValueError:
            return Response({"error": "Missing required columns"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)


@extend_schema(
    tags=["carga-masiva"],
    summary="Carga masiva de actividades",
    description=(
        "Crea actividades en lote desde un archivo CSV o XLSX. "
        "Columnas requeridas: tipo_actividad, descripcion, fecha_inicio, fecha_fin, asociado_email. "
        "El creador queda registrado como el usuario autenticado. "
        "Las filas inválidas se reportan sin bloquear las válidas."
    ),
    request={"multipart/form-data": _bulk_request},
    responses={
        200: _bulk_response,
        400: OpenApiResponse(description="Formato no soportado o columnas faltantes"),
        401: OpenApiResponse(description="No autenticado"),
        403: OpenApiResponse(description="Se requiere rol administrador"),
    },
)
class BulkUploadActividadesView(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [IsAdmin]

    def post(self, request: Request) -> Response:
        file = request.FILES.get("file")
        if file is None:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            fieldnames, rows = parse_file(file)
        except Exception:
            return Response({"error": "Unsupported file format"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = bulk_upload_actividades(rows, fieldnames, creator=request.user)
        except ValueError:
            return Response({"error": "Missing required columns"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)
