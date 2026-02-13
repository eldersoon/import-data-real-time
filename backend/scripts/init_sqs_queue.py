#!/usr/bin/env python3
"""Script to initialize SQS queue in LocalStack"""

import os
import sys
import time
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, EndpointConnectionError

QUEUE_NAME = "vehicle-import-queue"
ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
REGION = os.getenv("AWS_REGION", "us-east-1")
MAX_RETRIES = 30
RETRY_DELAY = 2


def wait_for_localstack():
    """Wait for LocalStack to be ready"""
    import urllib.request
    
    print("Waiting for LocalStack to be ready...")
    for i in range(1, MAX_RETRIES + 1):
        try:
            urllib.request.urlopen(f"{ENDPOINT_URL}/_localstack/health", timeout=2)
            print("LocalStack is ready!")
            return True
        except Exception:
            if i == MAX_RETRIES:
                print(f"LocalStack failed to start after {MAX_RETRIES} attempts")
                return False
            print(f"Waiting for LocalStack... ({i}/{MAX_RETRIES})")
            time.sleep(RETRY_DELAY)
    return False


def create_queue():
    """Create SQS queue"""
    config = Config(
        region_name=REGION,
        retries={'max_attempts': 3}
    )
    
    sqs = boto3.client(
        'sqs',
        endpoint_url=ENDPOINT_URL,
        aws_access_key_id='test',
        aws_secret_access_key='test',
        config=config
    )
    
    try:
        # Try to get queue URL first
        response = sqs.get_queue_url(QueueName=QUEUE_NAME)
        queue_url = response['QueueUrl']
        print(f"Queue already exists: {queue_url}")
        return queue_url
    except ClientError as e:
        if e.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
            # Queue doesn't exist, create it
            print(f"Creating SQS queue: {QUEUE_NAME}")
            try:
                response = sqs.create_queue(
                    QueueName=QUEUE_NAME,
                    Attributes={
                        'VisibilityTimeout': '300',
                        'MessageRetentionPeriod': '345600'
                    }
                )
                queue_url = response['QueueUrl']
                print(f"Queue created successfully!")
                print(f"Queue URL: {queue_url}")
                
                # Verify by listing queues
                print("Verifying queue...")
                queues = sqs.list_queues()
                print(f"Available queues: {queues.get('QueueUrls', [])}")
                
                return queue_url
            except Exception as e:
                print(f"Failed to create queue: {e}")
                sys.exit(1)
        else:
            print(f"Error checking queue: {e}")
            sys.exit(1)


def main():
    """Main function"""
    if not wait_for_localstack():
        sys.exit(1)
    
    # Wait a bit more for services to be fully ready
    time.sleep(3)
    
    queue_url = create_queue()
    print(f"\n✅ Queue initialized: {queue_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
