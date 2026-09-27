from rest_framework import serializers

from activities.models import Activity
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
        creator = self.context["request"].user
        return Activity.objects.create(creator=creator, **validated_data)
