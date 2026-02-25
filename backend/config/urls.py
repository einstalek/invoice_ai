from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth: login/logout/password, JWT token refresh
    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),
    # Auth: Google OAuth, user profile, memberships
    path("api/auth/", include("accounts.urls")),

    # Core API
    path("api/orgs/", include("organizations.urls")),
    path("api/orgs/<uuid:org_id>/invoices/", include("invoices.urls")),
    path("api/notifications/", include("notifications.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
