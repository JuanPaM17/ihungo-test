from django.contrib import admin

from activities.models import Activity


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("activity_type", "asociado", "creator", "start_datetime", "end_datetime")
    list_filter = ("activity_type",)
    search_fields = ("asociado__user__email", "creator__email", "description")
    ordering = ("-start_datetime",)
