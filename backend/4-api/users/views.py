from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from users.models import Asociado
from users.serializers import AsociadoSerializer


class AsociadoViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Asociado.objects.select_related("user").all()
    serializer_class = AsociadoSerializer
    permission_classes = [IsAuthenticated]
