from django.contrib import admin

from registrations.models import RegistrationRequest


@admin.register(RegistrationRequest)
class RegistrationRequestAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "status", "requested_at")
    list_filter = ("status",)
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-requested_at",)
