# Module 4: Messaging & Event-Driven Architecture

## Objectives

After completing this module, you will:
- Understand message queues vs. pub/sub patterns
- Design event-driven systems
- Handle idempotency in distributed systems
- Implement retry and backoff strategies
- Design dead-letter queues and failure recovery
- Choose between RabbitMQ, Kafka, SQS/SNS, and alternatives

## 4.1 Message Queues vs. Pub/Sub

Two fundamental messaging patterns:

### Message Queues (Point-to-Point)

One producer, one consumer per message.

```
Producer                Consumer
    ↓
    Enqueue: "Send email to user@example.com"
    ↓
Queue (persistent, durable)
    ↓
Consumer reads
    ↓
Message deleted from queue
```

#### Use Case: Task Distribution

```
API Server (producer):
"ProcessImage" task
↓
Task Queue
├→ Worker 1 processes task
├→ Worker 2 idle
├→ Worker 3 idle

Next task:
"ProcessImage" task
↓
Task Queue
├→ Worker 1 still processing
├→ Worker 2 processes task
├→ Worker 3 idle

Distribution: Each task goes to first available worker.
```

#### Example: RabbitMQ, AWS SQS

```
Producer sends:
{"task": "send_email", "to": "user@example.com"}

Queue holds message.

Consumer polls:
GET message → processes → DELETE

If consumer crashes before DELETE:
Message goes back in queue (auto requeue).
Another consumer processes it.
```

### Pub/Sub (Publish-Subscribe)

One producer, many consumers receive same message.

```
Producer
    ↓
Topic: "order.created"
    ├→ Subscriber 1 (Email Service)
    ├→ Subscriber 2 (Analytics Service)
    ├→ Subscriber 3 (Recommendation Service)
    └→ Subscriber 4 (Inventory Service)

All subscribers receive same message.
```

#### Use Case: Event Broadcasting

```
Order placed event:
{
  "event": "order.placed",
  "order_id": 123,
  "user_id": 456,
  "items": [...],
  "amount": 99.99
}

Email Service: Sends confirmation email
Analytics Service: Logs event for analysis
Recommendation Service: Updates recommendations
Inventory Service: Decrements stock

All receive and process independently.
If one fails, others continue.
```

#### Example: Kafka, AWS SNS

```
Producer publishes event to Topic.

Topic subscribers:
- Email Service gets copy
- Analytics Service gets copy
- Inventory Service gets copy

Each processes independently.
Message isn't deleted until all subscribers acknowledge (or timeout).
```

### Comparison

| Aspect | Message Queue | Pub/Sub |
|---|---|---|
| Consumption | One consumer | All subscribers |
| Message lifetime | Until consumed | Published to all |
| Ordering | Per queue | Per topic |
| Scaling | Distribute work | Broadcast updates |
| Decoupling | Decouples rate | Decouples timing |

## 4.2 Event-Driven Architecture

Design systems around events rather than requests.

### Traditional (Request-Driven)

```
API Request
↓
Synchronous call chain:
Order Service → Payment Service → Inventory Service → Notification Service
    ↓
Response

Problems:
- Chain can't be broken (all must succeed)
- If Payment Service down, entire order fails
- Synchronous blocking (threads wait)
```

### Event-Driven

```
API Request
↓
Order Service: Create order, emit "OrderCreated" event
↓
Return immediately (fast)

Meanwhile:
Event broker (Kafka) publishes event
    ↓
Payment Service: subscribes, processes payment
Inventory Service: subscribes, decrements stock
Notification Service: subscribes, sends email
Analytics Service: subscribes, logs event

Each service independent:
- If Payment down, order still created
- If Inventory down, manually fix later
- If Notification down, retry without blocking user
```

### Event Sourcing

Don't store state, store events (immutable log).

```
State (traditional):
Table: orders
├→ order_id=123, status="paid", user_id=456

Events (event sourcing):
├→ T+0: OrderCreated(order_id=123, user_id=456)
├→ T+1: PaymentProcessed(order_id=123, amount=99.99)
├→ T+2: OrderShipped(order_id=123, tracking_id=TRK123)
├→ T+3: OrderDelivered(order_id=123)

Current state = apply all events in order

Benefits:
- Complete audit trail
- Can rebuild state from events
- Temporal queries ("what was state at T+1?")
```

## 4.3 Idempotency

Critical for reliability: operations that succeed regardless of retries.

### Problem: Network Retries

```
User clicks "Place Order"

Request 1 sent:
POST /api/orders {order_data}

Network timeout (no response for 5 seconds).

User's browser retries:
Request 2 sent (same data)

Server receives both:
Does this create 2 orders or 1 order?

If not idempotent:
- 2 orders created
- Charged twice
- Sent 2 confirmations
- Inventory decremented twice
```

### Solution: Idempotency Keys

Each request has unique ID, operation is idempotent:

```python
@app.route('/api/orders', methods=['POST'])
def create_order():
    # Client must provide idempotency_key
    idempotency_key = request.headers['Idempotency-Key']
    order_data = request.json
    
    # Check if we've already processed this exact request
    existing_order = db.query(
        "SELECT * FROM orders WHERE idempotency_key = ?",
        idempotency_key
    )
    
    if existing_order:
        # We've already created this order, return same response
        return existing_order
    
    # First time seeing this request
    order = create_order_in_db(order_data)
    db.execute(
        "INSERT INTO idempotency_keys (key, order_id) VALUES (?, ?)",
        idempotency_key, order.id
    )
    
    return order
```

**HTTP Header**:
```
POST /api/orders HTTP/1.1
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
```

### Idempotency in Messages

Message consumed multiple times (re-delivered):

```
Consumer reads: {message_id: 123, action: "deduct_balance", amount: 50}

Processing:
1. Check: Have we processed this message_id before?
   SELECT * FROM processed_messages WHERE message_id = 123
   
   Result: Not found (first time)
   
2. Process: Deduct $50 from balance
3. Record: INSERT INTO processed_messages VALUES (123, timestamp)
4. Commit

Later, message redelivered:
1. Check: Have we processed message_id 123?
   Result: Found (already processed)
   
2. Skip processing, return success

Result: Amount deducted exactly once, even if message delivered twice.
```

## 4.4 Retry Strategies

Network failures require retries. But retries must be smart.

### Naive Retry (WRONG)

```python
def call_payment_service(amount):
    for i in range(3):  # Retry 3 times
        try:
            return payment_service.charge(amount)
        except Exception as e:
            print(f"Attempt {i} failed, retrying")
            # Immediately retry (WRONG!)
    
    raise PaymentFailed()

# Problem:
# If payment service is down:
# T+0: Attempt 1 (fails in 1ms, timeout)
# T+1: Attempt 2 (fails in 1ms, timeout)
# T+2: Attempt 3 (fails in 1ms, timeout)
# Total: 3ms wasted, service still down
```

### Exponential Backoff (BETTER)

```python
import random
import time

def call_payment_service(amount):
    max_retries = 3
    base_delay = 1  # 1 second
    
    for attempt in range(max_retries):
        try:
            return payment_service.charge(amount)
        
        except Exception as e:
            if attempt == max_retries - 1:
                raise  # Give up after final attempt
            
            # Exponential backoff: 1s, 2s, 4s
            delay = base_delay * (2 ** attempt)
            
            # Jitter: random variance to prevent thundering herd
            jitter = random.uniform(0, delay * 0.1)
            
            total_delay = delay + jitter
            
            print(f"Attempt {attempt + 1} failed, waiting {total_delay:.1f}s")
            time.sleep(total_delay)
    
    raise PaymentFailed()

# Behavior:
# T+0: Attempt 1 (fails)
# T+1.05: Attempt 2 (fails after 1s + jitter backoff)
# T+3.12: Attempt 3 (fails after 2s + jitter backoff)
# Total: 4.1 seconds of intelligent waiting
```

### Jitter (Prevents Thundering Herd)

```
Without jitter (bad):
T+0: 10,000 retries all wait 2 seconds
T+2: All 10,000 fire simultaneously (thundering herd)

With jitter (good):
T+0: 10,000 retries all wait 2s ± random(0-0.1s)
T+2.05: Retry 1 fires
T+2.07: Retry 2 fires
T+2.09: Retry 3 fires
...
T+2.15: Retry 10,000 fires (spread out)

Prevents overwhelming service.
```

### Circuit Breaker with Retries

When should you stop retrying?

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
def call_payment_service(amount):
    return payment_service.charge(amount)

def place_order(order):
    max_retries = 3
    base_delay = 1
    
    for attempt in range(max_retries):
        try:
            charge_result = call_payment_service(order.amount)
            return create_order(order, charge_result)
        
        except CircuitBreakerOpen:
            # Circuit is open (service failing)
            # Don't retry, fail fast
            raise PaymentServiceUnavailable()
        
        except PaymentServiceError as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.1)
                time.sleep(delay)
            else:
                raise
```

## 4.5 Dead-Letter Queues (DLQ)

When messages fail repeatedly, move them to dead-letter queue.

### Problem: Poison Message

```
Message in queue:
{"operation": "invalid_json": ***

Consumer tries to parse JSON:
  → Fails
  → Retries with backoff
  → Still fails (will always fail)
  → Retries forever
  → Queue blocked, no progress

This is a poison message.
```

### Solution: DLQ

```
Normal Queue
├→ Consumer 1: processes successfully
├→ Consumer 2: processes successfully
├→ Poison Message: fails
    ├→ Retry 1: fails
    ├→ Retry 2: fails
    └→ Retry 3: fails (max retries reached)
       → Move to DLQ

Dead Letter Queue
├→ Manual inspection
├→ Fix issue
├→ Re-queue message

Normal processing continues without blockage.
```

### Implementation

```python
import json
from datetime import datetime

def process_message(queue_name, dlq_name, max_retries=3):
    while True:
        message = queue.get_message(queue_name)
        if not message:
            continue
        
        attempt_count = message.get('attempt_count', 0)
        
        try:
            # Parse and process
            data = json.loads(message['body'])
            process_data(data)
            queue.delete_message(queue_name, message['id'])
        
        except Exception as e:
            attempt_count += 1
            
            if attempt_count >= max_retries:
                # Move to DLQ
                dlq_message = {
                    'original_message': message,
                    'error': str(e),
                    'failed_at': datetime.now().isoformat(),
                    'attempts': attempt_count
                }
                
                queue.send_message(dlq_name, json.dumps(dlq_message))
                queue.delete_message(queue_name, message['id'])
            
            else:
                # Requeue with incremented count
                message['attempt_count'] = attempt_count
                delay = exponential_backoff(attempt_count)
                queue.send_message_with_delay(queue_name, message, delay)
                queue.delete_message(queue_name, message['id'])
```

## 4.6 Choosing Message Systems

### RabbitMQ

```
Model: Message queues + Pub/Sub
Protocol: AMQP (binary, efficient)
Ordering: Per queue
Persistence: Disk-based (durable)
Cluster: Built-in clustering

Good for:
- Task queues (email, image processing)
- Traditional message patterns
- Guaranteed ordering per queue

Bad for:
- High-throughput streaming (100K+ msg/sec)
- Distributed systems at scale
- Long data retention
```

### Apache Kafka

```
Model: Distributed pub/sub, event streams
Protocol: Custom binary
Ordering: Per partition
Persistence: Disk-based, distributed
Cluster: Distributed by design (Zookeeper coordination)

Good for:
- High-throughput event streaming (1M+ msg/sec)
- Event sourcing
- Data pipeline
- Durable event log
- Multi-datacenter replication

Bad for:
- Simple request-response (overkill)
- Traditional task queues (complex for this)
- Operational simplicity (more moving parts)
```

### AWS SQS (Simple Queue Service)

```
Model: Managed message queue
Ordering: Best effort (standard), guaranteed (FIFO)
Persistence: AWS managed (99.99% durability)
Scaling: Automatic

Good for:
- Startup MVP (minimal ops)
- Variable load (auto-scales)
- AWS ecosystem integration
- Task distribution

Bad for:
- Strict ordering (standard SQS doesn't guarantee)
- Real-time (<100ms latency not guaranteed)
- Complex routing
```

### Comparison Table

| Feature | RabbitMQ | Kafka | SQS |
|---|---|---|---|
| Throughput | 50K msg/sec | 1M+ msg/sec | 1M msg/sec |
| Latency | < 10ms | 100ms-1s | 100ms-30s |
| Ordering | Per queue | Per partition | FIFO only |
| Persistence | Optional | Always | Always |
| Operations | Medium | High | Low (managed) |
| Cost | Low (self-hosted) | Medium | Low → High (at scale) |

## 4.7 Production Recommendations

### Monitor Queue Depth

```
Metrics:
- Queue length (messages waiting)
- Consumer lag (oldest message age)
- Processing time per message
- Error rate

Alert if:
- Queue depth growing (consumers can't keep up)
- Consumer lag > 1 minute (SLA violation)
- Error rate > 1% (something broken)
```

### Design for Partial Failures

```
Event publishes to 3 services:
Service A: succeeds
Service B: fails
Service C: fails

Problem: What's the overall status?

Solution: Decouple services via event broker
- Service A completes its work independently
- Service B retries via DLQ
- Service C retries via DLQ

Each service succeeds/fails independently.
System degrades gracefully.
```

### Idempotency is Non-Negotiable

Every async operation must be idempotent:
- Charging payment twice = disaster
- Sending email twice = annoying
- Logging event twice = acceptable

For critical operations, always track processed IDs.

---

## Exam & Practice

### Multiple Choice Questions

**Q1**: You send a message to a queue 3 times (due to retries). Consumer processes it once. What pattern enabled this?

A) Circuit breaker
B) Idempotency key
C) Dead letter queue
D) Exponential backoff

**Q2**: A distributed system has Kafka broker down. Publishing fails immediately. Is this good or bad?

A) Good (fast failure)
B) Bad (need at least some queuing)
C) Depends on use case
D) Kafka never fails

**Q3**: Message takes 5 minutes to process (very slow consumer). Should you retry faster or slower?

A) Faster (more attempts)
B) Slower (exponential backoff)
C) Same delay (don't change retry logic)
D) Never retry (poison message)

**Q4**: You observe queue depth growing (messages accumulating). What's likely happening?

A) Producer is too slow
B) Consumer is too slow
C) Network is slow
D) Queue is running out of space

**Q5**: Two microservices: Service A publishes "OrderCreated", Service B subscribes. Service B crashes for 1 hour. What happens?

A) Events are lost
B) Events wait in queue (Pub/Sub)
C) Events wait in queue (Message Queue)
D) A and B both need repair

### Hands-on Tasks

**Task 1: Idempotent Payment Processing**

Design a payment API that handles retries:
- Client can retry same payment with same idempotency key
- Must charge exactly once
- Charge should be atomic (either fully charged or not)

Implement (pseudocode or real code):
- Idempotency key storage
- Duplicate detection
- Retry handling
- Error responses

**Task 2: Event-Driven Order Processing**

Design an order system with multiple independent services:
- Order Service: creates order
- Payment Service: processes payment
- Inventory Service: reserves stock
- Notification Service: sends confirmation

Any service can fail independently without blocking others.
Design the event flow, DLQ strategy, and monitoring.

### Incident Scenario

**Scenario: Cascading Notification Failures**

Timeline:
- T+0: Promotion starts, 100K orders expected
- T+0: Orders flowing through fine
- T+5min: Email service crashes
- T+5min: "OrderConfirmation" messages pile up in queue
- T+6min: Queue filling with thousands of unprocessed messages
- T+7min: Queue runs out of memory/disk
- T+7min: New messages fail (producers can't add messages)
- T+8min: Order service can't publish events, orders start failing
- T+9min: Entire order system down because notification queue failed

**Questions:**
1. How do you prevent notification failures from crashing order system?
2. What circuit breaker strategy helps?
3. Design a DLQ strategy for this scenario
4. How do you recover from full queue?
5. What monitoring would have caught this?

---

**Next**: [Module 5: Fault Tolerance & Reliability](05-fault-tolerance.md)
