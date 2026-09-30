from rest_framework import serializers

from activities.models import Activity
from activities.services import ActivityValidationError, create_activity, update_activity
from users.models import Asociado, User
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
    asociado = serializers.PrimaryKeyRelatedField(
        queryset=Asociado.objects.all(),
        required=False,
        allow_null=True,
    )

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

    def validate(self, attrs):
        # On PATCH (partial=True), asociado is not required — it keeps the existing value.
        if self.partial:
            return attrs

        user: User = self.context["request"].user
        if "asociado" not in attrs or attrs.get("asociado") is None:
            if user.role == User.Role.ADMIN:
                raise serializers.ValidationError(
                    {"asociado": "Este campo es requerido para administradores."}
                )
            try:
                attrs["asociado"] = user.asociado_profile
            except Exception:
                raise serializers.ValidationError(
                    {"asociado": "No se encontró el perfil de asociado para este usuario."}
                )
        return attrs

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
