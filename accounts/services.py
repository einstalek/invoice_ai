import json
import logging
from datetime import timezone as dt_timezone
from typing import Optional, Tuple

from django.utils import timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError

from .models import GoogleCredential

logger = logging.getLogger(__name__)

def _to_google_expiry(expiry):
    if not expiry:
        return None
    if timezone.is_aware(expiry):
        expiry = expiry.astimezone(dt_timezone.utc).replace(tzinfo=None)
    return expiry


def _to_db_expiry(expiry):
    if not expiry:
        return None
    if timezone.is_naive(expiry):
        return timezone.make_aware(expiry, timezone=dt_timezone.utc)
    return expiry


def build_user_credentials(cred: GoogleCredential) -> Credentials:
    scopes = json.loads(cred.scopes or "[]")
    return Credentials(
        token=cred.access_token,
        refresh_token=cred.refresh_token,
        token_uri=cred.token_uri,
        client_id=cred.client_id,
        client_secret=cred.client_secret,
        scopes=scopes,
        expiry=_to_google_expiry(cred.expiry),
    )


def get_user_credentials(user) -> Tuple[Optional[Credentials], Optional[str]]:
    cred = getattr(user, "google_credential", None)
    if not cred or not cred.refresh_token:
        return None, None
    credentials = build_user_credentials(cred)
    if credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
        except RefreshError as exc:
            logger.warning("Google token refresh failed for user %s: %s", user.id, exc)
            message = str(exc)
            if "invalid_grant" in message or "revoked" in message:
                cred.access_token = None
                cred.refresh_token = None
                cred.expiry = None
                cred.save(update_fields=["access_token", "refresh_token", "expiry", "updated_at"])
            return None, None
        cred.access_token = credentials.token
        cred.refresh_token = credentials.refresh_token
        cred.expiry = _to_db_expiry(credentials.expiry)
        cred.save(update_fields=["access_token", "refresh_token", "expiry", "updated_at"])
    return credentials, cred.spreadsheet_id


def set_user_spreadsheet_id(user, spreadsheet_id: str) -> None:
    cred = getattr(user, "google_credential", None)
    if not cred:
        return
    cred.spreadsheet_id = spreadsheet_id
    cred.save(update_fields=["spreadsheet_id", "updated_at"])
