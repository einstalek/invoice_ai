"""
DRF permission classes for invoice views.

Provides reusable permission checks to replace repeated manual auth logic.
"""

from rest_framework.permissions import BasePermission

from organizations.models import OrganizationMembership
from organizations.services import get_active_membership


class HasActiveMembership(BasePermission):
    """
    Permission check: User must have an active organization membership.

    This replaces manual checks for:
        membership = get_active_membership(request.user)
        if not membership:
            return Response({"error": "No active organization."}, status=400)
    """

    message = "No active organization membership."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        membership = get_active_membership(request.user)
        return membership is not None


class IsAdmin(BasePermission):
    """
    Permission check: User must be an admin in their active organization.

    This replaces manual checks for:
        membership = get_active_membership(request.user)
        if not membership:
            return Response({"error": "No active organization."}, status=400)
        if membership.role != OrganizationMembership.ROLE_ADMIN:
            return Response({"error": "Admin access required."}, status=403)

    Note: This permission should be used WITH IsAuthenticated and HasActiveMembership.
    """

    message = "Admin access required."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        membership = get_active_membership(request.user)
        if not membership:
            return False

        return membership.role == OrganizationMembership.ROLE_ADMIN
