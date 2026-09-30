from django.db.models import Q
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from users.models import Asociado
from users.serializers import AsociadoSerializer


class AsociadoViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = AsociadoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Asociado.objects.select_related("user").all()
        params = self.request.query_params

        nombre = params.get("nombre")
        email = params.get("email")
        ciudad = params.get("ciudad")
        identificacion = params.get("identificacion")

        if nombre:
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
