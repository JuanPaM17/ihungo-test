from django.contrib import admin, messages

from registrations.models import RegistrationRequest
from registrations.services import RegistrationServiceError, approve_request, reject_request


@admin.register(RegistrationRequest)
class RegistrationRequestAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "status", "requested_at")
    list_filter = ("status",)
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-requested_at",)
    actions = ["approve_selected", "reject_selected"]

    @admin.action(description="Aprobar solicitudes seleccionadas")
    def approve_selected(self, request, queryset):
        for registration in queryset:
            try:
                approve_request(registration)
                self.message_user(request, f"Solicitud de {registration.email} aprobada.", messages.SUCCESS)
            except RegistrationServiceError as exc:
                self.message_user(request, f"{registration.email}: {exc.message}", messages.ERROR)

    @admin.action(description="Rechazar solicitudes seleccionadas")
    def reject_selected(self, request, queryset):
        for registration in queryset:
            try:
                reject_request(registration)
                self.message_user(request, f"Solicitud de {registration.email} rechazada.", messages.SUCCESS)
            except RegistrationServiceError as exc:
                self.message_user(request, f"{registration.email}: {exc.message}", messages.ERROR)
