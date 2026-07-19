"""FastAPI router for the Statement Ingestion & Parsing Framework.

Both endpoints require authentication: the resolved :data:`CurrentUser` isolates
statement parsing to the caller (bank statements contain PII and financial
history). Domain errors are raised directly and translated into the unified
error envelope by the global handler registered in :mod:`core.errors`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from auth.dependencies import CurrentUserDep
from core.errors import register_domain_exception
from financial.exceptions import AccountNotFound, AccountOwnershipError
from statements import exceptions, service
from statements.exceptions import (
    CorruptStatement,
    EmptyStatement,
    ExtractionFailed,
    FileTooLarge,
    NormalizationFailed,
    UnsupportedFileType,
    ValidationFailed,
)
from statements.schemas import (
    ImportResponse,
    UploadResponse,
    ValidateResponse,
)

# Register statement domain exceptions with the global envelope handler so the
# API emits a single consistent ``{"error": {"code", "message"}}`` shape instead
# of raw HTTPException text.
register_domain_exception(UnsupportedFileType, 415, "unsupported_file_type")
register_domain_exception(FileTooLarge, 413, "file_too_large")
register_domain_exception(EmptyStatement, 422, "empty_statement")
register_domain_exception(CorruptStatement, 422, "corrupt_statement")
register_domain_exception(ExtractionFailed, 422, "extraction_failed")
register_domain_exception(NormalizationFailed, 422, "normalization_failed")
register_domain_exception(ValidationFailed, 422, "validation_failed")
register_domain_exception(AccountNotFound, 404, "account_not_found")
register_domain_exception(
    AccountOwnershipError, 403, "account_access_denied"
)


router = APIRouter(prefix="/statements", tags=["statements"])


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_statement(
    current_user: CurrentUserDep,
    file: UploadFile = File(...),
) -> UploadResponse:
    """Accept a file upload, detect format, extract, normalize.

    Returns normalized transactions for the authenticated user.
    """
    result = await service.process_upload(file, user_id=current_user.id)
    return UploadResponse(**result)


@router.post(
    "/validate",
    response_model=ValidateResponse,
    status_code=status.HTTP_200_OK,
)
async def validate_statement(
    current_user: CurrentUserDep,
    file: UploadFile = File(...),
) -> ValidateResponse:
    """Validate a statement file without extracting or normalizing.

    Returns a validation result and basic info for the authenticated user.
    """
    result = await service.validate_upload(file, user_id=current_user.id)
    return ValidateResponse(**result)


@router.post(
    "/import",
    response_model=ImportResponse,
    status_code=status.HTTP_200_OK,
)
async def import_statement(
    current_user: CurrentUserDep,
    file: UploadFile = File(...),
    account_id: str = Query(..., description="Target account (must be owned)."),
    auto_categorize: bool = Query(default=True),
) -> ImportResponse:
    """Extract, parse, normalize, and persist a statement's transactions.

    The transactions are booked to ``account_id`` (which must belong to the
    authenticated user) with ``source = statement``. The account balance is
    adjusted atomically for every imported posted transaction.
    """
    import uuid

    try:
        account_uuid = uuid.UUID(account_id)
    except ValueError as exc:
        raise ValidationFailed(
            "Invalid account_id format.",
            details={"account_id": account_id},
        ) from exc

    result = await service.store_statement(
        file,
        user_id=current_user.id,
        account_id=account_uuid,
        auto_categorize=auto_categorize,
    )
    return ImportResponse(**result)
