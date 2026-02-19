import asyncio
import json
import logging
from typing import Any

import boto3

from app.config import settings

logger = logging.getLogger(__name__)


def _get_sqs_client():
    kwargs = {"region_name": settings.aws_region}
    if settings.aws_endpoint_url:
        kwargs["endpoint_url"] = settings.aws_endpoint_url
    return boto3.client("sqs", **kwargs)


# ---------------------------------------------------------------------------
# Producer: send a message to SQS
# ---------------------------------------------------------------------------

def send_message(
    payload: dict[str, Any],
    *,
    message_group_id: str | None = None,
    message_deduplication_id: str | None = None,
) -> str:
    """Send a JSON payload to the configured SQS queue.

    Args:
        payload: Dict that will be JSON-serialised as the message body.
        message_group_id: Required for FIFO queues; ignored for standard queues.
        message_deduplication_id: Required for FIFO queues without content-based
            deduplication; ignored for standard queues.

    Returns:
        The SQS MessageId of the sent message.
    """
    client = _get_sqs_client()
    body = json.dumps(payload)
    kwargs: dict[str, Any] = {
        "QueueUrl": settings.sqs_queue_url,
        "MessageBody": body,
    }
    if message_group_id:
        kwargs["MessageGroupId"] = message_group_id
    if message_deduplication_id:
        kwargs["MessageDeduplicationId"] = message_deduplication_id

    response = client.send_message(**kwargs)
    message_id: str = response["MessageId"]
    logger.info("Sent SQS message %s to %s", message_id, settings.sqs_queue_url)
    return message_id


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
