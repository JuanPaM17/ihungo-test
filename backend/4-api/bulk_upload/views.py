from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from bulk_upload.parsers import parse_file
from bulk_upload.services import bulk_upload_actividades, bulk_upload_asociados
from users.models import User


class IsAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.role == User.Role.ADMIN


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
