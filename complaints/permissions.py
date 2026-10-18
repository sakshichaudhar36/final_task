from rest_framework.permissions import BasePermission, SAFE_METHODS
class ComplaintPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role == "management":
            return True
        if obj.reporter_id == user.id:
            return True
        if obj.assigned_staff_id == user.id:
            return True
        return False