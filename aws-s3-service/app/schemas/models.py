from typing import Any

from pydantic import BaseModel


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
