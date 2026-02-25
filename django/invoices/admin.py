from django.contrib import admin

from .models import InvoiceSubmission, InvoiceReviewAssignment


@admin.register(InvoiceSubmission)
class InvoiceSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "organization",
        "submitted_by",
        "status",
        "invoice_file",
        "created_at",
        "updated_at",
    )
    list_filter = ("status",)
    search_fields = ("organization__name", "submitted_by__email")


@admin.register(InvoiceReviewAssignment)
class InvoiceReviewAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "submission",
        "reviewer",
        "status",
        "assigned_by",
        "created_at",
        "updated_at",
    )
    list_filter = ("status",)
    search_fields = ("submission__id", "reviewer__email", "assigned_by__email")
