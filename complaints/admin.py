from django.contrib import admin
from .models import Complaint, ComplaintHistory, Evidence
class ComplaintHistoryInline(admin.TabularInline):
    model = ComplaintHistory
    extra = 0
    readonly_fields = [
        "actor",
        "action",
        "previous_status",
        "new_status",
        "reason",
        "created_at",
    ]
    can_delete = False
@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "title",
        "reporter",
        "assigned_staff",
        "location",
        "priority",
        "status",
        "is_public",
        "created_at",
    ]
    list_filter = ["status", "priority", "category", "is_public"]
    search_fields = ["title", "description", "reporter__username"]
    inlines = [ComplaintHistoryInline]
@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "complaint",
        "uploaded_by",
        "description",
        "created_at",
    ]
    readonly_fields = ["created_at"]
# Register your models here.
