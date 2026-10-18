from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
@admin.register(User)
class CampusPulseUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "role",
        "email_verified",
        "is_active",
        "is_staff",
    )
    list_filter = (
        "role",
        "email_verified",
        "is_active",
        "is_staff",
    )
    fieldsets = UserAdmin.fieldsets + (
        (
            "CampusPulse information",
            {"fields": ("role", "email_verified")},
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "CampusPulse information",
            {"fields": ("email", "role", "email_verified")},
        ),
    )