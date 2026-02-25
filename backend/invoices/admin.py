from django.contrib import admin

from .models import Invoice, InvoiceApproval, InvoiceActivity


class InvoiceApprovalInline(admin.TabularInline):
    model = InvoiceApproval
    extra = 0
    readonly_fields = ("user", "round", "decision", "comment", "created_at")


class InvoiceActivityInline(admin.TabularInline):
    model = InvoiceActivity
    extra = 0
    readonly_fields = ("user", "action", "comment", "changes", "created_at")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number", "organization", "status", "supplier_name",
        "total_amount", "currency", "created_at",
    )
    list_filter = ("status", "supply_type", "service_category")
    search_fields = ("invoice_number", "supplier_name", "buyer_name")
    inlines = [InvoiceApprovalInline, InvoiceActivityInline]


@admin.register(InvoiceApproval)
class InvoiceApprovalAdmin(admin.ModelAdmin):
    list_display = ("invoice", "user", "round", "decision", "created_at")
    list_filter = ("decision",)


@admin.register(InvoiceActivity)
class InvoiceActivityAdmin(admin.ModelAdmin):
    list_display = ("invoice", "user", "action", "created_at")
    list_filter = ("action",)
