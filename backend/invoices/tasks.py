"""Celery tasks for async invoice processing."""

import logging

from celery import shared_task

from .models import Invoice, InvoiceActivity
from .services.pdf_service import extract_text
from .services.llm_service import call_llm, map_llm_response_to_fields
from .services.export_service import export_to_google_sheets
from organizations.models import Organization, OrganizationMembership, Supplier
from notifications.models import Notification

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def process_invoice(self, invoice_id: str) -> None:
    """
    Full extraction pipeline:
    1. Extract text from PDF (pdfplumber)
    2. Call LLM via Replicate API
    3. Parse response and populate Invoice fields
    4. Try to auto-match supplier by VAT ID
    5. Update status to PENDING_REVIEW (or EXTRACTION_FAILED)
    """
    try:
        invoice = Invoice.objects.select_related("organization").get(pk=invoice_id)
    except Invoice.DoesNotExist:
        logger.error("Invoice %s not found", invoice_id)
        return

    try:
        # Step 1: PDF text extraction
        extracted_text = extract_text(invoice.pdf_file)
        invoice.extracted_text = extracted_text
        invoice.save(update_fields=["extracted_text"])

        # Step 2: LLM extraction
        llm_response = call_llm(extracted_text)
        invoice.llm_raw_response = llm_response
        invoice.save(update_fields=["llm_raw_response"])

        # Step 3: Map LLM response to model fields
        fields = map_llm_response_to_fields(llm_response)
        for field_name, value in fields.items():
            setattr(invoice, field_name, value)

        # Step 4: Auto-match supplier by VAT ID
        if fields.get("supplier_vat_id"):
            matched_supplier = Supplier.objects.filter(
                organization=invoice.organization,
                vat_id=fields["supplier_vat_id"],
            ).first()
            if matched_supplier:
                invoice.supplier = matched_supplier

        # Step 5: Mark as ready for review
        invoice.status = Invoice.Status.PENDING_REVIEW
        invoice.save()

        InvoiceActivity.objects.create(
            invoice=invoice,
            user=None,  # system event
            action=InvoiceActivity.Action.EXTRACTION_COMPLETED,
        )

        # Notify org members that a new invoice is ready
        member_user_ids = OrganizationMembership.objects.filter(
            organization=invoice.organization,
            status=OrganizationMembership.Status.ACTIVE,
        ).values_list("user_id", flat=True)

        Notification.objects.bulk_create([
            Notification(
                user_id=uid,
                organization=invoice.organization,
                invoice=invoice,
                type=Notification.Type.APPROVAL_NEEDED,
                title=f"Invoice {invoice.invoice_number or 'new'} ready for review",
            )
            for uid in member_user_ids if uid is not None
        ])

        logger.info("Invoice %s processed successfully", invoice_id)

    except Exception as exc:
        logger.exception("Invoice %s extraction failed: %s", invoice_id, exc)

        invoice.extraction_error = str(exc)
        invoice.status = Invoice.Status.EXTRACTION_FAILED
        invoice.save(update_fields=["extraction_error", "status"])

        InvoiceActivity.objects.create(
            invoice=invoice,
            user=None,
            action=InvoiceActivity.Action.EXTRACTION_FAILED,
            comment=str(exc),
        )

        # Retry on transient errors (network, API rate limits)
        # Skip retry when running synchronously (no broker)
        if self.request.called_directly:
            return
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=15)
def export_to_erp(self, invoice_id: str) -> None:
    """
    Export a booked invoice to the organization's configured ERP system.
    Currently supports Google Sheets.
    """
    try:
        invoice = Invoice.objects.select_related("organization").get(pk=invoice_id)
    except Invoice.DoesNotExist:
        logger.error("Invoice %s not found", invoice_id)
        return

    org = invoice.organization

    if org.erp_type == Organization.ErpType.NONE:
        logger.info("Org %s has no ERP configured, skipping export", org.id)
        return

    try:
        if org.erp_type == Organization.ErpType.GOOGLE_SHEETS:
            export_to_google_sheets(invoice)
        elif org.erp_type == Organization.ErpType.QUICKBOOKS:
            # TODO: QuickBooks integration
            logger.warning("QuickBooks export not yet implemented")
            return

        logger.info("Invoice %s exported to %s", invoice_id, org.erp_type)

    except Exception as exc:
        logger.exception("ERP export failed for invoice %s: %s", invoice_id, exc)
        if self.request.called_directly:
            return
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
