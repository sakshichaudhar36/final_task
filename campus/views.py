from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import CampusLocation
from .serializers import CampusLocationSerializer
class CampusLocationListView(generics.ListAPIView):
    serializer_class = CampusLocationSerializer
    permission_classes = [AllowAny]
    def get_queryset(self):
        return CampusLocation.objects.filter(is_active=True)
# Create your views here.
