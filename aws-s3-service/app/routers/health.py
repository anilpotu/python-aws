from fastapi import APIRouter

from app.schemas.models import MessageResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=MessageResponse)
async def health_check():
    return MessageResponse(message="ok")
