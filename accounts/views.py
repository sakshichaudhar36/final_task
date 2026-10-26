from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
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
class VerifyEmailOTPView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        otp = str(request.data.get("otp", "")).strip()
        if not email or not otp:
            return Response(
                {"detail": "Email and OTP are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "Invalid email or OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.email_verified:
            return Response(
                {"detail": "Email is already verified."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not user.verification_otp_hash or not user.verification_otp_expires_at:
            return Response(
                {"detail": "No valid OTP found. Please register again or request a new OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if timezone.now() > user.verification_otp_expires_at:
            return Response(
                {"detail": "OTP has expired. Please request a new OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not check_password(otp, user.verification_otp_hash):
            return Response(
                {"detail": "Invalid email or OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.email_verified = True
        user.is_active = True
        user.verification_otp_hash = ""
        user.verification_otp_expires_at = None
        user.save(
            update_fields=[
                "email_verified",
                "is_active",
                "verification_otp_hash",
                "verification_otp_expires_at",
            ]
        )
        return Response(
            {"detail": "Email verified successfully. You can now log in."},
            status=status.HTTP_200_OK,
        )
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