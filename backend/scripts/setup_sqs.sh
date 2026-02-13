#!/bin/bash
# Script to setup SQS queue in LocalStack

QUEUE_NAME="vehicle-import-queue"
ENDPOINT_URL="http://localhost:4566"
REGION="us-east-1"

echo "Creating SQS queue: $QUEUE_NAME"

aws --endpoint-url=$ENDPOINT_URL \
    --region=$REGION \
    sqs create-queue \
    --queue-name $QUEUE_NAME

if [ $? -eq 0 ]; then
    echo "Queue created successfully!"
    echo "Queue URL: $ENDPOINT_URL/000000000000/$QUEUE_NAME"
else
    echo "Failed to create queue. Make sure LocalStack is running."
    exit 1
fi
