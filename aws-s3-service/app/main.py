import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import health, s3, sns
from app.routers import users
from app.services import db_service
from app.services.sqs_service import poll_sqs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialise PostgreSQL connection pool
    await db_service.init_pool()

    # Start SQS consumer background task
    stop_event = asyncio.Event()
    sqs_task = asyncio.create_task(poll_sqs(stop_event))

    yield

    # Shutdown
    stop_event.set()
    sqs_task.cancel()
    try:
        await sqs_task
    except asyncio.CancelledError:
        pass

    await db_service.close_pool()


app = FastAPI(
    title="AWS S3 Service",
    description="REST API for S3 file operations, user data (PostgreSQL), SNS notifications, and SQS",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(s3.router)
app.include_router(sns.router)
app.include_router(users.router)
