"""
Invoice submission service.

Handles creation and resubmission of invoice submissions.
"""

import logging
from typing import Dict, List, Optional

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from organizations.models import OrganizationMembership, Organization
from ..models import InvoiceSubmission, InvoiceReviewAssignment, InvoiceSubmissionComment
from .exceptions import (
    SelfAssignmentError,
    InvalidReviewerError,
    FileUploadError,
)

User = get_user_model()
logger = logging.getLogger(__name__)


class InvoiceSubmissionService:
    """Service for invoice submission operations."""

    @staticmethod
    def create_submission(
        user: User,
        membership: OrganizationMembership,
        invoice_data: Dict,
        invoice_file: UploadedFile,
        reviewer_ids: List[int],
    ) -> InvoiceSubmission:
        """
        Create a new invoice submission with review assignments.

        Args:
            user: User creating the submission
            membership: User's organization membership
            invoice_data: Parsed invoice data dictionary
            invoice_file: Uploaded invoice PDF file
            reviewer_ids: List of reviewer user IDs

        Returns:
            Created InvoiceSubmission instance

        Raises:
            SelfAssignmentError: If user tries to assign themselves as reviewer
            InvalidReviewerError: If reviewer IDs are invalid
            FileUploadError: If file upload fails
        """
        # Validate no self-assignment
        if user.id in reviewer_ids:
            raise SelfAssignmentError("You cannot assign yourself as a reviewer.")

        # Validate reviewer IDs are admins in the organization
        valid_reviewer_ids = list(
            OrganizationMembership.objects.filter(
                organization=membership.organization,
                role=OrganizationMembership.ROLE_ADMIN,
                user_id__in=reviewer_ids,
            ).values_list("user_id", flat=True)
        )

        if len(valid_reviewer_ids) != len(reviewer_ids):
            raise InvalidReviewerError("Invalid reviewer selection.")

        logger.info(
            "Creating invoice submission: user=%s org=%s reviewers=%s file=%s size=%s",
            user.id,
            membership.organization_id,
            valid_reviewer_ids,
            getattr(invoice_file, "name", None),
            getattr(invoice_file, "size", None),
        )

        try:
            with transaction.atomic():
                # Create submission
                submission = InvoiceSubmission.objects.create(
                    organization=membership.organization,
                    submitted_by=user,
                    invoice_data=invoice_data,
                    invoice_file=invoice_file,
                )

                # Create review assignments
                assignments = [
                    InvoiceReviewAssignment(
                        submission=submission,
                        reviewer_id=reviewer_id,
                        assigned_by=user,
                    )
                    for reviewer_id in valid_reviewer_ids
                ]
                InvoiceReviewAssignment.objects.bulk_create(assignments)

                logger.info(
                    "Created invoice submission: id=%s reviewers=%s",
                    submission.id,
                    len(assignments),
                )

                return submission

        except Exception as exc:
            logger.exception(
                "Failed to create invoice submission (user=%s org=%s): %s",
                user.id,
                membership.organization_id,
                exc,
            )
            raise FileUploadError("Failed to upload invoice PDF. Please try again.")

    @staticmethod
    def resubmit_submission(
        submission: InvoiceSubmission,
        invoice_data: Dict,
        invoice_file: Optional[UploadedFile] = None,
        comment_message: Optional[str] = None,
    ) -> InvoiceSubmission:
        """
        Resubmit an existing submission with updated data.

        Updates submission data, optionally updates file, resets all review
        assignments to PENDING, and optionally adds a comment.

        Args:
            submission: Existing InvoiceSubmission to resubmit
            invoice_data: Updated invoice data dictionary
            invoice_file: Optional new invoice PDF file
            comment_message: Optional comment from submitter

        Returns:
            Updated InvoiceSubmission instance

        Raises:
            FileUploadError: If file upload fails
        """
        logger.info(
            "Resubmitting invoice: submission=%s has_file=%s has_comment=%s",
            submission.id,
            invoice_file is not None,
            bool(comment_message),
        )

        # Update file if provided
        if invoice_file:
            logger.info(
                "Updating invoice file: submission=%s file=%s size=%s",
                submission.id,
                getattr(invoice_file, "name", None),
                getattr(invoice_file, "size", None),
            )
            submission.invoice_file = invoice_file

        # Update submission data and reset status
        submission.invoice_data = invoice_data
        submission.status = InvoiceSubmission.STATUS_PENDING
        submission.reviewed_by = None
        submission.exported_at = None
        submission.exported_by = None

        try:
            # Save submission
            update_fields = [
                "invoice_data",
                "status",
                "reviewed_by",
                "exported_at",
                "exported_by",
                "updated_at",
            ]
            if invoice_file:
                update_fields.append("invoice_file")

            submission.save(update_fields=update_fields)

            # Reset all review assignments to PENDING
            submission.review_assignments.update(
                status=InvoiceReviewAssignment.STATUS_PENDING,
                updated_at=timezone.now(),
            )

            # Add comment if provided
            if comment_message:
                InvoiceSubmissionComment.objects.create(
                    submission=submission,
                    author=submission.submitted_by,
                    message=comment_message,
                    author_is_admin=False,
                )

            logger.info("Resubmitted invoice successfully: submission=%s", submission.id)
            return submission

        except Exception as exc:
            logger.exception(
                "Failed to resubmit invoice (submission=%s): %s",
                submission.id,
                exc,
            )
            raise FileUploadError("Failed to upload invoice PDF. Please try again.")

    @staticmethod
    def validate_reviewers_for_organization(
        organization: Organization,
        reviewer_ids: List[int],
        exclude_user_id: Optional[int] = None,
    ) -> List[int]:
        """
        Validate and return admin reviewer IDs for an organization.

        Args:
            organization: Organization instance
            reviewer_ids: List of reviewer user IDs to validate
            exclude_user_id: Optional user ID to exclude (e.g., submitter)

        Returns:
            List of valid admin user IDs

        Raises:
            SelfAssignmentError: If exclude_user_id is in reviewer_ids
            InvalidReviewerError: If any reviewer is not an admin
        """
        if exclude_user_id and exclude_user_id in reviewer_ids:
            raise SelfAssignmentError("You cannot assign yourself as a reviewer.")

        valid_reviewer_ids = list(
            OrganizationMembership.objects.filter(
                organization=organization,
                role=OrganizationMembership.ROLE_ADMIN,
                user_id__in=reviewer_ids,
            ).values_list("user_id", flat=True)
        )

        if len(valid_reviewer_ids) != len(reviewer_ids):
            raise InvalidReviewerError("Invalid reviewer selection.")

        return valid_reviewer_ids
