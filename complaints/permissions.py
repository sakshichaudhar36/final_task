from rest_framework.permissions import BasePermission, SAFE_METHODS
class IsManagement(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "management"
        )
class ComplaintObjectPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.role == "management":
            return True
        if request.method in SAFE_METHODS:
            return (
                obj.reporter_id == user.id
                or obj.assigned_staff_id == user.id
            )
        return False