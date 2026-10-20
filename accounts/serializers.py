from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
User = get_user_model()
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

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=password,
            role=User.Role.STUDENT,
            email_verified=True,
            is_active=True,
        )

        return user
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

        # Return user details along with JWT tokens.
        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "role": self.user.role,
            "email_verified": self.user.email_verified,
        }

        return data
class CampusPulseRefreshSerializer(TokenRefreshSerializer):
    pass
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
