from django.conf import settings
from django.db import models

from organizations.models import Organization
from .storage import get_invoice_storage


class InvoiceSubmission(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHANGES_REQUESTED = "changes_requested"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_CHANGES_REQUESTED, "Changes requested"),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="invoice_submissions",
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="invoice_submissions",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    invoice_data = models.JSONField()
    invoice_file = models.FileField(
        upload_to="invoice_submissions/%Y/%m/%d/",
        null=True,
        blank=True,
        storage=get_invoice_storage(),
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invoice_reviews",
    )
    exported_at = models.DateTimeField(null=True, blank=True)
    exported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invoice_exports",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.organization_id}:{self.submitted_by_id}:{self.status}"

    @classmethod
    def reviewable_statuses(cls):
        return {cls.STATUS_PENDING}

    @classmethod
    def deletable_statuses(cls):
        return {cls.STATUS_PENDING, cls.STATUS_CHANGES_REQUESTED}


class InvoiceReviewAssignment(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_DECLINED = "declined"
    STATUS_CHANGES_REQUESTED = "changes_requested"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_DECLINED, "Declined"),
        (STATUS_CHANGES_REQUESTED, "Changes requested"),
    ]

    submission = models.ForeignKey(
        InvoiceSubmission,
        on_delete=models.CASCADE,
        related_name="review_assignments",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="invoice_review_assignments",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invoice_review_assignments_created",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "reviewer"], name="unique_invoice_review_assignment"
            )
        ]

    def __str__(self) -> str:
        return f"InvoiceReviewAssignment(submission={self.submission_id}, reviewer={self.reviewer_id}, status={self.status})"


class InvoiceSubmissionComment(models.Model):
    submission = models.ForeignKey(
        InvoiceSubmission,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invoice_submission_comments",
    )
    message = models.TextField()
    author_is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"InvoiceSubmissionComment(submission={self.submission_id}, author={self.author_id})"
