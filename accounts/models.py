from django.conf import settings
from django.db import models


class GoogleCredential(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="google_credential",
    )
    refresh_token = models.TextField(null=True, blank=True)
    access_token = models.TextField(null=True, blank=True)
    token_uri = models.TextField(null=True, blank=True)
    client_id = models.TextField(null=True, blank=True)
    client_secret = models.TextField(null=True, blank=True)
    scopes = models.TextField(null=True, blank=True)
    expiry = models.DateTimeField(null=True, blank=True)
    spreadsheet_id = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"GoogleCredential(user={self.user_id})"


class UserPreference(models.Model):
    THEME_SYSTEM = "system"
    THEME_LIGHT = "light"
    THEME_DARK = "dark"
    THEME_CHOICES = [
        (THEME_SYSTEM, "System"),
        (THEME_LIGHT, "Light"),
        (THEME_DARK, "Dark"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preference",
    )
    theme = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default=THEME_SYSTEM,
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"UserPreference(user={self.user_id}, theme={self.theme})"
