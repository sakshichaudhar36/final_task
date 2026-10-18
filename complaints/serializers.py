from django.contrib.auth import get_user_model
from rest_framework import serializers
from campus.models import CampusLocation
from .models import Complaint, ComplaintHistory, Evidence
User = get_user_model()
class ComplaintSerializer(serializers.ModelSerializer):
    reporter_username = serializers.CharField(
        source="reporter.username",
        read_only=True,
    )
    assigned_staff_username = serializers.CharField(
        source="assigned_staff.username",
        read_only=True,
        default=None,
    )
    class Meta:
        model = Complaint
        fields = [
            "id",
            "title",
            "description",
            "category",
            "location",
            "reporter",
            "reporter_username",
            "assigned_staff",
            "assigned_staff_username",
            "priority",
            "status",
            "is_public",
            "created_at",
            "updated_at",
            "resolved_at",
            "verified_at",
        ]
        read_only_fields = [
            "id",
            "reporter",
            "assigned_staff",
            "status",
            "is_public",
            "created_at",
            "updated_at",
            "resolved_at",
            "verified_at",
        ]
class AssignmentSerializer(serializers.Serializer):
    staff_id = serializers.IntegerField()
    def validate_staff_id(self, value):
        if not User.objects.filter(
            pk=value,
            role=User.Role.STAFF,
            is_active=True,
        ).exists():
            raise serializers.ValidationError(
                "Select an active staff account."
            )
        return value
class StatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Complaint.Status.choices)
    reason = serializers.CharField(required=False, allow_blank=True)
class VerificationSerializer(serializers.Serializer):
    approved = serializers.BooleanField()
    reason = serializers.CharField(required=False, allow_blank=True)
    def validate(self, attrs):
        if not attrs["approved"] and not attrs.get("reason", "").strip():
            raise serializers.ValidationError({
                "reason": "Provide a reason when rejecting resolution."
            })
        return attrs
class ReopenSerializer(serializers.Serializer):
    reason = serializers.CharField()
class EvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evidence
        fields = ["id", "file", "description", "uploaded_by", "created_at"]
        read_only_fields = ["id", "uploaded_by", "created_at"]
class ComplaintHistorySerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(
        source="actor.username",
        read_only=True,
        default=None,
    )
    class Meta:
        model = ComplaintHistory
        fields = [
            "id",
            "action",
            "previous_status",
            "new_status",
            "reason",
            "actor_username",
            "created_at",
        ]
class PublicComplaintSerializer(serializers.ModelSerializer):
    location_name = serializers.CharField(
        source="location.name",
        read_only=True,
    )
    class Meta:
        model = Complaint
        fields = [
            "id",
            "title",
            "category",
            "location_name",
            "status",
            "created_at",
            "updated_at",
        ]