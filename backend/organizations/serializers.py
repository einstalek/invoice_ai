from rest_framework import serializers

from accounts.serializers import UserSerializer
from .models import Organization, OrganizationMembership, Supplier


# ---------------------------------------------------------------------------
# Organization
# ---------------------------------------------------------------------------
class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            "id", "name", "vat_number", "address", "country",
            "erp_type", "erp_config", "required_approvals", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Strip sensitive OAuth credentials from the response.
        # Expose only a boolean flag so the frontend can show connection status.
        erp_config = data.get("erp_config")
        if erp_config and isinstance(erp_config, dict) and "google_credentials" in erp_config:
            erp_config = {**erp_config}
            erp_config.pop("google_credentials")
            erp_config["google_sheets_connected"] = True
            data["erp_config"] = erp_config
        return data

    def update(self, instance, validated_data):
        # When saving erp_config, preserve existing google_credentials
        # so a normal settings save doesn't wipe out the OAuth tokens.
        new_erp_config = validated_data.get("erp_config")
        if new_erp_config is not None:
            old_erp_config = instance.erp_config or {}
            google_credentials = old_erp_config.get("google_credentials")
            if google_credentials:
                new_erp_config["google_credentials"] = google_credentials
            validated_data["erp_config"] = new_erp_config
        return super().update(instance, validated_data)


class OrganizationCreateSerializer(serializers.ModelSerializer):
    """Used when creating a new org — auto-creates OWNER membership."""

    class Meta:
        model = Organization
        fields = ["id", "name", "vat_number", "address", "country"]
        read_only_fields = ["id"]


# ---------------------------------------------------------------------------
# Membership
# ---------------------------------------------------------------------------
class MembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = OrganizationMembership
        fields = [
            "id", "user", "organization", "role", "status",
            "invited_email", "invited_by", "created_at",
        ]
        read_only_fields = fields


class InviteMemberSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=OrganizationMembership.Role.choices)


# ---------------------------------------------------------------------------
# Supplier
# ---------------------------------------------------------------------------
class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            "id", "organization", "name", "vat_id", "address",
            "country", "country_group", "email", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]
