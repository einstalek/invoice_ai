import os
import logging

from django.contrib.auth import logout
from django.http import JsonResponse
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication

from accounts.models import UserPreference
from accounts.services import get_user_credentials
from google_sheets_utils import get_user_filled_row_count, get_user_spreadsheet_title
from organizations.models import OrganizationInvite, OrganizationMembership
from organizations.services import get_active_membership
from invoices.models import InvoiceSubmission, InvoiceSubmissionComment, InvoiceReviewAssignment
from django.db.models import OuterRef, Subquery

logger = logging.getLogger(__name__)


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


class AuthStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response(
                {
                    "authenticated": False,
                    "connected": False,
                    "google_connected": False,
                    "spreadsheet_id": None,
                    "spreadsheet_title": None,
                    "spreadsheet_rows": None,
                    "active_org": None,
                    "theme_preference": UserPreference.THEME_SYSTEM,
                }
            )

        cred = getattr(request.user, "google_credential", None)
        connected = bool(cred and cred.refresh_token)
        spreadsheet_title = None
        spreadsheet_rows = None
        active_org = None

        if connected and cred and cred.spreadsheet_id:
            credentials, _ = get_user_credentials(request.user)
            if credentials:
                try:
                    spreadsheet_title = get_user_spreadsheet_title(
                        credentials, cred.spreadsheet_id
                    )
                    worksheet_name = os.getenv("GOOGLE_SHEETS_WORKSHEET")
                    spreadsheet_rows = get_user_filled_row_count(
                        credentials, cred.spreadsheet_id, worksheet_name
                    )
                except Exception:
                    spreadsheet_title = None
                    spreadsheet_rows = None

        active_membership = (
            OrganizationMembership.objects.select_related("organization")
            .filter(user=request.user, is_active=True)
            .first()
        )
        if active_membership:
            active_org = {
                "id": active_membership.organization_id,
                "name": active_membership.organization.name,
                "role": active_membership.role,
            }

        preference = getattr(request.user, "preference", None)
        theme_preference = (
            preference.theme if preference else UserPreference.THEME_SYSTEM
        )

        return Response(
            {
                "authenticated": True,
                "user_id": request.user.id,
                "connected": connected,
                "google_connected": connected,
                "spreadsheet_id": cred.spreadsheet_id if cred else None,
                "spreadsheet_title": spreadsheet_title,
                "spreadsheet_rows": spreadsheet_rows,
                "google_email": request.user.email,
                "google_name": (
                    f"{request.user.first_name} {request.user.last_name}".strip() or None
                ),
                "google_given_name": request.user.first_name or None,
                "google_family_name": request.user.last_name or None,
                "active_org": active_org,
                "theme_preference": theme_preference,
            }
        )


class GoogleTokenView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Connect Google to continue."}, status=401)
        try:
            credentials, _ = get_user_credentials(request.user)
        except Exception as exc:
            logger.exception("Failed to load Google credentials for user %s: %s", request.user.id, exc)
            return Response({"error": "Google connection error. Please reconnect."}, status=401)
        if not credentials:
            return Response({"error": "Google connection expired. Please reconnect."}, status=401)
        return Response(
            {
                "access_token": credentials.token,
                "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
            }
        )


class GoogleDisconnectView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        if request.user.is_authenticated:
            if hasattr(request.user, "google_credential"):
                request.user.google_credential.delete()
            logout(request)
        return JsonResponse({"ok": True})


class ThemePreferenceView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        theme = (request.data.get("theme") or "").strip().lower()
        if theme not in (
            UserPreference.THEME_SYSTEM,
            UserPreference.THEME_LIGHT,
            UserPreference.THEME_DARK,
        ):
            return Response({"error": "Invalid theme."}, status=400)
        preference, _ = UserPreference.objects.update_or_create(
            user=request.user,
            defaults={"theme": theme},
        )
        return Response({"theme": preference.theme})


class NotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        email = (request.user.email or "").strip().lower()
        invites = []
        if email:
            invites = (
                OrganizationInvite.objects.select_related("organization", "invited_by")
                .filter(email__iexact=email, status=OrganizationInvite.STATUS_PENDING)
                .order_by("-created_at")
            )

        membership = get_active_membership(request.user)
        role = membership.role if membership else None
        invoice_mode = None
        invoices = []

        if membership:
            if role == OrganizationMembership.ROLE_ADMIN:
                invoice_mode = "approvals"
                invoices = (
                    InvoiceReviewAssignment.objects.select_related(
                        "submission", "submission__submitted_by"
                    )
                    .filter(
                        reviewer=request.user,
                        status=InvoiceReviewAssignment.STATUS_PENDING,
                        submission__organization=membership.organization,
                        submission__status=InvoiceSubmission.STATUS_PENDING,
                    )
                    .order_by("-submission__created_at")
                )
            else:
                invoice_mode = "requests"
                comments_qs = InvoiceSubmissionComment.objects.filter(
                    submission=OuterRef("pk")
                ).order_by("-created_at")
                invoices = (
                    InvoiceSubmission.objects.filter(
                        organization=membership.organization,
                        submitted_by=request.user,
                        status=InvoiceSubmission.STATUS_CHANGES_REQUESTED,
                    )
                    .annotate(
                        last_comment_message=Subquery(comments_qs.values("message")[:1]),
                        last_comment_at=Subquery(comments_qs.values("created_at")[:1]),
                    )
                    .order_by("-updated_at")
                )

        return Response(
            {
                "role": role,
                "invites": [
                    {
                        "id": invite.id,
                        "org_id": invite.organization_id,
                        "org_name": invite.organization.name,
                        "invited_by": invite.invited_by.email
                        if invite.invited_by
                        else None,
                        "created_at": invite.created_at.isoformat(),
                    }
                    for invite in invites
                ],
                "invoice_mode": invoice_mode,
                "invoices": [
                    {
                        "id": submission.submission.id
                        if isinstance(submission, InvoiceReviewAssignment)
                        else submission.id,
                        "submitted_by": (
                            submission.submission.submitted_by.email
                            if isinstance(submission, InvoiceReviewAssignment)
                            and getattr(submission.submission, "submitted_by", None)
                            else submission.submitted_by.email
                            if getattr(submission, "submitted_by", None)
                            else None
                        ),
                        "created_at": (
                            submission.submission.created_at.isoformat()
                            if isinstance(submission, InvoiceReviewAssignment)
                            else submission.created_at.isoformat()
                        ),
                        "updated_at": (
                            submission.submission.updated_at.isoformat()
                            if isinstance(submission, InvoiceReviewAssignment)
                            else submission.updated_at.isoformat()
                        ),
                        "last_comment": getattr(submission, "last_comment_message", None),
                        "last_comment_at": getattr(submission, "last_comment_at", None),
                    }
                    for submission in invoices
                ],
            }
        )
