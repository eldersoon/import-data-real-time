#!/bin/bash
# Simple script to create SQS queue using curl

QUEUE_NAME="vehicle-import-queue"
ENDPOINT_URL="${AWS_ENDPOINT_URL:-http://localhost:4566}"
REGION="${AWS_REGION:-us-east-1}"

echo "Creating SQS queue: $QUEUE_NAME"

# Create queue using AWS API via curl
RESPONSE=$(curl -s -X POST \
  "${ENDPOINT_URL}/" \
  -H "Content-Type: application/x-amz-json-1.0" \
  -H "X-Amz-Target: AWSSimpleQueueServiceV20121105.CreateQueue" \
  -d "{
    \"QueueName\": \"${QUEUE_NAME}\",
    \"Attributes\": {
      \"VisibilityTimeout\": \"300\",
      \"MessageRetentionPeriod\": \"345600\"
    }
  }")

if echo "$RESPONSE" | grep -q "QueueUrl"; then
    echo "✅ Queue created successfully!"
    echo "$RESPONSE" | grep -o '"QueueUrl":"[^"]*"' | cut -d'"' -f4
else
    # Check if queue already exists
    QUEUE_URL_RESPONSE=$(curl -s -X POST \
      "${ENDPOINT_URL}/" \
      -H "Content-Type: application/x-amz-json-1.0" \
      -H "X-Amz-Target: AWSSimpleQueueServiceV20121105.GetQueueUrl" \
      -d "{\"QueueName\": \"${QUEUE_NAME}\"}")
    
    if echo "$QUEUE_URL_RESPONSE" | grep -q "QueueUrl"; then
        echo "✅ Queue already exists!"
        echo "$QUEUE_URL_RESPONSE" | grep -o '"QueueUrl":"[^"]*"' | cut -d'"' -f4
    else
        echo "❌ Failed to create queue"
        echo "Response: $RESPONSE"
        exit 1
    fi
fi
