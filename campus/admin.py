from django.contrib import admin
from .models import CampusLocation
@admin.register(CampusLocation)
class CampusLocationAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "building",
        "qr_code",
        "is_active",
    ]
    list_filter = ["is_active", "building"]
    search_fields = ["name", "building", "qr_code"]