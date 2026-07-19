"""FastAPI router for the Statement Ingestion & Parsing Framework."""

from __future__ import annotations

from fastapi import APIRouter, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse

from apps.backend.statements import service
from apps.backend.statements.exceptions import (
    UnsupportedFileType,
    FileTooLarge,
    EmptyStatement,
    CorruptStatement,
    ExtractionFailed,
    NormalizationFailed,
    ValidationFailed,
)
from apps.backend.statements.schemas import UploadResponse, ValidateResponse


router = APIRouter(prefix="/statements", tags=["statements"])


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_200_OK)
async def upload_statement(file: UploadFile = File(...)):
    """
    Accept a file upload, detect format, extract, normalize, and return normalized transactions.
    """
    try:
        result = await service.process_upload(file)
        return UploadResponse(**result)
    except UnsupportedFileType as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(exc),
        ) from exc
    except FileTooLarge as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(exc),
        ) from exc
    except (EmptyStatement, CorruptStatement, ExtractionFailed, NormalizationFailed) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # pragma: no cover - unexpected
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {exc}",
        ) from exc


@router.post("/validate", response_model=ValidateResponse, status_code=status.HTTP_200_OK)
async def validate_statement(file: UploadFile = File(...)):
    """
    Validate a statement file without extracting or normalizing.
    Returns validation result and basic info.
    """
    try:
        result = await service.validate_upload(file)
        return ValidateResponse(**result)
    except UnsupportedFileType as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(exc),
        ) from exc
    except FileTooLarge as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(exc),
        ) from exc
    except (EmptyStatement, CorruptStatement) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # pragma: no cover - unexpected
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {exc}",
        ) from exc

