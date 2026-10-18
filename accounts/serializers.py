
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.core.mail import send_mail
from django.urls import reverse

from rest_framework import serializers
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)


User = get_user_model()


# ------------------------------------------
# 1. STUDENT REGISTRATION SERIALIZER
# ------------------------------------------

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )

    confirm_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "confirm_password",
        ]

    def validate_email(self, value):
        value = value.strip().lower()
        allowed_domain = "akgec.ac.in"

        if value.rsplit("@", 1)[-1].lower() != allowed_domain:
            raise serializers.ValidationError(
                "Use your approved college email address."
            )

        return value

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })

        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        password = validated_data.pop("password")

        # Create an unverified student account.
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=password,
            role=User.Role.STUDENT,
            email_verified=False,
            is_active=False,
        )

        # Generate a signed email-verification token.
        token = signing.dumps(
            {"user_id": user.pk},
            salt="campuspulse-email-verification",
        )

        # Build the verification URL.
        verify_path = reverse("verify-email")

        base_url = getattr(
            settings,
            "FRONTEND_BASE_URL",
            "http://127.0.0.1:8000",
        ).rstrip("/")

        verification_url = (
            f"{base_url}{verify_path}?token={token}"
        )

        # Send the verification email.
        send_mail(
            subject="Verify your CampusPulse college email",
            message=(
                "Welcome to CampusPulse!\n\n"
                "Please verify your college email using this link:\n"
                f"{verification_url}\n\n"
                "This verification link expires after 24 hours."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return user


# ------------------------------------------
# 2. JWT LOGIN SERIALIZER
# ------------------------------------------

class CampusPulseTokenSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add role to the JWT claims.
        token["role"] = user.role

        return token

    def validate(self, attrs):
        # Authenticate username and password.
        data = super().validate(attrs)

        # Block login until the email is verified.
        if not self.user.email_verified:
            raise serializers.ValidationError(
                "Verify your college email before logging in."
            )

        # Return user details along with JWT tokens.
        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "role": self.user.role,
            "email_verified": self.user.email_verified,
        }

        return data


# ------------------------------------------
# 3. JWT REFRESH SERIALIZER
# ------------------------------------------

class CampusPulseRefreshSerializer(TokenRefreshSerializer):
    pass


# ------------------------------------------
# 4. USER PROFILE SERIALIZER
# ------------------------------------------

class ProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = User

        fields = [
            "id",
            "username",
            "email",
            "role",
            "email_verified",
        ]

        read_only_fields = [
            "id",
            "username",
            "email",
            "role",
            "email_verified",
        ]
