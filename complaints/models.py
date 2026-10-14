from django.conf import settings
from django.db import models
class Complaint(models.Model):
    class Category(models.TextChoices):
        ELECTRICAL = "electrical", "Electrical"
        PLUMBING = "plumbing", "Plumbing"
        CLEANLINESS = "cleanliness", "Cleanliness"
        CIVIL = "civil", "Civil Maintenance"
        OTHER = "other", "Other"
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        ASSIGNED = "assigned", "Assigned"
        IN_PROGRESS = "in_progress", "In Progress"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Verified / Closed"
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"
    title = models.CharField(max_length=200)
    description = models.TextField()
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reported_complaints",
    )
    location = models.ForeignKey(
        "campus.CampusLocation",
        on_delete=models.PROTECT,
        related_name="complaints",
    )
    category = models.CharField(
        max_length=30,
        choices=Category.choices,
        default=Category.OTHER,
    )
    suggested_category = models.CharField(
        max_length=30,
        blank=True,
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED,
    )
    assigned_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_complaints",
    )
    is_public = models.BooleanField(default=False)
    resolution_verified = models.BooleanField(default=False)
    resolution_note = models.TextField(blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"#{self.id} - {self.title}"
class ComplaintHistory(models.Model):
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name="history",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )

    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Complaint #{self.complaint_id}: {self.new_status}"


class Evidence(models.Model):
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name="evidence",
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )

    file = models.FileField(upload_to="private_evidence/")
    description = models.CharField(max_length=250, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evidence for complaint #{self.complaint_id}"

# Create your models here.
