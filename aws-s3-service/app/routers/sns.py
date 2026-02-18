from fastapi import APIRouter

from app.schemas.models import SNSPublishRequest, SNSPublishResponse
from app.services import sns_service

router = APIRouter(prefix="/sns", tags=["sns"])


@router.post("/publish", response_model=SNSPublishResponse)
async def publish(body: SNSPublishRequest):
    """Publish a custom message to the configured SNS topic."""
    message_id = sns_service.publish_message(
        message=body.message,
        subject=body.subject,
    )
    return SNSPublishResponse(message_id=message_id)
