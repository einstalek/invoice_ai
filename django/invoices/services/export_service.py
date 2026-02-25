"""
Invoice export service.

Handles exporting approved invoices to Google Sheets.
"""

import logging
from typing import Tuple

from django.utils import timezone
from django.contrib.auth import get_user_model

from accounts.services import get_user_credentials, set_user_spreadsheet_id
from google_sheets_utils import append_invoice_to_user_sheet, create_user_spreadsheet
from organizations.models import OrganizationMembership
from ..models import InvoiceSubmission, InvoiceReviewAssignment
from .exceptions import (
    ExportPermissionError,
    GoogleCredentialsError,
    SubmissionAlreadyExportedError,
    SubmissionNotApprovedError,
    MissingInvoiceDataError,
)

User = get_user_model()
logger = logging.getLogger(__name__)


class InvoiceExportService:
    """Service for invoice export operations."""

    @staticmethod
    def export_to_google_sheets(
        submission: InvoiceSubmission,
        user: User,
        membership: OrganizationMembership,
    ) -> Tuple[str, str]:
        """
        Export an approved invoice to Google Sheets.

        Args:
            submission: InvoiceSubmission to export
            user: User performing the export
            membership: User's organization membership

        Returns:
            Tuple of (spreadsheet_id, exported_at_iso)

        Raises:
            SubmissionNotApprovedError: If submission is not approved
            SubmissionAlreadyExportedError: If submission already exported
            ExportPermissionError: If user lacks export permission
            GoogleCredentialsError: If Google credentials are missing
            MissingInvoiceDataError: If invoice data is missing
        """
        # Validate submission is approved
        if submission.status != InvoiceSubmission.STATUS_APPROVED:
            raise SubmissionNotApprovedError("Submission is not approved.")

        # Validate not already exported
        if submission.exported_at:
            raise SubmissionAlreadyExportedError("Submission already exported.")

        # Validate export permission
        InvoiceExportService._validate_export_permission(submission, user, membership)

        # Validate invoice data exists
        invoice = submission.invoice_data or {}
        if not invoice:
            raise MissingInvoiceDataError("Missing invoice data.")

        # Get Google credentials
        credentials, spreadsheet_id = get_user_credentials(user)
        if not credentials:
            raise GoogleCredentialsError("Google account not connected.")

        try:
            # Create spreadsheet if needed
            if not spreadsheet_id:
                spreadsheet_id = create_user_spreadsheet(credentials)
                set_user_spreadsheet_id(user, spreadsheet_id)

            # Append invoice to sheet
            append_invoice_to_user_sheet(credentials, spreadsheet_id, invoice)

            # Update submission with export metadata
            submission.exported_at = timezone.now()
            submission.exported_by = user
            submission.save(update_fields=["exported_at", "exported_by", "updated_at"])

            logger.info(
                "Invoice exported to Google Sheets: submission=%s user=%s spreadsheet=%s",
                submission.id,
                user.id,
                spreadsheet_id,
            )

            return spreadsheet_id, submission.exported_at.isoformat()

        except Exception as exc:
            logger.exception(
                "Failed to export invoice to Google Sheets (submission=%s user=%s): %s",
                submission.id,
                user.id,
                exc,
            )
            raise

    @staticmethod
    def _validate_export_permission(
        submission: InvoiceSubmission,
        user: User,
        membership: OrganizationMembership,
    ):
        """
        Validate user has permission to export submission.

        Admin OR approved reviewer can export.

        Args:
            submission: InvoiceSubmission to export
            user: User attempting export
            membership: User's organization membership

        Raises:
            ExportPermissionError: If user lacks export permission
        """
        # Check if there are review assignments
        assignments_qs = submission.review_assignments.select_related("reviewer")

        if assignments_qs.exists():
            # If assignments exist, user must be admin OR an approved reviewer
            if membership.role != OrganizationMembership.ROLE_ADMIN:
                # Check if user is an approved reviewer
                assignment = assignments_qs.filter(reviewer=user).first()
                if not assignment or assignment.status != InvoiceReviewAssignment.STATUS_APPROVED:
                    raise ExportPermissionError("Reviewer approval required.")
        # If no assignments, export is allowed (permission already checked by view)
