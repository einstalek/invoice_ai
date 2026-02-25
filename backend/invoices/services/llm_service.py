"""Call Replicate LLM API and parse invoice extraction response."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

import replicate
from django.conf import settings

from invoices.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

# Replicate model to use — configurable via settings
LLM_MODEL = getattr(settings, "LLM_MODEL", "qwen/qwen3-235b-a22b-instruct-2507")
LLM_POLL_INTERVAL = 0.75
LLM_MAX_WAIT = 300  # seconds


def call_llm(invoice_text: str) -> dict:
    """
    Send extracted text to Replicate LLM, return the raw parsed JSON response.

    Raises RuntimeError on failure or timeout.
    """
    prompt = SYSTEM_PROMPT + "\n" + USER_PROMPT_TEMPLATE.format(invoice_text=invoice_text)

    prediction = replicate.predictions.create(
        model=LLM_MODEL,
        input={"prompt": prompt},
    )

    elapsed = 0.0
    while prediction.status not in ("succeeded", "failed", "canceled"):
        time.sleep(LLM_POLL_INTERVAL)
        elapsed += LLM_POLL_INTERVAL
        if elapsed > LLM_MAX_WAIT:
            try:
                replicate.predictions.cancel(prediction.id)
            except Exception:
                pass
            raise RuntimeError(f"LLM prediction timed out after {LLM_MAX_WAIT}s")
        prediction = replicate.predictions.get(prediction.id)

    if prediction.status == "canceled":
        raise RuntimeError("LLM prediction was canceled")
    if prediction.status != "succeeded":
        raise RuntimeError(prediction.error or "LLM prediction failed")

    output = prediction.output
    if isinstance(output, list):
        output = "".join(output)
    if not output:
        raise RuntimeError("LLM returned empty output")

    return json.loads(output)


def _get_value(field_data):
    """Extract value from LLM response field (handles both dict and plain formats)."""
    if isinstance(field_data, dict):
        return field_data.get("value")
    return field_data


def _parse_date(value: str | None) -> datetime.date | None:
    """Parse date in dd.mm.yyyy format, return None on failure."""
    if not value or not isinstance(value, str):
        return None
    value = value.strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _parse_decimal(value) -> Decimal | None:
    """Parse a numeric string to Decimal, return None on failure."""
    if value is None:
        return None
    try:
        cleaned = str(value).replace(",", ".").replace(" ", "").strip()
        if not cleaned:
            return None
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None


# Map from LLM response keys → Invoice model field names
FIELD_MAPPING = {
    "invoice_number": ("invoice_number", str),
    "invoice_date": ("invoice_date", "date"),
    "invoice_due_date": ("invoice_due_date", "date"),
    "invoice_total_amounts": ("total_amount", "decimal"),
    "invoice_currency": ("currency", str),
    "description_keyword": ("description_keyword", str),
    "vat_rates": ("vat_rates", str),
    "supply_type": ("supply_type", str),
    "service_category": ("service_category", str),
    "supplier_name": ("supplier_name", str),
    "supplier_address": ("supplier_address", str),
    "supplier_country": ("supplier_country", str),
    "supplier_country_group": ("supplier_country_group", str),
    "supplier_vat_id": ("supplier_vat_id", str),
    "supplier_email": ("supplier_email", str),
    "buyer_name": ("buyer_name", str),
    "buyer_address": ("buyer_address", str),
    "buyer_country": ("buyer_country", str),
    "buyer_country_group": ("buyer_country_group", str),
    "buyer_vat_id": ("buyer_vat_id", str),
    "buyer_email": ("buyer_email", str),
}


def map_llm_response_to_fields(llm_response: dict) -> dict:
    """
    Convert the LLM JSON response into a dict of Invoice model field values.

    Returns a dict like {"invoice_number": "INV-001", "total_amount": Decimal("1500.00"), ...}
    Only includes fields that have non-empty values.
    """
    fields = {}

    for llm_key, (model_field, field_type) in FIELD_MAPPING.items():
        raw = llm_response.get(llm_key)
        value = _get_value(raw)

        if not value or (isinstance(value, str) and not value.strip()):
            continue

        if field_type == "date":
            parsed = _parse_date(value)
            if parsed:
                fields[model_field] = parsed
        elif field_type == "decimal":
            parsed = _parse_decimal(value)
            if parsed:
                fields[model_field] = parsed
        elif field_type is str:
            fields[model_field] = str(value).strip()

    return fields
