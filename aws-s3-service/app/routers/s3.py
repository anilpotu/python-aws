from fastapi import APIRouter, HTTPException

from app.schemas.models import S3FileResponse, S3UpdateRequest, S3UploadRequest, MessageResponse
from app.services import s3_service, sns_service

router = APIRouter(prefix="/s3", tags=["s3"])


@router.get("/{key:path}", response_model=S3FileResponse)
async def read_file(key: str):
    """Read a JSON file from S3."""
    try:
        content = s3_service.read_json_file(key)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {key}")
    return S3FileResponse(key=key, content=content)


@router.put("/{key:path}", response_model=S3FileResponse)
async def update_file(key: str, body: S3UpdateRequest):
    """Update (merge) a JSON file in S3 and notify via SNS."""
    try:
        updated = s3_service.update_json_file(key, body.content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {key}")

    sns_service.publish_message(
        message=f"S3 file updated: {key}",
        subject="S3 File Update",
    )
    return S3FileResponse(key=key, content=updated)


@router.post("/upload", response_model=MessageResponse)
async def upload_file(body: S3UploadRequest):
    """Upload a new JSON file to S3 and notify via SNS."""
    s3_service.upload_json_file(body.key, body.content)
    sns_service.publish_message(
        message=f"S3 file uploaded: {body.key}",
        subject="S3 File Upload",
    )
    return MessageResponse(message=f"Uploaded {body.key}")
