import uuid

from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        INVITE_RECEIVED = "INVITE_RECEIVED", "Invite Received"
        APPROVAL_NEEDED = "APPROVAL_NEEDED", "Approval Needed"
        EDIT_REQUESTED = "EDIT_REQUESTED", "Edit Requested"
        INVOICE_APPROVED = "INVOICE_APPROVED", "Invoice Approved"
        INVOICE_BOOKED = "INVOICE_BOOKED", "Invoice Booked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    invoice = models.ForeignKey(
        "invoices.Invoice",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    type = models.CharField(max_length=30, choices=Type.choices)
    title = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.type} → {self.user}"
