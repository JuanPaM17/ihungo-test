from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from users.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        ADMIN = "admin", "Administrador"
        ASSOCIATE = "associate", "Asociado"

    email = models.EmailField(unique=True)
    identification = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ASSOCIATE)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["identification", "first_name", "last_name"]

    def __str__(self) -> str:
        return self.email


class Asociado(models.Model):
    """Perfil extendido de un usuario con rol asociado."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="asociado_profile",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user.first_name} {self.user.last_name} ({self.user.email})"
