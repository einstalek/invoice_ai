import logging

import requests as http_requests
from django.conf import settings as django_settings
from django.db import IntegrityError
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsOrgMember, IsOrgOwner, IsOrgOwnerOrReadOnly
from accounts.models import User
from notifications.models import Notification
from .models import Organization, OrganizationMembership, Supplier
from .serializers import (
    OrganizationSerializer,
    OrganizationCreateSerializer,
    MembershipSerializer,
    InviteMemberSerializer,
    SupplierSerializer,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Organization
# ---------------------------------------------------------------------------
class OrganizationListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/orgs/         — list orgs the user belongs to
    POST /api/orgs/         — create a new org (user becomes OWNER)
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrganizationCreateSerializer
        return OrganizationSerializer

    def get_queryset(self):
        return Organization.objects.filter(
            memberships__user=self.request.user,
            memberships__status=OrganizationMembership.Status.ACTIVE,
        ).distinct()

    def perform_create(self, serializer):
        org = serializer.save()
        OrganizationMembership.objects.create(
            user=self.request.user,
            organization=org,
            role=OrganizationMembership.Role.OWNER,
            status=OrganizationMembership.Status.ACTIVE,
            invited_email=self.request.user.email,
        )


class OrganizationDetailView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/orgs/<org_id>/   — org details (any member)
    PATCH /api/orgs/<org_id>/   — update org settings (owner only)
    """

    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsOrgOwnerOrReadOnly]
    lookup_url_kwarg = "org_id"

    def get_queryset(self):
        return Organization.objects.all()


# ---------------------------------------------------------------------------
# Membership
# ---------------------------------------------------------------------------
class MembershipListView(generics.ListAPIView):
    """
    GET /api/orgs/<org_id>/members/ — list all memberships for this org
    """

    serializer_class = MembershipSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]

    def get_queryset(self):
        return OrganizationMembership.objects.filter(
            organization_id=self.kwargs["org_id"],
        ).select_related("user").order_by("created_at")


class InviteMemberView(APIView):
    """
    POST /api/orgs/<org_id>/members/invite/
    Body: {"email": "...", "role": "ACCOUNTANT"}

    Creates a PENDING membership. If the user already exists on the platform,
    links them immediately. Creates a notification for the invitee.
    """

    permission_classes = [IsAuthenticated, IsOrgOwner]

    def post(self, request, org_id):
        serializer = InviteMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        role = serializer.validated_data["role"]

        org = Organization.objects.get(pk=org_id)
        existing_user = User.objects.filter(email=email).first()

        try:
            membership = OrganizationMembership.objects.create(
                user=existing_user,
                organization=org,
                role=role,
                status=OrganizationMembership.Status.PENDING,
                invited_email=email,
                invited_by=request.user,
            )
        except IntegrityError:
            return Response(
                {"detail": "This email has already been invited to this organization."},
                status=status.HTTP_409_CONFLICT,
            )

        # Create notification for existing user
        if existing_user:
            Notification.objects.create(
                user=existing_user,
                organization=org,
                type=Notification.Type.INVITE_RECEIVED,
                title=f"You've been invited to join {org.name}",
            )

        return Response(
            MembershipSerializer(membership).data,
            status=status.HTTP_201_CREATED,
        )


class AcceptInviteView(APIView):
    """
    POST /api/orgs/<org_id>/members/accept/

    Current user accepts a pending invite to this org.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, org_id):
        membership = OrganizationMembership.objects.filter(
            organization_id=org_id,
            invited_email=request.user.email,
            status=OrganizationMembership.Status.PENDING,
        ).first()

        if not membership:
            return Response(
                {"detail": "No pending invite found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        membership.user = request.user
        membership.status = OrganizationMembership.Status.ACTIVE
        membership.save(update_fields=["user", "status"])

        return Response(MembershipSerializer(membership).data)


class DeactivateMemberView(APIView):
    """
    POST /api/orgs/<org_id>/members/<member_id>/deactivate/

    Owner deactivates a membership.
    """

    permission_classes = [IsAuthenticated, IsOrgOwner]

    def post(self, request, org_id, member_id):
        membership = OrganizationMembership.objects.filter(
            pk=member_id, organization_id=org_id,
        ).first()

        if not membership:
            return Response(
                {"detail": "Membership not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if membership.user == request.user:
            return Response(
                {"detail": "You cannot deactivate yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        membership.status = OrganizationMembership.Status.DEACTIVATED
        membership.save(update_fields=["status"])
        return Response(MembershipSerializer(membership).data)


# ---------------------------------------------------------------------------
# Supplier
# ---------------------------------------------------------------------------
class SupplierListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/orgs/<org_id>/suppliers/    — list suppliers
    POST /api/orgs/<org_id>/suppliers/    — create supplier
    """

    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]

    def get_queryset(self):
        return Supplier.objects.filter(
            organization_id=self.kwargs["org_id"]
        ).order_by("name")

    def perform_create(self, serializer):
        serializer.save(organization_id=self.kwargs["org_id"])


class SupplierDetailView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/orgs/<org_id>/suppliers/<pk>/   — supplier detail
    PATCH /api/orgs/<org_id>/suppliers/<pk>/   — update supplier
    """

    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]

    def get_queryset(self):
        return Supplier.objects.filter(organization_id=self.kwargs["org_id"])


# ---------------------------------------------------------------------------
# Google Sheets OAuth
# ---------------------------------------------------------------------------
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


class GoogleSheetsConnectView(APIView):
    """
    POST /api/orgs/<org_id>/google-sheets/connect/
    Body: {"code": "<auth_code_from_frontend>"}

    Exchanges a Google authorization code for access + refresh tokens
    and stores them in the organization's erp_config.
    """

    permission_classes = [IsAuthenticated, IsOrgOwner]

    def post(self, request, org_id):
        code = request.data.get("code")
        if not code:
            return Response(
                {"detail": "Authorization code is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        client_id = django_settings.GOOGLE_CLIENT_ID
        client_secret = django_settings.GOOGLE_CLIENT_SECRET
        if not client_id or not client_secret:
            return Response(
                {"detail": "Google OAuth is not configured on the server."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Exchange auth code for tokens
        token_response = http_requests.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": "postmessage",
                "grant_type": "authorization_code",
            },
            timeout=15,
        )

        if token_response.status_code != 200:
            logger.error(
                "Google token exchange failed: %s %s",
                token_response.status_code,
                token_response.text,
            )
            return Response(
                {"detail": "Failed to exchange authorization code with Google."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token_data = token_response.json()

        org = Organization.objects.get(pk=org_id)
        erp_config = org.erp_config or {}

        erp_config["google_credentials"] = {
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token", ""),
            "token_uri": GOOGLE_TOKEN_URL,
            "client_id": client_id,
            "client_secret": client_secret,
        }

        org.erp_config = erp_config
        org.erp_type = Organization.ErpType.GOOGLE_SHEETS
        org.save(update_fields=["erp_config", "erp_type"])

        return Response({"connected": True})


class GoogleSheetsDisconnectView(APIView):
    """
    POST /api/orgs/<org_id>/google-sheets/disconnect/

    Clears Google OAuth credentials from erp_config and resets erp_type.
    """

    permission_classes = [IsAuthenticated, IsOrgOwner]

    def post(self, request, org_id):
        org = Organization.objects.get(pk=org_id)
        erp_config = org.erp_config or {}

        erp_config.pop("google_credentials", None)

        org.erp_config = erp_config
        org.erp_type = Organization.ErpType.NONE
        org.save(update_fields=["erp_config", "erp_type"])

        return Response({"connected": False})
