from django.urls import path

from . import api


app_name = "organizations"

urlpatterns = [
    path("orgs", api.OrganizationListCreateView.as_view(), name="org_list_create"),
    path("orgs/activate", api.OrganizationActivateView.as_view(), name="org_activate"),
    path("orgs/invites", api.OrganizationInviteListView.as_view(), name="org_invites"),
    path(
        "orgs/invites/accept",
        api.OrganizationInviteAcceptView.as_view(),
        name="org_invite_accept",
    ),
    path(
        "orgs/invites/decline",
        api.OrganizationInviteDeclineView.as_view(),
        name="org_invite_decline",
    ),
    path("orgs/invites/create", api.OrganizationInviteCreateView.as_view(), name="org_invite_create"),
    path("orgs/info", api.OrganizationInfoView.as_view(), name="org_info"),
    path("orgs/members", api.OrganizationMembersView.as_view(), name="org_members"),
    path("orgs/members/remove", api.OrganizationMemberRemoveView.as_view(), name="org_member_remove"),
    path("orgs/members/promote", api.OrganizationMemberPromoteView.as_view(), name="org_member_promote"),
]
