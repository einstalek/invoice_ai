from django.urls import path

from . import views


urlpatterns = [
    path("invoices", views.invoices_page, name="invoices_page"),
    path("process", views.ProcessInvoiceView.as_view(), name="process"),
    path("process/cancel", views.CancelProcessInvoiceView.as_view(), name="process_cancel"),
    path("export", views.ExportInvoiceView.as_view(), name="export"),
    path("invoices/submissions", views.InvoiceSubmissionListCreateView.as_view(), name="invoice_submissions"),
    path("invoices/submissions/table", views.InvoiceSubmissionTableView.as_view(), name="invoice_submissions_table"),
    path("invoices/submissions/requests", views.InvoiceSubmissionRequestListView.as_view(), name="invoice_submission_requests"),
    path(
        "invoices/submissions/<int:submission_id>",
        views.InvoiceSubmissionDetailView.as_view(),
        name="invoice_submission_detail",
    ),
    path("invoices/submissions/approve", views.InvoiceSubmissionApproveView.as_view(), name="invoice_submission_approve"),
    path("invoices/submissions/reject", views.InvoiceSubmissionRejectView.as_view(), name="invoice_submission_reject"),
    path("invoices/submissions/request-edit", views.InvoiceSubmissionRequestEditView.as_view(), name="invoice_submission_request_edit"),
    path(
        "invoices/submissions/reviewers/add",
        views.InvoiceSubmissionAddReviewerView.as_view(),
        name="invoice_submission_add_reviewer",
    ),
    path("invoices/submissions/resubmit", views.InvoiceSubmissionResubmitView.as_view(), name="invoice_submission_resubmit"),
    path("invoices/submissions/delete", views.InvoiceSubmissionDeleteView.as_view(), name="invoice_submission_delete"),
]
