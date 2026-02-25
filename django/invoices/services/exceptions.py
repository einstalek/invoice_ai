"""
Service-level exceptions for invoice processing.

These exceptions represent business logic errors and are caught
by view layers to be converted into appropriate HTTP responses.
"""


class InvoiceServiceError(Exception):
    """Base exception for all invoice service errors."""
    pass


class AuthenticationRequiredError(InvoiceServiceError):
    """Raised when user is not authenticated."""
    pass


class NoActiveMembershipError(InvoiceServiceError):
    """Raised when user has no active organization membership."""
    pass


class AdminAccessRequiredError(InvoiceServiceError):
    """Raised when admin role is required but user is not an admin."""
    pass


class SubmissionNotFoundError(InvoiceServiceError):
    """Raised when submission doesn't exist or user lacks access."""
    pass


class InvalidStatusTransitionError(InvoiceServiceError):
    """Raised when attempting an invalid submission status transition."""
    pass


class ReviewPermissionError(InvoiceServiceError):
    """Raised when user lacks permission to perform review action."""
    pass


class InvalidReviewActionError(InvoiceServiceError):
    """Raised when review action is invalid for current state."""
    pass


class ExportPermissionError(InvoiceServiceError):
    """Raised when user lacks permission to export submission."""
    pass


class GoogleCredentialsError(InvoiceServiceError):
    """Raised when Google credentials are missing or invalid."""
    pass


class SelfAssignmentError(InvoiceServiceError):
    """Raised when user tries to assign themselves as reviewer."""
    pass


class InvalidReviewerError(InvoiceServiceError):
    """Raised when selected reviewer is invalid."""
    pass


class SubmissionAlreadyExportedError(InvoiceServiceError):
    """Raised when attempting to export an already exported submission."""
    pass


class SubmissionNotApprovedError(InvoiceServiceError):
    """Raised when attempting to export a non-approved submission."""
    pass


class MissingInvoiceDataError(InvoiceServiceError):
    """Raised when invoice data is missing or invalid."""
    pass


class FileUploadError(InvoiceServiceError):
    """Raised when file upload fails."""
    pass


class ProcessingError(InvoiceServiceError):
    """Raised when invoice processing fails."""
    pass


class OCREmptyError(ProcessingError):
    """Raised when OCR detects no text in the PDF."""
    pass


class ReplicateThrottledError(ProcessingError):
    """Raised when Replicate API is throttled."""
    pass
