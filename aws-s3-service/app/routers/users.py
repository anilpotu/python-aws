"""Router for user data operations.

Endpoints cover:
  - Reading S3 objects (personal / financial / health files)
  - Inserting, updating, and deleting records in PostgreSQL
  - Fetching DB records and publishing them to SQS
"""

import asyncio
import logging
from datetime import date, datetime

from fastapi import APIRouter, HTTPException

from app.schemas.models import (
    FinancialInfoCreate,
    FinancialInfoRecord,
    FinancialInfoUpdate,
    HealthInfoCreate,
    HealthInfoRecord,
    HealthInfoUpdate,
    MessageResponse,
    PersonalInfoCreate,
    PersonalInfoRecord,
    PersonalInfoUpdate,
    SQSSendRequest,
    SQSSendResponse,
    UserFullRecord,
)
from app.services import db_service, s3_service, sqs_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


# ---------------------------------------------------------------------------
# S3 — read user data files
# ---------------------------------------------------------------------------

@router.get("/{user_id}/s3/personal")
async def read_personal_from_s3(user_id: str) -> dict:
    """Read personal information JSON from S3."""
    try:
        return s3_service.read_personal_info(user_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Personal info not found in S3 for user {user_id}")


@router.get("/{user_id}/s3/financial")
async def read_financial_from_s3(user_id: str) -> dict:
    """Read financial information JSON from S3."""
    try:
        return s3_service.read_financial_info(user_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Financial info not found in S3 for user {user_id}")


@router.get("/{user_id}/s3/health")
async def read_health_from_s3(user_id: str) -> dict:
    """Read health information JSON from S3."""
    try:
        return s3_service.read_health_info(user_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Health info not found in S3 for user {user_id}")


@router.get("/{user_id}/s3/all")
async def read_all_from_s3(user_id: str) -> dict:
    """Read and merge personal, financial, and health information from S3."""
    try:
        return s3_service.read_all_user_info(user_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ---------------------------------------------------------------------------
# PostgreSQL — personal information
# ---------------------------------------------------------------------------

@router.post("/personal", response_model=PersonalInfoRecord, status_code=201)
async def create_personal(body: PersonalInfoCreate):
    """Insert personal information into the database."""
    try:
        record = await db_service.insert_personal(body.model_dump())
    except Exception as exc:
        logger.exception("Failed to insert personal info for user %s", body.user_id)
        raise HTTPException(status_code=409, detail=str(exc))
    return record


@router.get("/{user_id}/personal", response_model=PersonalInfoRecord)
async def get_personal(user_id: str):
    """Fetch personal information from the database."""
    record = await db_service.get_personal(user_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Personal info not found for user {user_id}")
    return record


@router.patch("/{user_id}/personal", response_model=PersonalInfoRecord)
async def update_personal(user_id: str, body: PersonalInfoUpdate):
    """Update personal information in the database."""
    record = await db_service.update_personal(user_id, body.model_dump(exclude_none=True))
    if record is None:
        raise HTTPException(status_code=404, detail=f"Personal info not found for user {user_id}")
    return record


@router.delete("/{user_id}/personal", response_model=MessageResponse)
async def delete_personal(user_id: str):
    """Delete personal information from the database."""
    deleted = await db_service.delete_personal(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Personal info not found for user {user_id}")
    return MessageResponse(message=f"Personal info deleted for user {user_id}")


# ---------------------------------------------------------------------------
# PostgreSQL — financial information
# ---------------------------------------------------------------------------

@router.post("/financial", response_model=FinancialInfoRecord, status_code=201)
async def create_financial(body: FinancialInfoCreate):
    """Insert financial information into the database."""
    try:
        record = await db_service.insert_financial(body.model_dump())
    except Exception as exc:
        logger.exception("Failed to insert financial info for user %s", body.user_id)
        raise HTTPException(status_code=409, detail=str(exc))
    return record


@router.get("/{user_id}/financial", response_model=FinancialInfoRecord)
async def get_financial(user_id: str):
    """Fetch financial information from the database."""
    record = await db_service.get_financial(user_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Financial info not found for user {user_id}")
    return record


@router.patch("/{user_id}/financial", response_model=FinancialInfoRecord)
async def update_financial(user_id: str, body: FinancialInfoUpdate):
    """Update financial information in the database."""
    record = await db_service.update_financial(user_id, body.model_dump(exclude_none=True))
    if record is None:
        raise HTTPException(status_code=404, detail=f"Financial info not found for user {user_id}")
    return record


@router.delete("/{user_id}/financial", response_model=MessageResponse)
async def delete_financial(user_id: str):
    """Delete financial information from the database."""
    deleted = await db_service.delete_financial(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Financial info not found for user {user_id}")
    return MessageResponse(message=f"Financial info deleted for user {user_id}")


# ---------------------------------------------------------------------------
# PostgreSQL — health information
# ---------------------------------------------------------------------------

@router.post("/health", response_model=HealthInfoRecord, status_code=201)
async def create_health(body: HealthInfoCreate):
    """Insert health information into the database."""
    try:
        record = await db_service.insert_health(body.model_dump())
    except Exception as exc:
        logger.exception("Failed to insert health info for user %s", body.user_id)
        raise HTTPException(status_code=409, detail=str(exc))
    return record


@router.get("/{user_id}/health", response_model=HealthInfoRecord)
async def get_health(user_id: str):
    """Fetch health information from the database."""
    record = await db_service.get_health(user_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Health info not found for user {user_id}")
    return record


@router.patch("/{user_id}/health", response_model=HealthInfoRecord)
async def update_health(user_id: str, body: HealthInfoUpdate):
    """Update health information in the database."""
    record = await db_service.update_health(user_id, body.model_dump(exclude_none=True))
    if record is None:
        raise HTTPException(status_code=404, detail=f"Health info not found for user {user_id}")
    return record


@router.delete("/{user_id}/health", response_model=MessageResponse)
async def delete_health(user_id: str):
    """Delete health information from the database."""
    deleted = await db_service.delete_health(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Health info not found for user {user_id}")
    return MessageResponse(message=f"Health info deleted for user {user_id}")


# ---------------------------------------------------------------------------
# PostgreSQL — full user record
# ---------------------------------------------------------------------------

@router.get("/{user_id}", response_model=UserFullRecord)
async def get_user_full(user_id: str):
    """Fetch all stored records (personal, financial, health) for a user."""
    record = await db_service.get_user_full(user_id)
    if not any([record["personal"], record["financial"], record["health"]]):
        raise HTTPException(status_code=404, detail=f"No records found for user {user_id}")
    return record


# ---------------------------------------------------------------------------
# SQS — fetch DB records and publish to queue
# ---------------------------------------------------------------------------

@router.post("/sqs/send", response_model=SQSSendResponse)
async def send_user_data_to_sqs(body: SQSSendRequest):
    """Fetch user data from the database and send it to SQS.

    data_type controls which records are included:
      - "personal"  → only personal info
      - "financial" → only financial info
      - "health"    → only health info
      - "all"       → personal + financial + health
    """
    user_id = body.user_id
    data_type = body.data_type

    if data_type == "personal":
        record = await db_service.get_personal(user_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Personal info not found for user {user_id}")
        payload = {"user_id": user_id, "data_type": "personal", "data": record}

    elif data_type == "financial":
        record = await db_service.get_financial(user_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Financial info not found for user {user_id}")
        payload = {"user_id": user_id, "data_type": "financial", "data": record}

    elif data_type == "health":
        record = await db_service.get_health(user_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Health info not found for user {user_id}")
        payload = {"user_id": user_id, "data_type": "health", "data": record}

    elif data_type == "all":
        full = await db_service.get_user_full(user_id)
        if not any([full["personal"], full["financial"], full["health"]]):
            raise HTTPException(status_code=404, detail=f"No records found for user {user_id}")
        payload = {"user_id": user_id, "data_type": "all", "data": full}

    else:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid data_type '{data_type}'. Must be one of: personal, financial, health, all",
        )

    # asyncpg returns datetime/date objects — convert to strings for JSON serialisation
    payload = _serialisable(payload)

    message_id = await asyncio.to_thread(
        sqs_service.send_message,
        payload,
        message_group_id=body.message_group_id,
        message_deduplication_id=body.message_deduplication_id,
    )
    logger.info("Sent user %s (%s) data to SQS, MessageId=%s", user_id, data_type, message_id)
    return SQSSendResponse(message_id=message_id, user_id=user_id, data_type=data_type)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialisable(obj):
    """Recursively convert non-JSON-serialisable types (date, datetime) to strings."""
    if isinstance(obj, dict):
        return {k: _serialisable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialisable(v) for v in obj]
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return obj
