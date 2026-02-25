import json
import os
from datetime import timezone as dt_timezone

from django.contrib.auth import get_user_model, login
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from google.auth.transport.requests import Request
from google.oauth2 import id_token as google_id_token
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from google_sheets_utils import OAUTH_SCOPES
from .forms import SignUpForm
from .models import GoogleCredential


def _build_flow(request) -> Flow:
    redirect_uri = request.build_absolute_uri(reverse("accounts:google_callback"))
    secret_json = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET_JSON")
    if secret_json:
        try:
            client_config = json.loads(secret_json)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Invalid GOOGLE_OAUTH_CLIENT_SECRET_JSON.") from exc
        return Flow.from_client_config(
            client_config,
            scopes=OAUTH_SCOPES,
            redirect_uri=redirect_uri,
        )
    client_secret_file = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET_FILE")
    if not client_secret_file:
        raise RuntimeError("Missing GOOGLE_OAUTH_CLIENT_SECRET_FILE.")
    return Flow.from_client_secrets_file(
        client_secret_file,
        scopes=OAUTH_SCOPES,
        redirect_uri=redirect_uri,
    )


def _get_or_create_user(id_info: dict):
    email = id_info.get("email")
    if not email:
        raise RuntimeError("Missing email from Google id_token.")
    given_name = id_info.get("given_name") or ""
    family_name = id_info.get("family_name") or ""

    user_model = get_user_model()
    user = user_model.objects.filter(email=email).first()
    if not user:
        user = user_model.objects.filter(username=email).first()
    if not user:
        user = user_model.objects.create_user(
            username=email,
            email=email,
            first_name=given_name,
            last_name=family_name,
            password=None,
        )
        user.set_unusable_password()
        user.save(update_fields=["password"])
    else:
        updates = {}
        if given_name and not user.first_name:
            updates["first_name"] = given_name
        if family_name and not user.last_name:
            updates["last_name"] = family_name
        if updates:
            user_model.objects.filter(id=user.id).update(**updates)
    return user


def _save_credentials(user, credentials: Credentials) -> GoogleCredential:
    cred, _ = GoogleCredential.objects.get_or_create(user=user)
    refresh_token = credentials.refresh_token or cred.refresh_token
    expiry = credentials.expiry
    if expiry and timezone.is_naive(expiry):
        expiry = timezone.make_aware(expiry, timezone=dt_timezone.utc)
    scopes = json.dumps(list(credentials.scopes) if credentials.scopes else [])
    cred.refresh_token = refresh_token
    cred.access_token = credentials.token
    cred.token_uri = credentials.token_uri
    cred.client_id = credentials.client_id
    cred.client_secret = credentials.client_secret
    cred.scopes = scopes
    cred.expiry = expiry
    cred.save()
    return cred


@csrf_exempt
def google_oauth_start(request):
    try:
        flow = _build_flow(request)
    except RuntimeError as exc:
        return HttpResponseBadRequest(str(exc))
    next_url = request.GET.get("next")
    if next_url:
        request.session["post_auth_redirect"] = next_url
    else:
        request.session.pop("post_auth_redirect", None)
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    request.session["oauth_state"] = state
    return redirect(authorization_url)


@csrf_exempt
def google_oauth_callback(request):
    if request.GET.get("error"):
        return redirect("/")
    try:
        flow = _build_flow(request)
        flow.state = request.session.get("oauth_state")
        flow.fetch_token(authorization_response=request.build_absolute_uri())
    except Exception as exc:
        return HttpResponseBadRequest(str(exc))

    credentials = flow.credentials
    try:
        id_info = google_id_token.verify_oauth2_token(
            credentials.id_token,
            Request(),
            credentials.client_id,
        )
    except Exception as exc:
        return HttpResponseBadRequest(str(exc))

    user = _get_or_create_user(id_info)
    login(request, user)
    _save_credentials(user, credentials)
    redirect_to = request.session.pop("post_auth_redirect", "/")
    if (
        not isinstance(redirect_to, str)
        or not redirect_to.startswith("/")
        or redirect_to.startswith("//")
    ):
        redirect_to = "/"
    return redirect(redirect_to)


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/")
    else:
        form = SignUpForm()
    return render(request, "registration/signup.html", {"form": form})
