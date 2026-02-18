import logging

import boto3

from app.config import settings

logger = logging.getLogger(__name__)


def _get_sns_client():
    kwargs = {"region_name": settings.aws_region}
    if settings.aws_endpoint_url:
        kwargs["endpoint_url"] = settings.aws_endpoint_url
    return boto3.client("sns", **kwargs)


def publish_message(message: str, subject: str | None = None) -> str:
    """Publish a message to the configured SNS topic. Returns the MessageId."""
    client = _get_sns_client()
    kwargs = {
        "TopicArn": settings.sns_topic_arn,
        "Message": message,
    }
    if subject:
        kwargs["Subject"] = subject

    response = client.publish(**kwargs)
    message_id = response["MessageId"]
    logger.info("Published SNS message %s to %s", message_id, settings.sns_topic_arn)
    return message_id
