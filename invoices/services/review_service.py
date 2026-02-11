"""
Invoice review service.

Handles review workflows including approval, rejection, change requests,
and reviewer management.
"""

import logging
from typing import Dict, Tuple

from django.db import transaction
from django.contrib.auth import get_user_model

from organizations.models import OrganizationMembership, Organization
from ..models import InvoiceSubmission, InvoiceReviewAssignment, InvoiceSubmissionComment
from .exceptions import (
    ReviewPermissionError,
    InvalidReviewActionError,
    SelfAssignmentError,
    InvalidReviewerError,
)

User = get_user_model()
logger = logging.getLogger(__name__)


class InvoiceReviewService:
    """Service for invoice review operations."""

    @staticmethod
    def approve_submission(
        submission: InvoiceSubmission,
        reviewer: User,
        has_assignments: bool = None,
    ) -> Tuple[InvoiceSubmission, Dict]:
        """
        Approve a submission as a reviewer.

        If all reviewers have approved, the submission is automatically approved.

        Args:
            submission: InvoiceSubmission to approve
            reviewer: User performing the approval
            has_assignments: Optional flag indicating if assignments exist
                           (computed if not provided)

        Returns:
            Tuple of (updated submission, review payload dict)

        Raises:
            ReviewPermissionError: If user is not assigned as reviewer
            InvalidReviewActionError: If review already declined or changes requested
        """
        with transaction.atomic():
            assignments_qs = submission.review_assignments.select_for_update()
            if has_assignments is None:
                has_assignments = assignments_qs.exists()

            if has_assignments:
                # Find reviewer's assignment
                assignment = assignments_qs.filter(reviewer=reviewer).first()
                if not assignment:
                    raise ReviewPermissionError("Reviewer access required.")

                # Check current status
                if assignment.status == InvoiceReviewAssignment.STATUS_DECLINED:
                    raise InvalidReviewActionError("Review already declined.")
                if assignment.status == InvoiceReviewAssignment.STATUS_CHANGES_REQUESTED:
                    raise InvalidReviewActionError("Changes already requested.")

                # Update assignment to APPROVED
                if assignment.status != InvoiceReviewAssignment.STATUS_APPROVED:
                    assignment.status = InvoiceReviewAssignment.STATUS_APPROVED
                    assignment.save(update_fields=["status", "updated_at"])

                # Check if all reviewers approved
                all_approved = not assignments_qs.exclude(
                    status=InvoiceReviewAssignment.STATUS_APPROVED
                ).exists()

                if all_approved and submission.status != InvoiceSubmission.STATUS_APPROVED:
                    submission.status = InvoiceSubmission.STATUS_APPROVED
                    submission.reviewed_by = reviewer
                    submission.save(update_fields=["status", "reviewed_by", "updated_at"])
            else:
                # No assignments - admin can directly approve
                submission.status = InvoiceSubmission.STATUS_APPROVED
                submission.reviewed_by = reviewer
                submission.save(update_fields=["status", "reviewed_by", "updated_at"])

        logger.info(
            "Submission approved: id=%s reviewer=%s status=%s",
            submission.id,
            reviewer.id,
            submission.status,
        )

        # Build and return review payload
        review_payload = InvoiceReviewService._build_review_payload(submission, reviewer)
        return submission, review_payload

    @staticmethod
    def reject_submission(
        submission: InvoiceSubmission,
        reviewer: User,
        has_assignments: bool = None,
    ) -> Tuple[InvoiceSubmission, Dict]:
        """
        Reject a submission as a reviewer.

        Clears export metadata.

        Args:
            submission: InvoiceSubmission to reject
            reviewer: User performing the rejection
            has_assignments: Optional flag indicating if assignments exist

        Returns:
            Tuple of (updated submission, review payload dict)

        Raises:
            ReviewPermissionError: If user is not assigned as reviewer
            InvalidReviewActionError: If review already approved or changes requested
        """
        with transaction.atomic():
            assignments_qs = submission.review_assignments.select_for_update()
            if has_assignments is None:
                has_assignments = assignments_qs.exists()

            if has_assignments:
                # Find reviewer's assignment
                assignment = assignments_qs.filter(reviewer=reviewer).first()
                if not assignment:
                    raise ReviewPermissionError("Reviewer access required.")

                # Check current status
                if assignment.status == InvoiceReviewAssignment.STATUS_APPROVED:
                    raise InvalidReviewActionError("Review already approved.")
                if assignment.status == InvoiceReviewAssignment.STATUS_CHANGES_REQUESTED:
                    raise InvalidReviewActionError("Changes already requested.")

                # If already declined, return early (idempotent)
                if assignment.status == InvoiceReviewAssignment.STATUS_DECLINED:
                    review_payload = InvoiceReviewService._build_review_payload(submission, reviewer)
                    return submission, review_payload

                # Update assignment to DECLINED
                assignment.status = InvoiceReviewAssignment.STATUS_DECLINED
                assignment.save(update_fields=["status", "updated_at"])

            # Update submission to REJECTED and clear export data
            submission.status = InvoiceSubmission.STATUS_REJECTED
            submission.reviewed_by = reviewer
            submission.exported_at = None
            submission.exported_by = None
            submission.save(
                update_fields=["status", "reviewed_by", "exported_at", "exported_by", "updated_at"]
            )

        logger.info(
            "Submission rejected: id=%s reviewer=%s",
            submission.id,
            reviewer.id,
        )

        # Build and return review payload
        review_payload = InvoiceReviewService._build_review_payload(submission, reviewer)
        return submission, review_payload

    @staticmethod
    def request_changes(
        submission: InvoiceSubmission,
        reviewer: User,
        comment_message: str,
        has_assignments: bool = None,
    ) -> Tuple[InvoiceSubmission, Dict]:
        """
        Request changes to a submission with a mandatory comment.

        Clears export metadata.

        Args:
            submission: InvoiceSubmission to request changes for
            reviewer: User requesting changes
            comment_message: Comment explaining requested changes
            has_assignments: Optional flag indicating if assignments exist

        Returns:
            Tuple of (updated submission, review payload dict)

        Raises:
            ReviewPermissionError: If user is not assigned as reviewer
            InvalidReviewActionError: If review already approved or declined
        """
        with transaction.atomic():
            assignments_qs = submission.review_assignments.select_for_update()
            if has_assignments is None:
                has_assignments = assignments_qs.exists()

            if has_assignments:
                # Find reviewer's assignment
                assignment = assignments_qs.filter(reviewer=reviewer).first()
                if not assignment:
                    raise ReviewPermissionError("Reviewer access required.")

                # Check current status
                if assignment.status == InvoiceReviewAssignment.STATUS_APPROVED:
                    raise InvalidReviewActionError("Review already approved.")
                if assignment.status == InvoiceReviewAssignment.STATUS_DECLINED:
                    raise InvalidReviewActionError("Review already declined.")

                # If already changes_requested, return early (idempotent)
                if assignment.status == InvoiceReviewAssignment.STATUS_CHANGES_REQUESTED:
                    review_payload = InvoiceReviewService._build_review_payload(submission, reviewer)
                    return submission, review_payload

                # Update assignment to CHANGES_REQUESTED
                assignment.status = InvoiceReviewAssignment.STATUS_CHANGES_REQUESTED
                assignment.save(update_fields=["status", "updated_at"])

            # Update submission status and clear export data
            submission.status = InvoiceSubmission.STATUS_CHANGES_REQUESTED
            submission.reviewed_by = reviewer
            submission.exported_at = None
            submission.exported_by = None
            submission.save(
                update_fields=["status", "reviewed_by", "exported_at", "exported_by", "updated_at"]
            )

            # Create comment
            InvoiceSubmissionComment.objects.create(
                submission=submission,
                author=reviewer,
                message=comment_message,
                author_is_admin=True,
            )

        logger.info(
            "Changes requested: id=%s reviewer=%s",
            submission.id,
            reviewer.id,
        )

        # Build and return review payload
        review_payload = InvoiceReviewService._build_review_payload(submission, reviewer)
        return submission, review_payload

    @staticmethod
    def add_reviewer(
        submission: InvoiceSubmission,
        reviewer_id: int,
        assigned_by: User,
        organization: Organization,
    ) -> Tuple[InvoiceSubmission, Dict, bool]:
        """
        Add a reviewer to a submission.

        If submission was approved and a new reviewer is added, reverts to PENDING.

        Args:
            submission: InvoiceSubmission to add reviewer to
            reviewer_id: User ID of reviewer to add
            assigned_by: User adding the reviewer
            organization: Organization instance

        Returns:
            Tuple of (updated submission, review payload dict, created flag)

        Raises:
            SelfAssignmentError: If assigned_by tries to add themselves
            InvalidReviewerError: If reviewer is not an admin in organization
        """
        # Validate no self-assignment
        if str(reviewer_id) == str(assigned_by.id):
            raise SelfAssignmentError("You cannot assign yourself as a reviewer.")

        # Validate reviewer is admin
        reviewer_membership = OrganizationMembership.objects.filter(
            organization=organization,
            role=OrganizationMembership.ROLE_ADMIN,
            user_id=reviewer_id,
        ).first()
        if not reviewer_membership:
            raise InvalidReviewerError("Reviewer must be an admin in this organization.")

        with transaction.atomic():
            # Get or create assignment
            assignment, created = InvoiceReviewAssignment.objects.get_or_create(
                submission=submission,
                reviewer_id=reviewer_membership.user_id,
                defaults={"assigned_by": assigned_by},
            )

            # If created and submission was approved, revert to pending
            if created and submission.status == InvoiceSubmission.STATUS_APPROVED:
                submission.status = InvoiceSubmission.STATUS_PENDING
                submission.reviewed_by = None
                submission.exported_at = None
                submission.exported_by = None
                submission.save(
                    update_fields=["status", "reviewed_by", "exported_at", "exported_by", "updated_at"]
                )
                logger.info(
                    "Submission reverted to pending after adding reviewer: id=%s reviewer=%s",
                    submission.id,
                    reviewer_id,
                )

        logger.info(
            "Reviewer added: submission=%s reviewer=%s created=%s",
            submission.id,
            reviewer_id,
            created,
        )

        # Build and return review payload
        review_payload = InvoiceReviewService._build_review_payload(submission, assigned_by)
        return submission, review_payload, created

    @staticmethod
    def _build_review_payload(submission: InvoiceSubmission, viewer: User) -> Dict:
        """
        Build standardized review summary payload.

        Args:
            submission: InvoiceSubmission to build payload for
            viewer: User viewing the submission (affects can_export calculation)

        Returns:
            Dictionary with reviewers, review_summary, reviewer_status, can_export
        """
        assignments = list(
            submission.review_assignments.select_related("reviewer").order_by("created_at")
        )

        # Build reviewers list
        reviewers = []
        for assignment in assignments:
            reviewer = assignment.reviewer
            reviewers.append({
                "id": reviewer.id,
                "email": reviewer.email,
                "status": assignment.status,
                "is_current_user": reviewer.id == viewer.id,
            })

        # Build summary counts
        summary = {
            "total": len(assignments),
            "approved": sum(1 for a in assignments if a.status == InvoiceReviewAssignment.STATUS_APPROVED),
            "pending": sum(1 for a in assignments if a.status == InvoiceReviewAssignment.STATUS_PENDING),
            "declined": sum(1 for a in assignments if a.status == InvoiceReviewAssignment.STATUS_DECLINED),
            "changes_requested": sum(
                1 for a in assignments if a.status == InvoiceReviewAssignment.STATUS_CHANGES_REQUESTED
            ),
        }

        # Get viewer's status
        reviewer_status = None
        assignment_for_viewer = next(
            (a for a in assignments if a.reviewer_id == viewer.id), None
        )
        if assignment_for_viewer:
            reviewer_status = assignment_for_viewer.status

        # Calculate can_export
        has_assignments = len(assignments) > 0
        export_locked = bool(submission.exported_at)

        if has_assignments:
            can_export = (
                not export_locked
                and submission.status == InvoiceSubmission.STATUS_APPROVED
                and reviewer_status == InvoiceReviewAssignment.STATUS_APPROVED
            )
        else:
            can_export = (
                not export_locked
                and submission.status == InvoiceSubmission.STATUS_APPROVED
            )

        return {
            "reviewers": reviewers,
            "review_summary": summary,
            "reviewer_status": reviewer_status,
            "can_export": can_export,
        }
