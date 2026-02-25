from rest_framework import serializers

from accounts.serializers import UserSerializer
from organizations.serializers import SupplierSerializer
from .models import Invoice, InvoiceApproval, InvoiceActivity


# ---------------------------------------------------------------------------
# Activity & Approval (read-only, nested in invoice detail)
# ---------------------------------------------------------------------------
class InvoiceActivitySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = InvoiceActivity
        fields = ["id", "user", "action", "comment", "changes", "created_at"]
        read_only_fields = fields


class InvoiceApprovalSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = InvoiceApproval
        fields = ["id", "user", "round", "decision", "comment", "created_at"]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# Invoice list (lightweight)
# ---------------------------------------------------------------------------
class InvoiceListSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id", "status", "invoice_number", "invoice_date",
            "total_amount", "currency", "supplier_name",
            "uploaded_by", "created_at", "updated_at",
        ]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# Invoice detail (full data + nested activity/approvals)
# ---------------------------------------------------------------------------
class InvoiceDetailSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    booked_by = UserSerializer(read_only=True)
    supplier_detail = SupplierSerializer(source="supplier", read_only=True)
    activities = InvoiceActivitySerializer(many=True, read_only=True)
    approvals = serializers.SerializerMethodField()
    pdf_file = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            # Lifecycle
            "id", "organization", "uploaded_by", "pdf_file", "status",
            "supplier", "supplier_detail",
            "current_approval_round", "approvals_obtained",
            "booked_at", "booked_by",
            "created_at", "updated_at",
            # Extracted fields
            "invoice_number", "invoice_date", "invoice_due_date",
            "total_amount", "currency", "description_keyword",
            "vat_rates", "supply_type", "service_category",
            # Supplier (point-in-time)
            "supplier_name", "supplier_address", "supplier_country",
            "supplier_country_group", "supplier_vat_id", "supplier_email",
            # Buyer (point-in-time)
            "buyer_name", "buyer_address", "buyer_country",
            "buyer_country_group", "buyer_vat_id", "buyer_email",
            # LLM
            "llm_raw_response", "extracted_text", "extraction_error",
            # Nested
            "activities", "approvals",
        ]
        read_only_fields = fields

    def get_pdf_file(self, obj):
        """Return a signed S3 URL or local URL for the PDF."""
        from .services.file_service import get_signed_file_url
        return get_signed_file_url(obj.pdf_file)

    def get_approvals(self, obj):
        """Return only current-round approvals."""
        qs = obj.approvals.filter(round=obj.current_approval_round)
        return InvoiceApprovalSerializer(qs, many=True).data


# ---------------------------------------------------------------------------
# Invoice upload
# ---------------------------------------------------------------------------
class InvoiceUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ["id", "pdf_file"]
        read_only_fields = ["id"]


# ---------------------------------------------------------------------------
# Invoice field editing
# ---------------------------------------------------------------------------
EDITABLE_FIELDS = [
    "invoice_number", "invoice_date", "invoice_due_date",
    "total_amount", "currency", "description_keyword",
    "vat_rates", "supply_type", "service_category",
    "supplier_name", "supplier_address", "supplier_country",
    "supplier_country_group", "supplier_vat_id", "supplier_email",
    "buyer_name", "buyer_address", "buyer_country",
    "buyer_country_group", "buyer_vat_id", "buyer_email",
    "supplier",
]


class InvoiceEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = EDITABLE_FIELDS
        extra_kwargs = {f: {"required": False} for f in EDITABLE_FIELDS}


# ---------------------------------------------------------------------------
# Approve / Request edits
# ---------------------------------------------------------------------------
class InvoiceApprovalCreateSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=InvoiceApproval.Decision.choices)
    comment = serializers.CharField(required=False, allow_blank=True, default="")
