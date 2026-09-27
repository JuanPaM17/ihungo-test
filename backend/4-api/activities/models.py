from django.conf import settings
from django.db import models

from users.models import Asociado


class Activity(models.Model):
    class Type(models.TextChoices):
        WORKSHOP = "workshop", "Taller"
        SEMINAR = "seminar", "Seminario"
        MEETING = "meeting", "Reunión"
        TRAINING = "training", "Capacitación"
        OTHER = "other", "Otro"

    activity_type = models.CharField(max_length=20, choices=Type.choices)
    description = models.TextField(blank=True, default="")
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()

    asociado = models.ForeignKey(
        Asociado,
        on_delete=models.PROTECT,
        related_name="activities",
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_activities",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.get_activity_type_display()} — {self.asociado} ({self.start_datetime:%Y-%m-%d})"
