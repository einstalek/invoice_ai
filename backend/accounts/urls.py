from django.urls import path

from .views import GoogleLoginView, UserProfileView, UserMembershipsView, UserPendingInvitesView

urlpatterns = [
    path("google/", GoogleLoginView.as_view(), name="google_login"),
    path("me/", UserProfileView.as_view(), name="user_profile"),
    path("me/memberships/", UserMembershipsView.as_view(), name="user_memberships"),
    path("me/pending-invites/", UserPendingInvitesView.as_view(), name="user_pending_invites"),
]
