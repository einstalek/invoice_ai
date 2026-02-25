from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from organizations.models import OrganizationMembership
from .serializers import UserSerializer


class GoogleLoginView(SocialLoginView):
    """
    POST /api/auth/google/

    Accepts {"access_token": "..."} or {"code": "..."} from the frontend
    after the user completes Google OAuth consent. Returns JWT token pair.
    """

    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = "postmessage"  # For popup-based flow in React SPA


class UserProfileView(RetrieveUpdateAPIView):
    """
    GET  /api/auth/me/  — current user profile
    PATCH /api/auth/me/ — update full_name
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer(self, *args, **kwargs):
        # Allow partial updates
        kwargs["partial"] = True
        return super().get_serializer(*args, **kwargs)


class UserMembershipsView(APIView):
    """
    GET /api/auth/me/memberships/ — list orgs the current user belongs to.
    Lightweight endpoint so the frontend knows which orgs to show.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        memberships = request.user.memberships.filter(
            status="ACTIVE"
        ).select_related("organization")
        data = [
            {
                "id": str(m.id),
                "organization": {
                    "id": str(m.organization.id),
                    "name": m.organization.name,
                },
                "role": m.role,
            }
            for m in memberships
        ]
        return Response(data, status=status.HTTP_200_OK)


class UserPendingInvitesView(APIView):
    """
    GET /api/auth/me/pending-invites/ — list pending org invites for the current user.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        invites = OrganizationMembership.objects.filter(
            invited_email=request.user.email,
            status=OrganizationMembership.Status.PENDING,
        ).select_related("organization")
        data = [
            {
                "id": str(inv.id),
                "organization": {
                    "id": str(inv.organization.id),
                    "name": inv.organization.name,
                },
                "role": inv.role,
                "created_at": inv.created_at.isoformat(),
            }
            for inv in invites
        ]
        return Response(data, status=status.HTTP_200_OK)
