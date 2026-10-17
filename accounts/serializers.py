from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.core import signing
from django.core.mail import send_mail
from django.urls import reverse
User = get_user_model()
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )
    confirm_password = serializers.CharField(
        write_only=True,
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
        allowed_domain = "akgec.ac.in"
        if value.rsplit("@", 1)[-1].lower() != allowed_domain:
            raise serializers.ValidationError(
                "Use your approved college email address."
            )
        return value.lower()
    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })
        return data
    def create(self, validated_data):
        validated_data.pop("confirm_password")
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            role=User.Role.STUDENT,
            email_verified=False,
            is_active=True,
        )

        return user

class CampusPulseTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        if not self.user.email_verified:
            raise serializers.ValidationError(
                "Verify your college email before logging in."
            )

        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "role": self.user.role,
        }

        return data