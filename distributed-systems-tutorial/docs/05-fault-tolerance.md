# Module 5: Fault Tolerance & Reliability

## Objectives

After completing this module, you will:
- Implement circuit breaker and bulkhead patterns
- Design health checks and automatic recovery
- Understand leader election and distributed consensus
- Design multi-region failover strategies
- Handle graceful degradation
- Build self-healing systems

## 5.1 Circuit Breaker Pattern

Prevents repeated calls to failing services.

### Problem: Cascading Failures

```
Normal:
User Service (100ms) → calls Payment Service (50ms)
Total: 150ms

Payment Service starts failing (timeout 5s):
User Service waits for Payment Service
Threads fill up after ~10 seconds
User Service stops accepting requests
Entire system becomes unresponsive

This is cascading failure.
```

### Circuit Breaker Solution

Monitor service health, fail fast when unhealthy:

```
States:

CLOSED (normal):
├─ Requests flow through
├─ Count failures
└─ On threshold, transition to OPEN

OPEN (circuit broken):
├─ Requests fail immediately (fast)
├─ No attempt to call failing service
├─ After timeout (60s), transition to HALF_OPEN

HALF_OPEN (testing recovery):
├─ Allow single test request
├─ If success, reset to CLOSED
├─ If fail, go back to OPEN
```

### Implementation

```python
from enum import Enum
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold=5, success_threshold=2, timeout=60):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
    
    def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            # Circuit is open, check if recovery timeout passed
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                # Circuit still open, fail fast
                raise CircuitBreakerOpen(f"Circuit open, retry in {self.timeout}s")
        
        try:
            result = func(*args, **kwargs)
            
            if self.state == CircuitState.HALF_OPEN:
                # Test call succeeded
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
            
            return result
        
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.state == CircuitState.HALF_OPEN:
                # Test failed, go back to open
                self.state = CircuitState.OPEN
            
            elif self.failure_count >= self.failure_threshold:
                # Too many failures, open circuit
                self.state = CircuitState.OPEN
            
            raise

# Usage
payment_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

def charge_user(user_id, amount):
    try:
        return payment_breaker.call(payment_service.charge, user_id, amount)
    except CircuitBreakerOpen:
        # Service is failing, return cached result or error
        return {"status": "payment_service_unavailable"}
```

## 5.2 Bulkhead Pattern

Isolate resources to prevent total system failure.

### Problem: Resource Exhaustion

```
Single thread pool (100 threads):
├─ 50 threads: handling /api/orders
├─ 30 threads: handling /api/payments
├─ 10 threads: handling /api/recommendations
└─ 10 threads: handling /api/notifications

If /api/payments has memory leak (threads hang):
All 30 threads in payments hang.
Orders, recommendations, notifications are fine.

But when next payment request comes:
All 100 threads filled (already used by orders, etc)
Payment request has no thread.

Then what happens to the orders that were working?
They're competing for threads with waiting payments.

Result: Entire system slows down (cascading).
```

### Bulkhead Solution

Separate thread pools per service:

```
Service A
├─ Thread pool A (30 threads)
├─ Max queue: 100 requests

Service B
├─ Thread pool B (40 threads)
├─ Max queue: 200 requests

Service C
├─ Thread pool C (30 threads)
├─ Max queue: 100 requests

If Service A has memory leak (threads hang):
├─ Service A is degraded (thread starvation)
├─ Service B unaffected (own threads)
└─ Service C unaffected (own threads)

Failure is isolated to Service A.
```

### Implementation

```python
from concurrent.futures import ThreadPoolExecutor, RejectedExecutionError

class BulkheadExecutor:
    def __init__(self, name, core_threads, max_threads, queue_size):
        self.name = name
        self.executor = ThreadPoolExecutor(
            max_workers=max_threads,
            thread_name_prefix=f"bulkhead-{name}"
        )
        self.queue_size = queue_size
        self.active_tasks = 0
    
    def submit(self, func, *args, **kwargs):
        if self.active_tasks >= self.queue_size:
            raise RejectedExecutionError(
                f"Bulkhead {self.name} queue full"
            )
        
        self.active_tasks += 1
        
        def wrapped():
            try:
                return func(*args, **kwargs)
            finally:
                self.active_tasks -= 1
        
        return self.executor.submit(wrapped)

# Usage
payment_executor = BulkheadExecutor("payment", core_threads=20, max_threads=50, queue_size=100)
order_executor = BulkheadExecutor("order", core_threads=30, max_threads=80, queue_size=200)

def process_payment():
    try:
        return payment_executor.submit(payment_service.charge, user_id, amount)
    except RejectedExecutionError:
        return {"status": "payment_service_overloaded"}

def create_order():
    try:
        return order_executor.submit(order_service.create, order_data)
    except RejectedExecutionError:
        return {"status": "order_service_overloaded"}
```

## 5.3 Health Checks and Self-Healing

Systems that detect and recover from failures automatically.

### Health Check Endpoints

Every service must expose health status:

```
GET /health

Response (healthy):
{
  "status": "healthy",
  "checks": {
    "database": {
      "status": "ok",
      "latency_ms": 2
    },
    "cache": {
      "status": "ok",
      "latency_ms": 1
    },
    "disk_usage_percent": 45,
    "memory_usage_percent": 60
  },
  "version": "1.2.3"
}

Response (degraded):
{
  "status": "degraded",
  "checks": {
    "database": {
      "status": "slow",
      "latency_ms": 5000
    },
    "cache": {
      "status": "error",
      "error": "connection timeout"
    }
  }
}

Response (unhealthy):
{
  "status": "unhealthy",
  "error": "database is down"
}
```

### Load Balancer Health Checking

Load balancer monitors service health:

```
Load Balancer
├─ Server 1
│  ├─ Health check: PASS (200 OK)
│  └─ Status: HEALTHY
│
├─ Server 2
│  ├─ Health check: FAIL (timeout)
│  └─ Status: UNHEALTHY
│
└─ Server 3
   ├─ Health check: PASS (200 OK)
   └─ Status: HEALTHY

Traffic distribution:
New requests → Server 1 or Server 3 (skip Server 2)
```

### Kubernetes Self-Healing

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-service
spec:
  containers:
  - name: app
    image: my-service:v1.0
    livenessProbe:
      httpGet:
        path: /health
        port: 8080
      initialDelaySeconds: 10
      periodSeconds: 5
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 3

Behavior:
- Every 5s: Check GET /health
- If fails 3 times: Kill pod and restart
- Before passing traffic: Check GET /ready
- If not ready: Don't send requests (but don't kill)
```

### Automatic Restart with Exponential Backoff

```python
def restart_with_backoff(service_name, max_retries=5):
    for attempt in range(max_retries):
        try:
            service.start()
            logger.info(f"Service {service_name} started successfully")
            return
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Service {service_name} failed after {max_retries} attempts")
                raise
            
            delay = 2 ** attempt  # 1s, 2s, 4s, 8s, 16s
            logger.warning(f"Service {service_name} failed, retrying in {delay}s")
            time.sleep(delay)
```

## 5.4 Leader Election

When multiple services need to coordinate on a single leader:

### Problem: Duplicate Leaders

```
Cluster: 3 servers
├─ Server 1: thinks it's leader
├─ Server 2: thinks it's leader (network partition)
└─ Server 3: thinks it's leader (network partition)

Both leaders might:
- Accept writes (conflict)
- Delete data (inconsistency)
- Process same batch twice (duplicates)

Solution: Use consensus algorithm to elect single leader.
```

### Consensus Algorithms Overview

#### Raft Algorithm

```
Follower → Candidate → Leader

Normal operation:
- 1 Leader, 2 Followers
- Leader sends heartbeats every 150ms
- Followers receive heartbeats, reset timeout

Leader fails:
- Followers stop receiving heartbeats
- Timeout triggers (300-450ms)
- Follower becomes Candidate
- Candidate requests vote from other servers
- If gets majority (2 out of 3), becomes Leader
- New leader starts sending heartbeats

Result: New leader elected in < 500ms
```

### Distributed Lock (etcd/Zookeeper)

```
Multiple services need to coordinate:

Service A: Try to acquire lock
├─ Write to etcd: /distributed_locks/batch_processor = "service_a"
├─ If write succeeds: acquired lock
└─ Process batch

Service B: Try to acquire lock
├─ Write to etcd: /distributed_locks/batch_processor = "service_b"
├─ If write fails (key exists): didn't acquire lock
└─ Wait and retry

Leader-only processing:
```python
def acquire_lock(lock_name, ttl_seconds=60):
    try:
        etcd_client.put(f"/locks/{lock_name}", hostname, lease=ttl_seconds)
        return True
    except AlreadyExistsError:
        return False

def process_batch():
    if acquire_lock("batch_processor"):
        try:
            # Safely process (only one service at a time)
            process()
        finally:
            etcd_client.delete("/locks/batch_processor")
    else:
        # Another service has lock, skip this batch
        pass
```

## 5.5 Multi-Region Failover

Surviving entire datacenter failures.

### Architecture

```
Primary Region (US-EAST)
├─ Load Balancer
├─ App Servers (10)
├─ Database Primary
└─ Cache Cluster

Secondary Region (US-WEST)
├─ Load Balancer
├─ App Servers (2, minimal)
├─ Database Replica
└─ Cache Cluster

Tertiary Region (EU-WEST)
├─ Minimal infrastructure

DNS:
Resolves service.example.com to:
1. Primary region (50% weight)
2. Secondary region (40% weight)
3. Tertiary region (10% weight)
```

### Failover Procedure

```
Normal:
- Primary region: 100K req/sec
- Secondary region: 5K req/sec (monitors)

Primary region primary database fails:
- Database replica promotes to primary
- Replication restarts from secondary
- Application continues (same region)
- Uptime: 5-30 minutes

Entire primary region fails:
- DNS detects via health checks
- Shifts 100K req/sec to secondary (overloaded)
- Secondary scales up from 2 servers to 10 servers
- Meanwhile, replicate data from secondary to tertiary
- Time: 5-30 minutes for detection, 3-10 minutes for failover
- Total downtime: ~15 minutes

Result: 99.95% - 99.99% availability
```

### Data Replication Strategy

```
Primary → Secondary (synchronous)
        ↘
          Tertiary (asynchronous)

Why?
- Primary → Secondary: must be in sync (for failover)
- Primary → Tertiary: can be async (disaster recovery only)

Trade-off:
- Synchronous to Secondary: slower writes
- Asynchronous to Tertiary: might lose minutes of data
```

## 5.6 Graceful Degradation

System should degrade elegantly when failing:

```
Fully Functional:
├─ Orders: real-time processing
├─ Recommendations: ML-based, personalized
├─ Notifications: instant
├─ Inventory: real-time

Database slow (99.9 → 95% success):
├─ Orders: still real-time (most succeed)
├─ Recommendations: fallback to trending (ignore personalization)
├─ Notifications: async only (no real-time)
├─ Inventory: cached (stale but available)

Database down:
├─ Orders: read-only (can't create new)
├─ Recommendations: trending only
├─ Notifications: queued (process later)
├─ Inventory: cache only (hours stale, acceptable)

Goal: System is 60% functional instead of 0% functional.
```

### Implementation

```python
def get_recommendations(user_id):
    try:
        # Try ML-based personalized recommendations
        if recommendation_service.is_healthy():
            return recommendation_service.get_personalized(user_id)
    except:
        pass
    
    try:
        # Fallback: trending recommendations
        return recommendation_service.get_trending()
    except:
        pass
    
    try:
        # Last resort: cached popular items
        return cache.get("popular_items")
    except:
        pass
    
    # Everything failed, return empty
    return []
```

## 5.7 Production Recommendations

### Health Check Checklist

Every service should check:
- [ ] Can connect to database
- [ ] Can connect to cache (if critical)
- [ ] Disk space (> 10% free)
- [ ] Memory (< 90% used)
- [ ] Database replication lag (< 1 second)
- [ ] Message queue depth (< 1000)
- [ ] Recent successful request (last 5 minutes)

### Monitoring Service Dependencies

```
Service Dependency Graph:
API Gateway → Auth Service, Order Service, User Service
Order Service → Payment Service, Inventory Service, Database
Payment Service → Payment Gateway, Database

For each dependency, monitor:
- Availability (% successful calls)
- Latency (p50, p95, p99)
- Error rate (failures)
- Timeout rate

Alert if:
- Availability < 99% for critical path
- Latency p99 > SLA
- Error rate > 1%
```

### Test Failover Regularly

Don't wait for emergency:
```
Monthly: Kill database replica → verify failover works
Quarterly: Simulate region failure → ensure runbook works
Yearly: Full disaster recovery test
```

---

## Exam & Practice

### Multiple Choice Questions

**Q1**: A service has 100 threads. Payment service has memory leak (threads hang). Using bulkheads, what happens?

A) All 100 threads hang
B) Only payment threads hang, others continue
C) System detects leak, restarts payment service
D) Transactions rollback

**Q2**: Circuit breaker is OPEN. Service recovers but circuit stays open. When does it try again?

A) Immediately (circuit should reset)
B) After timeout expires (transitions to HALF_OPEN)
C) When admin manually resets
D) Never (circuit permanently broken)

**Q3**: You have 3 database replicas in primary region. Primary fails. What's the best next action?

A) Promote replica 1 immediately
B) Wait for manual intervention
C) All replicas fail (total loss)
D) Requires consensus vote among replicas

**Q4**: Multi-region setup: primary US-EAST, secondary US-WEST. Primary fails completely. Expected downtime?

A) 0 minutes (instant)
B) 5-30 minutes (detection + failover)
C) 1-3 hours (manual recovery)
D) System is down (no redundancy)

**Q5**: A critical service degrades (latency goes to 5s). Should you immediately fail over?

A) Yes (always fail over immediately)
B) No (try circuit breaker + fallbacks first)
C) Maybe (depends on SLA)
D) Never (failover is risky)

### Hands-on Tasks

**Task 1: Circuit Breaker Design**

Design circuit breaker policy for:
- Payment Service: Critical, failure = revenue loss
- Recommendation Service: Nice-to-have, failure = users see default
- Analytics Service: Background, failure = lost data

For each, specify:
- Failure threshold
- Recovery timeout
- Fallback behavior
- Monitoring/alerting

**Task 2: Multi-Region Failover**

Design system for:
- Primary region: 1M req/sec
- Secondary region: 10K req/sec (standby)
- RTO (Recovery Time Objective): 10 minutes
- RPO (Recovery Point Objective): 1 minute of data

Specify:
- Data replication strategy
- Scaling plan for secondary
- DNS failover mechanism
- Testing schedule

### Incident Scenario

**Scenario: Cascading Failure from Payment Service Degradation**

Timeline:
- T+0: Payment gateway (external API) starts having network issues (99% success → 70% success)
- T+0: Your payment service starts retrying (exponential backoff kicks in)
- T+5min: Your payment service has 500 pending payment requests (threads fill up)
- T+10min: Database gets hammered by retries (connection pool exhausted)
- T+12min: Order service (which calls payment service) starts timing out
- T+15min: All services blocked waiting for database
- T+20min: Entire system is degraded (API gateway still responds but 50% error rate)
- T+40min: Alert finally fires
- T+50min: On-call engineer investigates

**Questions:**
1. How would circuit breaker have prevented this?
2. How would bulkheads have helped?
3. What monitoring would catch this at T+5min?
4. Design the failover strategy (payments, inventory, notifications)
5. How do you recover (immediate) and prevent (long-term)?

---

**Next**: [Module 6: Performance Optimization](06-performance-optimization.md)
