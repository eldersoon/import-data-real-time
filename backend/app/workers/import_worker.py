"""SQS worker for processing import jobs"""

import uuid
import time
from app.infrastructure.sqs.consumer import SQSConsumer
from app.workers.processor import JobProcessor
from app.core.logging import get_logger

logger = get_logger(__name__)


class ImportWorker:
    """Worker that consumes SQS messages and processes jobs"""

    def __init__(self):
        self.consumer = SQSConsumer()
        self.processor = JobProcessor()
        self.running = False

    def start(self) -> None:
        """Start the worker loop."""
        self.running = True
        logger.info("worker_started")

        while self.running:
            try:
                messages = self.consumer.receive_messages(max_messages=1, wait_time_seconds=20)

                if not messages:
                    continue

                for message in messages:
                    parsed = self.consumer.parse_message(message)
                    if not parsed:
                        # Invalid message, delete it
                        self.consumer.delete_message(message.get('ReceiptHandle', ''))
                        continue

                    job_id_str = parsed.get('job_id')
                    receipt_handle = parsed.get('receipt_handle')

                    if not job_id_str:
                        logger.warning("message_missing_job_id")
                        self.consumer.delete_message(receipt_handle)
                        continue

                    try:
                        job_id = uuid.UUID(job_id_str)
                        logger.info("processing_job", job_id=job_id_str)

                        # Process the job
                        self.processor.process_job(job_id)

                        # Delete message after successful processing
                        self.consumer.delete_message(receipt_handle)
                        logger.info("job_processed_successfully", job_id=job_id_str)

                    except ValueError:
                        logger.error("invalid_job_id", job_id=job_id_str)
                        self.consumer.delete_message(receipt_handle)
                    except Exception as e:
                        logger.error("job_processing_error", job_id=job_id_str, error=str(e))
                        # Don't delete message on error - let it retry
                        # In production, you might want to implement dead letter queue

            except KeyboardInterrupt:
                logger.info("worker_stopped_by_user")
                self.running = False
                break
            except Exception as e:
                logger.error("worker_error", error=str(e))
                time.sleep(5)  # Wait before retrying

        logger.info("worker_stopped")


def main():
    """Main entry point for the worker."""
    worker = ImportWorker()
    worker.start()


if __name__ == "__main__":
    main()
