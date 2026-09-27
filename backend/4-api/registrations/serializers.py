from rest_framework import serializers

from registrations.models import RegistrationRequest


class RegistrationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistrationRequest
        fields = ("id", "first_name", "last_name", "email", "status", "requested_at")
        read_only_fields = ("id", "status", "requested_at")
