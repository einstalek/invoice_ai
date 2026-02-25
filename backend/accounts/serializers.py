from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer as BaseRegisterSerializer
from dj_rest_auth.serializers import JWTSerializer as BaseJWTSerializer

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Read-only user representation returned by profile and nested endpoints."""

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "is_active", "date_joined"]
        read_only_fields = fields


class RegisterSerializer(BaseRegisterSerializer):
    """Override dj-rest-auth register to drop username, add full_name."""

    username = None
    full_name = serializers.CharField(required=True, max_length=255)

    def validate_email(self, email):
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data["full_name"] = self.validated_data.get("full_name", "")
        return data

    def custom_signup(self, request, user):
        user.full_name = self.validated_data.get("full_name", "")
        user.save(update_fields=["full_name"])


class JWTSerializer(BaseJWTSerializer):
    """Extend JWT response to include user profile data."""

    user = UserSerializer(read_only=True)


class GoogleLoginSerializer(serializers.Serializer):
    """Accepts a Google OAuth2 access token from the frontend."""

    access_token = serializers.CharField(required=False)
    id_token = serializers.CharField(required=False)
    code = serializers.CharField(required=False)

    def validate(self, attrs):
        if not any([attrs.get("access_token"), attrs.get("id_token"), attrs.get("code")]):
            raise serializers.ValidationError(
                "One of access_token, id_token, or code is required."
            )
        return attrs
