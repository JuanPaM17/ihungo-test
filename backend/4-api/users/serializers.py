from rest_framework import serializers

from users.models import Asociado, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "identification", "first_name", "last_name", "city", "role")
        read_only_fields = ("id",)


class AsociadoSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    city = serializers.CharField(source="user.city", read_only=True)
    identification = serializers.CharField(source="user.identification", read_only=True)

    class Meta:
        model = Asociado
        fields = ("id", "user", "email", "identification", "first_name", "last_name", "city", "created_at")
        read_only_fields = ("id", "created_at")


class AsociadoWriteSerializer(serializers.Serializer):
    """Serializer para crear y actualizar un Asociado junto con su User."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, required=False)
    identification = serializers.CharField(max_length=30)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    city = serializers.CharField(max_length=100)

    def validate_email(self, value: str) -> str:
        qs = User.objects.filter(email=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.user.pk)
        if qs.exists():
            raise serializers.ValidationError("Ya existe un usuario con ese email.")
        return value

    def validate_identification(self, value: str) -> str:
        qs = User.objects.filter(identification=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.user.pk)
        if qs.exists():
            raise serializers.ValidationError("Ya existe un usuario con esa identificación.")
        return value
