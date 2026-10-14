from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("CampusPulse Details", {
            "fields": ("role", "email_verified"),
        }),
    )

    list_display = (
        "username",
        "email",
        "role",
        "email_verified",
        "is_active",
    )

# Register your models here.
