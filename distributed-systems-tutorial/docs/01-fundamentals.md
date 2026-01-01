# Module 1: Distributed Systems Fundamentals

## Objectives

After completing this module, you will:
- Understand why distributed systems are necessary and what problems they solve
- Know the CAP theorem and its real-world implications
- Distinguish between synchronous and asynchronous communication patterns
- Recognize common distributed system failures and pitfalls
- Understand latency, throughput, and availability trade-offs
- Know when to use distributed architecture vs. monolithic approach

## 1.1 The Monolithic vs. Distributed Decision

### Monolithic Architecture

A monolith is a single application handling all business logic:

```
Client Request
↓
Web Framework (Django, Express, Spring)
├→ User Service Logic
├→ Order Service Logic
├→ Payment Service Logic
├→ Notification Service Logic
↓
Single Database
↓
Response
```

#### Monolith Advantages

1. **Simplicity**: Everything in one codebase, one process
2. **Easy Debugging**: Set a breakpoint, trace through code
3. **Transactions**: ACID transactions across all operations
4. **Performance**: No network overhead between services
5. **Deployment**: One artifact to deploy

#### Monolith Disadvantages

1. **Scaling**: Must scale entire application, even if only one feature is slow
2. **Technology Lock-in**: Must use same language/framework for all features
3. **Reliability**: One bug can crash entire system
4. **Development**: Large teams cause merge conflicts and slow deployments
5. **Resource Inefficiency**: Must allocate resources for peak load to all services

### Distributed Architecture

Split monolith into independent services:

```
Client Request
↓
API Gateway (single entry point)
↓
User Service    Order Service    Payment Service    Notification Service
(separate)      (separate)       (separate)         (separate)
↓               ↓                ↓                  ↓
DB Instance 1   DB Instance 2    DB Instance 3      Async Queue
```

#### Distributed Architecture Advantages

1. **Horizontal Scaling**: Scale only the services that need it
2. **Technology Diversity**: Python service + Go service + Java service in same system
3. **Resilience**: One service fails, others continue (partial degradation)
4. **Team Autonomy**: Teams can deploy services independently
5. **Resource Efficiency**: Pay for only what you use

#### Distributed Architecture Disadvantages

1. **Operational Complexity**: Multiple services to monitor, deploy, debug
2. **Network Latency**: Inter-service calls are slow (1-100ms vs 1-10μs local calls)
3. **Consistency Challenges**: Data spread across multiple databases
4. **Testing Difficulty**: Must test service interactions and failure modes
5. **Debugging Nightmare**: Request spans multiple services, hard to trace

### When to Use Monolith vs. Distributed

**Use Monolith If:**
- Team < 10 engineers
- Single problem domain
- Scaling needs are predictable and uniform
- Operational expertise is limited
- Time to market is critical

**Use Distributed If:**
- Different parts scale at different rates
- Different teams own different services
- Technology diversity is beneficial
- High availability/reliability is critical
- System is already struggling with monolith

### The Startup Dilemma

**Wrong**: Start with microservices for "scalability"
- You don't have scale problems yet
- You add operational complexity you can't manage
- You slow down feature development

**Right**: Start with a well-structured monolith
- Simple deployment and debugging
- Quick iteration on features
- When you hit scaling walls, split specific services

## 1.2 The CAP Theorem: The Fundamental Trade-off

CAP theorem states: In any distributed system, you can achieve at most 2 out of 3:

- **Consistency (C)**: Every read returns the most recent write
- **Availability (A)**: System responds to all requests (no timeouts)
- **Partition Tolerance (P)**: System survives network failures

### Understanding Each Property

#### Consistency (C)

All servers see the same data at the same time.

```
Write Operation: Update user balance from $100 to $110

Instant Consistency (Strong):
- Server 1 updated immediately
- Server 2 updated immediately
- Server 3 updated immediately
- All reads return $110

Reality: This requires synchronous replication. Slow across networks.
```

#### Availability (A)

System always responds to requests (within timeout).

```
Request Pattern:
- Request arrives at Server 1
- Server 1 must respond within 1 second
- Server 1 can't wait for other servers to acknowledge

Result: Server 1 might serve stale data, but it responds fast.
```

#### Partition Tolerance (P)

System survives network failures (partitions).

```
Network Partition Event:
Server 1 ←→ Server 2  (can communicate)
Server 1 ⸸ Server 3    (network down)

System must still function:
- Servers 1-2 can talk to each other
- Server 3 is isolated

The system needs to handle being split.
```

### The Real Choice: CP vs. AP

Network partitions WILL happen (switches fail, cables cut, cloud zones go down). So you really choose:

#### CP Systems: Consistency + Partition Tolerance (sacrifice Availability)

When network splits, system stops accepting writes to avoid inconsistency.

**Example: Traditional SQL Database with Transactions**

```
Primary DB (Leader)
↓
Synchronous Replication
↓
Replica DB (Follower)

Write happens:
1. Client sends write to Primary
2. Primary waits for Replica to acknowledge
3. Both have updated data
4. Primary acknowledges to client

Network partition (Primary ⸸ Replica):
- Primary stops accepting writes (rejects new requests)
- System is unavailable but consistent
- When partition heals, everything is consistent again
```

**Real systems using CP:**
- PostgreSQL (with synchronous replication)
- MySQL (with group replication)
- Traditional banking systems
- Anything with distributed transactions

**Trade-off**: When network fails, system becomes unavailable (but data is safe).

#### AP Systems: Availability + Partition Tolerance (sacrifice Consistency)

When network splits, system keeps serving but data might be inconsistent.

**Example: NoSQL Database (MongoDB, DynamoDB)**

```
Node A (replica)
↓
Asynchronous Replication
↓
Node B (replica)

Write happens:
1. Client writes to Node A
2. Node A immediately acknowledges
3. Node B gets updated asynchronously (might take seconds)

Network partition (Node A ⸸ Node B):
- Node A keeps accepting writes
- Node B keeps accepting writes
- They have conflicting data
- System is available but temporarily inconsistent
- When partition heals, data eventually converges (eventually consistent)
```

**Real systems using AP:**
- DynamoDB, Cassandra, MongoDB (default settings)
- Redis, Memcached (caches)
- DNS (eventually consistent)
- Social media systems (feeds, likes)

**Trade-off**: Temporary inconsistency, but system always responds.

### CAP in Practice: Real Examples

#### Example 1: E-Commerce Checkout (needs CP)

```
User in US clicks "Place Order"
↓
Write to database: {user_id: 123, order: item_xyz}
↓
System must ensure:
- Order counted once (not duplicated)
- Inventory decremented once
- Payment charged once

If network partitions, better to fail the order than charge twice.
→ Use CP system
```

#### Example 2: Social Media Feed (AP is fine)

```
User A likes User B's post
↓
Like counter updates

If AP (asynchronous replication):
- Some servers might show 1,234 likes
- Some might show 1,235 likes (before replication)
- Within seconds, all servers converge

This is acceptable. Users won't notice 1-second inconsistency.
→ Use AP system
```

#### Example 3: Analytics System (AP is fine)

```
Server A records: page_view event
Server B records: page_view event (data not yet replicated from A)

If 2-minute delay before data replicates, who cares?
Queries are run hours/days later anyway.
→ Use AP system
```

### CAP Theorem Limitations

CAP theorem is often misunderstood:

1. **It's a trade-off, not religion**: Systems can be tuned along a spectrum
2. **Partition tolerance is assumed**: In cloud systems, P is mandatory
3. **Latency matters**: Consistency latency (how long to replicate) impacts real systems
4. **Different data, different choices**: Same system can use CP for critical data, AP for non-critical

## 1.3 Latency, Throughput, and Availability

### Latency vs. Throughput vs. Cost

These are separate dimensions (not the CAP triangle):

```
Latency (L): How fast does one request complete? (milliseconds)
Throughput (T): How many requests per second? (requests/sec)
Cost (C): How much infrastructure do you need?

You can optimize for any 2:
- Low L + High T = Very expensive (premium hardware)
- Low L + Low C = Low T (can't handle scale)
- High T + Low C = High L (slow responses)
```

### Latency Deep Dive

Latency is the time from request to response.

#### Components of Latency

```
Total Latency = Network + Processing + Database + Serialization

Example breakdown (100ms request):
1. Network round-trip (client → server): 5ms
2. Server receives request: 0.1ms
3. Processing (business logic): 10ms
4. Database query: 50ms
5. Processing response: 5ms
6. Serialization (JSON encoding): 5ms
7. Network round-trip (server → client): 5ms
8. Browser rendering: 19.9ms
────────────────────────────
Total: ~100ms
```

#### Latency SLAs (Service Level Agreements)

Real production latency targets:

| System Type | p50 (median) | p95 | p99 | Notes |
|---|---|---|---|---|
| Web API (public) | 100ms | 500ms | 1000ms | Consumer-facing |
| Internal Service | 10ms | 50ms | 100ms | Backend-to-backend |
| Cache/Redis | 1ms | 5ms | 10ms | Mostly in-memory |
| Database Query | 5ms | 20ms | 50ms | With index hits |
| Distributed System | 50ms | 200ms | 1000ms | Multiple hops |

**Key insight**: p99 matters more than p50. One slow query makes user experience bad.

#### Reducing Latency

1. **Caching**: Store results, avoid expensive computation
2. **Connection pooling**: Reuse database connections (avoid TCP handshake)
3. **Async operations**: Don't wait for non-critical operations
4. **Geographic distribution**: Serve from location close to user
5. **Database optimization**: Indexes, query tuning
6. **Parallelization**: Execute independent operations concurrently

### Throughput Deep Dive

Throughput is requests per second (or transactions per second).

#### Throughput Limits

```
Single Server Throughput = Requests per sec / Avg Request Time

Example: Average request takes 50ms
Throughput = 1000ms / 50ms = 20 requests/sec

To increase throughput:
1. Reduce request time (latency optimization) → more reqs/sec
2. Add more servers → cumulative throughput
```

#### Scaling Throughput

**Vertical Scaling (bigger server)**
```
1 server with 4 CPU cores: 1,000 req/sec
1 server with 8 CPU cores: ~1,800 req/sec (not linear)
Problem: Limited by single server capacity (max ~100K req/sec typical)
```

**Horizontal Scaling (more servers)**
```
1 server: 1,000 req/sec
10 servers: 10,000 req/sec (linear scaling)
100 servers: 100,000 req/sec
Problem: Database becomes bottleneck, complexity increases
```

#### Throughput Targets

| System | Target Throughput | Infrastructure |
|---|---|---|
| Startup MVP | 100 req/sec | 1-2 servers |
| Mid-size service | 10,000 req/sec | 50-100 servers |
| Large service | 100,000 req/sec | 1,000+ servers |
| Mega-scale | 1,000,000+ req/sec | Custom infrastructure |

### Availability Deep Dive

Availability is the percentage of time system is operational.

#### Availability Tiers

```
99% availability = 3.7 days downtime per year
99.9% availability = 8.7 hours downtime per year (three nines)
99.99% availability = 52.6 minutes downtime per year (four nines)
99.999% availability = 5.3 minutes downtime per year (five nines)

Formula: (1 - availability) * seconds_per_year = downtime_seconds
```

#### Achieving High Availability

```
Single server: No redundancy
↓
99% availability (3.7 days downtime)

Single server + manual failover:
System dies, ops team restarts
↓
95% availability (18 days downtime)

Load balancer + 3 identical servers (any one can fail):
If one dies, others continue
↓
99.99% availability (if each server is 99% available)
↓
Formula: 1 - (0.01 × 0.01 × 0.01) = 99.9999%

But database is single point of failure:
↓
99.9% availability (if database is 99.9% available)
```

#### Architecture for High Availability

```
Load Balancer (health checking)
├→ Server 1 (99% uptime)
├→ Server 2 (99% uptime)
├→ Server 3 (99% uptime)
↓
Database Primary
↓
Database Replica (automatic failover)

Failure scenarios:
- Server dies → LB routes to others (immediate)
- Database dies → Replica promoted automatically (5-30 seconds)
- Load balancer dies → Use DNS failover or multiple LBs

Result: 99.99%+ availability
```

## 1.4 Synchronous vs. Asynchronous Communication

Two fundamental patterns for service-to-service communication:

### Synchronous (Request-Response)

Client waits for server response before continuing.

```
User Service        Order Service
    ↓                   
    Request: "Get user details"
    ↓────────────────────→
    (blocks, waiting)
                        Process request
                        ↓
    ←────────Response───↓
    ↓
Continue
```

#### Synchronous Advantages

1. **Simple**: Easy to understand and code
2. **Immediate feedback**: Know success/failure immediately
3. **Transactions**: Can ensure consistency
4. **Debugging**: Easy to trace request flow

#### Synchronous Disadvantages

1. **Tight coupling**: Services must be available
2. **Cascading failures**: If downstream service slow, upstream blocked
3. **Resource waste**: Thread/connection held while waiting
4. **Scaling limit**: Throughput limited by slowest service
5. **Timeout handling**: What if service takes too long?

#### Synchronous Example (REST API)

```
POST /api/orders HTTP/1.1

Server handles synchronously:
1. Validate user (calls User Service - waits)
2. Check inventory (calls Inventory Service - waits)
3. Process payment (calls Payment Service - waits)
4. Create order in database
5. Return response

If Payment Service is slow (5 second timeout):
- Customer waits 5+ seconds for response
- If timeout, order might be partial (inconsistent state)
```

### Asynchronous (Event-Based)

Sender doesn't wait for response. Uses message queue.

```
Order Service                   Notification Service
(producer)                      (consumer)
    ↓
    Publish: "OrderCreated" event
    ↓────→ Message Queue (durable)
    ↓
Continue immediately
(doesn't wait)
                                ↓
                                Consumer: reads from queue
                                Process notification
                                (might take minutes)
```

#### Asynchronous Advantages

1. **Decoupling**: Services don't need to know about each other
2. **Resilience**: If Notification Service down, order still completes
3. **Throughput**: Can process many events quickly
4. **Flexibility**: Multiple consumers can process same event
5. **Fault tolerance**: Messages persist in queue if consumer fails

#### Asynchronous Disadvantages

1. **Complexity**: Harder to reason about ordering and consistency
2. **Debugging**: Events might be processed minutes later, hard to trace
3. **Guarantees**: Need to handle duplicate messages, failures
4. **Latency**: Notification might not appear immediately
5. **Testing**: Must test eventual consistency scenarios

#### Asynchronous Example (Event-Driven)

```
POST /api/orders HTTP/1.1

Server handles asynchronously:
1. Validate user (fast, local check)
2. Create order in database
3. Publish "OrderCreated" event to message queue
4. Return response immediately (200 OK)

Meanwhile, asynchronous processing:
- Notification Service reads event → sends confirmation email (1s later)
- Analytics Service reads event → logs analytics (2s later)
- Inventory Service reads event → decrements stock (3s later)

If Email Service fails:
- Order still created
- Email retried later
- System recovers automatically
```

### Hybrid Approach (Most Production Systems)

Real systems use BOTH:

```
Critical Path (Synchronous):
- User submits order
- Validate user, check payment
- If validation fails, reject immediately (can't be async)
- If valid, create order in database

Non-Critical Path (Asynchronous):
- After order created, emit event
- Email confirmation (eventually)
- Update analytics (eventually)
- Update recommendation engine (eventually)

Result: Fast response to user (milliseconds), background work happens slowly
```

## 1.5 Common Distributed System Failures

### Network Failures

**The Problem**: Networks are unreliable.

```
Your architecture assumes:
- Message sent from A to B arrives
- Message arrives intact
- Message arrives only once

Reality:
- Messages get lost (packet loss, 0.1% typical)
- Messages arrive twice (TCP retry, application retried)
- Messages arrive out of order (UDP)
- Messages take too long (network congestion)
- Entire network partition (switch failure)
```

**Real Example: Payment Processing**

```
1. Customer submits payment
2. Your service sends message to Payment Gateway
3. Network timeout (5 seconds, no response)
4. Your service doesn't know: did payment succeed or fail?

Option A: Assume failed, return error to customer
- But payment actually succeeded (gateway processing it)
- Now customer tries again → double charge

Option B: Assume succeeded
- But payment actually failed
- Customer thinks payment worked, they get service
- Later reconciliation shows they weren't charged

Solution: Idempotent operations (payment ID to detect duplicates)
```

### Cascading Failures

When one failure causes another, causing another...

```
Normal Load:
User Service (500ms response)
↓
Payment Service (100ms response)
↓
Payment Gateway (50ms response)
Result: 650ms per request, 10 servers needed for 100 req/sec

Payment Gateway Degrades (now 5 seconds):
Payment Service waits 5s instead of 50ms (threads fill up)
↓
After 10s, all Payment Service threads blocked
↓
User Service waits for Payment Service (threads fill up)
↓
After 10s, User Service unresponsive
↓
Load balancer marks User Service unhealthy
↓
Traffic routed to remaining servers (more load)
↓
Entire system collapses

This is cascading failure. One service degradation → system-wide outage.
```

**Prevention**:
- Timeouts (don't wait forever)
- Circuit breakers (stop sending requests to broken service)
- Bulkheads (isolate threads/resources)
- Rate limiting (shed traffic gracefully)

### Distributed Consensus Problems

When multiple servers need to agree on state:

```
Leader Election Problem:
- Server A thinks it's the leader
- Server B also thinks it's the leader
- Both start accepting writes
- Data diverges
- System is inconsistent

Network Partition Problem:
Network splits system into two parts:
- Part A: 2 servers (can talk to each other)
- Part B: 3 servers (can talk to each other)
- Parts can't talk to each other

Question: Which part is authoritative?
- If Part A decides it's the leader: might conflict with Part B
- If Part B decides it's the leader: conflict with Part A
- If neither assumes leadership: system is unavailable

Solution: Consensus protocols (Raft, Paxos, etc.)
```

### Data Inconsistency Patterns

**Read-write inconsistency**:

```
User updates profile name to "Alice"
Write goes to Server A

User immediately reads profile
Request goes to Server B (different server)

Server B hasn't replicated from A yet.
User sees old name "Bob"

This is temporary, but users notice and complain.
```

**Stale cache**:

```
Inventory cache shows 50 items

Backend updates inventory to 40 items in database

Cache still shows 50

Customer orders 45 items

"We have 50" but actually only have 40

Over-allocation problem.
```

## 1.6 Common Pitfalls and Anti-Patterns

### Pitfall 1: Assuming Network is Reliable

**Wrong approach:**
```
if (service.call(request)) {
    // Success
} else {
    // Failure
}
```

Network might silently fail, timeout, or partially succeed. Always:
- Set timeouts (don't wait forever)
- Implement retries with backoff
- Handle partial failures
- Assume network partitions happen

### Pitfall 2: Tight Service Coupling

**Wrong:**
```python
# OrderService directly calls PaymentService
def create_order(user_id, items):
    # Blocks waiting for payment
    payment_result = payment_service.process(amount)
    if payment_result.success:
        return create_order_in_db(user_id, items)
    else:
        raise PaymentFailed()
```

**Right:**
```python
def create_order(user_id, items):
    order = create_order_in_db(user_id, items, status="pending")
    
    # Async: don't wait for payment
    queue.publish("order.created", {
        "order_id": order.id,
        "user_id": user_id,
        "amount": calculate_amount(items)
    })
    
    return order  # Return immediately
```

### Pitfall 3: Not Handling Duplicates

**Wrong:**
```python
@app.route('/process_payment', methods=['POST'])
def process_payment():
    amount = request.json['amount']
    
    # If called twice, charges twice
    db.execute("UPDATE balance SET balance = balance - ?", amount)
    
    return {"status": "success"}
```

**Right:**
```python
@app.route('/process_payment', methods=['POST'])
def process_payment():
    idempotency_key = request.json['idempotency_key']
    amount = request.json['amount']
    
    # Check if we've already processed this request
    existing = db.query("SELECT * FROM payments WHERE idempotency_key = ?", idempotency_key)
    if existing:
        return existing  # Return same result
    
    # First time processing
    db.execute("INSERT INTO payments (idempotency_key, amount) VALUES (?, ?)", 
               idempotency_key, amount)
    
    return {"status": "success"}
```

### Pitfall 4: No Circuit Breaker

**Wrong:**
```python
def get_user_recommendations(user_id):
    # If recommendation_service is failing, keep hammering it
    try:
        return recommendation_service.get_recommendations(user_id)
    except Exception:
        # Retry immediately, no backoff
        return recommendation_service.get_recommendations(user_id)
```

**Right:**
```python
circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    timeout=60,  # Open circuit for 60 seconds
    expected_exception=ServiceError
)

def get_user_recommendations(user_id):
    try:
        @circuit_breaker
        def call_service():
            return recommendation_service.get_recommendations(user_id)
        
        return call_service()
    except CircuitBreakerOpen:
        # Service is failing, return cached/default result
        return get_cached_recommendations(user_id)
```

### Pitfall 5: Not Monitoring Distributed Traces

**Problem:**
```
User reports: "My order took 30 seconds to create"

Where is the time spent?
- Network latency? (1-2ms)
- Validation? (5ms)
- Database? (500ms)
- Payment service? (20,000ms)
- Queue publishing? (5ms)
- ???

Without distributed tracing, you can't find the bottleneck.
```

**Solution**: Use distributed tracing (Jaeger, Zipkin)
- Every request gets a trace ID
- Every service logs with trace ID
- Can see entire request path and timing

### Pitfall 6: Assuming Ordered Message Processing

**Wrong:**
```
Message 1: "Create user Alice"
Message 2: "Delete user Alice"

Assuming they process in order...

But in distributed queue:
- Message 1 goes to Worker A
- Message 2 goes to Worker B
- If Worker B faster: Alice gets deleted before creation!

Result: Inconsistent state
```

**Right**: Design for out-of-order processing
- Each message should be idempotent
- Don't rely on ordering unless critical
- Use ordered partitioning for critical sequences

## 1.7 Production Recommendations

### Design Principle 1: Assume Everything Fails

- Servers fail
- Networks fail
- Databases fail
- Load balancers fail

Design with redundancy and automatic recovery.

### Design Principle 2: Optimize for Operational Simplicity

A system that's 80% optimized but easy to operate beats a 95% optimized but fragile system.

- Choose boring, well-understood technologies
- Avoid premature optimization
- Build observability in from the start

### Design Principle 3: Progressive Disclosure of Complexity

Start simple:
1. Single-server monolith (good enough for MVP)
2. Separate database (when you hit scaling issues)
3. Caching layer (when database becomes bottleneck)
4. Service decomposition (when teams are stepping on each other)
5. Async messaging (when you need loose coupling)
6. Multi-region (when geography matters)

Don't start at level 5 and work backward.

### Design Principle 4: Measure Everything

- Latency percentiles (p50, p95, p99)
- Error rates
- Throughput
- Database query times
- Cache hit rates
- Service dependencies

Without measurements, you're making decisions blind.

---

## Exam & Practice

### Multiple Choice Questions

**Q1**: A system handles financial transactions where consistency is critical. Network partitions occasionally occur. Which CAP property should be sacrificed?

A) Consistency
B) Availability
C) Partition Tolerance
D) None - all three can be guaranteed

**Q2**: A web application has average request time of 100ms. How many requests per second can a single server handle with optimal resource utilization?

A) 10 requests/sec
B) 100 requests/sec
C) 500 requests/sec
D) 1000 requests/sec

**Q3**: You observe that when the Payment Service becomes slow (5 sec response time), the entire order system grinds to a halt within 30 seconds. This is an example of:

A) Network partition failure
B) Cascading failure
C) Distributed consensus failure
D) Data inconsistency

**Q4**: An e-commerce site implements asynchronous email notifications. Customers don't receive confirmation emails for 2-3 minutes after placing orders. Is this acceptable?

A) No, customers must receive confirmation immediately
B) Yes, as long as the order was created immediately
C) Only if you monitor email queue depth
D) Only for VIP customers

**Q5**: You're designing a system where the same user action (place order with same order ID) arrives twice due to network retry. What's the most critical property to implement?

A) Load balancing
B) Replication
C) Idempotency
D) Circuit breaking

### Hands-on Tasks

**Task 1: CAP Analysis**

You're designing a system with three components:
1. User Profile Service (1000s of profiles, read-heavy)
2. Inventory Service (1000s of items, must be accurate)
3. Social Feed Service (millions of events, eventual consistency OK)

For each, decide: CP or AP? Justify your choice with failure scenarios.

**Task 2: Latency Budget Allocation**

You have a 1-second SLA for API response time. You control:
- Load balancer (5ms)
- Business logic (?)
- Database query (?)
- Response serialization (?)
- Network overhead (100ms total, fixed)

Available infrastructure:
- Fast database: 50ms latency, expensive
- Standard database: 200ms latency, cheap
- Slow database: 500ms latency, very cheap

What's your latency budget? What database would you choose? Justify.

### Incident Scenario

**Scenario: Cascading Failure During Sale Event**

Your company runs a flash sale. Expected traffic: 100,000 requests/sec.

**Timeline:**
- T+0: Sale starts, traffic surge begins
- T+5min: Recommendation Service starts timing out (slow third-party API)
- T+6min: User Service threads fill up waiting for Recommendation Service
- T+7min: Order Service can't reach User Service, returns errors
- T+8min: Users see "Service Unavailable"
- T+20min: Alert fires, team wakes up
- T+40min: Team disables Recommendation Service
- T+42min: System recovers

**Questions:**
1. How would you have prevented this?
2. What monitoring would have caught this at T+5min?
3. Design a circuit breaker strategy for this system
4. How would you test for this failure before it happens in production?
5. What's the root cause and how do you fix it long-term?

---

**Next**: [Module 2: System Scalability](02-scalability.md)
