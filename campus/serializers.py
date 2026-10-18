from rest_framework import serializers
from .models import CampusLocation
class CampusLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampusLocation
        fields = [
            "id",
            "name",
            "building",
            "description",
            "qr_code",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]