# PROJECT 2: Distributed Systems & Event-Driven Architecture

**A complex distributed system demonstrating scalability, resilience, and cloud-native patterns.**

---

## 🎯 Problem Statement

### Real-World Context
As products scale, single-service monoliths hit limits:
- Database becomes bottleneck (can't shard in monolith)
- Different services need different scaling profiles
- Teams can't deploy independently
- Technology choices locked in (all Flask, all PostgreSQL)

### This Project Solves
Building a **microservices platform** that:
1. **Decouples services** via async messaging
2. **Scales independently** (order service scales 10x, inventory stays 2x)
3. **Handles failures gracefully** (if email service down, orders still process)
4. **Distributes data** (order DB separate from inventory DB)
5. **Implements observability** across service boundaries
6. **Manages distributed transactions** (eventual consistency)

### Architecture Pattern
**Event-driven microservices** with:
- User Service (manages users/auth)
- Order Service (processes orders)
- Inventory Service (tracks stock)
- Payment Service (handles payments)
- Notification Service (sends emails/SMS)
- All communicating via message queue (RabbitMQ/Kafka)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Client Applications                        │
└────────────────────────┬────────────────────────────────────┘
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
┌───▼─────────┐   ┌──────▼──────┐   ┌────────▼──────┐
│   API GW    │   │    API GW    │   │    API GW     │
│  (US East)  │   │    (EU)      │   │    (AP)       │
└───┬─────────┘   └──────┬───────┘   └────────┬──────┘
    │                    │                    │
    └────────────────────┼────────────────────┘
                         │
    ┌────────────────────┼────────────────────────┬──────────┐
    │                    │                        │          │
┌───▼──────────┐  ┌──────▼──────┐  ┌─────────────▼──┐  ┌────▼─────┐
│ User Service │  │Order Service│  │Inventory Svc   │  │Payment Svc
│   (Flask)    │  │ (Go)        │  │  (Node.js)     │  │ (Python)
│   + Postgres │  │ + Postgres  │  │ + MongoDB      │  │ + Postgres
└───┬──────────┘  └──────┬──────┘  └─────────┬──────┘  └────┬──────┘
    │                    │                   │              │
    └────────────────────┼───────────────────┼──────────────┘
                         │                   │
         ┌───────────────┼───────────────────┼──────────┐
         │               │                   │          │
     ┌───▼────────┐  ┌──▼──────┐  ┌─────────▼──┐  ┌───▼─────┐
     │ RabbitMQ   │  │  Redis   │  │    Kafka   │  │ DynamoDB
     │ (Events)   │  │ (Cache)  │  │  (Events)  │  │(Notifications)
     └───┬────────┘  └──┬───────┘  └─────────┬──┘  └────┬────┘
         │              │                    │          │
         └──────────────┼────────────────────┴──────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
    ┌────▼────┐  ┌─────▼──────┐  ┌───▼──────┐
    │Prometheus     │  Jaeger    │  │CloudWatch
    │(Metrics)      │  (Tracing) │  │(Logs)
    └────┬────┘  └─────┬──────┘  └───┬──────┘
         │             │            │
         └─────────────┼────────────┘
                       │
             ┌─────────▼──────────┐
             │  Grafana Dashboard │
             │  + Alerts          │
             └────────────────────┘
```

### Service Responsibilities

| Service | Purpose | Technology | Scaling |
|---|---|---|---|
| **User Service** | Auth, profiles, permissions | Flask + PostgreSQL | 3 pods (stable load) |
| **Order Service** | Process orders, manage state | Go + PostgreSQL | 5-20 pods (high variance) |
| **Inventory Service** | Track stock, reservations | Node.js + MongoDB | 2-5 pods |
| **Payment Service** | Handle payments, reconciliation | Python + PostgreSQL | 2-10 pods |
| **Notification Service** | Emails, SMS, push notifications | Python + SQS | 1-3 pods (async) |

### Request Flow Example (Place Order)

```
1. Client: POST /api/orders
   Headers: Authorization: Bearer JWT
   Body: {product_id: 123, quantity: 5}

2. API Gateway routes to Order Service

3. Order Service:
   a. Validate JWT (call User Service or cache)
   b. Check inventory (call Inventory Service)
   c. Create order (PostgreSQL)
   d. Publish "OrderCreated" event to RabbitMQ

4. Message Queue listeners:
   a. Payment Service: Attempts payment
   b. Inventory Service: Reserves stock
   c. Notification Service: Queues confirmation email

5. Async processing:
   a. Payment succeeds → "PaymentProcessed" event
   b. Inventory reserves → "StockReserved" event
   c. When all complete → "OrderConfirmed" event
   d. Email sent asynchronously

6. Client gets response immediately:
   {order_id: 789, status: "pending"}
   
   Real-world processing happens in background

7. WebSocket or polling updates client:
   Order confirmed → email sent
```

---

## 🔧 Technology Decisions

### Why Event-Driven (Not Direct Calls)?

**Direct calls (synchronous):**
```python
# Order Service calls Inventory Service directly
def place_order(order):
    if not inventory_service.has_stock(order.product_id):
        return error("Out of stock")
    payment = payment_service.charge(order.amount)
    # If payment fails, inventory was checked but order might still be created
```

**Problems:**
- If Inventory Service is slow, Order Service waits
- If Payment Service is down, entire order process fails
- No retry mechanism (lost requests)
- Tight coupling (hard to change independently)

**Event-driven (asynchronous):**
```python
def place_order(order):
    # Create order immediately
    order = Order.create(order)
    
    # Publish event, return immediately
    event_bus.publish("OrderCreated", order)
    return order  # Still pending
    
# Separate listener processes event
@event_listener("OrderCreated")
def on_order_created(order):
    if not inventory.has_stock(order.product_id):
        event_bus.publish("OrderFailed", {"reason": "out_of_stock"})
        return
    
    payment = payment_service.charge(order.amount)
    event_bus.publish("PaymentProcessed", payment)
```

**Benefits:**
- Services decouple (no direct calls)
- Resilient (message queue retries)
- Scalable (process events in parallel)
- Observable (audit trail of all events)

---

### Why RabbitMQ (Not Kafka)?

| Aspect | RabbitMQ | Kafka |
|---|---|---|
| **Use Case** | Task queues, microservices | Event streaming, analytics |
| **Delivery** | Exactly once | At least once |
| **Latency** | Low (ms) | Higher (s) |
| **Retention** | Hours | Days/months |
| **Complexity** | Simple | Complex |
| **Cost** | Cheaper | More expensive |

**Choice: RabbitMQ**
- Most events are fire-and-forget (don't need replay)
- Low latency needed (order processing < 500ms)
- Simpler operations
- Perfect for microservices

**If we needed Kafka:**
- Event replay (audit trail)
- Event sourcing (event = source of truth)
- High-throughput streaming (millions events/sec)
- Multiple subscribers per event (not priority)

---

### Why Go (for Order Service)?

| Language | Use Case | This Project |
|---|---|---|
| **Python** | Rapid development, ML, scripts | User Service ✓ |
| **Go** | High concurrency, performance | Order Service ✓ |
| **Node.js** | Real-time, I/O-bound | Inventory ✓ |
| **Rust** | Systems, extreme perf | NOT needed |

**Order Service is bottleneck** → needs:
- Low memory (lean containers)
- High concurrency (goroutines)
- Fast startup (new instances often)
- Compiled (no startup time)

Go delivers all of these.

---

### Why MongoDB (for Inventory)?

**Inventory data is semi-structured:**
```json
{
  "product_id": 123,
  "sku": "PROD-123-BLU",
  "stock": 50,
  "metadata": {
    "supplier": "factory-x",
    "warehouse": "us-west-2a",
    "last_restock": "2024-01-01",
    "dimensions": {
      "width": 10,
      "height": 20,
      "depth": 15
    }
  },
  "reservations": [
    {"order_id": 456, "qty": 5, "expires_at": "2024-01-02"}
  ]
}
```

**MongoDB advantages:**
- Flexible schema (metadata varies per product)
- Nested documents (reservations array)
- JSONB queries
- Horizontal scaling (sharding)

---

## 📊 Observability Across Services

### Distributed Tracing (Jaeger)

```
User places order

Trace ID: abc-def-ghi

1. API Gateway (span 1)
   └─ Order Service (span 2)
      ├─ Validate JWT (span 3) → User Service
      ├─ Check inventory (span 4) → Inventory Service
      └─ Create order (span 5) → PostgreSQL
          └─ Insert (span 6) → 45ms

Each span:
- Operation name (check_inventory)
- Duration (150ms)
- Service (inventory-service)
- Tags (product_id: 123)
- Errors (if any)
```

**Benefits:**
- See entire request flow across services
- Identify bottleneck (payment took 2000ms)
- Correlate logs (same trace ID)
- Performance analytics

### Metrics Across Services

```yaml
# Each service exports metrics
order_service_metrics:
  orders_created_total: 1000
  orders_failed_total: 50
  order_processing_duration_ms: 250  # p99

inventory_metrics:
  stock_checked_total: 5000
  reservations_active: 300
  reservation_expiry_failures: 5

payment_metrics:
  charges_total: 900
  charge_failures_total: 100
  charge_duration_ms: 500

# Central Prometheus scrapes all
# Grafana shows unified dashboard
```

### Correlation IDs (Linking Logs)

```
Client request arrives with:
  X-Request-ID: req-123-abc-def

All services log with this ID:
  [Order Service] [req-123] Creating order
  [Inventory Service] [req-123] Checking stock
  [Payment Service] [req-123] Processing payment
  [Notification Service] [req-123] Sending email

Log aggregator groups by req-123:
  Shows full transaction flow
  Traces issue origin
```

---

## 🛡️ Resilience Patterns

### Saga Pattern (Distributed Transactions)

**Problem:** Order requires multiple services to succeed.
**Solution:** Saga coordinates steps with compensation.

```
Step 1: Order Service creates order
  └─ Compensation: Delete order

Step 2: Payment Service charges customer
  └─ Compensation: Refund

Step 3: Inventory Service reserves stock
  └─ Compensation: Release reservation

Step 4: Notification Service sends email
  └─ Compensation: N/A (async, low priority)

If any step fails:
  Execute compensation steps in reverse order
  Order automatically rolled back
```

### Circuit Breaker

```python
from pybreaker import CircuitBreaker

inventory_breaker = CircuitBreaker(fail_max=5, reset_timeout=60)

@inventory_breaker
def check_stock(product_id):
    return inventory_service.check(product_id)

# After 5 failures in 60 seconds:
# Circuit opens → requests fail immediately (fast fail)
# After 60 seconds → try again (half-open state)
```

### Retry with Exponential Backoff

```python
def charge_with_retry(payment_info, max_retries=3):
    for attempt in range(max_retries):
        try:
            return payment_gateway.charge(payment_info)
        except TransientError:
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            sleep(wait_time)
            continue
        except PermanentError:
            raise  # Don't retry permanent errors
    
    raise MaxRetriesExceeded()
```

### Bulkhead Pattern

```yaml
# Isolate resources per service
Order Service:
  Thread pool: 20 threads
  Max connections: 50
  Memory: 1GB limit
  
Inventory Service:
  Thread pool: 10 threads
  Max connections: 30
  Memory: 512MB limit

If one service gets slow, doesn't affect others
```

---

## 📈 Scaling Strategies

### Services Scale Independently

```
Morning peak (8 AM):
- Order Service: 3 → 15 pods (spike from users)
- Inventory Service: 2 → 3 pods (minimal change)
- User Service: 3 pods (stable)
- Payment Service: 2 → 5 pods

Evening (10 PM):
- All services → baseline

Cost: Pay for what you use
- Monolith 10x growth = 10x cost
- Microservices selective growth = 3x cost
```

### Data Partitioning (Sharding)

```
Orders by region:
- US orders → us-east-1 cluster
- EU orders → eu-west-1 cluster
- AP orders → ap-southeast-1 cluster

Sharding key: region_id
Query: SELECT * FROM orders WHERE region_id = 'US' AND order_id = 123

Benefits:
- Each shard smaller (faster queries)
- Distribute load across databases
- Regional compliance (data residency)
```

### Caching Strategy

```
Cache layers:

1. Client-side: Browser cache (1 hour)
2. CDN: CloudFront (24 hours) for static assets
3. Redis: Hot data (product info, user prefs) - 1 hour TTL
4. Database: Source of truth

Sequence:
GET /api/products/123
→ Check Redis (cache hit 90%)
→ Return cached product
→ On cache miss → Query DB → Update Redis
```

---

## ⚠️ Failure Scenarios

### Inventory Service Down

```
Sequence:
1. Order Service needs inventory check
2. Circuit breaker detects failure (5 failures in 60s)
3. Circuit opens → fail fast
4. Order Service catches error
5. Response to user: "Temporarily unavailable"
6. Retry: Inventory Service restarts, circuit resets
7. System recovers
```

### Database Replication Lag

```
Scenario:
Order Service writes order → Primary DB
Inventory Service reads from read replica
Read replica 30 seconds behind

Order just created, but inventory doesn't see it yet
Result: Race condition

Solution:
- Use write-after-read consistency
- After write, read from primary for next few seconds
- Use change data capture (CDC) for real-time replication
```

### Message Queue Backlog

```
Scenario:
Notification Service is slow
Messages queue up in RabbitMQ
Users complain about late emails

Metrics:
Queue depth: 10,000 messages
Publish rate: 100/sec
Consume rate: 20/sec
Current time to process: 8+ hours

Solution:
- HPA scales Notification Service pods 5 → 50
- Consume rate increases to 500/sec
- Queue clears in 20 minutes
```

---

## 🔗 Key Files

- Order Service: `services/order/`
- Inventory Service: `services/inventory/`
- Docker Compose: `docker/docker-compose.yml`
- Kubernetes: `kubernetes/`
- CI/CD: `cicd/`
- Observability: `observability/`
- Docs: [docs/decisions.md](docs/decisions.md)

---

## 📞 Questions This Demonstrates

✅ How do you decompose monoliths?
✅ How do you handle eventual consistency?
✅ How do you trace requests across services?
✅ How do you scale services independently?
✅ How do you handle distributed failures?
✅ What trade-offs exist between monoliths and microservices?
✅ How do you manage data across service boundaries?
