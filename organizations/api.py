from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Organization, OrganizationInvite, OrganizationMembership
from .services import get_active_membership


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


class OrganizationListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        memberships = (
            OrganizationMembership.objects.select_related("organization")
            .filter(user=request.user)
            .order_by("organization__name")
        )
        active_membership = next((m for m in memberships if m.is_active), None)
        return Response(
            {
                "organizations": [
                    {
                        "id": membership.organization_id,
                        "name": membership.organization.name,
                        "role": membership.role,
                        "is_active": membership.is_active,
                    }
                    for membership in memberships
                ],
                "active_org": {
                    "id": active_membership.organization_id,
                    "name": active_membership.organization.name,
                    "role": active_membership.role,
                }
                if active_membership
                else None,
            }
        )

    def post(self, request):
        name = (request.data.get("name") or "").strip()
        if not name:
            return Response({"error": "Organization name is required."}, status=400)

        invite_emails = request.data.get("invite_emails") or []
        if isinstance(invite_emails, str):
            invite_emails = [invite_emails]
        if not isinstance(invite_emails, list):
            invite_emails = []

        normalized_emails = []
        invalid_emails = []
        for raw_email in invite_emails:
            if not isinstance(raw_email, str):
                continue
            email = raw_email.strip().lower()
            if not email:
                continue
            try:
                validate_email(email)
            except ValidationError:
                invalid_emails.append(raw_email)
                continue
            if request.user.email and email == request.user.email.lower():
                continue
            normalized_emails.append(email)

        if invalid_emails:
            return Response(
                {"error": "Invalid invite emails.", "invalid_emails": invalid_emails},
                status=400,
            )

        try:
            with transaction.atomic():
                org = Organization.objects.create(name=name, created_by=request.user)
                OrganizationMembership.objects.filter(
                    user=request.user, is_active=True
                ).update(is_active=False)
                OrganizationMembership.objects.create(
                    user=request.user,
                    organization=org,
                    role=OrganizationMembership.ROLE_ADMIN,
                    is_active=True,
                )
                for email in sorted(set(normalized_emails)):
                    try:
                        OrganizationInvite.objects.create(
                            organization=org,
                            email=email,
                            invited_by=request.user,
                        )
                    except IntegrityError:
                        continue
        except IntegrityError:
            return Response({"error": "Organization name already exists."}, status=400)

        return Response(
            {
                "id": org.id,
                "name": org.name,
                "active": True,
            },
            status=201,
        )


class OrganizationActivateView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        org_id = request.data.get("org_id")
        if not org_id:
            return Response({"error": "Organization id is required."}, status=400)

        membership = get_object_or_404(
            OrganizationMembership,
            user=request.user,
            organization_id=org_id,
        )

        with transaction.atomic():
            OrganizationMembership.objects.filter(
                user=request.user, is_active=True
            ).exclude(id=membership.id).update(is_active=False)
            if not membership.is_active:
                membership.is_active = True
                membership.save(update_fields=["is_active"])

        return Response(
            {
                "id": membership.organization_id,
                "name": membership.organization.name,
                "active": True,
            }
        )


class OrganizationInviteListView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        email = (request.user.email or "").strip().lower()
        if not email:
            return Response({"invites": []})
        invites = (
            OrganizationInvite.objects.select_related("organization", "invited_by")
            .filter(email__iexact=email, status=OrganizationInvite.STATUS_PENDING)
            .order_by("-created_at")
        )
        return Response(
            {
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
                ]
            }
        )


class OrganizationInviteAcceptView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        invite_id = request.data.get("invite_id")
        if not invite_id:
            return Response({"error": "Invite id is required."}, status=400)

        invite = get_object_or_404(
            OrganizationInvite,
            id=invite_id,
            status=OrganizationInvite.STATUS_PENDING,
            email__iexact=request.user.email or "",
        )

        with transaction.atomic():
            invite.status = OrganizationInvite.STATUS_ACCEPTED
            invite.save(update_fields=["status"])

            membership, _ = OrganizationMembership.objects.get_or_create(
                user=request.user,
                organization=invite.organization,
                defaults={
                    "role": OrganizationMembership.ROLE_MEMBER,
                    "is_active": False,
                },
            )

            has_active = OrganizationMembership.objects.filter(
                user=request.user, is_active=True
            ).exists()
            if not has_active and not membership.is_active:
                membership.is_active = True
                membership.save(update_fields=["is_active"])

        return Response(
            {
                "id": invite.organization_id,
                "name": invite.organization.name,
                "active": membership.is_active,
            }
        )


class OrganizationInviteDeclineView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        invite_id = request.data.get("invite_id")
        if not invite_id:
            return Response({"error": "Invite id is required."}, status=400)

        invite = get_object_or_404(
            OrganizationInvite,
            id=invite_id,
            status=OrganizationInvite.STATUS_PENDING,
            email__iexact=request.user.email or "",
        )
        invite.status = OrganizationInvite.STATUS_DECLINED
        invite.save(update_fields=["status"])
        return Response({"ok": True})


class OrganizationInfoView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        membership = get_active_membership(request.user)
        if not membership:
            return Response({})

        org = membership.organization
        admins = (
            OrganizationMembership.objects.select_related("user")
            .filter(organization=org, role=OrganizationMembership.ROLE_ADMIN)
            .order_by("user__email")
        )
        member_count = OrganizationMembership.objects.filter(organization=org).count()

        return Response(
            {
                "id": org.id,
                "name": org.name,
                "role": membership.role,
                "role_label": membership.get_role_display(),
                "admins": [
                    {
                        "id": admin.user_id,
                        "email": admin.user.email,
                    }
                    for admin in admins
                ],
                "member_count": member_count,
            }
        )


class OrganizationMembersView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        membership = get_active_membership(request.user)
        if not membership:
            return Response({"error": "No active organization."}, status=400)
        if membership.role != OrganizationMembership.ROLE_ADMIN:
            return Response({"error": "Admin access required."}, status=403)

        members = (
            OrganizationMembership.objects.select_related("user")
            .filter(organization=membership.organization)
            .order_by("user__email")
        )

        return Response(
            {
                "org": {
                    "id": membership.organization_id,
                    "name": membership.organization.name,
                },
                "members": [
                    {
                        "membership_id": member.id,
                        "email": member.user.email,
                        "role": member.role,
                        "is_self": member.user_id == request.user.id,
                    }
                    for member in members
                ],
                "member_count": members.count(),
            }
        )


class OrganizationMemberRemoveView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        membership = get_active_membership(request.user)
        if not membership:
            return Response({"error": "No active organization."}, status=400)
        if membership.role != OrganizationMembership.ROLE_ADMIN:
            return Response({"error": "Admin access required."}, status=403)

        membership_id = request.data.get("membership_id")
        if not membership_id:
            return Response({"error": "Membership id is required."}, status=400)

        target = get_object_or_404(
            OrganizationMembership,
            id=membership_id,
            organization=membership.organization,
        )
        if target.user_id == request.user.id:
            return Response({"error": "You cannot remove yourself."}, status=400)
        if target.role == OrganizationMembership.ROLE_ADMIN:
            admin_count = OrganizationMembership.objects.filter(
                organization=membership.organization,
                role=OrganizationMembership.ROLE_ADMIN,
            ).count()
            if admin_count <= 1:
                return Response({"error": "At least one admin is required."}, status=400)

        target.delete()
        return Response({"ok": True})


class OrganizationMemberPromoteView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        membership = get_active_membership(request.user)
        if not membership:
            return Response({"error": "No active organization."}, status=400)
        if membership.role != OrganizationMembership.ROLE_ADMIN:
            return Response({"error": "Admin access required."}, status=403)

        membership_id = request.data.get("membership_id")
        if not membership_id:
            return Response({"error": "Membership id is required."}, status=400)

        target = get_object_or_404(
            OrganizationMembership,
            id=membership_id,
            organization=membership.organization,
        )
        if target.role == OrganizationMembership.ROLE_ADMIN:
            return Response({"ok": True})

        target.role = OrganizationMembership.ROLE_ADMIN
        target.save(update_fields=["role"])
        return Response({"ok": True})


class OrganizationInviteCreateView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        membership = get_active_membership(request.user)
        if not membership:
            return Response({"error": "No active organization."}, status=400)
        if membership.role != OrganizationMembership.ROLE_ADMIN:
            return Response({"error": "Admin access required."}, status=403)

        invite_emails = request.data.get("invite_emails") or []
        if isinstance(invite_emails, str):
            invite_emails = [invite_emails]
        if not isinstance(invite_emails, list):
            invite_emails = []

        normalized_emails = []
        invalid_emails = []
        for raw_email in invite_emails:
            if not isinstance(raw_email, str):
                continue
            email = raw_email.strip().lower()
            if not email:
                continue
            try:
                validate_email(email)
            except ValidationError:
                invalid_emails.append(raw_email)
                continue
            if request.user.email and email == request.user.email.lower():
                continue
            normalized_emails.append(email)

        if invalid_emails:
            return Response(
                {"error": "Invalid invite emails.", "invalid_emails": invalid_emails},
                status=400,
            )

        created = 0
        skipped = 0
        with transaction.atomic():
            for email in sorted(set(normalized_emails)):
                if OrganizationMembership.objects.filter(
                    organization=membership.organization, user__email__iexact=email
                ).exists():
                    skipped += 1
                    continue
                try:
                    OrganizationInvite.objects.create(
                        organization=membership.organization,
                        email=email,
                        invited_by=request.user,
                    )
                    created += 1
                except IntegrityError:
                    skipped += 1

        return Response({"created": created, "skipped": skipped})
