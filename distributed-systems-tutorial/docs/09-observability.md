# Module 9: Observability in Distributed Systems

## Objectives

After completing this module, you will:
- Collect and aggregate metrics from distributed systems
- Implement distributed tracing
- Correlate logs across services
- Define SLOs and SLIs
- Design effective alerting
- Build dashboards for system health

## 9.1 Observability Fundamentals

Observability: Understanding system internals from external outputs.

Three pillars:

```
Metrics: Quantitative measurements
├─ CPU utilization: 45%
├─ Request latency: p99 = 200ms
├─ Error rate: 0.5%
├─ Cache hit rate: 92%
└─ Database connections: 45/100

Logs: Structured records of events
├─ [2024-01-15 10:23:45] service=order request_id=123 status=200 latency=45ms
├─ [2024-01-15 10:23:46] service=payment request_id=123 status=failed error=timeout
└─ [2024-01-15 10:23:47] service=email request_id=123 status=queued

Traces: Request flow across services
├─ Request ID: 123
├─ Service A (10ms)
│  └─ Database query (5ms)
├─ Service B (15ms)
│  └─ Cache lookup (1ms)
│  └─ API call (14ms)
└─ Total: 25ms
```

## 9.2 Metrics Collection and Aggregation

### Key Metrics

```
RED Method (for user-facing services):
- Rate: Requests per second
- Errors: Error rate (percent failing)
- Duration: Latency (p50, p95, p99)

USE Method (for infrastructure):
- Utilization: % capacity used
- Saturation: % load waiting for resource
- Errors: Error count
```

### Metrics Collection

```python
from prometheus_client import Counter, Histogram, Gauge

# Counter (monotonically increasing)
requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint']
)

# Histogram (distribution)
request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0]
)

# Gauge (can go up/down)
active_connections = Gauge(
    'http_active_connections',
    'Currently active HTTP connections'
)

# Usage
requests_total.labels(method='GET', endpoint='/api/orders').inc()
request_duration.observe(0.045)  # 45ms request
active_connections.set(25)
```

### Metrics Aggregation Stack

```
Application (Prometheus client)
    ↓
Prometheus Server (scrapes metrics every 15s)
    ↓
Time Series Database (stores metrics)
    ↓
Query Engine
    ↓
Grafana Dashboard (visualization)
    ↓
Alerting Engine (fires alerts on thresholds)
```

## 9.3 Distributed Tracing

Following a request across services.

### Trace Propagation

```
Client sends request to API Gateway:
GET /api/orders/123
Header: X-Trace-ID: 550e8400-e29b-41d4-a716-446655440000

API Gateway:
├─ Extracts trace ID
├─ Logs with trace ID
├─ Forwards to Order Service (X-Trace-ID header)

Order Service:
├─ Receives trace ID
├─ Logs with trace ID
├─ Calls Payment Service (X-Trace-ID header)

Payment Service:
├─ Receives trace ID
├─ Logs with trace ID
├─ Responds

Later: Search logs by trace ID 550e8400-...
All related logs from all services appear together.
```

### Distributed Tracing Implementation

```python
from jaeger_client import Config
import opentelemetry.trace as trace

# Setup tracer
jaeger_config = Config(
    config={
        'sampler': {'type': 'const', 'param': 1},
        'logging': True,
    },
    service_name='order-service',
)
tracer = jaeger_config.initialize_tracer()

# Use tracer
@app.route('/api/orders/<order_id>')
def get_order(order_id):
    span = tracer.start_active_span('get_order')
    
    try:
        # Fetch from database (creates child span)
        with tracer.start_active_span('db_query'):
            order = db.query(order_id)
        
        # Call other service (propagates trace ID)
        with tracer.start_active_span('call_user_service'):
            user = requests.get(
                f'http://user-service/users/{order.user_id}',
                headers={'X-Trace-ID': span.context.trace_id}
            )
        
        return {'order': order, 'user': user}
    
    finally:
        span.finish()

# Result: Full trace with timing for each operation
```

## 9.4 Log Correlation

Bringing logs from multiple services together.

### Structured Logging

```
Bad logging:
log("Error processing order")  # No context

Good structured logging:
log(
    "error_processing_order",
    {
        "trace_id": "550e8400",
        "service": "order-service",
        "order_id": 123,
        "user_id": 456,
        "error": "payment_timeout",
        "timestamp": "2024-01-15T10:23:45Z"
    }
)

Benefits:
- Searchable (trace_id, service, order_id)
- Parseable (JSON format)
- Consistent (standard fields)
```

### ELK Stack (Elasticsearch, Logstash, Kibana)

```
Application (structured logs)
    ↓
Logstash (parses JSON)
    ↓
Elasticsearch (indexes logs)
    ↓
Kibana (search and visualization)

Query: trace_id = 550e8400 AND timestamp > 2024-01-15T10:00:00Z
Result: All logs from all services for that trace

Example: Debug why user's order failed
1. Find order in logs
2. Get trace ID from logs
3. Search all traces with that ID
4. See order → payment → inventory → notification flow
5. Find exactly where it failed
```

## 9.5 SLOs and SLIs

Service Level Objectives (goals) and Indicators (measurements).

### SLI Definition

```
SLI (Service Level Indicator): What we measure

Examples:
- API availability: 99.5% of requests return 200
- API latency: 95% of requests complete in < 500ms
- Database durability: 99.999% of writes persist
- Feature completeness: Core features available

Each SLI is a measurement: 0-100%
```

### SLO Definition

```
SLO (Service Level Objective): What we target

Example SLOs:
- API availability: 99.9% per month (max 43 minutes downtime)
- API latency: 99% of requests < 200ms p99
- Database availability: 99.95% per month
- System reliability: 99.99% availability (four nines)

SLO = target for SLI
```

### Error Budget

```
SLO: 99.9% availability (1 - 99.9% = 0.1% failures allowed)
Per month (30 days): 0.1% * 30 * 24 * 60 = ~43 minutes
Total monthly failure budget: 43 minutes

Usage:
- Jan 1: 15 minutes downtime (28 minutes left)
- Jan 15: Maintenance (10 minutes downtime, 18 minutes left)
- Jan 28: Bug causes 5 minutes outage (13 minutes left)

Error budget: Visual indicator of headroom
```

### SLI Calculation

```python
# Calculate SLI: API latency

total_requests = db.query("SELECT COUNT(*) FROM requests WHERE timestamp > now() - interval '1 day'")
fast_requests = db.query("SELECT COUNT(*) FROM requests WHERE latency < 500ms AND timestamp > now() - interval '1 day'")

sli = (fast_requests / total_requests) * 100
print(f"Latency SLI: {sli}%")  # e.g., 97.5%

# Compare to SLO
slo = 99.0
if sli < slo:
    alert("SLI below SLO")
```

## 9.6 Alerting Strategy

When to alert (and when not to):

### Alert Fatigue

```
Bad: Alert on every anomaly
├─ Alert on 1% deviation: 100 alerts/hour
├─ Team ignores alerts (too many)
├─ Real issues missed
└─ Result: No trust in alerting

Good: Alert on actionable issues
├─ Alert if SLO at risk
├─ Alert if error rate > 5%
├─ Alert if latency > 2x SLA
└─ Result: Team acts immediately
```

### Alert Design

```
AlertRule: HighErrorRate

Condition:
- Error rate > 5% for 5 minutes

Action:
- Page on-call engineer (urgent)
- Log alert
- Create incident ticket

NotAlertRule: LowCacheHitRate

Condition:
- Cache hit rate drops to 85%

Action:
- Create ticket (not urgent)
- Investigate during work hours
- Don't page

Rule: Only page on actionable alerts
```

### Multi-level Alerting

```
Threshold 1 (Warning): 80% capacity
├─ Action: Log alert, create ticket

Threshold 2 (Alert): 90% capacity
├─ Action: Page on-call, declare incident

Threshold 3 (Critical): 99% capacity
├─ Action: Auto-scale, page all on-calls

Benefit: Early warnings (threshold 1) before emergencies (threshold 3)
```

## 9.7 Dashboards and Runbooks

### Example Dashboard: Order Service Health

```
Top row (RED metrics):
├─ Request Rate: 5,000 req/sec (green)
├─ Error Rate: 0.3% (green)
└─ Latency p99: 180ms (green)

Middle row (Dependencies):
├─ Payment Service: 99.8% available (green)
├─ Inventory Service: 99.5% available (yellow, degraded)
└─ User Service: 100% available (green)

Bottom row (Infrastructure):
├─ CPU Utilization: 65% (green)
├─ Memory: 72% (yellow)
├─ Disk: 45% (green)
└─ Active Connections: 450/1000 (green)

Trends (last hour):
├─ Request rate: steady
├─ Error rate: increasing (investigating)
└─ Latency: increasing (investigation needed)
```

### Runbook Structure

```
**Alert: HighErrorRate**

Severity: Urgent
Page: OrderService on-call

Symptoms:
- Alert fires when error rate > 5% for 5 minutes

Investigation:
1. Check recent deployments (might be bad code)
2. Check downstream dependencies (Payment Service status)
3. Check database (replication lag, slow queries)
4. Check infrastructure (CPU, memory, disk)

Remediation:
- If recent deployment: rollback
- If Payment Service down: failover to backup
- If database issue: increase connections, restart

Escalation:
- If unfamiliar with issue: escalate to team lead
- If ongoing > 15 minutes: page backup engineer
- If ongoing > 30 minutes: page senior on-call
```

## 9.8 Production Recommendations

### Observability as Code

```python
# Define SLOs in code (not dashboards)
SLOS = {
    'order_service_availability': {
        'name': 'Order Service Availability',
        'target': 0.999,
        'window': '30d',
        'indicator': 'http_requests_success_rate',
    },
    'payment_latency': {
        'name': 'Payment Processing Latency',
        'target': 0.99,  # 99% < 500ms
        'window': '7d',
        'indicator': 'payment_latency_p99',
        'threshold': 0.5,  # 500ms
    }
}

# Generate alerts from SLOs
for slo_name, config in SLOS.items():
    create_alert_rule(
        name=slo_name,
        metric=config['indicator'],
        threshold=config['target'],
    )
```

### Test Alerting

Regularly test that alerts work:
```
Monthly: Inject failure (kill service, trigger alerts)
Quarterly: Simulate cascading failure
Yearly: Full disaster recovery drill

Don't discover alerts don't work during real incident.
```

---

## Exam & Practice

### Multiple Choice Questions

**Q1**: SLO is 99.9%, achieved 99.2% this month. What's the status?

A) Great, above target
B) Below target, need investigation
C) Good enough
D) Check error budget

**Q2**: Trace ID 550e8400 appears in logs from Service A, B, C. What's true?

A) Services are communicating
B) Same request went through all 3
C) All 3 have the same issue
D) Requests are parallelized

**Q3**: Alert fires on "CPU > 70%". What's the problem?

A) Threshold too high
B) No context (why is CPU high?)
C) Too frequent (alert fatigue)
D) All of above

**Q4**: Error rate is 0.5%, but SLI target is 99%. Does alert fire?

A) Yes (0.5% is bad)
B) No (0.5% is within budget)
C) Depends on error budget remaining
D) Need more information

**Q5**: You instrument every line of code with logging. What happens?

A) Perfect observability
B) Disk fills up (too many logs)
C) Performance degrades (I/O overhead)
D) B and C

### Hands-on Tasks

**Task 1: SLO Definition**

Define SLOs for:
- Order creation API (critical)
- Recommendation service (nice-to-have)
- Analytics processing (background job)

For each specify:
- SLI (what to measure)
- SLO (target)
- Error budget (acceptable downtime)
- Alert thresholds

**Task 2: Distributed Tracing Implementation**

Design tracing system for order processing:
- Client → API Gateway → Order Service → Payment Service → Database
- Capture latency for each hop
- Log any failures

Specify:
- How trace ID propagates
- What to measure
- How to query traces later

### Incident Scenario

**Scenario: Alert Storm from Cascading Issues**

Timeline:
- T+0: Payment Service becomes slow (latency 5s → 50s)
- T+1: Order Service timeout waiting for Payment
- T+2: Order error rate jumps to 5%
- T+2: Alert fires: "HighErrorRate"
- T+3: Alert fires: "HighLatency"
- T+4: Alert fires: "PaymentServiceDown"
- T+5: Alert fires: "DatabaseHighLoad"
- T+6: Alert fires: "DatabaseConnectionPoolExhausted"
- T+7: 10 more alerts fire in rapid succession (alert storm)
- T+8: Team overwhelmed, can't identify root cause
- T+30min: Payment Service restarted, issues clear

**Questions:**
1. Which alert would you have investigated first?
2. How could you reduce alert noise?
3. What's the root cause? (Payment or Database?)
4. Design alert deduplication/grouping strategy
5. How to prioritize alerts during storms?

---

**Next**: [Module 10: Deployment & Scaling Strategies](10-deployment-scaling.md)
