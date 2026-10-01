from django.db.models import Q
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from activities.permissions import IsAdmin
from users.models import Asociado
from users.serializers import AsociadoSerializer, AsociadoWriteSerializer
from users.services import AsociadoValidationError, create_asociado, delete_asociado, update_asociado

_WRITE_METHODS = ("POST", "PUT", "PATCH", "DELETE")


class AsociadoViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        if self.request.method in _WRITE_METHODS:
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method in _WRITE_METHODS:
            return AsociadoWriteSerializer
        return AsociadoSerializer

    def get_queryset(self):
        qs = Asociado.objects.select_related("user").all()
        params = self.request.query_params

        nombre = params.get("nombre")
        email = params.get("email")
        ciudad = params.get("ciudad")
        identificacion = params.get("identificacion")

        if nombre:
            partes = nombre.split()
            if len(partes) >= 2:
                qs = qs.filter(
                    Q(user__first_name__icontains=partes[0], user__last_name__icontains=partes[1])
                    | Q(user__first_name__icontains=partes[1], user__last_name__icontains=partes[0])
                    | Q(user__first_name__icontains=nombre)
                    | Q(user__last_name__icontains=nombre)
                )
            else:
                qs = qs.filter(
                    Q(user__first_name__icontains=nombre) | Q(user__last_name__icontains=nombre)
                )
        if email:
            qs = qs.filter(user__email__icontains=email)
        if ciudad:
            qs = qs.filter(user__city__icontains=ciudad)
        if identificacion:
            qs = qs.filter(user__identification__icontains=identificacion)

        return qs

    def create(self, request, *args, **kwargs):
        serializer = AsociadoWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        asociado = create_asociado(serializer.validated_data)
        return Response(AsociadoSerializer(asociado).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        asociado = self.get_object()
        serializer = AsociadoWriteSerializer(asociado, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        asociado = update_asociado(asociado, serializer.validated_data)
        return Response(AsociadoSerializer(asociado).data)

    def destroy(self, request, *args, **kwargs):
        asociado = self.get_object()
        try:
            delete_asociado(asociado)
        except AsociadoValidationError as e:
            return Response({"code": e.code, "detail": e.message}, status=status.HTTP_409_CONFLICT)
        return Response(status=status.HTTP_204_NO_CONTENT)
