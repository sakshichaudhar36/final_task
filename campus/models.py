from django.conf import settings
from django.db import models
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    def __str__(self):
        return self.name

class CampusLocation(models.Model):
    name = models.CharField(max_length=150)
    building = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    qr_code = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

# Create your models here.
