"""SQS message consumer"""

import json
from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError
from app.infrastructure.sqs.client import get_sqs_client
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SQSConsumer:
    """Consumes messages from SQS queue"""

    def __init__(self):
        self.client = get_sqs_client()
        self.queue_url = settings.sqs_queue_url

    def receive_messages(
        self,
        max_messages: int = 1,
        wait_time_seconds: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Receive messages from the SQS queue.

        Args:
            max_messages: Maximum number of messages to receive (1-10)
            wait_time_seconds: Long polling wait time

        Returns:
            List of message dictionaries
        """
        try:
            response = self.client.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=min(max_messages, 10),
                WaitTimeSeconds=wait_time_seconds,
                MessageAttributeNames=['All']
            )

            messages = response.get('Messages', [])
            if messages:
                logger.info(
                    "messages_received",
                    count=len(messages)
                )
            return messages

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'AWS.SimpleQueueService.NonExistentQueue':
                logger.error("sqs_queue_not_found", queue_url=self.queue_url)
                raise ValueError(f"SQS queue not found: {self.queue_url}")
            logger.error("failed_to_receive_messages", error=str(e))
            raise
        except Exception as e:
            logger.error("failed_to_receive_messages", error=str(e))
            raise

    def parse_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse SQS message.

        Args:
            message: Raw SQS message

        Returns:
            Parsed message dictionary or None if invalid
        """
        try:
            body = json.loads(message.get('Body', '{}'))
            receipt_handle = message.get('ReceiptHandle', '')

            return {
                'job_id': body.get('job_id'),
                'receipt_handle': receipt_handle,
            }
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("failed_to_parse_message", error=str(e))
            return None

    def delete_message(self, receipt_handle: str) -> None:
        """
        Delete a message from the queue.

        Args:
            receipt_handle: Message receipt handle
        """
        try:
            self.client.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle
            )
            logger.debug("message_deleted", receipt_handle=receipt_handle[:20])
        except Exception as e:
            logger.error("failed_to_delete_message", error=str(e))
            raise
