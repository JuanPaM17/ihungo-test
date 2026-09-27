from rest_framework import serializers

from activities.models import Activity
from activities.services import ActivityValidationError, create_activity, update_activity
from users.serializers import AsociadoSerializer, UserSerializer


class ActivityReadSerializer(serializers.ModelSerializer):
    asociado = AsociadoSerializer(read_only=True)
    creator = UserSerializer(read_only=True)

    class Meta:
        model = Activity
        fields = (
            "id",
            "activity_type",
            "description",
            "start_datetime",
            "end_datetime",
            "asociado",
            "creator",
            "created_at",
            "updated_at",
        )


class ActivityWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = (
            "id",
            "activity_type",
            "description",
            "start_datetime",
            "end_datetime",
            "asociado",
        )
        read_only_fields = ("id",)

    def create(self, validated_data: dict) -> Activity:
        try:
            return create_activity(validated_data, creator=self.context["request"].user)
        except ActivityValidationError:
            raise

    def update(self, instance: Activity, validated_data: dict) -> Activity:
        try:
            return update_activity(instance, validated_data)
        except ActivityValidationError:
            raise
