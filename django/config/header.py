import os
from typing import Dict, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest

from organizations.models import OrganizationMembership


def _get_initials(given_name: str, family_name: str, full_name: str, email: str) -> str:
    if given_name and family_name:
        return (given_name[0] + family_name[0]).upper()
    if full_name:
        parts = [p for p in full_name.strip().split() if p]
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        if len(parts) == 1:
            return parts[0][:2].upper()
    if email:
        handle = email.split("@", 1)[0]
        parts = [p for p in handle.replace("-", " ").replace("_", " ").replace(".", " ").split() if p]
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        if len(parts) == 1:
            return parts[0][:2].upper()
    return ""


def build_header_context(request: HttpRequest, active_page: str) -> Dict[str, Optional[str]]:
    user = request.user
    is_authenticated = bool(user and user.is_authenticated)
    active_org = None
    if is_authenticated:
        membership = (
            OrganizationMembership.objects.select_related("organization")
            .filter(user=user, is_active=True)
            .first()
        )
        if membership:
            active_org = membership.organization

    google_connected = False
    if is_authenticated and hasattr(user, "google_credential"):
        google_connected = bool(user.google_credential.refresh_token)

    first_name = user.first_name if is_authenticated else ""
    last_name = user.last_name if is_authenticated else ""
    full_name = f"{first_name} {last_name}".strip() if is_authenticated else ""
    email = user.email if is_authenticated else ""

    return {
        "header_active_page": active_page,
        "header_is_authenticated": is_authenticated,
        "header_show_login": not is_authenticated,
        "header_show_account": is_authenticated,
        "header_show_org": is_authenticated,
        "header_show_notifications": is_authenticated,
        "header_google_permission_note": is_authenticated and not google_connected,
        "header_account_email": email,
        "header_account_initials": _get_initials(first_name, last_name, full_name, email),
        "header_org_name": "org",
        "header_active_org_name": active_org.name if active_org else "",
    }


def build_index_context(request: HttpRequest) -> Dict[str, Optional[str]]:
    context = build_header_context(request, "extractor")
    context.update(
        {
            "google_api_key": os.getenv("GOOGLE_API_KEY", ""),
            "google_client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        }
    )
    return context
