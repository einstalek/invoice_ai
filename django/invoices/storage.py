import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage
try:
    from storages.backends.s3boto3 import S3Boto3Storage
except Exception:
    S3Boto3Storage = None


def get_invoice_storage():
    if os.getenv("DJANGO_COLLECTSTATIC") == "1":
        return FileSystemStorage(location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL)
    bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
    if not bucket:
        raise RuntimeError(
            "AWS_STORAGE_BUCKET_NAME must be set to store invoice PDFs. "
            "Configure S3 or disable invoice uploads."
        )
    if not S3Boto3Storage:
        raise RuntimeError(
            "django-storages is required for S3 invoice storage. "
            "Install it and configure AWS credentials."
        )
    return S3Boto3Storage()
