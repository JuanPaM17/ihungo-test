from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.serializers import BaseSerializer

from activities.filters import filter_by_date_range
from activities.models import Activity
from activities.serializers import ActivityReadSerializer, ActivityWriteSerializer


class ActivityViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        queryset = Activity.objects.select_related("asociado__user", "creator").all()
        return filter_by_date_range(
            queryset,
            desde=self.request.query_params.get("desde"),
            hasta=self.request.query_params.get("hasta"),
        )

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return ActivityWriteSerializer
        return ActivityReadSerializer
