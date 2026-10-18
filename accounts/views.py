from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import (
    RegisterSerializer,
    CampusPulseTokenSerializer,
    CampusPulseRefreshSerializer,
    ProfileSerializer,
)
User = get_user_model()
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        token = request.query_params.get("token")

        if not token:
            return Response(
                {"detail": "Verification token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            data = signing.loads(
                token,
                salt="campuspulse-email-verification",
                max_age=86400,
            )
            user = User.objects.get(pk=data["user_id"])
        except (signing.BadSignature, signing.SignatureExpired,
                User.DoesNotExist, KeyError, TypeError):
            return Response(
                {"detail": "Invalid or expired verification link."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.email_verified:
            return Response({"detail": "Email already verified."})
        user.email_verified = True
        user.is_active = True
        user.save(update_fields=["email_verified", "is_active"])

        return Response({
            "detail": "College email verified. You can now log in."
        })
class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CampusPulseTokenSerializer
class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
    serializer_class = CampusPulseRefreshSerializer
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"detail": "Logged out successfully."})
class MyProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    def get_object(self):
        return self.request.user