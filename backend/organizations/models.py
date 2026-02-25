import uuid

from django.conf import settings
from django.db import models


class Organization(models.Model):
    class ErpType(models.TextChoices):
        NONE = "NONE", "None"
        GOOGLE_SHEETS = "GOOGLE_SHEETS", "Google Sheets"
        QUICKBOOKS = "QUICKBOOKS", "QuickBooks"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    vat_number = models.CharField(max_length=50, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    erp_type = models.CharField(
        max_length=20, choices=ErpType.choices, default=ErpType.NONE
    )
    erp_config = models.JSONField(null=True, blank=True)
    required_approvals = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "organizations"

    def __str__(self):
        return self.name


class OrganizationMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        ACCOUNTANT = "ACCOUNTANT", "Accountant"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACTIVE = "ACTIVE", "Active"
        DEACTIVATED = "DEACTIVATED", "Deactivated"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="memberships",
    )
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    invited_email = models.EmailField()
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invitations_sent",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "organization_memberships"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "organization"],
                condition=models.Q(user__isnull=False),
                name="unique_user_per_org",
            ),
            models.UniqueConstraint(
                fields=["invited_email", "organization"],
                name="unique_invite_per_org",
            ),
        ]

    def __str__(self):
        return f"{self.invited_email} — {self.organization.name} ({self.role})"


class Supplier(models.Model):
    class CountryGroup(models.TextChoices):
        EE = "EE", "Estonia"
        EU_OTHER = "EU_OTHER", "EU (other)"
        NON_EU = "NON_EU", "Non-EU"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="suppliers"
    )
    name = models.CharField(max_length=255)
    vat_id = models.CharField(max_length=50, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    country_group = models.CharField(
        max_length=20, choices=CountryGroup.choices, null=True, blank=True
    )
    email = models.EmailField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "suppliers"
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "vat_id"],
                condition=models.Q(vat_id__isnull=False),
                name="unique_supplier_vat_per_org",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.organization.name})"
