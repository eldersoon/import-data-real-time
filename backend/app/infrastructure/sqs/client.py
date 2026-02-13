"""SQS client configuration"""

import boto3
from botocore.config import Config
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_sqs_client():
    """
    Get configured SQS client.

    Returns:
        Boto3 SQS client
    """
    config = Config(
        region_name=settings.aws_region,
    )

    client_kwargs = {
        "config": config,
    }

    if settings.aws_endpoint_url:
        client_kwargs["endpoint_url"] = settings.aws_endpoint_url

    if settings.aws_access_key_id:
        client_kwargs["aws_access_key_id"] = settings.aws_access_key_id

    if settings.aws_secret_access_key:
        client_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key

    return boto3.client("sqs", **client_kwargs)
