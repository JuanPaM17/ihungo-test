from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from registrations.models import RegistrationRequest
from registrations.serializers import RegistrationRequestSerializer
from users.models import User


class RegistrationRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = RegistrationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"].lower().strip()

        if User.objects.filter(email=email).exists():
            return Response(
                {"error": {"code": "USER_ALREADY_EXISTS", "message": "Ya existe un usuario registrado con este correo."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if RegistrationRequest.objects.filter(email=email, status=RegistrationRequest.Status.PENDING).exists():
            return Response(
                {"error": {"code": "REGISTRATION_ALREADY_PENDING", "message": "Ya existe una solicitud de registro pendiente para este correo."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save(email=email)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
