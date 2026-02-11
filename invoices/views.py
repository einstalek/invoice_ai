import json
import logging
import os
import shutil
import tempfile
import traceback
from pathlib import Path

from django.shortcuts import render
from django.db.models import OuterRef, Subquery
from rest_framework.authentication import SessionAuthentication
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
import replicate

from config.header import build_header_context
from organizations.models import OrganizationMembership
from organizations.services import get_active_membership
from utils import (
    get_prediction_cache_key,
    get_cancel_cache_key,
    CANCEL_CACHE_TTL,
)
from django.core.cache import cache

from .models import InvoiceSubmission, InvoiceSubmissionComment, InvoiceReviewAssignment
from .services.submission_service import InvoiceSubmissionService
from .services.review_service import InvoiceReviewService
from .services.export_service import InvoiceExportService
from .services.file_service import InvoiceFileService
from .services.processing_service import InvoiceProcessingService
from .services.exceptions import (
    SelfAssignmentError,
    InvalidReviewerError,
    FileUploadError,
    ReviewPermissionError,
    InvalidReviewActionError,
    ExportPermissionError,
    GoogleCredentialsError,
    SubmissionAlreadyExportedError,
    SubmissionNotApprovedError,
    MissingInvoiceDataError,
    ProcessingError,
    OCREmptyError,
    ReplicateThrottledError,
)

logger = logging.getLogger(__name__)


def _parse_reviewer_ids(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        raw_list = value
    elif isinstance(value, str):
        value = value.strip()
        if not value:
            return []
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = [value]
        raw_list = parsed if isinstance(parsed, list) else [parsed]
    else:
        raw_list = [value]
    reviewer_ids = []
    for item in raw_list:
        try:
            reviewer_ids.append(int(item))
        except (TypeError, ValueError):
            continue
    return list({rid for rid in reviewer_ids if rid})


def _build_review_payload(submission, viewer):
    """Legacy wrapper for InvoiceReviewService._build_review_payload()."""
    payload = InvoiceReviewService._build_review_payload(submission, viewer)
    return payload["reviewers"], payload["review_summary"], payload["reviewer_status"]

def build_invoice_file_url(file_field, request=None) -> str | None:
    """Legacy wrapper for InvoiceFileService.get_signed_file_url()."""
    return InvoiceFileService.get_signed_file_url(file_field, request)

class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


class ProcessInvoiceView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        # Validate file upload
        if "file" not in request.FILES:
            return Response({"error": "No file part"}, status=400)

        file = request.FILES.get("file")
        if not file or not file.name:
            return Response({"error": "No selected file"}, status=400)

        request_id = request.data.get("request_id")

        # Save file to temp directory
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, file.name)

        try:
            # Write uploaded file to temp location
            with open(temp_path, "wb") as f:
                for chunk in file.chunks():
                    f.write(chunk)

            # Process using service
            result = InvoiceProcessingService.process_invoice_file(
                file_path=Path(temp_path),
                request_id=request_id,
            )

            return Response(result)

        except OCREmptyError as e:
            return Response({
                "error": str(e),
                "code": "OCR_EMPTY",
            }, status=422)

        except ReplicateThrottledError as e:
            return Response({
                "error": str(e),
                "code": "RATE_LIMITED",
            }, status=429)

        except ProcessingError as e:
            # Check if it's a cancellation
            if "cancelled" in str(e).lower():
                return Response({"error": str(e)}, status=409)
            return Response({"error": str(e)}, status=502)

        except Exception as exc:
            traceback.print_exc()
            payload = {"error": str(exc) or "Internal error"}
            if settings.DEBUG:
                payload["traceback"] = traceback.format_exc()
            return Response(payload, status=500)

        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir)


class CancelProcessInvoiceView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    def post(self, request):
        request_id = request.data.get("request_id")
        if not request_id:
            return Response({"error": "Missing request_id."}, status=400)

        cache_key = get_prediction_cache_key(request_id)
        cancel_key = get_cancel_cache_key(request_id)
        cache.set(cancel_key, True, timeout=CANCEL_CACHE_TTL)
        prediction_id = cache.get(cache_key)
        if not prediction_id:
            return Response({"ok": True, "status": "cancel_requested"}, status=202)

        try:
            prediction = replicate.predictions.cancel(prediction_id)
        except Exception as exc:
            logger.exception("Failed to cancel Replicate prediction: %s", exc)
            return Response({"error": "Failed to cancel prediction."}, status=500)
        finally:
            cache.delete(cache_key)
            cache.delete(cancel_key)

        return Response({"ok": True, "status": prediction.status})


class ExportInvoiceView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Google account not connected."}, status=401)

        # Get submission ID
        submission_id = request.data.get("submission_id")
        if not submission_id:
            return Response({"error": "Export requires an approved submission."}, status=400)

        # Get active membership
        membership = get_active_membership(request.user)
        if not membership:
            return Response({"error": "No active organization."}, status=400)

        # Find submission
        submission = InvoiceSubmission.objects.filter(
            id=submission_id,
            organization=membership.organization,
        ).first()
        if not submission:
            return Response({"error": "Submission not found."}, status=404)

        # Export using service
        try:
            spreadsheet_id, exported_at = InvoiceExportService.export_to_google_sheets(
                submission=submission,
                user=request.user,
                membership=membership,
            )

            return Response({
                "ok": True,
                "spreadsheet_id": spreadsheet_id,
                "exported_at": exported_at,
                "exported_by": request.user.email,
            })

        except SubmissionNotApprovedError as e:
            return Response({"error": str(e)}, status=400)
        except SubmissionAlreadyExportedError as e:
            return Response({"error": str(e)}, status=409)
        except ExportPermissionError as e:
            return Response({"error": str(e)}, status=403)
        except GoogleCredentialsError as e:
            return Response({"error": str(e)}, status=401)
        except MissingInvoiceDataError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as exc:
            logger.exception("Unexpected error in export view: %s", exc)
            return Response({"error": f"Google Sheets export failed: {exc}"}, status=500)


class InvoiceSubmissionListCreateView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required."}, status=401)

        membership = get_active_membership(request.user)
        if not membership:
            return Response({"error": "No active organization."}, status=400)
        if membership.role != OrganizationMembership.ROLE_ADMIN:
            return Response({"error": "Admin access required."}, status=403)

        submissions = (
            InvoiceSubmission.objects.select_related("submitted_by")
            .filter(organization=membership.organization, status=InvoiceSubmission.STATUS_PENDING)
            .order_by("-created_at")
        )

        return Response(
            {
                "submissions": [
                    {
                        "id": submission.id,
                        "submitted_by": submission.submitted_by.email,
                        "created_at": submission.created_at.isoformat(),
                    }
                    for submission in submissions
                ]
            }
        )

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required."}, status=401)

        # Parse invoice data
        invoice_payload = None
        if "invoice_data" in request.data:
            invoice_payload = request.data.get("invoice_data")
        elif "invoice" in request.data:
            invoice_payload = request.data.get("invoice")
        else:
            if request.FILES:
                return Response(
                    {"error": "Missing invoice_data for file upload."}, status=400
                )
            invoice_payload = request.data

        if isinstance(invoice_payload, str):
            try:
                invoice = json.loads(invoice_payload)
            except json.JSONDecodeError:
                return Response({"error": "Invalid invoice_data JSON."}, status=400)
        elif isinstance(invoice_payload, dict):
            invoice = invoice_payload
        else:
            invoice = None

        if not invoice:
            return Response({"error": "Missing invoice data."}, status=400)

        # Get active membership
        membership = get_active_membership(request.user)
        if not membership:
            return Response({"error": "No active organization."}, status=400)

        # Parse reviewer IDs
        reviewer_ids = []
        if hasattr(request.data, "getlist"):
            reviewer_ids = _parse_reviewer_ids(request.data.getlist("reviewer_ids"))
        if not reviewer_ids:
            reviewer_ids = _parse_reviewer_ids(request.data.get("reviewer_ids"))
        if not reviewer_ids:
            # Check if user is sole admin (no reviewers needed)
            admin_ids = list(
                OrganizationMembership.objects.filter(
                    organization=membership.organization,
                    role=OrganizationMembership.ROLE_ADMIN,
                ).values_list("user_id", flat=True)
            )
            if not (len(admin_ids) == 1 and admin_ids[0] == request.user.id):
                return Response({"error": "Select at least one reviewer."}, status=400)

        # Get file
        file_obj = request.FILES.get("invoice_file") or request.FILES.get("file")
        if not file_obj:
            return Response({"error": "Invoice PDF is required."}, status=400)

        # Create submission using service
        try:
            submission = InvoiceSubmissionService.create_submission(
                user=request.user,
                membership=membership,
                invoice_data=invoice,
                invoice_file=file_obj,
                reviewer_ids=reviewer_ids,
            )
            return Response({"ok": True, "id": submission.id}, status=201)

        except SelfAssignmentError as e:
            return Response({"error": str(e)}, status=400)
        except InvalidReviewerError as e:
            return Response({"error": str(e)}, status=400)
        except FileUploadError as e:
            return Response({"error": str(e)}, status=500)
        except Exception as exc:
            logger.exception("Unexpected error in submission creation: %s", exc)
            return Response({"error": "Internal error"}, status=500)


class InvoiceSubmissionDetailView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required."}, status=401)

        membership = get_active_membership(request.user)
        if not membership:
            return Response({"error": "No active organization."}, status=400)
        submission = InvoiceSubmission.objects.select_related("submitted_by").filter(
            id=submission_id,
            organization=membership.organization,
        ).first()
        if not submission:
            return Response({"error": "Submission not found."}, status=404)
        if (
            membership.role != OrganizationMembership.ROLE_ADMIN
            and submission.submitted_by_id != request.user.id
        ):
            return Response({"error": "Access denied."}, status=403)

        file_url = build_invoice_file_url(submission.invoice_file)

        comments = [
            {
                "id": comment.id,
                "message": comment.message,
                "created_at": comment.created_at.isoformat(),
                "author_email": comment.author.email if comment.author else None,
                "author_is_admin": comment.author_is_admin,
            }
            for comment in submission.comments.select_related("author").order_by("created_at")
        ]

        reviewers, review_summary, reviewer_status = _build_review_payload(submission, request.user)
        has_assignments = review_summary["total"] > 0
        export_locked = bool(submission.exported_at)
        if has_assignments:
            can_review = (
                submission.status in InvoiceSubmission.reviewable_statuses()
                and reviewer_status == InvoiceReviewAssignment.STATUS_PENDING
            )
            can_export = (
                not export_locked
                and submission.status == InvoiceSubmission.STATUS_APPROVED
                and (
                    reviewer_status == InvoiceReviewAssignment.STATUS_APPROVED
                    or membership.role == OrganizationMembership.ROLE_ADMIN
                )
            )
        else:
            can_review = (
                membership.role == OrganizationMembership.ROLE_ADMIN
                and submission.status in InvoiceSubmission.reviewable_statuses()
            )
            can_export = (
                not export_locked
                and membership.role == OrganizationMembership.ROLE_ADMIN
                and submission.status == InvoiceSubmission.STATUS_APPROVED
            )

        return Response(
            {
                "id": submission.id,
                "status": submission.status,
                "submitted_by": submission.submitted_by.email,
                "created_at": submission.created_at.isoformat(),
                "exported_at": submission.exported_at.isoformat()
                if submission.exported_at
                else None,
                "exported_by": submission.exported_by.email
                if submission.exported_by
                else None,
                "invoice_data": submission.invoice_data,
                "invoice_file_url": file_url,
                "comments": comments,
                "can_review": can_review,
                "can_export": can_export,
                "reviewers": reviewers,
                "review_summary": review_summary,
                "reviewer_status": reviewer_status,
            }
        )


class InvoiceSubmissionApproveView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required."}, status=401)

        # Check membership and admin role
        membership = get_active_membership(request.user)
        if not membership:
            return Response({"error": "No active organization."}, status=400)
        if membership.role != OrganizationMembership.ROLE_ADMIN:
            return Response({"error": "Admin access required."}, status=403)

        # Get submission ID
        submission_id = request.data.get("submission_id")
        if not submission_id:
            return Response({"error": "Submission id is required."}, status=400)

        # Find submission
        submission = InvoiceSubmission.objects.filter(
            id=submission_id,
            organization=membership.organization,
            status__in=InvoiceSubmission.reviewable_statuses(),
        ).first()
        if not submission:
            return Response({"error": "Submission not found."}, status=404)

        # Approve using service
        try:
            submission, review_payload = InvoiceReviewService.approve_submission(
                submission=submission,
                reviewer=request.user,
            )

            return Response({
                "ok": True,
                "status": submission.status,
                **review_payload,
            })

        except ReviewPermissionError as e:
            return Response({"error": str(e)}, status=403)
        except InvalidReviewActionError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as exc:
            logger.exception("Unexpected error in approve view: %s", exc)
            return Response({"error": "Internal error"}, status=500)


class InvoiceSubmissionRejectView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required."}, status=401)

        # Check membership and admin role
        membership = get_active_membership(request.user)
        if not membership:
            return Response({"error": "No active organization."}, status=400)
        if membership.role != OrganizationMembership.ROLE_ADMIN:
            return Response({"error": "Admin access required."}, status=403)

        # Get submission ID
        submission_id = request.data.get("submission_id")
        if not submission_id:
            return Response({"error": "Submission id is required."}, status=400)

        # Find submission
        submission = InvoiceSubmission.objects.filter(
            id=submission_id,
            organization=membership.organization,
            status__in=InvoiceSubmission.reviewable_statuses(),
        ).first()
        if not submission:
            return Response({"error": "Submission not found."}, status=404)

        # Reject using service
        try:
            submission, review_payload = InvoiceReviewService.reject_submission(
                submission=submission,
                reviewer=request.user,
            )

            return Response({
                "ok": True,
                "status": submission.status,
                **review_payload,
            })

        except ReviewPermissionError as e:
            return Response({"error": str(e)}, status=403)
        except InvalidReviewActionError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as exc:
            logger.exception("Unexpected error in reject view: %s", exc)
            return Response({"error": "Internal error"}, status=500)


class InvoiceSubmissionRequestEditView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required."}, status=401)

        # Check membership and admin role
        membership = get_active_membership(request.user)
        if not membership:
            return Response({"error": "No active organization."}, status=400)
        if membership.role != OrganizationMembership.ROLE_ADMIN:
            return Response({"error": "Admin access required."}, status=403)

        # Get submission ID and message
        submission_id = request.data.get("submission_id")
        message = (request.data.get("message") or "").strip()

        if not submission_id:
            return Response({"error": "Submission id is required."}, status=400)
        if not message:
            return Response({"error": "Commentary is required."}, status=400)

        # Find submission
        submission = InvoiceSubmission.objects.filter(
            id=submission_id,
            organization=membership.organization,
            status__in=InvoiceSubmission.reviewable_statuses(),
        ).first()
        if not submission:
            return Response({"error": "Submission not found."}, status=404)

        # Request changes using service
        try:
            submission, review_payload = InvoiceReviewService.request_changes(
                submission=submission,
                reviewer=request.user,
                comment_message=message,
            )

            return Response({
                "ok": True,
                "status": submission.status,
                **review_payload,
            })

        except ReviewPermissionError as e:
            return Response({"error": str(e)}, status=403)
        except InvalidReviewActionError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as exc:
            logger.exception("Unexpected error in request changes view: %s", exc)
            return Response({"error": "Internal error"}, status=500)


class InvoiceSubmissionAddReviewerView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required."}, status=401)

        # Check membership and admin role
        membership = get_active_membership(request.user)
        if not membership:
            return Response({"error": "No active organization."}, status=400)
        if membership.role != OrganizationMembership.ROLE_ADMIN:
            return Response({"error": "Admin access required."}, status=403)

        # Get submission ID and reviewer ID
        submission_id = request.data.get("submission_id")
        reviewer_id = request.data.get("reviewer_id")

        if not submission_id:
            return Response({"error": "Submission id is required."}, status=400)
        if not reviewer_id:
            return Response({"error": "Reviewer id is required."}, status=400)

        # Find submission
        submission = InvoiceSubmission.objects.filter(
            id=submission_id,
            organization=membership.organization,
        ).first()
        if not submission:
            return Response({"error": "Submission not found."}, status=404)

        # Validate submission status
        if submission.status not in {
            InvoiceSubmission.STATUS_PENDING,
            InvoiceSubmission.STATUS_APPROVED,
        }:
            return Response(
                {"error": "Reviewers can only be added to pending or approved submissions."},
                status=400,
            )

        # Add reviewer using service
        try:
            submission, review_payload, created = InvoiceReviewService.add_reviewer(
                submission=submission,
                reviewer_id=reviewer_id,
                assigned_by=request.user,
                organization=membership.organization,
            )

            return Response({
                "ok": True,
                "status": submission.status,
                "created": created,
                **review_payload,
            })

        except SelfAssignmentError as e:
            return Response({"error": str(e)}, status=400)
        except InvalidReviewerError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as exc:
            logger.exception("Unexpected error in add reviewer view: %s", exc)
            return Response({"error": "Internal error"}, status=500)


class InvoiceSubmissionResubmitView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required."}, status=401)

        # Get active membership
        membership = get_active_membership(request.user)
        if not membership:
            return Response({"error": "No active organization."}, status=400)

        # Get submission ID
        submission_id = request.data.get("submission_id")
        if not submission_id:
            return Response({"error": "Submission id is required."}, status=400)

        # Find submission
        submission = InvoiceSubmission.objects.filter(
            id=submission_id,
            organization=membership.organization,
            submitted_by=request.user,
            status__in=[InvoiceSubmission.STATUS_CHANGES_REQUESTED, InvoiceSubmission.STATUS_PENDING],
        ).first()
        if not submission:
            return Response({"error": "Submission not found."}, status=404)

        # Parse invoice data
        invoice_payload = None
        if "invoice_data" in request.data:
            invoice_payload = request.data.get("invoice_data")
        elif "invoice" in request.data:
            invoice_payload = request.data.get("invoice")
        else:
            invoice_payload = request.data

        if isinstance(invoice_payload, str):
            try:
                invoice = json.loads(invoice_payload)
            except json.JSONDecodeError:
                return Response({"error": "Invalid invoice_data JSON."}, status=400)
        elif isinstance(invoice_payload, dict):
            invoice = invoice_payload
        else:
            invoice = None

        if not invoice:
            return Response({"error": "Missing invoice data."}, status=400)

        # Get optional file and comment
        file_obj = request.FILES.get("invoice_file") or request.FILES.get("file")
        message = (request.data.get("message") or "").strip()

        # Resubmit using service
        try:
            InvoiceSubmissionService.resubmit_submission(
                submission=submission,
                invoice_data=invoice,
                invoice_file=file_obj,
                comment_message=message if message else None,
            )
            return Response({"ok": True})

        except FileUploadError as e:
            return Response({"error": str(e)}, status=500)
        except Exception as exc:
            logger.exception("Unexpected error in resubmit: %s", exc)
            return Response({"error": "Internal error"}, status=500)


class InvoiceSubmissionRequestListView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required."}, status=401)
        membership = get_active_membership(request.user)
        if not membership:
            return Response({"error": "No active organization."}, status=400)

        comments_qs = InvoiceSubmissionComment.objects.filter(
            submission=OuterRef("pk")
        ).order_by("-created_at")

        submissions = (
            InvoiceSubmission.objects.filter(
                organization=membership.organization,
                submitted_by=request.user,
                status=InvoiceSubmission.STATUS_CHANGES_REQUESTED,
            )
            .annotate(
                last_comment_message=Subquery(comments_qs.values("message")[:1]),
                last_comment_at=Subquery(comments_qs.values("created_at")[:1]),
                last_comment_by=Subquery(comments_qs.values("author__email")[:1]),
            )
            .order_by("-updated_at")
        )

        payload = []
        for submission in submissions:
            last_comment_at = getattr(submission, "last_comment_at", None)
            payload.append(
                {
                    "id": submission.id,
                    "created_at": submission.created_at.isoformat(),
                    "updated_at": submission.updated_at.isoformat(),
                    "last_comment": getattr(submission, "last_comment_message", None),
                    "last_comment_at": last_comment_at.isoformat() if last_comment_at else None,
                    "last_comment_by": getattr(submission, "last_comment_by", None),
                }
            )

        return Response({"submissions": payload})


class InvoiceSubmissionTableView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required."}, status=401)
        membership = get_active_membership(request.user)
        if not membership:
            return Response({"error": "No active organization."}, status=400)
        status_param = request.GET.get("status", "pending")
        submission_qs = InvoiceSubmission.objects.filter(organization=membership.organization)
        if membership.role != OrganizationMembership.ROLE_ADMIN:
            submission_qs = submission_qs.filter(submitted_by=request.user)
        if status_param:
            if status_param == "active":
                submission_qs = submission_qs.filter(
                    status__in=[
                        InvoiceSubmission.STATUS_PENDING,
                        InvoiceSubmission.STATUS_CHANGES_REQUESTED,
                    ]
                )
            elif status_param != "all":
                submission_qs = submission_qs.filter(status=status_param)

        comments_qs = InvoiceSubmissionComment.objects.filter(
            submission=OuterRef("pk")
        ).order_by("-created_at")

        submissions = (
            submission_qs.select_related("submitted_by")
            .annotate(
                last_comment_message=Subquery(comments_qs.values("message")[:1]),
                last_comment_at=Subquery(comments_qs.values("created_at")[:1]),
            )
            .order_by("-created_at")
        )

        payload = []
        for submission in submissions:
            invoice_number = None
            if submission.invoice_data:
                raw = submission.invoice_data.get("invoice_number")
                if isinstance(raw, dict):
                    invoice_number = raw.get("value")
                else:
                    invoice_number = raw
            payload.append(
                {
                    "id": submission.id,
                    "invoice_number": invoice_number,
                    "submitted_by": submission.submitted_by.email if submission.submitted_by else None,
                    "comment": submission.last_comment_message,
                    "created_at": submission.created_at.isoformat(),
                    "status": submission.status,
                }
            )

        return Response({"submissions": payload, "role": membership.role})


def invoices_page(request):
    context = build_header_context(request, "invoices")
    return render(request, "invoices.html", context)


class InvoiceSubmissionDeleteView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required."}, status=401)
        membership = get_active_membership(request.user)
        if not membership:
            return Response({"error": "No active organization."}, status=400)

        submission_id = request.data.get("submission_id")
        if not submission_id:
            return Response({"error": "Submission id is required."}, status=400)

        if membership.role == OrganizationMembership.ROLE_ADMIN:
            submission = InvoiceSubmission.objects.filter(
                id=submission_id,
                organization=membership.organization,
            ).first()
        else:
            submission = InvoiceSubmission.objects.filter(
                id=submission_id,
                organization=membership.organization,
                submitted_by=request.user,
                status__in=InvoiceSubmission.deletable_statuses(),
            ).first()
        if not submission:
            return Response({"error": "Submission not found."}, status=404)

        if submission.invoice_file:
            submission.invoice_file.delete(save=False)
        submission.delete()

        return Response({"ok": True})
