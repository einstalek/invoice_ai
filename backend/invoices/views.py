from django.db import IntegrityError
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

import logging

from accounts.permissions import IsOrgMember
from notifications.models import Notification
from organizations.models import OrganizationMembership
from .models import Invoice, InvoiceApproval, InvoiceActivity
from .serializers import (
    InvoiceListSerializer,
    InvoiceDetailSerializer,
    InvoiceUploadSerializer,
    InvoiceEditSerializer,
    InvoiceApprovalCreateSerializer,
    EDITABLE_FIELDS,
)

logger = logging.getLogger(__name__)


def _run_task(task, *args):
    """Try Celery .delay(); fall back to synchronous execution if broker is unavailable."""
    try:
        task.delay(*args)
    except Exception:
        logger.warning("Celery unavailable, running %s synchronously", task.name)
        task(*args)


class InvoiceListView(generics.ListAPIView):
    """
    GET /api/orgs/<org_id>/invoices/

    Supports filtering via query params:
      ?status=PENDING_REVIEW
      ?supplier=<uuid>
      ?invoice_date_after=2024-01-01&invoice_date_before=2024-12-31
      ?search=keyword
      ?ordering=-created_at
    """

    serializer_class = InvoiceListSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "status": ["exact"],
        "supplier": ["exact"],
        "supply_type": ["exact"],
        "service_category": ["exact"],
        "currency": ["exact"],
        "invoice_date": ["gte", "lte"],
        "total_amount": ["gte", "lte"],
    }
    search_fields = ["invoice_number", "supplier_name", "buyer_name", "description_keyword"]
    ordering_fields = ["created_at", "invoice_date", "total_amount", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Invoice.objects.filter(
            organization_id=self.kwargs["org_id"],
        ).select_related("uploaded_by")


class InvoiceUploadView(APIView):
    """
    POST /api/orgs/<org_id>/invoices/upload/

    Upload a PDF — creates Invoice in PROCESSING status.
    Celery task will be triggered in Phase 5.
    """

    permission_classes = [IsAuthenticated, IsOrgMember]

    def post(self, request, org_id):
        serializer = InvoiceUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        invoice = Invoice.objects.create(
            organization_id=org_id,
            uploaded_by=request.user,
            pdf_file=serializer.validated_data["pdf_file"],
            status=Invoice.Status.PROCESSING,
        )

        InvoiceActivity.objects.create(
            invoice=invoice,
            user=request.user,
            action=InvoiceActivity.Action.UPLOADED,
        )

        from .tasks import process_invoice
        _run_task(process_invoice, str(invoice.id))

        return Response(
            InvoiceDetailSerializer(invoice).data,
            status=status.HTTP_201_CREATED,
        )


class InvoiceDetailView(generics.RetrieveAPIView):
    """
    GET /api/orgs/<org_id>/invoices/<pk>/
    """

    serializer_class = InvoiceDetailSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]

    def get_queryset(self):
        return Invoice.objects.filter(
            organization_id=self.kwargs["org_id"],
        ).select_related("uploaded_by", "booked_by", "supplier").prefetch_related(
            "activities__user", "approvals__user",
        )


class InvoiceEditView(APIView):
    """
    PATCH /api/orgs/<org_id>/invoices/<pk>/edit/

    Edit extracted fields. Creates an activity log entry with field diffs.
    Only allowed when status is PENDING_REVIEW or EXTRACTION_FAILED.
    """

    permission_classes = [IsAuthenticated, IsOrgMember]

    def patch(self, request, org_id, pk):
        invoice = Invoice.objects.filter(
            pk=pk, organization_id=org_id,
        ).first()

        if not invoice:
            return Response(
                {"detail": "Invoice not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if invoice.status not in (
            Invoice.Status.PENDING_REVIEW,
            Invoice.Status.EXTRACTION_FAILED,
        ):
            return Response(
                {"detail": f"Cannot edit invoice in {invoice.status} status."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = InvoiceEditSerializer(invoice, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Build diff before saving
        changes = {}
        for field in EDITABLE_FIELDS:
            if field in serializer.validated_data:
                old_val = getattr(invoice, field)
                new_val = serializer.validated_data[field]
                # Normalize for comparison (FK → id)
                if hasattr(old_val, "pk"):
                    old_val = str(old_val.pk) if old_val else None
                if hasattr(new_val, "pk"):
                    new_val = str(new_val.pk) if new_val else None
                old_str = str(old_val) if old_val is not None else None
                new_str = str(new_val) if new_val is not None else None
                if old_str != new_str:
                    changes[field] = {"old": old_str, "new": new_str}

        if not changes:
            return Response(
                {"detail": "No changes detected."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save()

        # If invoice was EXTRACTION_FAILED and fields are being filled manually,
        # move to PENDING_REVIEW
        if invoice.status == Invoice.Status.EXTRACTION_FAILED:
            invoice.status = Invoice.Status.PENDING_REVIEW
            invoice.save(update_fields=["status"])

        InvoiceActivity.objects.create(
            invoice=invoice,
            user=request.user,
            action=InvoiceActivity.Action.FIELDS_EDITED,
            changes=changes,
        )

        invoice.refresh_from_db()
        return Response(InvoiceDetailSerializer(invoice).data)


class InvoiceApproveView(APIView):
    """
    POST /api/orgs/<org_id>/invoices/<pk>/approve/
    Body: {"decision": "APPROVED"} or {"decision": "EDIT_REQUESTED", "comment": "..."}

    Multi-approval logic per spec:
    - APPROVED: increment approvals_obtained, check against required_approvals
    - EDIT_REQUESTED: increment round, reset approvals_obtained, back to PENDING_REVIEW
    """

    permission_classes = [IsAuthenticated, IsOrgMember]

    def post(self, request, org_id, pk):
        invoice = Invoice.objects.filter(
            pk=pk, organization_id=org_id,
        ).select_related("organization").first()

        if not invoice:
            return Response(
                {"detail": "Invoice not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if invoice.status not in (
            Invoice.Status.PENDING_REVIEW,
            Invoice.Status.APPROVED,
        ):
            return Response(
                {"detail": f"Cannot review invoice in {invoice.status} status."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = InvoiceApprovalCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        decision = serializer.validated_data["decision"]
        comment = serializer.validated_data.get("comment", "")

        # Require comment for edit requests
        if decision == InvoiceApproval.Decision.EDIT_REQUESTED and not comment:
            return Response(
                {"detail": "Comment is required when requesting edits."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create approval record
        try:
            approval = InvoiceApproval.objects.create(
                invoice=invoice,
                user=request.user,
                round=invoice.current_approval_round,
                decision=decision,
                comment=comment,
            )
        except IntegrityError:
            return Response(
                {"detail": "You have already reviewed this invoice in the current round."},
                status=status.HTTP_409_CONFLICT,
            )

        # Activity log
        action = (
            InvoiceActivity.Action.APPROVED
            if decision == InvoiceApproval.Decision.APPROVED
            else InvoiceActivity.Action.EDIT_REQUESTED
        )
        InvoiceActivity.objects.create(
            invoice=invoice,
            user=request.user,
            action=action,
            comment=comment,
        )

        if decision == InvoiceApproval.Decision.APPROVED:
            invoice.approvals_obtained += 1
            if invoice.approvals_obtained >= invoice.organization.required_approvals:
                invoice.status = Invoice.Status.APPROVED
                # Notify org members
                self._notify_org(invoice, Notification.Type.INVOICE_APPROVED,
                                 f"Invoice {invoice.invoice_number or invoice.id} approved")
            invoice.save(update_fields=["approvals_obtained", "status"])
        else:
            # EDIT_REQUESTED — new round
            invoice.current_approval_round += 1
            invoice.approvals_obtained = 0
            invoice.status = Invoice.Status.PENDING_REVIEW
            invoice.save(update_fields=[
                "current_approval_round", "approvals_obtained", "status",
            ])
            # Notify org members that edits were requested
            self._notify_org(invoice, Notification.Type.EDIT_REQUESTED,
                             f"Edits requested on invoice {invoice.invoice_number or invoice.id}")

        invoice.refresh_from_db()
        return Response(InvoiceDetailSerializer(invoice).data)

    def _notify_org(self, invoice, notif_type, title):
        """Create notifications for all active members of the org (except current user)."""
        member_user_ids = OrganizationMembership.objects.filter(
            organization=invoice.organization,
            status=OrganizationMembership.Status.ACTIVE,
        ).exclude(user=self.request.user).values_list("user_id", flat=True)

        Notification.objects.bulk_create([
            Notification(
                user_id=uid,
                organization=invoice.organization,
                invoice=invoice,
                type=notif_type,
                title=title,
            )
            for uid in member_user_ids if uid is not None
        ])


class InvoiceBookView(APIView):
    """
    POST /api/orgs/<org_id>/invoices/<pk>/book/

    Mark invoice as BOOKED. Actual ERP export will be a Celery task (Phase 5).
    """

    permission_classes = [IsAuthenticated, IsOrgMember]

    def post(self, request, org_id, pk):
        invoice = Invoice.objects.filter(
            pk=pk, organization_id=org_id,
        ).first()

        if not invoice:
            return Response(
                {"detail": "Invoice not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if invoice.status != Invoice.Status.APPROVED:
            return Response(
                {"detail": "Only approved invoices can be booked."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoice.status = Invoice.Status.BOOKED
        invoice.booked_at = timezone.now()
        invoice.booked_by = request.user
        invoice.save(update_fields=["status", "booked_at", "booked_by"])

        InvoiceActivity.objects.create(
            invoice=invoice,
            user=request.user,
            action=InvoiceActivity.Action.BOOKED,
        )

        from .tasks import export_to_erp
        _run_task(export_to_erp, str(invoice.id))

        # Notify org
        member_user_ids = OrganizationMembership.objects.filter(
            organization=invoice.organization,
            status=OrganizationMembership.Status.ACTIVE,
        ).exclude(user=request.user).values_list("user_id", flat=True)

        Notification.objects.bulk_create([
            Notification(
                user_id=uid,
                organization=invoice.organization,
                invoice=invoice,
                type=Notification.Type.INVOICE_BOOKED,
                title=f"Invoice {invoice.invoice_number or invoice.id} booked",
            )
            for uid in member_user_ids if uid is not None
        ])

        invoice.refresh_from_db()
        return Response(InvoiceDetailSerializer(invoice).data)
