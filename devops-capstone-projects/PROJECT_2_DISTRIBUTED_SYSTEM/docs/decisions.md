# PROJECT 2: Architecture & Technology Decisions

## Decision 1: Event-Driven (Async) vs Synchronous Service Calls

### Decision: Event-Driven with RabbitMQ

**Synchronous (Bad for scale):**
```python
def place_order(order):
    # Order Service calls Inventory Service
    if not inventory.check_stock(order.product_id):
        raise OutOfStock()
    
    # Order Service calls Payment Service
    payment = payment.charge(order.amount)
    
    # Now order is complete (took 500ms)
    return order
```

**Problems:**
- Tight coupling (Order Service depends on Inventory, Payment, etc.)
- Cascading failures (if Inventory slow, whole order process slow)
- No retry (if Inventory times out, order fails)
- Tight resource usage (waiting for other services)

**Event-Driven (Good for scale):**
```python
def place_order(order):
    # Create order immediately
    order = Order.create(order)
    
    # Publish event (takes 10ms)
    event_bus.publish("OrderCreated", order)
    
    # Return immediately (client gets response)
    return {"order_id": order.id, "status": "pending"}

# Separate services listen to events
@event_listener("OrderCreated")
def on_order_created(order):
    # Inventory service processes independently
    # Can fail and retry without affecting client
    
@event_listener("OrderCreated")
def charge_customer(order):
    # Payment service processes independently
    # If fails, order still exists (can retry later)
```

**Benefits:**
- Loose coupling (services don't know about each other)
- Resilient (retry failed events in queue)
- Scalable (process events in parallel)
- Observable (audit trail of all events)

---

## Decision 2: RabbitMQ vs Kafka

| Criteria | RabbitMQ | Kafka |
|---|---|---|
| **Message model** | Queue-based | Log-based |
| **Delivery guarantee** | Exactly once | At least once |
| **Retention** | Hours (default) | Days/months |
| **Latency** | <100ms | 100-1000ms |
| **Throughput** | 1M msg/sec | 10M+ msg/sec |
| **Complexity** | Simple | Complex |
| **Cost** | Cheaper | More expensive |
| **Use case** | Task queues | Event streaming |

**Choice: RabbitMQ**

Reasons:
- Most events don't need replay (order created → processed)
- Latency matters (users expect response < 500ms)
- Operational simplicity (fewer knobs)
- Cost (don't need Kafka's extreme throughput)

**If we chose Kafka:**
- Would handle millions of events/sec
- Could replay events (full audit trail)
- Event sourcing (events = system state)
- More operational overhead

**Verdict:** RabbitMQ perfect for this project. Kafka overkill unless you're Uber/Netflix.

---

## Decision 3: Multiple Service Languages (Polyglot)

### Services & Languages

| Service | Language | Why |
|---|---|---|
| **User Service** | Python (Flask) | Rapid dev, auth libraries rich |
| **Order Service** | Go | High concurrency, fast startup |
| **Inventory Service** | Node.js | I/O-bound, fast prototyping |
| **Payment Service** | Python | Lots of payment libraries |
| **Notification Service** | Python | SQS integration, Lambda-friendly |

### Why Different Languages?

**Order Service is the bottleneck:**
- Handles 80% of requests
- Needs low latency (<100ms)
- High concurrency (1000s simultaneous)
- Go provides:
  - Goroutines (concurrency without threads)
  - Fast compilation (deploys quickly)
  - Small memory footprint (lean containers)
  - Built-in HTTP server

**Inventory Service is I/O-bound:**
- Calls MongoDB frequently
- Checks Redis cache
- Node.js perfect because:
  - Non-blocking I/O
  - JavaScript ecosystem (excellent)
  - Fast prototyping

**Other services stay Python:**
- Team already knows Python
- Rich library ecosystems
- Not on critical path (doesn't cause bottleneck)

### Downsides of Polyglot

❌ More languages = more DevOps expertise needed
❌ Harder to share code/libraries
❌ Team needs to learn multiple languages
❌ Monitoring becomes more complex

**Verdict:** Worth it for bottleneck services (Go). Use same language elsewhere.

---

## Decision 4: Saga Pattern for Distributed Transactions

### Problem: What if Payment Fails?

```
Scenario:
1. Create order (Order Service)
2. Charge customer (Payment Service) ← FAILS
3. Reserve inventory (Inventory Service)
4. Send confirmation (Notification Service)

Issue: Order created but not paid. Inventory reserved but no money.
```

### Solution: Choreography Saga

```
Step 1: Order Service creates order
  Event: "OrderCreated"
  
Step 2: Payment Service listens for OrderCreated
  Event: "PaymentProcessed" or "PaymentFailed"
  
Step 3: Inventory Service listens for PaymentProcessed
  Event: "StockReserved" or "StockReservationFailed"
  
Step 4: If any fails, compensation kicks in
  PaymentFailed → Compensation: None needed (no charge)
  StockReservationFailed → Compensation: Refund customer
```

### Alternative: Orchestration Saga

```
Saga Orchestrator (separate service)
  ├─ Call Order Service (create)
  ├─ Call Payment Service (charge)
  ├─ Call Inventory Service (reserve)
  └─ Call Notification Service (send)

If any fails, orchestrator executes compensation
  (calls with "rollback" parameter)
```

**Choice: Choreography (event-based)**
- Services are loosely coupled
- Events are source of truth
- Easier to understand (see events flow)
- Natural fit with RabbitMQ

**When to use Orchestration:**
- Complex workflows
- Many steps with branching logic
- Need central visibility
- Strong consistency important

---

## Decision 5: MongoDB vs PostgreSQL for Inventory

**Inventory data example:**
```json
{
  "product_id": "PROD-123",
  "sku": "SKU-456",
  "stock": 100,
  "reservations": [
    {"order_id": 789, "qty": 5, "expires_at": "2024-01-02"},
    {"order_id": 790, "qty": 3, "expires_at": "2024-01-03"}
  ],
  "warehouse_info": {
    "location": "warehouse-us-west",
    "temperature": 20,
    "last_audit": "2024-01-01"
  },
  "supplier": {
    "id": "SUPP-111",
    "name": "Factory X",
    "contract_terms": {...}
  }
}
```

### Why MongoDB?

| Aspect | PostgreSQL | MongoDB |
|---|---|---|
| **Schema** | Rigid (must define columns) | Flexible (store JSON directly) |
| **Nested data** | Joins required (complex) | Arrays embedded (simple) |
| **Query** | SQL JOIN | JSONB query |
| **Transactions** | Strong (ACID) | Eventual (BASE) |
| **Scale** | Vertical | Horizontal (sharding) |

**Choice: MongoDB**
- Inventory varies per product
- Nested reservation arrays
- Semi-structured metadata
- Horizontal scaling needed

**Trade-off accepted:**
- ❌ No strong transactions across services
- ✅ Simpler schema (flexible)
- ✅ Faster prototyping
- ✅ Easier to scale horizontally

---

## Decision 6: Cache Strategy (Redis)

**What gets cached:**
```
1. User profiles (read frequently)
   Key: user:123
   Value: {id: 123, name: "John", role: "admin"}
   TTL: 1 hour

2. Product catalog (rarely changes)
   Key: product:456
   Value: {id: 456, name: "Widget", price: 99.99}
   TTL: 24 hours

3. Reservation locks (prevent double-booking)
   Key: reservation:789
   Value: {product_id: 456, qty: 5}
   TTL: 5 minutes (expires reservation)

4. Rate limit counters
   Key: rate_limit:user:123
   Value: 45  (45 requests this minute)
   TTL: 1 minute
```

**Cache-aside pattern:**
```python
def get_user(user_id):
    # Check cache first
    cached = redis.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)
    
    # Cache miss, fetch from DB
    user = db.query(User).get(user_id)
    
    # Populate cache
    redis.setex(f"user:{user_id}", 3600, json.dumps(user))
    
    return user
```

**Write-through pattern:**
```python
def update_user(user_id, data):
    # Update database
    user = db.query(User).get(user_id)
    user.name = data['name']
    db.commit()
    
    # Update cache
    redis.setex(f"user:{user_id}", 3600, json.dumps(user.to_dict()))
    
    return user
```

**Cache invalidation (hardest problem in CS):**
```python
# When product metadata changes, invalidate cache
def update_product(product_id, data):
    product = db.query(Product).get(product_id)
    product.name = data['name']
    db.commit()
    
    # Delete from cache (TTL-based expiry is backup)
    redis.delete(f"product:{product_id}")
```

---

## Decision 7: Eventual Consistency vs Strong Consistency

### Eventual Consistency (This Project)

```
Time: T=0
Inventory: 100 units
User places order for 5 units

Time: T+100ms
Order Service: "Order created" (response to user)
Inventory Service: Still processing reservation

Time: T+500ms
Inventory Service: "Stock reserved"
System: Order confirmed

Between T+100ms and T+500ms:
- Client thinks order is confirmed
- System still processing
- If inventory fails, order is rolled back (compensation)
```

**Pros:**
- Fast (user gets response immediately)
- Scalable (services process independently)
- Resilient (failures don't block user)

**Cons:**
- Complex (must handle failures)
- Data inconsistency (temporary)
- Tricky to debug (events flow across time)

### Strong Consistency Alternative

```
Time: T=0
User places order for 5 units

Time: T=0
Order Service requests lock from Inventory Service
Inventory Service locks 5 units

Time: T+100ms
All services complete
Order fully confirmed

Time: T+100ms
Lock released
System: Order committed
```

**Pros:**
- Simple (ACID guarantees)
- Debuggable (point-in-time consistency)

**Cons:**
- Slow (must wait for all services)
- Bottleneck (locks hold resources)
- Less resilient (cascading failures)

**Choice: Eventual Consistency**
- Trade speed for consistency
- Acceptable for e-commerce (temporary inconsistency OK)
- Better scalability

---

## Decision 8: Multiple Databases (No Shared DB)

### Why Not Shared Database?

```
Bad: All services use same DB
  Order Service writes orders
  Inventory Service writes inventory
  
Problems:
- Schema coupling (hard to change without coordinating)
- Performance coupling (one slow query affects all)
- Scaling limitation (single DB is bottleneck)
- Technology coupling (all must use SQL)
```

### This Project: Separate DBs

```
Order Service → PostgreSQL
  - ACID needed (transactions)
  - Relational data (orders → customers)
  
Inventory Service → MongoDB
  - Flexible schema (product metadata varies)
  - High scale (sharded)
  
User Service → PostgreSQL
  - Strong consistency needed
  - Relational data
  
Payment Service → PostgreSQL
  - Financial data (must be transactional)
```

**Data consistency across DBs:**
```
Order created in Order DB
Inventory must know about it

Solution: Order Service publishes "OrderCreated" event
Inventory Service subscribes and updates its own DB

Temporary inconsistency (OK):
  Order DB has order
  Inventory DB delayed by 100ms
  Both eventually consistent

This is acceptable for e-commerce
```

---

## Key Trade-offs Summary

| Decision | Chosen | Trade-off |
|---|---|---|
| **Communication** | Event-driven | More complex, but loosely coupled |
| **Message Queue** | RabbitMQ | Can't replay events, but simpler |
| **Languages** | Polyglot | More complexity, but optimal performance |
| **Transactions** | Saga pattern | Eventual consistency, but resilient |
| **Inventory DB** | MongoDB | Less consistent, but more flexible |
| **Consistency** | Eventual | Temporary inconsistency, but fast |
| **Cache** | Redis | One more component, but big speedup |

**Lesson:** Every architectural choice is a trade-off. This project accepts complexity, eventual consistency, and operational overhead in exchange for scalability and resilience.
