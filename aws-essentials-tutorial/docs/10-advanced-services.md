# Module 10: Advanced Services Overview

This module covers advanced AWS services that enable event-driven, scalable, and serverless architectures. These services are often overlooked but solve critical problems elegantly.

## 10.1 Event-Driven Architecture

Instead of applications constantly polling for work, services notify each other when events occur. Decouples systems and improves scalability.

```
Traditional (Polling):
Application polls database every second
    "Any new orders?"
    → Database: No
    → Database: No
    → Database: Yes! (new order placed 2 seconds ago)
    → Delay: 0-2 seconds to process order

Event-Driven:
Order placed → SNS publishes "OrderCreated" event
    ↓
Payment service subscribes, processes immediately
    ↓
Fulfillment service subscribes, packs order immediately
    ↓
Latency: < 100ms
```

## 10.2 SNS: Simple Notification Service

SNS publishes messages to subscribers. Use for loosely coupled systems.

### Publisher-Subscriber Pattern

```bash
# Create topic
aws sns create-topic --name OrderEvents

# Subscribe services
aws sns subscribe --topic-arn arn:aws:sns:us-east-1:123456789012:OrderEvents \
  --protocol lambda \
  --notification-endpoint arn:aws:lambda:us-east-1:123456789012:function:ProcessPayment

aws sns subscribe --topic-arn arn:aws:sns:us-east-1:123456789012:OrderEvents \
  --protocol lambda \
  --notification-endpoint arn:aws:lambda:us-east-1:123456789012:function:PackOrder

# Publish event
aws sns publish --topic-arn arn:aws:sns:us-east-1:123456789012:OrderEvents \
  --message '{
    "orderId": "order-123",
    "customerId": "customer-456",
    "amount": 99.99,
    "timestamp": "2024-01-15T10:00:00Z"
  }'

# Both ProcessPayment and PackOrder functions invoked automatically
```

Benefits:
- Payment service doesn't know about fulfillment
- Easy to add new subscribers without changing publisher
- Scaling: Publish to 100,000 subscribers instantly

## 10.3 SQS: Simple Queue Service

SQS queues messages. Use for asynchronous processing and decoupling.

### Queue vs. Topic

| Aspect | SNS (Topic) | SQS (Queue) |
|--------|-----------|-----------|
| Pattern | Publish-subscribe | Producer-consumer |
| Delivery | All subscribers immediately | One consumer at a time |
| Retention | Discarded after delivery | Until deleted by consumer |
| Use case | Notifications | Tasks, jobs, buffering |

```bash
# Create queue
aws sqs create-queue --queue-name OrderProcessing

# Producer sends message
aws sqs send-message --queue-url https://queue.amazonaws.com/123456789012/OrderProcessing \
  --message-body '{"orderId": "order-123"}'

# Consumer receives and processes
aws sqs receive-message --queue-url https://queue.amazonaws.com/123456789012/OrderProcessing \
  --max-number-of-messages 10

# Consumer deletes message after processing
aws sqs delete-message --queue-url https://queue.amazonaws.com/123456789012/OrderProcessing \
  --receipt-handle "..."
```

Use SQS for:
- Buffering burst load (queue messages, process at steady rate)
- Retry logic (message stays in queue if processing fails)
- Batch processing (consumer pulls 10 messages, processes all)

## 10.4 EventBridge

EventBridge routes events between AWS services and custom applications.

### Event-Driven Workflows

```bash
# Rule: When EC2 instance state changes to "stopped"
aws events put-rule --name stopped-instance-cleanup \
  --event-pattern '{
    "source": ["aws.ec2"],
    "detail-type": ["EC2 Instance State-change Notification"],
    "detail": {"state": ["stopped"]}
  }'

# Target: Invoke Lambda to clean up resources
aws events put-targets --rule stopped-instance-cleanup \
  --targets Id=1,Arn=arn:aws:lambda:us-east-1:123456789012:function:cleanup

# When EC2 stops, Lambda automatically invoked
```

Use cases:
- Stop task when EC2 terminates
- Process CloudTrail events
- Scheduled tasks (cron-like)
- Cross-account event routing

## 10.5 Lambda: Serverless Functions

Run code without managing servers. Pay per execution.

### Lambda Architecture

```python
import json
import boto3

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    # event: Input (S3 file upload, API request, etc.)
    # context: Runtime info (function name, remaining time, etc.)
    
    # Process event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    # Download file
    obj = s3.get_object(Bucket=bucket, Key=key)
    content = obj['Body'].read()
    
    # Store in DynamoDB
    table = dynamodb.Table('Files')
    table.put_item(Item={'key': key, 'size': len(content)})
    
    # Return response
    return {
        'statusCode': 200,
        'body': json.dumps({'processed': True})
    }
```

### Execution Models

**Direct invocation**: Synchronous
```bash
aws lambda invoke --function-name my-function \
  --payload '{"key": "value"}' \
  response.json

# Waits for function to return
# Returns immediately: {"statusCode": 200, ...}
```

**Async invocation**: Fire and forget
```bash
aws lambda invoke --function-name my-function \
  --invocation-type Event \
  --payload '{"key": "value"}' \
  response.json

# Returns immediately, function runs in background
```

### Limitations

- **Timeout**: 15 minute maximum
- **Memory**: 128 MB to 10 GB
- **Ephemeral storage**: 512 MB to 10 GB (/tmp directory)
- **Concurrent executions**: 1000 default (per account)

Use Lambda for:
- API endpoints (via API Gateway)
- Scheduled tasks (via EventBridge)
- Event processing (S3 uploads, DynamoDB changes)

Don't use Lambda for:
- Long-running jobs (> 15 minutes)
- Compute-intensive tasks (expensive)
- State-heavy applications

## 10.6 API Gateway

API Gateway exposes your applications to the internet. Handles HTTPS, throttling, authentication.

### REST API

```bash
# Create API
aws apigateway create-rest-api --name my-api

# Create resource and method
RESOURCE_ID=$(aws apigateway get-resources --rest-api-id abc123 \
  --query 'items[?path==`/`].id' --output text)

aws apigateway put-method --rest-api-id abc123 \
  --resource-id $RESOURCE_ID \
  --http-method GET \
  --authorization-type NONE

# Integrate with Lambda
aws apigateway put-integration --rest-api-id abc123 \
  --resource-id $RESOURCE_ID \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:123456789012:function:my-function/invocations

# Deploy
aws apigateway create-deployment --rest-api-id abc123 \
  --stage-name prod
```

API Gateway provides:
- HTTPS automatically
- Rate limiting (throttling)
- API keys and authentication
- CORS handling
- Request/response transformation
- Caching

## 10.7 Step Functions: Orchestration

Step Functions coordinate multi-step workflows. Useful for complex business logic.

```json
{
  "Comment": "Order processing workflow",
  "StartAt": "ValidateOrder",
  "States": {
    "ValidateOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:validate-order",
      "Next": "ProcessPayment"
    },
    "ProcessPayment": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:process-payment",
      "Catch": [
        {
          "ErrorEquals": ["PaymentFailed"],
          "Next": "NotifyCustomer"
        }
      ],
      "Next": "ShipOrder"
    },
    "ShipOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:ship-order",
      "Next": "Success"
    },
    "NotifyCustomer": {
      "Type": "Task",
      "Resource": "arn:aws:sns:...:send-notification",
      "End": true
    },
    "Success": {
      "Type": "Succeed"
    }
  }
}
```

Features:
- Visual workflow editor
- Error handling and retries
- Parallel execution
- Choice logic (if-then)
- State persistence (can resume after long waits)

## 10.8 Architecture Example: Serverless Event-Driven System

```
User uploads file to S3
    ↓
S3 triggers Lambda
    ↓
Lambda processes file, publishes "FileProcessed" event to SNS
    ↓
Payment service subscribes: Charges user
    ↓
Notification service subscribes: Sends email
    ↓
API Gateway exposes results via REST endpoint
    ↓
Lambda queries DynamoDB for status
    ↓
Returns JSON response

Cost model:
- User uploads: 0 cost (S3 PUT)
- Lambda processing: $0.0000002 per request + $0.0000166667 per GB-second
- SNS publish: $0.50 per million
- DynamoDB query: $0.25 per million requests

Total cost: < $0.01 per user operation
vs. running EC2 24/7: $30-100/month
```

## 10.9 Common Mistakes

**Mistake 1: Lambda for everything**
Lambda has 15-minute timeout and can't run compute-intensive jobs. Use EC2 for long tasks.

**Mistake 2: SQS dead-letter queues not configured**
Messages that fail 3 times disappear. Send them to dead-letter queue for investigation.

**Mistake 3: SNS for request-response**
SNS publishes to multiple subscribers. If you need one consumer, use SQS.

**Mistake 4: EventBridge rules too broad**
Rule matching every event = high costs. Be specific with event patterns.

**Mistake 5: No idempotency in handlers**
If Lambda is invoked twice (network retry), process message twice. Always make operations idempotent.

## Assessment

### Practice Questions

**Q1: Task queue with retry logic. Use:**
A) SNS (topic)
B) SQS (queue)
C) EventBridge
D) Lambda

**Q2: Lambda function timeout 15 minutes. Run 1-hour batch job?**
A) Extend timeout (not possible)
B) Use EC2 or ECS
C) Chain multiple Lambdas
D) Stream processing (Kinesis)

**Q3: Notify 1000 subscribers of new event. Use:**
A) SQS (1000 queues?)
B) SNS (topic with 1000 subscribers)
C) EventBridge (rule routing)
D) Lambda (invoke all)

**Q4: S3 file upload triggers processing. Event source?**
A) S3 event notifications to SNS/SQS/Lambda
B) Lambda polling S3
C) CloudTrail monitoring S3
D) EventBridge rule

**Q5: Step function retry failed task 3 times. Configuration?**
A) Lambda internal retry
B) Step function Retry policy
C) SNS dead-letter queue
D) Not possible

### Hands-On Labs

**Lab 1: SNS/SQS Event Routing**

Create SNS topic, SQS queue, publish events, verify delivery.

**Lab 2: Lambda & API Gateway**

Create Lambda function, expose via API Gateway, test HTTP requests.

### Production Incident Scenario

**Scenario: Event Loss During Surge**

Black Friday: Traffic surge 100x normal. Messages published to SNS but subscribers can't keep up.

Problem: SNS delivers to subscribers in parallel. If subscriber is slow, messages pile up in memory.

Solution (already implemented):
- Payment service has SQS queue as SNS subscriber
- SNS publishes to SQS
- Payment service consumes from SQS at its own pace
- If SQS queue grows, auto-scaling increases consumers

Architecture:
```
SNS → SQS → Auto-scaling consumer fleet
(messages persist)   (independent scaling)
```

Prevention:
- Always use queues for async processing
- Don't subscribe Lambda directly to SNS (Lambda has concurrency limit)
- Monitor queue depth and scale consumers
- Set up alarms for queue depth > threshold

---

Next: [Final Project: Production-Ready AWS Deployment](../final-project.md)
