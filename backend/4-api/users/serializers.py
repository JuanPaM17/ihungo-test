from rest_framework import serializers

from users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "identification", "first_name", "last_name", "city", "role")
        read_only_fields = ("id",)
