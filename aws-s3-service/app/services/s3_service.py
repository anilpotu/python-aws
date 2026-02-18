import json
import logging
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)


def _get_s3_client():
    kwargs = {"region_name": settings.aws_region}
    if settings.aws_endpoint_url:
        kwargs["endpoint_url"] = settings.aws_endpoint_url
    return boto3.client("s3", **kwargs)


def read_json_file(key: str) -> dict[str, Any]:
    """Read a JSON file from S3 and return its contents as a dict."""
    client = _get_s3_client()
    try:
        response = client.get_object(Bucket=settings.s3_bucket_name, Key=key)
        body = response["Body"].read().decode("utf-8")
        return json.loads(body)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchKey":
            raise FileNotFoundError(f"S3 key not found: {key}") from e
        raise


def update_json_file(key: str, updates: dict[str, Any]) -> dict[str, Any]:
    """Read a JSON file from S3, merge updates into it, and upload it back."""
    existing = read_json_file(key)
    existing.update(updates)
    upload_json_file(key, existing)
    return existing


def upload_json_file(key: str, content: dict[str, Any]) -> None:
    """Upload a JSON dict to S3 as a file."""
    client = _get_s3_client()
    body = json.dumps(content, indent=2)
    client.put_object(
        Bucket=settings.s3_bucket_name,
        Key=key,
        Body=body.encode("utf-8"),
        ContentType="application/json",
    )
    logger.info("Uploaded JSON file to s3://%s/%s", settings.s3_bucket_name, key)
