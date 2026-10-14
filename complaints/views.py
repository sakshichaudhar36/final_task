from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import Complaint, ComplaintHistory, Evidence
from .serializers import (
    ComplaintSerializer,
    ComplaintHistorySerializer,
    EvidenceSerializer,
)
from .permissions import IsManagement, ComplaintObjectPermission
from campus.models import CampusLocation


class ComplaintViewSet(viewsets.ModelViewSet):
    serializer_class = ComplaintSerializer
    permission_classes = [IsAuthenticated, ComplaintObjectPermission]

    def get_queryset(self):
        user = self.request.user

        if user.role == "management":
            return Complaint.objects.select_related(
                "reporter", "assigned_staff", "location"
            ).all()

        if user.role == "staff":
            return Complaint.objects.filter(
                assigned_staff=user
            ).select_related("reporter", "location")

        return Complaint.objects.filter(
            reporter=user
        ).select_related("location")

    def perform_create(self, serializer):
        user = self.request.user

        if user.role != "student":
            raise PermissionDenied(
                "Only students can submit complaints in this workflow."
            )

        if not user.email_verified:
            raise PermissionDenied(
                "Verify your college email before reporting a problem."
            )

        location = serializer.validated_data["location"]

        if not location.is_active:
            raise ValidationError({
                "location": "This campus location is inactive."
            })

        with transaction.atomic():
            complaint = serializer.save(
                reporter=user,
                status=Complaint.Status.SUBMITTED,
                is_public=False,
            )

            ComplaintHistory.objects.create(
                complaint=complaint,
                actor=user,
                old_status="",
                new_status=Complaint.Status.SUBMITTED,
                reason="Complaint submitted",
            )

    def update(self, request, *args, **kwargs):
        raise PermissionDenied(
            "Use the dedicated complaint workflow endpoints."
        )

    def partial_update(self, request, *args, **kwargs):
        raise PermissionDenied(
            "Use the dedicated complaint workflow endpoints."
        )

    def destroy(self, request, *args, **kwargs):
        raise PermissionDenied(
            "Complaints cannot be deleted through this endpoint."
        )

    @action(detail=True, methods=["patch"])
    def assign(self, request, pk=None):
        complaint = self.get_object()

        if request.user.role != "management":
            raise PermissionDenied(
                "Only management can assign complaints."
            )

        staff_id = request.data.get("staff_id")

        from django.contrib.auth import get_user_model
        User = get_user_model()

        staff = User.objects.filter(
            id=staff_id,
            role="staff",
            is_active=True,
            email_verified=True,
        ).first()

        if not staff:
            raise ValidationError({
                "staff_id": "A valid, active staff member is required."
            })

        old_status = complaint.status

        with transaction.atomic():
            complaint.assigned_staff = staff

            if complaint.status == Complaint.Status.SUBMITTED:
                complaint.status = Complaint.Status.ASSIGNED

            complaint.save(
                update_fields=["assigned_staff", "status", "updated_at"]
            )

            ComplaintHistory.objects.create(
                complaint=complaint,
                actor=request.user,
                old_status=old_status,
                new_status=complaint.status,
                reason=f"Assigned to staff ID {staff.id}",
            )

        return Response(self.get_serializer(complaint).data)

    @action(detail=True, methods=["patch"])
    def update_status(self, request, pk=None):
        complaint = self.get_object()
        user = request.user

        new_status = request.data.get("status")
        reason = request.data.get("reason", "")

        if new_status not in [
            Complaint.Status.IN_PROGRESS,
            Complaint.Status.RESOLVED,
        ]:
            raise ValidationError({
                "status": "Use the verification endpoint for closure."
            })

        if user.role == "staff":
            if complaint.assigned_staff_id != user.id:
                raise PermissionDenied(
                    "You can update only your assigned complaints."
                )

        elif user.role != "management":
            raise PermissionDenied(
                "You cannot change this complaint's status."
            )

        if new_status == Complaint.Status.IN_PROGRESS:
            if complaint.status not in [
                Complaint.Status.ASSIGNED,
                Complaint.Status.IN_PROGRESS,
            ]:
                raise ValidationError(
                    "This complaint cannot enter progress from its current status."
                )

        if new_status == Complaint.Status.RESOLVED:
            if complaint.status not in [
                Complaint.Status.ASSIGNED,
                Complaint.Status.IN_PROGRESS,
            ]:
                raise ValidationError(
                    "Only assigned or in-progress complaints can be resolved."
                )

            if not complaint.evidence.exists():
                raise ValidationError(
                    "Upload repair evidence before marking the complaint resolved."
                )

        old_status = complaint.status

        with transaction.atomic():
            complaint.status = new_status

            if new_status == Complaint.Status.RESOLVED:
                complaint.resolution_note = reason

            complaint.save()

            ComplaintHistory.objects.create(
                complaint=complaint,
                actor=user,
                old_status=old_status,
                new_status=new_status,
                reason=reason,
            )

        return Response(self.get_serializer(complaint).data)

    @action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        complaint = self.get_object()

        if request.user.role not in ["student", "management"]:
            raise PermissionDenied(
                "Only the reporting student or management can verify resolution."
            )

        if (
            request.user.role == "student"
            and complaint.reporter_id != request.user.id
        ):
            raise PermissionDenied(
                "You can verify only your own complaint."
            )

        if complaint.status != Complaint.Status.RESOLVED:
            raise ValidationError(
                "Only resolved complaints can be verified."
            )

        approved = request.data.get("approved")

        if not isinstance(approved, bool):
            raise ValidationError({
                "approved": "Provide true or false."
            })

        reason = request.data.get("reason", "")

        if not approved and not reason.strip():
            raise ValidationError({
                "reason": "Provide a reason for reopening."
            })

        old_status = complaint.status

        with transaction.atomic():
            if approved:
                complaint.status = Complaint.Status.CLOSED
                complaint.resolution_verified = True
                complaint.is_public = True
                complaint.closed_at = timezone.now()
                history_reason = "Resolution verified"
            else:
                complaint.status = Complaint.Status.IN_PROGRESS
                complaint.resolution_verified = False
                complaint.is_public = False
                complaint.closed_at = None
                history_reason = reason

            complaint.save()

            ComplaintHistory.objects.create(
                complaint=complaint,
                actor=request.user,
                old_status=old_status,
                new_status=complaint.status,
                reason=history_reason,
            )

        return Response(self.get_serializer(complaint).data)

    @action(detail=True, methods=["post"])
    def reopen(self, request, pk=None):
        complaint = self.get_object()

        if (
            request.user.role != "student"
            or complaint.reporter_id != request.user.id
        ):
            raise PermissionDenied(
                "Only the reporting student can request reopening."
            )

        if complaint.status != Complaint.Status.CLOSED:
            raise ValidationError(
                "Only closed complaints can be reopened using this endpoint."
            )

        reason = request.data.get("reason", "").strip()

        if not reason:
            raise ValidationError({
                "reason": "A reopening reason is required."
            })

        old_status = complaint.status

        with transaction.atomic():
            complaint.status = Complaint.Status.IN_PROGRESS
            complaint.resolution_verified = False
            complaint.is_public = False
            complaint.closed_at = None
            complaint.save()

            ComplaintHistory.objects.create(
                complaint=complaint,
                actor=request.user,
                old_status=old_status,
                new_status=complaint.status,
                reason=reason,
            )

        return Response(self.get_serializer(complaint).data)

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        complaint = self.get_object()

        history = complaint.history.select_related("actor").order_by(
            "created_at"
        )

        return Response(
            ComplaintHistorySerializer(history, many=True).data
        )

    @action(detail=True, methods=["post"])
    def evidence(self, request, pk=None):
        complaint = self.get_object()
        user = request.user

        if (
            user.role != "staff"
            or complaint.assigned_staff_id != user.id
        ):
            if user.role != "management":
                raise PermissionDenied(
                    "Only assigned staff or authorized management can upload evidence."
                )

        serializer = EvidenceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            raise ValidationError({
                "file": "An evidence file is required."
            })

        max_size = 5 * 1024 * 1024

        if uploaded_file.size > max_size:
            raise ValidationError({
                "file": "Maximum file size is 5 MB."
            })

        allowed_types = {
            "image/jpeg",
            "image/png",
            "application/pdf",
        }

        if uploaded_file.content_type not in allowed_types:
            raise ValidationError({
                "file": "Only JPEG, PNG or PDF files are accepted."
            })

        evidence = serializer.save(
            complaint=complaint,
            uploaded_by=user,
            file=uploaded_file,
        )

        return Response(
            {
                "message": "Evidence uploaded successfully.",
                "evidence_id": evidence.id,
            },
            status=status.HTTP_201_CREATED,
        )

@api_view(["GET"])
@permission_classes([AllowAny])
def public_complaints(request):
    queryset = Complaint.objects.filter(
        status=Complaint.Status.CLOSED,
        resolution_verified=True,
        is_public=True,
    ).select_related("location").order_by("-closed_at")

    category = request.query_params.get("category")
    location_id = request.query_params.get("location")
    search = request.query_params.get("search")

    if category:
        queryset = queryset.filter(category=category)

    if location_id:
        queryset = queryset.filter(location_id=location_id)

    if search:
        queryset = queryset.filter(
            Q(title__icontains=search)
            | Q(description__icontains=search)
        )

    data = [
        {
            "id": complaint.id,
            "title": complaint.title,
            "category": complaint.category,
            "location": complaint.location.name,
            "status": complaint.status,
            "closed_at": complaint.closed_at,
        }
        for complaint in queryset
    ]

    return Response(data)


@api_view(["GET"])
@permission_classes([AllowAny])
def public_stats(request):
    total = Complaint.objects.count()

    submitted = Complaint.objects.filter(
        status=Complaint.Status.SUBMITTED
    ).count()

    in_progress = Complaint.objects.filter(
        status__in=[
            Complaint.Status.ASSIGNED,
            Complaint.Status.IN_PROGRESS,
        ]
    ).count()

    closed = Complaint.objects.filter(
        status=Complaint.Status.CLOSED,
        resolution_verified=True,
    ).count()

    rate = round((closed / total) * 100, 2) if total else 0

    return Response({
        "total": total,
        "pending": submitted,
        "in_progress": in_progress,
        "verified_resolved": closed,
        "resolution_rate": rate,
    })

# Create your views here.
