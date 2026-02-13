"""SQS message publisher"""

import json
import uuid
from app.infrastructure.sqs.client import get_sqs_client
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SQSPublisher:
    """Publishes messages to SQS queue"""

    def __init__(self):
        self.client = get_sqs_client()
        self.queue_url = settings.sqs_queue_url

    def publish_job(self, job_id: uuid.UUID) -> None:
        """
        Publish a job to the SQS queue.

        Args:
            job_id: Job UUID to publish
        """
        try:
            message_body = {
                "job_id": str(job_id),
            }

            response = self.client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message_body),
            )

            logger.info(
                "job_published_to_sqs",
                job_id=str(job_id),
                message_id=response.get("MessageId"),
            )
        except Exception as e:
            logger.error(
                "failed_to_publish_job",
                job_id=str(job_id),
                error=str(e),
            )
            raise
