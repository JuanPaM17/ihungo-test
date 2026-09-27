from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from users.models import Asociado, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "first_name", "last_name", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("email", "identification", "first_name", "last_name")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Información personal", {"fields": ("identification", "first_name", "last_name", "city")}),
        ("Rol y permisos", {"fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "identification", "first_name", "last_name", "city", "role", "password1", "password2"),
        }),
    )


@admin.register(Asociado)
class AsociadoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "user", "created_at")
    search_fields = ("user__email", "user__first_name", "user__last_name")
    ordering = ("user__last_name",)
