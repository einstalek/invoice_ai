"""
File service for handling invoice file operations.

Provides S3 signed URL generation and file URL handling.
"""

import logging
import os
from typing import Optional

import boto3
from botocore.config import Config
from django.conf import settings

logger = logging.getLogger(__name__)


class InvoiceFileService:
    """Service for invoice file operations."""

    @staticmethod
    def get_signed_file_url(file_field, request=None) -> Optional[str]:
        """
        Generate signed S3 URL or return local URL for invoice file.

        Args:
            file_field: Django FileField instance
            request: Optional HTTP request (unused, kept for compatibility)

        Returns:
            Signed URL string or None if file doesn't exist
        """
        if not file_field:
            return None

        storage_class = file_field.storage.__class__.__name__
        logger.info(
            "Invoice file lookup: key=%s storage=%s",
            file_field.name,
            storage_class,
        )

        # Check for local file fallback
        local_root = getattr(settings, "MEDIA_ROOT", None)
        if local_root:
            local_path = os.path.join(local_root, file_field.name)
            if os.path.exists(local_path):
                logger.info("Local file exists but fallback disabled: path=%s", local_path)

        # Get URL from storage backend
        url = file_field.url

        # If already signed, return as-is
        if "X-Amz-Signature" in url or "Signature=" in url:
            logger.info("Invoice file has signed URL from storage backend.")
            return url

        # If no S3 bucket configured, return storage URL
        bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
        if not bucket:
            logger.warning("No AWS_STORAGE_BUCKET_NAME set; using storage url.")
            return url

        # Generate signed S3 URL
        key = file_field.name
        try:
            region = getattr(settings, "AWS_S3_REGION_NAME", None)
            endpoint_url = None
            if region:
                endpoint_url = f"https://s3.{region}.amazonaws.com"

            logger.info(
                "Signing S3 URL: bucket=%s key=%s region=%s endpoint=%s",
                bucket, key, region, endpoint_url
            )

            client = boto3.client(
                "s3",
                region_name=region,
                endpoint_url=endpoint_url,
                aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", None),
                aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
                config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
            )

            expires = int(getattr(settings, "AWS_QUERYSTRING_EXPIRE", 3600))
            signed_url = client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expires,
            )

            logger.info("Signed URL generated for key=%s (expires=%s)", key, expires)
            return signed_url

        except Exception as exc:
            logger.exception("Failed to sign invoice file url (%s): %s", key, exc)
            return url
