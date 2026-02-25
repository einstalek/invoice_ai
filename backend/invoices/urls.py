from django.urls import path

from . import views

urlpatterns = [
    path("", views.InvoiceListView.as_view(), name="invoice_list"),
    path("upload/", views.InvoiceUploadView.as_view(), name="invoice_upload"),
    path("<uuid:pk>/", views.InvoiceDetailView.as_view(), name="invoice_detail"),
    path("<uuid:pk>/edit/", views.InvoiceEditView.as_view(), name="invoice_edit"),
    path("<uuid:pk>/approve/", views.InvoiceApproveView.as_view(), name="invoice_approve"),
    path("<uuid:pk>/book/", views.InvoiceBookView.as_view(), name="invoice_book"),
]
