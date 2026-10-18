from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from accounts.permissions import IsManagement
from .models import CampusLocation
from .serializers import CampusLocationSerializer
class CampusLocationViewSet(viewsets.ModelViewSet):
    queryset = CampusLocation.objects.all().order_by("building", "name")
    serializer_class = CampusLocationSerializer
    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated(), IsManagement()]
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated and (
            self.request.user.role == "management"
        ):
            return queryset
        return queryset.filter(is_active=True)
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)