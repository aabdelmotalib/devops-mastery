# PROJECT 2: Scaling & Failure Scenarios

## Scenario 1: RabbitMQ Message Queue Backup

### Symptoms

```
Notification Service gets slow
Users complain about delayed emails

Metrics:
  Queue depth: 50,000 messages
  Messages/sec in: 500/sec
  Messages/sec out: 50/sec
  Time to process all: 1000 seconds = 16+ minutes
```

### Root Cause

```
Notification Service:
- Sends emails via SMTP
- SMTP server is slow (takes 500ms per email)
- But only processing 50 emails/sec

Order Service:
- Creating 500 orders/sec
- Each publishes "OrderCreated" event
- Queue filling up 10x faster than draining
```

### Auto-scaling Solution

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: notification-hpa
spec:
  scaleTargetRef:
    kind: Deployment
    name: notification-service
  
  minReplicas: 1
  maxReplicas: 50  # Scale aggressively
  
  metrics:
  - type: Pods
    pods:
      metric:
        name: rabbitmq_queue_depth
      target:
        type: AverageValue
        averageValue: "1000"  # Scale if queue > 1000/pod

# Behavior: Scale up fast, down slow
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 30  # Scale immediately
      policies:
      - type: Percent
        value: 200  # Double pods every 30s
        periodSeconds: 30
    scaleDown:
      stabilizationWindowSeconds: 600  # Wait 10 min before scaling down
      policies:
      - type: Pods
        value: 1
        periodSeconds: 120
```

### Manual Intervention

```bash
# Check queue depth
kubectl exec -it rabbitmq-0 -- rabbitmqctl list_queues name messages

# name                          messages
# order.created                 45000
# notification.queued           12000

# Scale up notification service immediately
kubectl scale deployment notification-service --replicas=20

# Monitor processing
kubectl logs -f deployment/notification-service | grep "processed"

# Once caught up, scale back down
kubectl autoscale deployment notification-service --min=1 --max=50
```

### Prevention

```python
# Implement backpressure
# If queue depth gets high, reject new orders temporarily

def place_order(order):
    # Check RabbitMQ queue depth
    queue_depth = get_queue_depth('notification')
    
    if queue_depth > 10000:
        # Queue too deep, reject with 503 Service Unavailable
        return {"error": "System overloaded, try again later"}, 503
    
    # Safe to proceed
    order = Order.create(order)
    event_bus.publish("OrderCreated", order)
    return order
```

---

## Scenario 2: Order Service Database Replication Lag

### Problem

```
Order Service writes to PostgreSQL Primary
Inventory Service reads from Read Replica

Replica 5 seconds behind primary

Scenario:
1. Order created: INSERT orders SET ... (primary)
2. Order published to RabbitMQ
3. Inventory Service reads: SELECT * FROM orders WHERE id = 123
4. Read replica hasn't replicated yet
5. Inventory reads "order not found"
6. Inventory publishes "OrderNotFound" event
7. Order gets cancelled incorrectly
```

### Solutions

**1. Read from Primary (Simple, increases load)**
```python
def create_order(order):
    # Always write to primary
    order = db_primary.create(order)
    
    # For this user's subsequent reads, use primary temporarily
    # (ensures read-after-write consistency)
    session = get_session()
    session.read_from = 'primary'  # For next 5 seconds
    
    return order
```

**2. Check Replication Lag (Elegant)**
```python
def get_order_with_consistency(order_id, required_lag=0):
    # If we can accept 5 second lag, read from replica
    
    actual_lag = get_replication_lag()  # seconds
    
    if actual_lag <= required_lag:
        return db_replica.query(Order).get(order_id)
    else:
        # Lag too high, read from primary
        return db_primary.query(Order).get(order_id)
```

**3. Optimize Replication (Complex, effective)**
```bash
# Increase replication speed
# On RDS console:
# - Use max_wal_senders = 10 (default 2)
# - Use wal_keep_size = 2GB (default 1GB)
# - Monitor replica CPU (might be bottleneck)

# Vertical scale replica if CPU high
aws rds modify-db-instance \
  --db-instance-identifier saasdb-read \
  --db-instance-class db.t3.large  # Bigger instance
```

### Monitoring Alert

```yaml
- alert: ReplicationLag
  expr: pg_replication_lag_seconds > 5
  for: 5m
  annotations:
    summary: "Replication lag > 5 seconds"
    runbook: "docs/replication-lag.md"
```

---

## Scenario 3: Order Service Pod OOMKilled

### Symptoms

```
Pods keep restarting
Memory usage climbs steadily

Timeline:
T=0: 300MB
T=1min: 450MB
T=2min: 650MB
T=3min: 950MB (approaching 1GB limit)
T=4min: 1050MB → OOMKilled
T=4min+30s: Pod restarts, memory resets to 300MB
T=8min: 1050MB again → OOMKilled again
```

### Debug Memory Leak

```bash
# Enable memory profiler in Python
# See memory usage by line of code

pip install memory-profiler
python -m memory_profiler app.py > memory_profile.txt

# Example output:
# Line #      Mem usage    Increment   Line Contents
# 45          10.5 MiB      0.0 MiB   def process_order(order):
# 46          10.5 MiB      0.0 MiB       user = User.query.get(order.user_id)
# 47          210.5 MiB    200.0 MiB       user_history = [o for o in db.query(Order).filter_by(user_id=order.user_id).all()]
#                                           ↑ BUG: Loading all orders into memory!

# Fix:
# Use pagination or limit query
user_history = db.query(Order).filter_by(user_id=order.user_id).limit(100).all()
```

### Mitigation (Immediate)

```yaml
# Increase memory limit temporarily
resources:
  limits:
    memory: "2Gi"  # Was 1Gi
  requests:
    memory: "1Gi"  # Was 512Mi

# Buy time to fix code
```

### Fix (Permanent)

```python
# BEFORE: Loads all data into memory
def get_order_history(user_id):
    return db.query(Order).filter_by(user_id=user_id).all()  # ALL orders

# AFTER: Lazy-load with pagination
def get_order_history(user_id, page=1, per_page=50):
    return (db.query(Order)
            .filter_by(user_id=user_id)
            .order_by(Order.created_at.desc())
            .limit(per_page)
            .offset((page - 1) * per_page)
            .all())
```

### Deploy Fix

```bash
# Build new image with fix
docker build -t order-service:v2.1.0 .
docker push ECR/order-service:v2.1.0

# Deploy with gradual rollout (10% → 50% → 100%)
kubectl set image deployment/order-service order-service=ECR/order-service:v2.1.0

# Monitor memory
kubectl top pods | grep order-service
# Should stay < 500MB now
```

---

## Scenario 4: Cascade Failure (Inventory → Order → Payment)

### Failure Chain

```
T=0: Inventory Service database goes down
     (hardware failure, network partition)

T=30s: Inventory Service health checks fail
       Kubernetes removes it from service mesh
       All requests to inventory: 503 Service Unavailable

T=30s: Order Service tries to call Inventory Service
       Circuit breaker detects failure (5 failures in 60s)
       Circuit OPEN → fail immediately
       Order Service responds: "Temporarily unavailable"

T=60s: Order Service circuit opens
       Can't create orders
       Users see errors
       Queue backs up

T=60s+: Notification Service backs up (can't send confirmation)
        Notification Service CPU spikes
        Notification Pod OOMKilled
        Email backlog grows

T=120s: System degraded
        - No new orders accepted
        - Emails delayed
        - Inventory still down
```

### Prevention: Bulkhead Pattern

```python
# Isolate resources per service
# If order service fails, doesn't bring down inventory

ThreadPool for inventory calls:
  Max threads: 20
  Queue size: 100
  Timeout: 5 seconds

ThreadPool for payment calls:
  Max threads: 10
  Queue size: 50
  Timeout: 10 seconds

If inventory queue full:
  New requests fail immediately (fail fast)
  Don't wait and consume all threads
```

### Recovery Strategy

```yaml
# 1. Isolate failures with circuit breaker
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: inventory-service
spec:
  hosts:
  - inventory
  http:
  - route:
    - destination:
        host: inventory
    retries:
      attempts: 3
      perTryTimeout: 5s
    timeout: 10s

# 2. Fallback when inventory is unavailable
def place_order(order):
    try:
        stock = inventory.check_stock(order.product_id)
        if not stock:
            return error("Out of stock")
    except ServiceUnavailable:
        # Inventory down, use fallback
        # Option 1: Accept order anyway (risky, might oversell)
        # Option 2: Reject with apology (safe, bad UX)
        # Option 3: Check recent cache (best effort)
        
        cached_stock = redis.get(f"stock:{order.product_id}")
        if cached_stock > 10:  # Reasonable guess it's still in stock
            logger.warning("Accepting order without inventory check")
            order = Order.create(order)
            event_bus.publish("OrderCreated", order)
            return order
        else:
            return error("Inventory service unavailable, try later")

# 3. Health check
@app.route('/health', methods=['GET'])
def health():
    checks = {
        'inventory': ping_inventory(),
        'payment': ping_payment(),
        'database': ping_database(),
    }
    
    if all(checks.values()):
        return {'status': 'healthy'}, 200
    else:
        # Degraded but still running
        return {'status': 'degraded', 'checks': checks}, 503
```

---

## Scenario 5: Data Inconsistency Between Microservices

### Problem

```
Order in Order Service: status = "confirmed"
Inventory in Inventory Service: reservation expired (no longer holding stock)

User expects order to be shipping
But inventory doesn't have the stock anymore

Question: Which is source of truth?
```

### Solution: Event Sourcing Pattern

```python
# Every change is captured as event
# Events are immutable and timestamped

OrderCreatedEvent:
  timestamp: 2024-01-01T12:00:00Z
  order_id: 123
  user_id: 456
  product_id: 789
  quantity: 5

StockReservedEvent:
  timestamp: 2024-01-01T12:00:15Z
  order_id: 123
  product_id: 789
  quantity: 5
  expires_at: 2024-01-02T12:00:15Z

OrderConfirmedEvent:
  timestamp: 2024-01-01T12:00:30Z
  order_id: 123

ReservationExpiredEvent:
  timestamp: 2024-01-02T12:00:16Z
  order_id: 123
  product_id: 789
  quantity: 5
```

**Replay events to reconstruct state:**
```python
def get_order_state(order_id):
    events = EventStore.get_events(order_id)
    
    state = {
        'order_id': order_id,
        'status': 'pending',
        'reserved': False,
        'confirmed': False,
    }
    
    for event in events:
        if isinstance(event, OrderCreatedEvent):
            state['status'] = 'created'
        elif isinstance(event, StockReservedEvent):
            state['reserved'] = True
        elif isinstance(event, OrderConfirmedEvent):
            state['status'] = 'confirmed'
        elif isinstance(event, ReservationExpiredEvent):
            state['reserved'] = False
            state['status'] = 'failed'
    
    return state
```

**Source of truth: Events (not database state)**
- Database state = derived from events
- Events = immutable record
- Can always reconstruct correct state

---

## Interview Questions These Scenarios Answer

**Q: "How do you handle distributed failures?"**
A: "Saga pattern for distributed transactions, circuit breaker to fail fast, bulkhead isolation, graceful degradation with fallbacks. Example: If inventory service down, we either accept order with cache-based check or reject with explanation."

**Q: "What's your strategy for eventual consistency?"**
A: "Read-after-write consistency, replication lag monitoring, fallback to primary if lag too high. Event sourcing for single source of truth."

**Q: "How do you debug issues across services?"**
A: "Distributed tracing with correlation IDs, central logging, metrics per service. All logs and events tagged with order_id to trace through system."

**Q: "What breaks first under load?"**
A: "Usually message queue (RabbitMQ), then database replication lag, then application memory. Scale queue consumers first, then database, then app pods."
