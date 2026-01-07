# Advanced AWS: Serverless & Lambda at Scale

## Overview

This module covers **AWS Lambda** and serverless computing patterns for production workloads. You'll learn how Lambda fits into your infrastructure, cost optimization, cold start mitigation, and when serverless is the right choice.

## Mental Model

```
Event Source (API Gateway, S3, DynamoDB)
        ↓
    CloudWatch Event / SNS / SQS
        ↓
    Lambda Function Invocation
        ↓
    Cold Start (first invocation) OR Warm Start (reused container)
        ↓
    Function Execution
    - Code runs
    - AWS services are called
        ↓
    Response to caller
        ↓
    CloudWatch Logs
    (Execution metrics, custom logs)
        ↓
    Cost = (GB-seconds × $0.0000166667) + (invocations × $0.0000002)
```

## What This Module Covers

1. **Lambda Fundamentals** - Functions, execution model, permissions
2. **Lambda Event Sources** - API Gateway, SQS, DynamoDB Streams
3. **Cold Start Optimization** - Reducing initialization time
4. **Lambda Concurrency** - Reserved vs provisioned capacity
5. **Production Patterns** - Error handling, retries, dead letter queues
6. **Cost Optimization** - Right-sizing memory, timeout tuning
7. **Observability** - CloudWatch metrics, X-Ray tracing
8. **Lambda Limitations** - When NOT to use serverless

## Key Concepts

### Lambda Execution Model

```
┌─────────────────────────────────┐
│ Lambda Container (created once) │
│                                 │
│  1. Initialize runtime (Python, Node, etc.)
│  2. Run function code
│  3. Create global variables (reused across invocations)
│
│  Subsequent calls reuse this container
└─────────────────────────────────┘

Cold Start: ~1000ms (create container + init runtime)
Warm Start: ~10ms (reuse container)
```

### Lambda Memory and CPU

Lambda **memory allocation determines CPU allocation**:

```
Memory | CPU Cores | Price per GB-second | Good for
-------|-----------|---------------------|----------
128MB  | 0.125     | $0.000016667        | Simple webhooks
512MB  | 0.5       | $0.000016667        | API endpoints
1024MB | 1         | $0.000016667        | Processing jobs
3008MB | 2         | $0.000016667        | Heavy computation
```

**Key insight:** More memory = more CPU = faster execution = sometimes cheaper!

```python
# Example: Processing a 100MB file
# Option 1: 512MB, takes 60 seconds
#   Cost: 60 × 0.512GB × $0.0000167 = $0.000512

# Option 2: 1024MB, takes 30 seconds (2x CPU)
#   Cost: 30 × 1.024GB × $0.0000167 = $0.000512
# Same cost but 2x faster!
```

### Lambda with API Gateway

```python
import json

def lambda_handler(event, context):
    """
    API Gateway sends HTTP request as event.
    We must return in a specific format.
    """
    
    # Parse request
    http_method = event['httpMethod']
    path = event['path']
    body = json.loads(event.get('body', '{}'))
    
    # Process
    if http_method == 'POST' and path == '/users':
        user_id = create_user(body)
        return {
            'statusCode': 201,
            'body': json.dumps({'id': user_id}),
            'headers': {'Content-Type': 'application/json'}
        }
    
    return {
        'statusCode': 404,
        'body': json.dumps({'error': 'Not found'})
    }
```

## Cold Start Mitigation

Cold starts are Lambda's biggest pain point. Here's how to minimize them:

### Strategy 1: Provisioned Concurrency

```bash
# Reserve container capacity—guaranteed warm starts
aws lambda put-provisioned-concurrency-config \
  --function-name my-api \
  --provisioned-concurrent-executions 10 \
  --qualifier LIVE

# Cost: ~$0.015/hour per concurrent execution
# Trade-off: Pay even if not used, but guaranteed fast response
```

### Strategy 2: Keep Functions Small

```python
# ❌ WRONG: Heavy initialization in handler
import pandas  # Large library, 50MB
import numpy

def lambda_handler(event, context):
    # Initialization happens EVERY cold start
    df = pandas.read_csv(event['file'])
    # ...process...
    return result

# ✅ RIGHT: Move heavy imports outside handler
# Initialization happens once, reused across requests
import pandas
import numpy

def lambda_handler(event, context):
    # This code reuses pandas library from previous invocation
    df = pandas.read_csv(event['file'])
    return result
```

### Strategy 3: Use Lambda Layers for Common Code

```bash
# Package common libraries
mkdir python
pip install requests -t python/lib/python3.9/site-packages/

zip -r layer.zip python/

# Upload layer
aws lambda publish-layer-version \
  --layer-name common-libs \
  --zip-file fileb://layer.zip \
  --compatible-runtimes python3.9

# Reference in function
aws lambda update-function-code \
  --function-name my-function \
  --zip-file fileb://function.zip

aws lambda update-function-configuration \
  --function-name my-function \
  --layers arn:aws:lambda:us-east-1:123456789:layer:common-libs:1
```

## Production Pattern: Async Processing with SQS

```python
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sqs = boto3.client('sqs')
s3 = boto3.client('s3')

QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/123456789/process-queue'

def api_handler(event, context):
    """API endpoint: receive request, queue for processing"""
    
    # Quick response to user
    data = json.loads(event['body'])
    
    # Send to processing queue
    sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps({
            'user_id': data['user_id'],
            'file_url': data['file_url']
        })
    )
    
    return {
        'statusCode': 202,
        'body': json.dumps({'status': 'Processing started'})
    }

def processor_handler(event, context):
    """SQS consumer: process messages from queue"""
    
    for record in event['Records']:
        try:
            message = json.loads(record['body'])
            
            # Do actual processing
            result = process_file(message['file_url'])
            
            # Save result
            s3.put_object(
                Bucket='results',
                Key=f"{message['user_id']}/result.json",
                Body=json.dumps(result)
            )
            
        except Exception as e:
            logger.error(f"Failed to process: {e}")
            # Message goes to DLQ (Dead Letter Queue)
            raise
```

## Common Mistakes

**Mistake 1: Expecting immediate responses from async operations**
```python
# ❌ WRONG
def api_handler(event, context):
    result = process_large_file()  # Takes 60 seconds!
    return {'statusCode': 200, 'body': result}
    # Client times out after 30 seconds

# ✅ RIGHT: Use SQS for async work
def api_handler(event, context):
    sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=event['body'])
    return {'statusCode': 202, 'body': 'Processing started'}
```

**Mistake 2: Not setting timeout appropriately**
```bash
# ❌ WRONG: Default 3 second timeout for 60-second job
aws lambda create-function --function-name process-job --timeout 3

# ✅ RIGHT: Match job requirements
aws lambda create-function --function-name process-job --timeout 900  # 15 minutes
```

**Mistake 3: No error handling in SQS consumer**
```python
# ❌ WRONG: Silent failures
def handler(event, context):
    for record in event['Records']:
        process_record(record)  # If this fails, message lost

# ✅ RIGHT: Structured error handling
def handler(event, context):
    for record in event['Records']:
        try:
            process_record(record)
        except Exception as e:
            logger.error(f"Failed: {e}")
            raise  # Lambda will retry, eventually DLQ
```

**Mistake 4: Storing state in global variables across invocations**
```python
# ❌ WRONG: Assumes same container reused
CACHE = {}

def handler(event, context):
    key = event['key']
    if key not in CACHE:
        CACHE[key] = expensive_lookup(key)  # Empty on cold start
    return CACHE[key]

# ✅ RIGHT: Use ElastiCache or DynamoDB
def handler(event, context):
    value = dynamodb.get_item(Key={'key': event['key']})
    return value
```

**Mistake 5: Lambda function doing too much**
```python
# ❌ WRONG: Single function handles everything
def lambda_handler(event, context):
    if event['type'] == 'user.created':
        send_welcome_email()
    elif event['type'] == 'order.placed':
        process_payment()
    elif event['type'] == 'inventory.low':
        reorder_stock()
    # 30 different responsibilities = hard to test, hard to scale
```

## Production Incident Scenario

### Scenario: "Lambda functions randomly timing out under load"

**Symptoms:**
- Functions complete in 5 seconds normally
- Under load, 20% fail with timeout error
- Timeout is 30 seconds
- CloudWatch shows high duration but not exceeding timeout

**Investigation:**

```bash
# 1. Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --start-time 2025-01-06T10:00:00Z \
  --end-time 2025-01-06T11:00:00Z \
  --period 60 \
  --statistics Average,Maximum

# Result: Average 5s, Maximum 28s, but graph shows spikes

# 2. Check concurrent execution limit
aws lambda get-concurrency --function-name my-api

# 3. See CloudWatch logs
aws logs tail /aws/lambda/my-api --follow

# Logs show: "Waiting in queue... for 15 seconds before execution"
```

**Root Cause:** Function hit **concurrent execution limit** (default 1000 per account, can be lower). Extra invocations queue up, then timeout while waiting.

**Solution:**

```bash
# 1. Increase reserved concurrency
aws lambda put-function-concurrency \
  --function-name my-api \
  --reserved-concurrent-executions 500

# 2. Monitor again
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --statistics Maximum

# 3. Alert when duration approaches timeout
aws cloudwatch put-metric-alarm \
  --alarm-name lambda-duration-high \
  --metric-name Duration \
  --namespace AWS/Lambda \
  --statistic Maximum \
  --threshold 20  # Alert if any function takes > 20 seconds
```

**Prevention:**
- Monitor concurrency utilization continuously
- Set alarms when approaching limits
- Use provisioned concurrency for critical functions
- Test with realistic load before deploying

## Practice Questions

1. **Scenario:** Your Lambda function needs to fetch data from RDS every invocation. It's slow. What's the problem?
   - Why? RDS connection setup is slow. Solution: Use RDS Proxy, connection pooling, or cache with ElastiCache.

2. **Decision:** You need to process 10,000 images daily. Lambda or EC2?
   - Why? Lambda if bursty (all 10K at once), EC2 if steady (spread throughout day).

3. **Cost:** Function runs 1 million times/month, average 300MB memory, 5 seconds duration. Estimate monthly cost.
   - Calculation: 1M invocations × $0.0000002 + (1M × 5s × 0.3GB × $0.0000167) = $0.25

## Further Reading

- [AWS Lambda best practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [Lambda cold start benchmark](https://mikhail.io/serverless/coldstarts/aws/)
- [Concurrency limits and scaling](https://docs.aws.amazon.com/lambda/latest/dg/concurrent-executions.html)

---

**Next:** Explore AWS RDS and database patterns in the final advanced module.
