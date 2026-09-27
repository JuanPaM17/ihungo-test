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
