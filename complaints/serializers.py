from rest_framework import serializers

from .models import Complaint, ComplaintHistory, Evidence


class ComplaintSerializer(serializers.ModelSerializer):
    reporter_username = serializers.CharField(
        source="reporter.username",
        read_only=True,
    )

    location_name = serializers.CharField(
        source="location.name",
        read_only=True,
    )

    class Meta:
        model = Complaint
        fields = [
            "id",
            "title",
            "description",
            "reporter",
            "reporter_username",
            "location",
            "location_name",
            "category",
            "suggested_category",
            "priority",
            "status",
            "assigned_staff",
            "is_public",
            "resolution_verified",
            "resolution_note",
            "created_at",
            "updated_at",
            "closed_at",
        ]

        read_only_fields = [
            "id",
            "reporter",
            "reporter_username",
            "location_name",
            "suggested_category",
            "priority",
            "status",
            "assigned_staff",
            "is_public",
            "resolution_verified",
            "resolution_note",
            "created_at",
            "updated_at",
            "closed_at",
        ]


class ComplaintHistorySerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(
        source="actor.username",
        read_only=True,
    )

    class Meta:
        model = ComplaintHistory
        fields = [
            "id",
            "actor_username",
            "old_status",
            "new_status",
            "reason",
            "created_at",
        ]


class EvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evidence
        fields = [
            "id",
            "description",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]