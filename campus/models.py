from django.conf import settings
from django.db import models
class CampusLocation(models.Model):
    name = models.CharField(max_length=150)
    building = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    qr_code = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_locations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.name} — {self.building}"
