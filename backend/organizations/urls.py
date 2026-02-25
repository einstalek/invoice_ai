from django.urls import path

from . import views

urlpatterns = [
    # Organizations
    path("", views.OrganizationListCreateView.as_view(), name="org_list_create"),
    path("<uuid:org_id>/", views.OrganizationDetailView.as_view(), name="org_detail"),

    # Members
    path("<uuid:org_id>/members/", views.MembershipListView.as_view(), name="member_list"),
    path("<uuid:org_id>/members/invite/", views.InviteMemberView.as_view(), name="member_invite"),
    path("<uuid:org_id>/members/accept/", views.AcceptInviteView.as_view(), name="member_accept"),
    path(
        "<uuid:org_id>/members/<uuid:member_id>/deactivate/",
        views.DeactivateMemberView.as_view(),
        name="member_deactivate",
    ),

    # Suppliers
    path("<uuid:org_id>/suppliers/", views.SupplierListCreateView.as_view(), name="supplier_list_create"),
    path("<uuid:org_id>/suppliers/<uuid:pk>/", views.SupplierDetailView.as_view(), name="supplier_detail"),

    # Google Sheets OAuth
    path("<uuid:org_id>/google-sheets/connect/", views.GoogleSheetsConnectView.as_view(), name="google_sheets_connect"),
    path("<uuid:org_id>/google-sheets/disconnect/", views.GoogleSheetsDisconnectView.as_view(), name="google_sheets_disconnect"),
]
