from rest_framework import generics
from rest_framework.permissions import AllowAny
from .serializers import RegisterSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView
from .serializers import CampusPulseTokenSerializer

class LoginView(TokenObtainPairView):
    serializer_class = CampusPulseTokenSerializer
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
