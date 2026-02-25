from rest_framework.permissions import BasePermission

from organizations.models import OrganizationMembership


class IsOrgMember(BasePermission):
    """
    Allows access if the user has an ACTIVE membership in the organization
    identified by the `org_id` URL kwarg.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        org_id = view.kwargs.get("org_id")
        if not org_id:
            return False
        return OrganizationMembership.objects.filter(
            user=request.user,
            organization_id=org_id,
            status=OrganizationMembership.Status.ACTIVE,
        ).exists()


class IsOrgOwner(BasePermission):
    """
    Allows access only if the user is an ACTIVE OWNER in the organization
    identified by the `org_id` URL kwarg.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        org_id = view.kwargs.get("org_id")
        if not org_id:
            return False
        return OrganizationMembership.objects.filter(
            user=request.user,
            organization_id=org_id,
            status=OrganizationMembership.Status.ACTIVE,
            role=OrganizationMembership.Role.OWNER,
        ).exists()


class IsOrgOwnerOrReadOnly(BasePermission):
    """
    Owners can do anything; members can only read (GET/HEAD/OPTIONS).
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        org_id = view.kwargs.get("org_id")
        if not org_id:
            return False

        membership = OrganizationMembership.objects.filter(
            user=request.user,
            organization_id=org_id,
            status=OrganizationMembership.Status.ACTIVE,
        ).first()

        if not membership:
            return False

        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True

        return membership.role == OrganizationMembership.Role.OWNER
