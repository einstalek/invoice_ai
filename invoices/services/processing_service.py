"""
Invoice processing service.

Wraps OCR/AI processing pipeline with better error handling.
"""

import logging
from pathlib import Path
from typing import Dict, Optional

from utils import (
    pipeline,
    ReplicateCancelled,
    ReplicateFailed,
)
from .exceptions import (
    ProcessingError,
    OCREmptyError,
    ReplicateThrottledError,
)

logger = logging.getLogger(__name__)


class InvoiceProcessingService:
    """Service for invoice OCR/AI processing."""

    @staticmethod
    def process_invoice_file(
        file_path: Path,
        request_id: Optional[str] = None,
    ) -> Dict:
        """
        Process invoice PDF through OCR/AI pipeline.

        Wraps utils.pipeline() with better error handling and normalized output.

        Args:
            file_path: Path to invoice PDF file
            request_id: Optional request ID for cancellation tracking

        Returns:
            Dictionary of parsed invoice data with normalized structure

        Raises:
            OCREmptyError: If no text detected in PDF
            ReplicateThrottledError: If Replicate API is rate limited
            ProcessingError: For other processing errors
        """
        logger.info("Processing invoice file: path=%s request_id=%s", file_path, request_id)

        try:
            # Call OCR/AI pipeline
            raw_result = pipeline(file_path, request_id=request_id)

        except ReplicateCancelled:
            raise ProcessingError("Request cancelled.")

        except ReplicateFailed as exc:
            error_message = str(exc) or "Replicate failed."
            raise ProcessingError(error_message)

        except Exception as exc:
            # Check for rate limiting
            message = str(exc)
            if "throttled" in message.lower() or "rate limit" in message.lower() or "429" in message:
                raise ReplicateThrottledError(
                    "Request was throttled. Please try again in a moment."
                )

            # Check for OCR empty
            if message == "OCR_EMPTY":
                raise OCREmptyError(
                    "No text detected in the PDF. If this is a scanned image, OCR may not be supported yet."
                )

            # Re-raise other exceptions
            raise

        # Normalize result format
        try:
            result_dict = InvoiceProcessingService._normalize_result(raw_result)
            logger.info("Invoice processed successfully: fields=%s", len(result_dict))
            return result_dict

        except Exception as exc:
            logger.exception("Failed to normalize processing result: %s", exc)
            raise ProcessingError(f"Failed to parse processing result: {exc}")

    @staticmethod
    def _normalize_result(raw_result) -> Dict:
        """
        Normalize processing result to consistent format.

        Converts all fields to {value, bbox} structure and filters empty values.

        Args:
            raw_result: Raw result from pipeline (string or dict)

        Returns:
            Normalized dictionary with {value, bbox} structure for each field
        """
        # Parse JSON string if needed
        if isinstance(raw_result, str):
            import json
            result_dict = json.loads(raw_result)
        else:
            result_dict = raw_result

        # Normalize to {value, bbox} format
        final_response = {}
        for k, v in result_dict.items():
            # Skip empty values
            if isinstance(v, str) and not v.strip():
                continue
            if isinstance(v, list) and not v:
                continue

            # Normalize to {value, bbox} format
            if isinstance(v, dict) and "value" in v:
                final_response[k] = v
            else:
                final_response[k] = {"value": v, "bbox": None}

        return final_response
