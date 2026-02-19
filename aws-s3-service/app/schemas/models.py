from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, EmailStr


# ---------------------------------------------------------------------------
# Generic S3 / SNS models (existing)
# ---------------------------------------------------------------------------

class S3FileResponse(BaseModel):
    key: str
    content: dict[str, Any]


class S3UpdateRequest(BaseModel):
    content: dict[str, Any]


class S3UploadRequest(BaseModel):
    key: str
    content: dict[str, Any]


class SNSPublishRequest(BaseModel):
    subject: str | None = None
    message: str


class SNSPublishResponse(BaseModel):
    message_id: str


class MessageResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# User personal information
# ---------------------------------------------------------------------------

class PersonalInfoBase(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    address: str | None = None
    date_of_birth: date | None = None


class PersonalInfoCreate(PersonalInfoBase):
    user_id: str


class PersonalInfoUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    date_of_birth: date | None = None


class PersonalInfoRecord(PersonalInfoCreate):
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# User financial information
# ---------------------------------------------------------------------------

class FinancialInfoBase(BaseModel):
    account_number: str | None = None
    credit_score: int | None = None
    annual_income: float | None = None
    total_debt: float | None = None


class FinancialInfoCreate(FinancialInfoBase):
    user_id: str


class FinancialInfoUpdate(FinancialInfoBase):
    pass


class FinancialInfoRecord(FinancialInfoCreate):
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# User health information
# ---------------------------------------------------------------------------

class HealthInfoBase(BaseModel):
    blood_type: str | None = None
    conditions: list[str] = []
    medications: list[str] = []
    allergies: list[str] = []


class HealthInfoCreate(HealthInfoBase):
    user_id: str


class HealthInfoUpdate(HealthInfoBase):
    pass


class HealthInfoRecord(HealthInfoCreate):
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Aggregated user view
# ---------------------------------------------------------------------------

class UserFullRecord(BaseModel):
    user_id: str
    personal: PersonalInfoRecord | None = None
    financial: FinancialInfoRecord | None = None
    health: HealthInfoRecord | None = None


# ---------------------------------------------------------------------------
# SQS payload models
# ---------------------------------------------------------------------------

class SQSSendRequest(BaseModel):
    user_id: str
    data_type: str  # "personal" | "financial" | "health" | "all"
    message_group_id: str | None = None
    message_deduplication_id: str | None = None


class SQSSendResponse(BaseModel):
    message_id: str
    user_id: str
    data_type: str
