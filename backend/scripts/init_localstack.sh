#!/bin/bash
# Script to initialize LocalStack and create SQS queue

QUEUE_NAME="vehicle-import-queue"
ENDPOINT_URL="${AWS_ENDPOINT_URL:-http://localhost:4566}"
REGION="${AWS_REGION:-us-east-1}"
MAX_RETRIES=30
RETRY_DELAY=2

echo "Waiting for LocalStack to be ready..."

# Wait for LocalStack to be ready
for i in $(seq 1 $MAX_RETRIES); do
    if curl -s -f "$ENDPOINT_URL/_localstack/health" > /dev/null 2>&1; then
        echo "LocalStack is ready!"
        break
    fi
    if [ $i -eq $MAX_RETRIES ]; then
        echo "LocalStack failed to start after $MAX_RETRIES attempts"
        exit 1
    fi
    echo "Waiting for LocalStack... ($i/$MAX_RETRIES)"
    sleep $RETRY_DELAY
done

echo "Creating SQS queue: $QUEUE_NAME"

# Create queue
aws --endpoint-url=$ENDPOINT_URL \
    --region=$REGION \
    sqs create-queue \
    --queue-name $QUEUE_NAME \
    --attributes VisibilityTimeout=300,MessageRetentionPeriod=345600

if [ $? -eq 0 ]; then
    echo "Queue created successfully!"
    echo "Queue URL: $ENDPOINT_URL/000000000000/$QUEUE_NAME"
    
    # List queues to verify
    echo "Verifying queue..."
    aws --endpoint-url=$ENDPOINT_URL \
        --region=$REGION \
        sqs list-queues
else
    echo "Failed to create queue. It might already exist."
    # Try to get queue URL
    QUEUE_URL=$(aws --endpoint-url=$ENDPOINT_URL \
        --region=$REGION \
        sqs get-queue-url \
        --queue-name $QUEUE_NAME \
        --output text 2>/dev/null)
    
    if [ -n "$QUEUE_URL" ]; then
        echo "Queue already exists: $QUEUE_URL"
        exit 0
    else
        exit 1
    fi
fi
