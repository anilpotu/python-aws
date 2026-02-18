import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import health, s3, sns
from app.services.sqs_service import poll_sqs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    stop_event = asyncio.Event()
    sqs_task = asyncio.create_task(poll_sqs(stop_event))
    yield
    stop_event.set()
    sqs_task.cancel()
    try:
        await sqs_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="AWS S3 Service",
    description="REST API for S3 file operations with SNS notifications and SQS consumer",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(s3.router)
app.include_router(sns.router)
