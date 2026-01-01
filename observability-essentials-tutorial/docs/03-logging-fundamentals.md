# Module 3: Logging Fundamentals

Logging is how applications communicate what's happening. This module covers structured logging, log levels, centralization strategies, and production logging patterns.

## Table of Contents

- [What Are Logs?](#what-are-logs)
- [Log Levels](#log-levels)
- [Structured Logging](#structured-logging)
- [Unstructured vs Structured](#unstructured-vs-structured)
- [Log Correlation](#log-correlation)
- [Logging in Production](#logging-in-production)
- [Common Pitfalls](#common-pitfalls)
- [Real-World Example](#real-world-example)
- [Exam Questions](#exam-questions)
- [Hands-On Tasks](#hands-on-tasks)
- [Production Incident Scenario](#production-incident-scenario)

## What Are Logs?

Logs are timestamped records of events that occurred in your system. Unlike metrics which aggregate data, logs capture individual events in detail.

### Log vs Metric

**Metric**: "Average database query took 250ms"
- One data point summarizing thousands of queries
- Aggregated
- Fixed structure
- Good for alerting

**Log**: "query_type=user_fetch duration_ms=248 user_id=5678 timestamp=2024-01-15T14:32:44Z"
- One record per event
- Raw detail
- Variable structure
- Good for investigation

### Types of Events to Log

**User actions**:
```
user_id=123 action=login ip_address=192.168.1.1 timestamp=2024-01-15T14:32:44Z
```

**System events**:
```
event=pod_started pod=api-server-1 namespace=production restart_count=2
```

**Errors and exceptions**:
```
level=ERROR error_type=DatabaseConnectionError service=user-api attempt=3 error_message="Connection timeout after 5000ms"
```

**State changes**:
```
event=config_reload service=cache old_ttl=3600 new_ttl=7200 config_version=v2.1
```

**Performance events**:
```
endpoint=/api/users duration_ms=2150 status=200 slow=true threshold_ms=1000 user_id=5678
```

## Log Levels

Standard log levels help classify events by severity. Most systems use: DEBUG, INFO, WARN, ERROR, CRITICAL.

### DEBUG: Development and Troubleshooting

**What to log**:
- Function entry/exit
- Variable values
- Loop iterations
- Detailed algorithm steps

**When to enable**:
- Actively debugging a problem
- Local development
- Rarely in production

**Example**:
```json
{
  "timestamp": "2024-01-15T14:32:44.123Z",
  "level": "DEBUG",
  "logger": "cache.redis",
  "message": "Redis get operation started",
  "key": "user:5678",
  "operation_id": "abc-123"
}
```

**Volume**: Very high (10,000+ lines for simple request)

### INFO: Standard Application Events

**What to log**:
- Application startup/shutdown
- Request received/completed
- User actions
- Configuration loaded
- Service connected/disconnected

**When to enable**: Always in production (default level)

**Example**:
```json
{
  "timestamp": "2024-01-15T14:32:44.234Z",
  "level": "INFO",
  "service": "api-server",
  "message": "User created account",
  "user_id": "john-doe",
  "email": "john@example.com",
  "request_id": "abc-123"
}
```

**Volume**: Moderate (100-1000 per minute for typical service)

### WARN: Potentially Problematic Events

**What to log**:
- Retry attempts (database, API calls)
- Fallback behaviors
- Deprecated API usage
- Unusual but non-failing conditions
- Resource warnings (memory, disk)

**When to enable**: Always in production

**Example**:
```json
{
  "timestamp": "2024-01-15T14:32:45.345Z",
  "level": "WARN",
  "service": "payment-processor",
  "message": "Payment API call failed, retrying",
  "retry_count": 1,
  "max_retries": 3,
  "error": "Connection timeout",
  "payment_id": "pay-5678"
}
```

**Volume**: Low to moderate (should trigger investigation)

### ERROR: Problems That Don't Stop Service

**What to log**:
- Failed operations that could be retried
- Validation failures
- Request errors (4xx, 5xx)
- Exceptions caught and handled
- Database query failures

**When to enable**: Always in production

**Example**:
```json
{
  "timestamp": "2024-01-15T14:32:46.456Z",
  "level": "ERROR",
  "service": "user-api",
  "message": "Database query failed",
  "query": "SELECT * FROM users WHERE id = ?",
  "error_type": "DatabaseConnectionError",
  "error_message": "Connection refused",
  "user_id": 5678,
  "request_id": "abc-123",
  "duration_ms": 5000
}
```

**Volume**: Should be minimal (<0.1% of logs in healthy system)

### CRITICAL: System Cannot Continue

**What to log**:
- Unrecoverable errors
- Data corruption detected
- System panics
- Crashes
- Security violations

**When to enable**: Always (immediate action required)

**Example**:
```json
{
  "timestamp": "2024-01-15T14:32:47.567Z",
  "level": "CRITICAL",
  "service": "data-store",
  "message": "Data corruption detected in index",
  "corruption_type": "btree_invariant_violation",
  "block_id": 12345,
  "action": "shutting_down"
}
```

**Volume**: Rare (should never happen in normal operation)

## Structured Logging

Structured logging means logs are formatted as machine-parseable key-value pairs (usually JSON), not free-form text.

### Why Structured Logging?

**Unstructured log**:
```
2024-01-15 14:32:44 User john tried to access user 5678 but was denied due to permission error
```

Problems:
- Can't parse programmatically
- Difficult to search for specific values
- Can't aggregate ("how many permission errors today?")
- Can't correlate with other systems

**Structured log**:
```json
{
  "timestamp": "2024-01-15T14:32:44Z",
  "level": "WARN",
  "user_id": "john",
  "action": "access_attempt",
  "target_user_id": 5678,
  "error": "permission_denied",
  "request_id": "abc-123"
}
```

Benefits:
- Easily parsed
- Can search: `error="permission_denied"`
- Can aggregate: `count by (error)`
- Easy to correlate with other logs using request_id

### Structured Log Format

**JSON is standard**:
```json
{
  "timestamp": "2024-01-15T14:32:44.123456Z",
  "level": "INFO",
  "logger": "auth.service",
  "message": "User authenticated",
  "user_id": "john-doe",
  "auth_method": "oauth",
  "request_id": "req-abc-123-def-456",
  "trace_id": "trace-xyz-789",
  "duration_ms": 234,
  "service": "auth-api",
  "version": "v1.2.3",
  "environment": "production"
}
```

**Key fields**:

| Field | Required | Purpose |
|-------|----------|---------|
| timestamp | Yes | ISO 8601 format, microsecond precision |
| level | Yes | DEBUG, INFO, WARN, ERROR, CRITICAL |
| message | Yes | Human-readable description |
| logger | Yes | Component generating log (service.module) |
| request_id | Yes | Correlate logs across services |
| trace_id | No | For distributed tracing |
| service | Yes | Which service generated log |
| user_id | If applicable | Who triggered this action |
| duration_ms | For operations | How long operation took |
| error | If error | Error type or message |
| tags | No | Custom fields for filtering |

### Log Sampling in Code

```python
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'service': 'user-api',
            'version': 'v1.0.0',
            'environment': 'production'
        }
        # Add exception info if present
        if record.exc_info:
            log_obj['error'] = str(record.exc_info[1])
            log_obj['error_type'] = record.exc_info[0].__name__
        return json.dumps(log_obj)

# In your application
def authenticate_user(username, password, request_id):
    try:
        user = db.query(User).filter_by(username=username).first()
        if not user:
            logger.warning(
                'Authentication failed',
                extra={
                    'user': username,
                    'reason': 'user_not_found',
                    'request_id': request_id
                }
            )
            return None
        
        if not user.verify_password(password):
            logger.warning(
                'Authentication failed',
                extra={
                    'user_id': user.id,
                    'reason': 'invalid_password',
                    'request_id': request_id
                }
            )
            return None
        
        logger.info(
            'User authenticated',
            extra={
                'user_id': user.id,
                'request_id': request_id,
                'duration_ms': 45
            }
        )
        return user
    except Exception as e:
        logger.error(
            'Authentication error',
            extra={
                'user': username,
                'request_id': request_id
            },
            exc_info=True  # Include stack trace
        )
        raise
```

## Unstructured vs Structured

### Example: Request Lifecycle

**Unstructured**:
```
2024-01-15 14:32:44 api-server Got request GET /api/users/123 from 192.168.1.1
2024-01-15 14:32:44 auth-service Checking auth for user 456
2024-01-15 14:32:44 cache-service Cache miss for user:123
2024-01-15 14:32:44 database-service Running query SELECT * FROM users WHERE id=123
2024-01-15 14:32:45 database-service Query completed in 845ms
2024-01-15 14:32:45 api-server Returning user data, 23 bytes
```

To find all logs for this request:
- Can't! No correlation ID
- Would need to grep timestamps (unreliable, overlapping)

**Structured**:
```json
{"timestamp":"2024-01-15T14:32:44Z","level":"INFO","service":"api-server","message":"Request started","method":"GET","path":"/api/users/123","request_id":"abc-123","client_ip":"192.168.1.1"}
{"timestamp":"2024-01-15T14:32:44Z","level":"INFO","service":"auth-service","message":"Auth check started","request_id":"abc-123","user_id":456}
{"timestamp":"2024-01-15T14:32:44Z","level":"INFO","service":"cache-service","message":"Cache lookup","request_id":"abc-123","key":"user:123","hit":false}
{"timestamp":"2024-01-15T14:32:44Z","level":"INFO","service":"database-service","message":"Query started","request_id":"abc-123","query_type":"select_user"}
{"timestamp":"2024-01-15T14:32:45Z","level":"INFO","service":"database-service","message":"Query completed","request_id":"abc-123","duration_ms":845}
{"timestamp":"2024-01-15T14:32:45Z","level":"INFO","service":"api-server","message":"Response sent","request_id":"abc-123","status":200,"response_bytes":23,"total_duration_ms":1050}
```

To find all logs for this request:
```
filter(request_id="abc-123")
# Returns all 6 logs instantly
```

## Log Correlation

Correlation is how you connect logs across services.

### Request ID (Most Important)

Every request should have a unique ID that flows through all services.

**Generation** (entry point):
```python
# In API Gateway
request_id = str(uuid.uuid4())
# Add to response headers for client tracking
headers['X-Request-ID'] = request_id
```

**Propagation** (between services):
```python
# In downstream service
@app.before_request
def before_request():
    request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
    # All logs in this request use this ID
    g.request_id = request_id

# In logging
logger.info('Doing something', extra={'request_id': g.request_id})

# When calling another service
requests.get(
    'http://other-service/api',
    headers={'X-Request-ID': g.request_id}
)
```

### Trace ID (Distributed Tracing)

For advanced tracing, use W3C Trace Context:

```
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
tracestate: vendor=value
```

**In Python**:
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("process_user") as span:
    # All logs in this span have trace context
    user = process_user_data(user_id)
```

### Span ID (Within Request)

Each discrete operation gets a span:

```
request_id: abc-123          # Top level
├─ span_id: auth-001        # Auth check
├─ span_id: cache-002       # Cache lookup
├─ span_id: db-003          # Database query
└─ span_id: response-004    # Response encoding
```

Each log includes: `request_id`, `span_id`, `trace_id` for full correlation.

## Logging in Production

### Volume and Cost

Logging at scale is expensive:

```
Typical application: 100 logs per request
Peak traffic: 100 requests/second
= 10,000 logs/second
= 36 billion logs per day
= ~10-15 TB daily storage (raw)
```

### Sampling Strategy

Don't log everything.

**Sample by log level**:
```python
if level == 'ERROR' or 'CRITICAL':
    # Log everything
    sample_rate = 1.0
elif level == 'WARN':
    # Log 50% of warnings
    sample_rate = 0.5
elif level == 'INFO':
    # Log 10% of info
    sample_rate = 0.1
else:
    # Log 0% of debug (unless explicitly enabled)
    sample_rate = 0.0
```

**Sample by user/session**:
```python
# Log all requests from premium users
# Log 1% of requests from free users
user_tier = get_user_tier(user_id)
sample_rate = 1.0 if user_tier == 'premium' else 0.01
```

**Sample errors always**:
```python
if level == 'ERROR':
    sample_rate = 1.0  # Never drop errors
```

### Retention Policy

```
Hot tier (0-7 days):    
  - Full resolution
  - All fields searchable
  - High cost
  
Warm tier (7-30 days):  
  - Indexed by error, user_id
  - Older fields not searchable
  - Medium cost
  
Cold tier (30-365 days):
  - Archive only
  - Compliance/audit
  - Low cost
```

### Rate Limiting and Backpressure

Application logs are network calls. High volume can overwhelm:

```python
import asyncio
from pythonaioqueue import Queue

# Async logging with bounded queue
class AsyncLogger:
    def __init__(self, max_queue=10000):
        self.queue = Queue(maxsize=max_queue)
        asyncio.create_task(self._send_logs())
    
    async def log(self, message):
        try:
            self.queue.put_nowait(message)
        except asyncio.QueueFull:
            # Queue full - drop low-priority logs
            if message['level'] == 'DEBUG':
                return
            # Retry for important logs
            await self.queue.put(message)
    
    async def _send_logs(self):
        while True:
            batch = []
            for _ in range(100):  # Batch size
                try:
                    batch.append(self.queue.get_nowait())
                except:
                    break
            if batch:
                await self._send_batch(batch)
            await asyncio.sleep(0.1)
```

## Common Pitfalls

### Pitfall 1: Logging PII (Personally Identifiable Information)

**Problem**:
```json
{"level":"ERROR","email":"john@example.com","ssn":"123-45-6789","credit_card":"4111-1111-1111-1111"}
```

Compliance issue, security risk.

**Solution**:
```json
{"level":"ERROR","email":"john@example.com [redacted]","ssn":"XXX-XX-XXXX","credit_card":"****-****-****-1111"}
```

Or better:
```json
{"level":"ERROR","user_id":"5678","request_id":"abc-123"}
// Join with secure log viewer that has access to user details
```

### Pitfall 2: Logging at Wrong Level

**Problem**:
```python
# This is an error, not a warning
logger.warning('Database connection failed')

# This is debug, not info
logger.info('Processing item 12345 of 50000')
```

Causes alert fatigue or missed errors.

**Solution**:
```python
# Use correct level
logger.error('Database connection failed')
logger.debug('Processing item 12345 of 50000')
```

### Pitfall 3: Missing Context

**Problem**:
```json
{"level":"ERROR","message":"Operation failed"}
```

Nobody can debug this - what operation? Failed why?

**Solution**:
```json
{"level":"ERROR","message":"Database update failed","operation":"user_update","user_id":5678,"error":"constraint_violation","request_id":"abc-123"}
```

### Pitfall 4: Unstructured Exception Logs

**Problem**:
```python
except Exception as e:
    logger.error(f"Error occurred: {str(e)}")
```

Stack trace is just text, not queryable.

**Solution**:
```python
except Exception as e:
    logger.error(
        'Operation failed',
        extra={
            'error_type': type(e).__name__,
            'error_message': str(e),
            'operation': 'user_update',
            'user_id': user_id
        },
        exc_info=True  # Add stack trace
    )
```

### Pitfall 5: Logging Sensitive Operations Without Rate Limiting

**Problem**:
```
1M failed login attempts from attacker
Each logs 1KB
= 1GB of logs per second
System collapses
```

**Solution**:
```python
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=100, period=60)  # Max 100 logs per minute
def log_failed_auth(username):
    logger.warning('Auth failed', extra={'user': username})
```

## Real-World Example

### E-Commerce Order Processing

**System**: Order service that processes purchases

```python
import logging
import json
import uuid
from datetime import datetime
from functools import wraps

# Setup structured logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'service': 'order-processor',
            'version': '1.0.0',
            'environment': 'production'
        }
        
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'order_id'):
            log_data['order_id'] = record.order_id
        if hasattr(record, 'duration_ms'):
            log_data['duration_ms'] = record.duration_ms
            
        if record.exc_info:
            log_data['error'] = str(record.exc_info[1])
            log_data['error_type'] = record.exc_info[0].__name__
            
        return json.dumps(log_data)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger(__name__)
logger.addHandler(handler)

def log_duration(func):
    """Decorator to log function duration"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start) * 1000
            logger.info(
                f'{func.__name__} completed',
                extra={'duration_ms': int(duration_ms)}
            )
            return result
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            logger.error(
                f'{func.__name__} failed',
                extra={'duration_ms': int(duration_ms)},
                exc_info=True
            )
            raise
    return wrapper

class OrderProcessor:
    def __init__(self, db, payment_service, notification_service):
        self.db = db
        self.payment = payment_service
        self.notifications = notification_service
    
    def process_order(self, order_id, user_id, request_id):
        """Process a customer order"""
        
        logger.info(
            'Order processing started',
            extra={
                'order_id': order_id,
                'user_id': user_id,
                'request_id': request_id
            }
        )
        
        try:
            # Get order
            order = self._get_order(order_id, request_id)
            if not order:
                logger.error(
                    'Order not found',
                    extra={
                        'order_id': order_id,
                        'request_id': request_id
                    }
                )
                return False
            
            # Process payment
            try:
                payment_result = self._process_payment(order, request_id)
                if not payment_result:
                    logger.error(
                        'Payment failed',
                        extra={
                            'order_id': order_id,
                            'amount': order.total,
                            'reason': 'payment_declined',
                            'request_id': request_id
                        }
                    )
                    return False
            except Exception as e:
                logger.error(
                    'Payment processing error',
                    extra={
                        'order_id': order_id,
                        'error': str(e),
                        'request_id': request_id
                    },
                    exc_info=True
                )
                return False
            
            logger.info(
                'Payment processed',
                extra={
                    'order_id': order_id,
                    'amount': order.total,
                    'payment_method': payment_result.method,
                    'request_id': request_id
                }
            )
            
            # Update order status
            self._update_order_status(order_id, 'paid', request_id)
            
            # Send notification
            try:
                self.notifications.send_order_confirmation(
                    order_id,
                    user_id,
                    request_id
                )
                logger.info(
                    'Confirmation email sent',
                    extra={
                        'order_id': order_id,
                        'user_id': user_id,
                        'request_id': request_id
                    }
                )
            except Exception as e:
                # Email failure doesn't block order
                logger.warning(
                    'Failed to send confirmation email',
                    extra={
                        'order_id': order_id,
                        'error': str(e),
                        'request_id': request_id
                    }
                )
            
            logger.info(
                'Order processing completed',
                extra={
                    'order_id': order_id,
                    'user_id': user_id,
                    'status': 'success',
                    'request_id': request_id
                }
            )
            return True
            
        except Exception as e:
            logger.error(
                'Order processing failed',
                extra={
                    'order_id': order_id,
                    'user_id': user_id,
                    'request_id': request_id
                },
                exc_info=True
            )
            return False
    
    @log_duration
    def _get_order(self, order_id, request_id):
        return self.db.query(Order).filter_by(id=order_id).first()
    
    @log_duration
    def _process_payment(self, order, request_id):
        return self.payment.charge(order.total, request_id)
    
    @log_duration
    def _update_order_status(self, order_id, status, request_id):
        self.db.query(Order).filter_by(id=order_id).update({'status': status})
        self.db.commit()
```

**Sample logs from processing an order**:
```json
{"timestamp":"2024-01-15T14:32:44Z","level":"INFO","logger":"order_processor","message":"Order processing started","service":"order-processor","version":"1.0.0","environment":"production","order_id":"ord-123","user_id":"5678","request_id":"abc-123"}
{"timestamp":"2024-01-15T14:32:44Z","level":"INFO","logger":"order_processor","message":"Payment processed","service":"order-processor","version":"1.0.0","environment":"production","order_id":"ord-123","amount":99.99,"payment_method":"visa","request_id":"abc-123","duration_ms":234}
{"timestamp":"2024-01-15T14:32:45Z","level":"INFO","logger":"order_processor","message":"Confirmation email sent","service":"order-processor","version":"1.0.0","environment":"production","order_id":"ord-123","user_id":"5678","request_id":"abc-123"}
{"timestamp":"2024-01-15T14:32:45Z","level":"INFO","logger":"order_processor","message":"Order processing completed","service":"order-processor","version":"1.0.0","environment":"production","order_id":"ord-123","user_id":"5678","status":"success","request_id":"abc-123"}
```

All logs correlated with `request_id`. Can query all logs for a specific order or user instantly.

## Exam Questions

1. **What is the primary advantage of structured logging over unstructured logging?**
   - A. Structured logs are shorter and use less storage
   - B. Structured logs can be machine-parsed, searched, and aggregated
   - C. Structured logs are easier for humans to read
   - D. Structured logs don't require timestamps

2. **Which log level should be used for retry attempts that eventually succeed?**
   - A. DEBUG
   - B. INFO
   - C. WARN
   - D. ERROR

3. **What is the purpose of a request_id in logs?**
   - A. To identify the log server
   - B. To correlate logs from a single request across multiple services
   - C. To measure log processing time
   - D. To encrypt sensitive log data

4. **Why is high-volume logging of PII problematic?**
   - A. It makes logs harder to read
   - B. It increases file size slightly
   - C. It creates security and compliance violations
   - D. It makes dashboards slower

5. **In a microservices architecture, what is the minimum set of correlation fields in every log?**
   - A. timestamp and level
   - B. message and service
   - C. request_id, service, and timestamp
   - D. user_id and error_type

## Hands-On Tasks

### Task 1: Implement Structured Logging

**Objective**: Add structured JSON logging to a simple application

**Requirements**:
1. Choose a language (Python recommended)
2. Create an application with 3 endpoints
3. Implement JSON logging with:
   - timestamp (ISO 8601)
   - level (INFO, WARN, ERROR)
   - message
   - service name
   - request_id
   - relevant business fields
4. Generate request_id for each request
5. Log at least 3 events per request (start, operation, end)

**Example structure (Python Flask)**:
```python
from flask import Flask, request, g
import json
import logging
import uuid
from datetime import datetime

app = Flask(__name__)

# Setup JSON logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'service': 'my-app',
            'request_id': getattr(g, 'request_id', 'unknown'),
            'message': record.getMessage()
        })

# ... setup handler ...

@app.before_request
def before_request():
    g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
    logger.info(f'Request started: {request.method} {request.path}')

@app.route('/api/test', methods=['GET'])
def test():
    logger.info('Processing test endpoint')
    # ... do work ...
    logger.info('Test endpoint completed')
    return {'result': 'ok'}

@app.after_request
def after_request(response):
    logger.info(f'Response sent: {response.status_code}')
    return response
```

**Acceptance criteria**:
- Application running and accepting requests
- All logs in valid JSON format
- request_id present in all logs
- 3+ log events per request
- Logs can be parsed with `jq` or similar

### Task 2: Create Log Correlation Analysis

**Objective**: Trace a request through multiple services

**Setup**:
1. Create 3 separate services (can be simple Flask/Express apps)
   - Service A (entry point)
   - Service B (business logic)
   - Service C (database)
2. Each service logs with request_id
3. Service A calls B, which calls C
4. Implement proper request_id propagation through HTTP headers

**Task**:
1. Make a request to Service A
2. Collect all logs generated
3. Show how you would filter logs by request_id
4. Demonstrate that you can reconstruct the request flow from logs

**Example query** (for Loki in next module):
```
{service=~"service-[a-c]"} | json request_id="abc-123"
```

**Acceptance criteria**:
- 3 services running and communicating
- request_id propagated through all services
- All logs in structured JSON
- Can show complete request flow from logs
- Query/filter demonstrates correlation

## Production Incident Scenario

### Scenario: Log Volume Explosion

**Background**:
Your log aggregation system is approaching storage limits. Log volume increased 50x overnight. No obvious changes were made.

**System facts**:
- 20 services generating logs
- 5 billion logs/day previously
- Now 250 billion logs/day
- Mostly ERROR level logs
- Storage costs multiplied by 50x

**Your Task**:

1. **Identify root cause**:
   - What could cause 50x growth?
   - How would you pinpoint which service?
   - What logs queries would help?

2. **Immediate action**:
   - How would you reduce volume without losing critical data?
   - What would you do first?

3. **Investigation**:
   - Which service is causing this?
   - Why did it start logging excessively?
   - How would you extract and analyze logs?

4. **Prevention**:
   - What monitoring would catch this faster?
   - What log sampling would prevent future incidents?
   - What alerting thresholds?

5. **Root cause scenarios** (pick most likely):
   - A. New code deployment with debug logging left enabled
   - B. Data pipeline processing 1000x more records
   - C. Misconfigured retry loop logging on each attempt
   - D. Upstream service started logging raw user data

**Deliverables**:
- Root cause analysis
- Immediate remediation steps (commands/code)
- Log queries used to investigate
- Proposed monitoring and alerting
- Code changes to prevent recurrence

---

**Next Module**: [Module 4: Log Aggregation with Loki & Fluent Bit](04-loki-fluent-bit.md)

---

**Version**: 1.0  
**Time to Complete**: 4-6 hours  
**Key Concepts**: Log levels, structured logging, JSON format, correlation, sampling, retention
