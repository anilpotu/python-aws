import asyncio
import json
import logging

import boto3

from app.config import settings

logger = logging.getLogger(__name__)


def _get_sqs_client():
    kwargs = {"region_name": settings.aws_region}
    if settings.aws_endpoint_url:
        kwargs["endpoint_url"] = settings.aws_endpoint_url
    return boto3.client("sqs", **kwargs)


def _process_message(message: dict) -> None:
    """Process a single SQS message. Customize this with your business logic."""
    body = message.get("Body", "")
    try:
        parsed = json.loads(body)
        logger.info("Processed SQS message: %s", parsed)
    except json.JSONDecodeError:
        logger.info("Processed SQS message (raw): %s", body)


async def poll_sqs(stop_event: asyncio.Event) -> None:
    """Long-poll SQS in a loop until stop_event is set."""
    client = _get_sqs_client()
    logger.info("SQS consumer started, polling %s", settings.sqs_queue_url)

    while not stop_event.is_set():
        try:
            response = await asyncio.to_thread(
                client.receive_message,
                QueueUrl=settings.sqs_queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20,
            )
            messages = response.get("Messages", [])
            for msg in messages:
                _process_message(msg)
                await asyncio.to_thread(
                    client.delete_message,
                    QueueUrl=settings.sqs_queue_url,
                    ReceiptHandle=msg["ReceiptHandle"],
                )
        except Exception:
            logger.exception("Error polling SQS")
            await asyncio.sleep(5)

    logger.info("SQS consumer stopped")
