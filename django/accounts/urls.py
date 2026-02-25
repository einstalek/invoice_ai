from django.urls import path

from . import api, views


app_name = "accounts"

urlpatterns = [
    path("auth/google/", views.google_oauth_start, name="google_start"),
    path("auth/google/callback/", views.google_oauth_callback, name="google_callback"),
    path("auth/signup/", views.signup, name="signup"),
    path("auth/status/", api.AuthStatusView.as_view(), name="status"),
    path("auth/status", api.AuthStatusView.as_view(), name="status_noslash"),
    path("notifications", api.NotificationsView.as_view(), name="notifications"),
    path("notifications/", api.NotificationsView.as_view(), name="notifications_slash"),
    path("auth/google/disconnect/", api.GoogleDisconnectView.as_view(), name="google_disconnect"),
    path("auth/google/disconnect", api.GoogleDisconnectView.as_view(), name="google_disconnect_noslash"),
    path("auth/google/token/", api.GoogleTokenView.as_view(), name="google_token"),
    path("auth/google/token", api.GoogleTokenView.as_view(), name="google_token_noslash"),
    path("auth/theme/", api.ThemePreferenceView.as_view(), name="theme_preference"),
    path("auth/theme", api.ThemePreferenceView.as_view(), name="theme_preference_noslash"),
]
