from rest_framework import serializers
from .models import CampusLocation, Department
class CampusLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampusLocation
        fields = ["id", "name", "building", "description", "qr_code"]
class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "description"]