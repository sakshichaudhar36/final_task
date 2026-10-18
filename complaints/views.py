from .ml_service import predict_complaint
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from accounts.permissions import IsManagement
from campus.models import CampusLocation
from .models import Complaint, ComplaintHistory, Evidence
from .permissions import ComplaintPermission
from .serializers import (
    ComplaintSerializer,
    AssignmentSerializer,
    StatusUpdateSerializer,
    VerificationSerializer,
    ReopenSerializer,
    EvidenceSerializer,
    ComplaintHistorySerializer,
    PublicComplaintSerializer,
)
User = get_user_model()
def record_history(complaint, actor, action, old_status="", reason=""):
    ComplaintHistory.objects.create(
        complaint=complaint,
        actor=actor,
        action=action,
        previous_status=old_status,
        new_status=complaint.status,
        reason=reason,
    )
class ComplaintViewSet(viewsets.ModelViewSet):
    serializer_class = ComplaintSerializer
    permission_classes = [IsAuthenticated, ComplaintPermission]
    def get_queryset(self):
        user = self.request.user
        queryset = Complaint.objects.select_related(
            "reporter", "assigned_staff", "location"
        ).order_by("-created_at")
        if user.role == "management":
            return queryset
        if user.role == "staff":
            return queryset.filter(assigned_staff=user)
        return queryset.filter(reporter=user)
    def perform_create(self, serializer):
        location_id = self.request.data.get("location")
        if not CampusLocation.objects.filter(
            pk=location_id,
            is_active=True,
        ).exists():
            raise ValidationError({
                "location": "Select an active campus location."
            })
        title = serializer.validated_data["title"]
        description = serializer.validated_data["description"]
        ml_result = predict_complaint(title, description)
        # Map ML category to Django category values
        suggested_category = ""
        if ml_result and ml_result.get("ml_available", True):
                predicted = ml_result.get("category")
                if isinstance(predicted, str):
                            category_mapping = {
                                "electrical": "electrical",
                                "electricity": "electrical",
                                "plumbing": "plumbing",
                                "water": "plumbing",
                                "cleanliness": "cleanliness",
                                "cleaning": "cleanliness",
                                "civil": "civil",
                                "civil maintenance": "civil",
                                "other": "other",
                            }
                            suggested_category = category_mapping.get(predicted.strip().lower(), "")
                            
        complaint = serializer.save(
            reporter=self.request.user,
            status=Complaint.Status.SUBMITTED,
            suggested_category=suggested_category,
        )
        
        record_history(
            complaint,
            self.request.user,
            "submitted",
            reason="Complaint submitted",
        )
    def update(self, request, *args, **kwargs):
        # General edits are not permitted through the detail endpoint.
        # Use the dedicated actions for status, assignment and verification.
        raise PermissionDenied(
            "Use the specific complaint actions to make changes."
        )
    def partial_update(self, request, *args, **kwargs):
        raise PermissionDenied(
            "Use the specific complaint actions to make changes."
        )
    @action(detail=True, methods=["patch"], permission_classes=[
        IsAuthenticated, IsManagement
    ])
    def assign(self, request, pk=None):
        complaint = self.get_object()
        serializer = AssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff = User.objects.get(
            pk=serializer.validated_data["staff_id"]
        )
        old_status = complaint.status
        complaint.assigned_staff = staff

        if complaint.status in [
            Complaint.Status.SUBMITTED,
            Complaint.Status.REOPENED,
        ]:
            complaint.status = Complaint.Status.ASSIGNED

        complaint.save()
        record_history(
            complaint,
            request.user,
            "assigned",
            old_status=old_status,
            reason=f"Assigned to {staff.username}",
        )

        return Response(ComplaintSerializer(complaint).data)

    @action(detail=True, methods=["patch"], permission_classes=[
        IsAuthenticated
    ])
    def update_status(self, request, pk=None):
        complaint = self.get_object()
        user = request.user

        if user.role != "management" and not (
            user.role == "staff"
            and complaint.assigned_staff_id == user.id
        ):
            raise PermissionDenied(
                "Only assigned staff or management can update status."
            )

        serializer = StatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["status"]
        reason = serializer.validated_data.get("reason", "")
        old_status = complaint.status

        allowed = {
            Complaint.Status.ASSIGNED: [
                Complaint.Status.IN_PROGRESS,
            ],
            Complaint.Status.IN_PROGRESS: [
                Complaint.Status.RESOLVED,
            ],
            Complaint.Status.REOPENED: [
                Complaint.Status.IN_PROGRESS,
            ],
        }

        if user.role != "management":
            if new_status not in allowed.get(old_status, []):
                raise ValidationError({
                    "status": f"Cannot change status from {old_status} to {new_status}."
                })

        complaint.status = new_status
        if new_status == Complaint.Status.RESOLVED:
            complaint.resolved_at = timezone.now()
        elif new_status == Complaint.Status.IN_PROGRESS:
            complaint.resolved_at = None
            complaint.verified_at = None

        complaint.save()
        record_history(
            complaint,
            user,
            "status_updated",
            old_status=old_status,
            reason=reason,
        )
        return Response(ComplaintSerializer(complaint).data)
    @action(detail=True, methods=["post"], permission_classes=[
        IsAuthenticated
    ])
    def evidence(self, request, pk=None):
        complaint = self.get_object()
        user = request.user

        if user.role != "management" and not (
            user.role == "staff"
            and complaint.assigned_staff_id == user.id
        ):
            raise PermissionDenied(
                "Only assigned staff or management can upload evidence."
            )

        if complaint.status not in [
            Complaint.Status.IN_PROGRESS,
            Complaint.Status.RESOLVED,
        ]:
            raise ValidationError(
                "Evidence can be uploaded while work is in progress or resolved."
            )

        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            raise ValidationError({"file": "A file is required."})

        if uploaded_file.size > 5 * 1024 * 1024:
            raise ValidationError({"file": "Maximum file size is 5 MB."})

        allowed_types = {
            "image/jpeg",
            "image/png",
            "application/pdf",
        }
        if uploaded_file.content_type not in allowed_types:
            raise ValidationError({
                "file": "Only JPEG, PNG, or PDF evidence is accepted."
            })

        serializer = EvidenceSerializer(data={
            "file": uploaded_file,
            "description": request.data.get("description", ""),
        })
        serializer.is_valid(raise_exception=True)
        evidence = serializer.save(
            complaint=complaint,
            uploaded_by=user,
        )
        record_history(
            complaint,
            user,
            "evidence_uploaded",
            reason="Evidence uploaded",
        )
        return Response(
            EvidenceSerializer(evidence).data,
            status=status.HTTP_201_CREATED,
        )
    @action(detail=True, methods=["post"], permission_classes=[
        IsAuthenticated
    ])
    def verify(self, request, pk=None):
        complaint = self.get_object()
        user = request.user
        if user.role != "management" and complaint.reporter_id != user.id:
            raise PermissionDenied(
                "Only the reporter or management can verify resolution."
            )
        if complaint.status != Complaint.Status.RESOLVED:
            raise ValidationError(
                "Only resolved complaints can be verified."
            )
        serializer = VerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        approved = serializer.validated_data["approved"]
        reason = serializer.validated_data.get("reason", "")
        old_status = complaint.status

        if approved:
            complaint.status = Complaint.Status.VERIFIED
            complaint.verified_at = timezone.now()
            complaint.is_public = True
            action_name = "resolution_verified"
        else:
            complaint.status = Complaint.Status.REOPENED
            complaint.verified_at = None
            complaint.resolved_at = None
            complaint.is_public = False
            action_name = "resolution_rejected"
        complaint.save()
        record_history(
            complaint,
            user,
            action_name,
            old_status=old_status,
            reason=reason,
        )
        return Response(ComplaintSerializer(complaint).data)
    @action(detail=True, methods=["post"], permission_classes=[
        IsAuthenticated
    ])
    def reopen(self, request, pk=None):
        complaint = self.get_object()
        user = request.user
        if user.role != "management" and complaint.reporter_id != user.id:
            raise PermissionDenied(
                "Only the reporter or management can reopen a complaint."
            )
        if complaint.status not in [
            Complaint.Status.RESOLVED,
            Complaint.Status.VERIFIED,
        ]:
            raise ValidationError(
                "Only resolved or verified complaints can be reopened."
            )
        serializer = ReopenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        old_status = complaint.status
        complaint.status = Complaint.Status.REOPENED
        complaint.resolved_at = None
        complaint.verified_at = None
        complaint.is_public = False
        complaint.save()
        record_history(
            complaint,
            user,
            "reopened",
            old_status=old_status,
            reason=serializer.validated_data["reason"],
        )
        return Response(ComplaintSerializer(complaint).data)
    @action(detail=True, methods=["get"], permission_classes=[
        IsAuthenticated
    ])
    def history(self, request, pk=None):
        complaint = self.get_object()
        records = complaint.history.select_related("actor")
        return Response(
            ComplaintHistorySerializer(records, many=True).data
        )
@api_view(["GET"])
@permission_classes([AllowAny])
def public_complaints(request):
    queryset = Complaint.objects.filter(
        is_public=True,
        status=Complaint.Status.VERIFIED,
    ).select_related("location").order_by("-updated_at")
    category = request.query_params.get("category")
    if category:
        queryset = queryset.filter(category=category)
    complaint_status = request.query_params.get("status")
    if complaint_status:
        queryset = queryset.filter(status=complaint_status)
    search = request.query_params.get("search")
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search)
            | Q(category__icontains=search)
            | Q(location__name__icontains=search)
        )
    return Response(
        PublicComplaintSerializer(queryset, many=True).data
    )
@api_view(["GET"])
@permission_classes([AllowAny])
def public_stats(request):
    queryset = Complaint.objects.filter(
        is_public=True,
        status=Complaint.Status.VERIFIED,
    )
    return Response({
        "verified_resolved": queryset.count(),
        "total_public_complaints": queryset.count(),
    })
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsManagement])
def management_analytics(request):
    queryset = Complaint.objects.all()
    return Response({
        "total": queryset.count(),
        "by_status": list(
            queryset.values("status").annotate(count=Count("id"))
        ),
        "by_category": list(
            queryset.values("category").annotate(count=Count("id"))
        ),
        "by_location": list(
            queryset.values(
                "location__name"
            ).annotate(count=Count("id"))
        ),
    })