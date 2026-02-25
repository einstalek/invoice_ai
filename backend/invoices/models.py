import uuid

from django.conf import settings
from django.db import models


class Invoice(models.Model):
    # ------------------------------------------------------------------
    # Enums
    # ------------------------------------------------------------------
    class Status(models.TextChoices):
        PROCESSING = "PROCESSING", "Processing"
        EXTRACTION_FAILED = "EXTRACTION_FAILED", "Extraction Failed"
        PENDING_REVIEW = "PENDING_REVIEW", "Pending Review"
        APPROVED = "APPROVED", "Approved"
        BOOKED = "BOOKED", "Booked"

    class SupplyType(models.TextChoices):
        GOODS = "GOODS", "Goods"
        SERVICES = "SERVICES", "Services"

    class ServiceCategory(models.TextChoices):
        SERV_0 = "SERV_0", "SERV_0"
        SERV_9 = "SERV_9", "SERV_9"
        SERV_13 = "SERV_13", "SERV_13"
        SERV_24 = "SERV_24", "SERV_24"
        SERV_EX = "SERV_EX", "SERV_EX"

    class CountryGroup(models.TextChoices):
        EE = "EE", "Estonia"
        EU_OTHER = "EU_OTHER", "EU (other)"
        NON_EU = "NON_EU", "Non-EU"

    # ------------------------------------------------------------------
    # Lifecycle & ownership
    # ------------------------------------------------------------------
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE, related_name="invoices"
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="uploaded_invoices"
    )
    pdf_file = models.FileField(upload_to="invoices/pdfs/%Y/%m/")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PROCESSING
    )
    supplier = models.ForeignKey(
        "organizations.Supplier",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices",
    )
    current_approval_round = models.PositiveIntegerField(default=1)
    approvals_obtained = models.PositiveIntegerField(default=0)
    booked_at = models.DateTimeField(null=True, blank=True)
    booked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="booked_invoices",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ------------------------------------------------------------------
    # Extracted / edited fields (typed columns for querying)
    # ------------------------------------------------------------------
    invoice_number = models.CharField(max_length=100, null=True, blank=True)
    invoice_date = models.DateField(null=True, blank=True)
    invoice_due_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    currency = models.CharField(max_length=10, null=True, blank=True)
    description_keyword = models.CharField(max_length=100, null=True, blank=True)
    vat_rates = models.CharField(max_length=50, null=True, blank=True)
    supply_type = models.CharField(
        max_length=20, choices=SupplyType.choices, null=True, blank=True
    )
    service_category = models.CharField(
        max_length=20, choices=ServiceCategory.choices, null=True, blank=True
    )

    # Supplier data (point-in-time from the PDF)
    supplier_name = models.CharField(max_length=255, null=True, blank=True)
    supplier_address = models.TextField(null=True, blank=True)
    supplier_country = models.CharField(max_length=100, null=True, blank=True)
    supplier_country_group = models.CharField(
        max_length=20, choices=CountryGroup.choices, null=True, blank=True
    )
    supplier_vat_id = models.CharField(max_length=50, null=True, blank=True)
    supplier_email = models.EmailField(null=True, blank=True)

    # Buyer data (point-in-time from the PDF)
    buyer_name = models.CharField(max_length=255, null=True, blank=True)
    buyer_address = models.TextField(null=True, blank=True)
    buyer_country = models.CharField(max_length=100, null=True, blank=True)
    buyer_country_group = models.CharField(
        max_length=20, choices=CountryGroup.choices, null=True, blank=True
    )
    buyer_vat_id = models.CharField(max_length=50, null=True, blank=True)
    buyer_email = models.EmailField(null=True, blank=True)

    # ------------------------------------------------------------------
    # LLM output
    # ------------------------------------------------------------------
    llm_raw_response = models.JSONField(null=True, blank=True)
    extracted_text = models.TextField(null=True, blank=True)
    extraction_error = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "invoices"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Invoice {self.invoice_number or self.id} — {self.status}"


class InvoiceApproval(models.Model):
    class Decision(models.TextChoices):
        APPROVED = "APPROVED", "Approved"
        EDIT_REQUESTED = "EDIT_REQUESTED", "Edit Requested"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="approvals"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="approvals"
    )
    round = models.PositiveIntegerField()
    decision = models.CharField(max_length=20, choices=Decision.choices)
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "invoice_approvals"
        constraints = [
            models.UniqueConstraint(
                fields=["invoice", "user", "round"],
                name="unique_approval_per_user_per_round",
            ),
        ]

    def __str__(self):
        return f"{self.user} — {self.decision} (round {self.round})"


class InvoiceActivity(models.Model):
    class Action(models.TextChoices):
        UPLOADED = "UPLOADED", "Uploaded"
        EXTRACTION_COMPLETED = "EXTRACTION_COMPLETED", "Extraction Completed"
        EXTRACTION_FAILED = "EXTRACTION_FAILED", "Extraction Failed"
        FIELDS_EDITED = "FIELDS_EDITED", "Fields Edited"
        APPROVED = "APPROVED", "Approved"
        EDIT_REQUESTED = "EDIT_REQUESTED", "Edit Requested"
        BOOKED = "BOOKED", "Booked"
        COMMENTED = "COMMENTED", "Commented"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="activities"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoice_activities",
    )
    action = models.CharField(max_length=30, choices=Action.choices)
    comment = models.TextField(null=True, blank=True)
    changes = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "invoice_activities"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} on {self.invoice_id}"
