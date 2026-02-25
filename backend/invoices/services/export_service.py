"""ERP export services — Google Sheets (MVP), QuickBooks (future)."""

import json
import logging
from typing import Any

import gspread
from google.oauth2.credentials import Credentials

from invoices.models import Invoice
from organizations.models import Organization

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

# Fields to export to Google Sheets (column order)
EXPORT_FIELDS = [
    "invoice_number",
    "invoice_date",
    "invoice_due_date",
    "total_amount",
    "currency",
    "vat_rates",
    "supply_type",
    "service_category",
    "description_keyword",
    "supplier_name",
    "supplier_vat_id",
    "supplier_country",
    "supplier_country_group",
    "buyer_name",
    "buyer_vat_id",
]


def _get_gspread_client(org: Organization) -> gspread.Client:
    """Build a gspread client from org's OAuth2 credentials in erp_config."""
    erp_config = org.erp_config or {}
    google_creds = erp_config.get("google_credentials")
    if not google_creds:
        raise ValueError(
            "Google Sheets is not connected. Please connect your Google account "
            "in organization settings."
        )

    creds = Credentials(
        token=google_creds["access_token"],
        refresh_token=google_creds.get("refresh_token"),
        token_uri=google_creds.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=google_creds.get("client_id"),
        client_secret=google_creds.get("client_secret"),
        scopes=SCOPES,
    )

    # If the token has been refreshed, persist the new access token
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request

        creds.refresh(Request())
        erp_config["google_credentials"]["access_token"] = creds.token
        org.erp_config = erp_config
        org.save(update_fields=["erp_config"])

    return gspread.authorize(creds)


def _format_value(value: Any) -> str:
    """Convert a model field value to a string suitable for a spreadsheet cell."""
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def export_to_google_sheets(invoice: Invoice) -> None:
    """
    Append an invoice row to the organization's configured Google Sheet.

    Expects org.erp_config to contain:
      {
        "google_credentials": { ... }, # OAuth2 tokens (from Google Sheets connect)
        "spreadsheet_id": "...",       # target spreadsheet ID
        "worksheet_name": "..."        # optional, defaults to first sheet
      }
    """
    org = invoice.organization
    if org.erp_type != Organization.ErpType.GOOGLE_SHEETS:
        raise ValueError(f"Organization ERP type is {org.erp_type}, not GOOGLE_SHEETS")

    erp_config = org.erp_config or {}
    spreadsheet_id = erp_config.get("spreadsheet_id")
    if not spreadsheet_id:
        raise ValueError("erp_config is missing 'spreadsheet_id'")

    client = _get_gspread_client(org)
    sheet = client.open_by_key(spreadsheet_id)

    worksheet_name = erp_config.get("worksheet_name")
    ws = sheet.worksheet(worksheet_name) if worksheet_name else sheet.sheet1

    # Ensure header row exists
    existing_header = ws.row_values(1)
    if not existing_header:
        ws.append_row(EXPORT_FIELDS, value_input_option="USER_ENTERED")

    # Build data row from invoice fields
    row = [_format_value(getattr(invoice, field, None)) for field in EXPORT_FIELDS]
    ws.append_row(row, value_input_option="USER_ENTERED")

    logger.info("Exported invoice %s to spreadsheet %s", invoice.id, spreadsheet_id)
