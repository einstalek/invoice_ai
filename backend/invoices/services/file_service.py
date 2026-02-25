"""Generate signed URLs for invoice PDF files stored on S3."""

import logging

import boto3
from botocore.config import Config
from django.conf import settings

logger = logging.getLogger(__name__)


def get_signed_file_url(file_field) -> str | None:
    """
    Return a URL for the invoice PDF.

    - If S3 is configured and the URL isn't already signed, generate a presigned URL.
    - Otherwise return the storage backend's default URL.
    """
    if not file_field:
        return None

    url = file_field.url

    # If already signed or no S3 bucket configured, return as-is
    bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
    if not bucket or "X-Amz-Signature" in url or "Signature=" in url:
        return url

    # Generate presigned S3 URL
    try:
        region = getattr(settings, "AWS_S3_REGION_NAME", None)
        client = boto3.client(
            "s3",
            region_name=region,
            endpoint_url=f"https://s3.{region}.amazonaws.com" if region else None,
            aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", None),
            aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
            config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
        )

        expires = int(getattr(settings, "AWS_QUERYSTRING_EXPIRE", 3600))
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": file_field.name},
            ExpiresIn=expires,
        )
    except Exception as exc:
        logger.exception("Failed to sign URL for %s: %s", file_field.name, exc)
        return url
