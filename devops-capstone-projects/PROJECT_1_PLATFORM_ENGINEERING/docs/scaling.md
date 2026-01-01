# Scaling Scenarios & Solutions

## Scenario 1: Traffic Increases 10x Overnight

### Metrics Before:
- 100 requests/sec
- 3 Flask pods
- 30 req/sec per pod
- Database: 500 connections used / 1000 pool size
- Latency: p99 = 100ms

### Metrics During Spike:
- 1000 requests/sec
- 3 Flask pods (can't keep up)
- 333 req/sec per pod (error rate climbs)
- Database: 1000 connections used (POOL EXHAUSTED)
- Latency: p99 = 2000ms (requests queued)
- Error rate: 15% (connection refused)

### Automatic Response (HPA):

**Minute 0-2:**
```
Prometheus detects CPU > 70%
HPA triggers scale-up
5 new pods start (total 8)
~90 seconds for new pods to start + warm up
Latency still elevated
```

**Minute 2-5:**
```
8 pods now handling load (125 req/sec each)
Latency drops to 300ms
Database connection pool: 600/1000 (safe)
CPU back to 65%
```

**Minute 5+:**
```
If traffic sustains:
  - HPA adds more pods (target 20 max)
  - Database read replicas queried for analytics
  - Cache hit ratio improves (warm cache)
  
If traffic drops:
  - HPA waits 5 minutes (scaleDown stabilization)
  - Excess pods removed (save cost)
```

### Manual Interventions Needed:

1. **Database bottleneck?**
   ```sql
   SHOW max_connections;  -- Default 100, should be 200+
   SHOW shared_buffers;   -- Should be 25% of RAM
   ```
   - Increase if needed (AWS RDS easy scaling)
   - Query slow log for optimization

2. **Memory leak?**
   ```bash
   kubectl top pods | grep api
   # If memory grows constantly, scale up pod memory limit
   # Redeploy with larger memory request
   ```

3. **Cache hit ratio low?**
   ```
   Add Redis cluster nodes
   Increase TTL for stable data
   Monitor cache-coherency
   ```

### Cost Impact:
- 3 pods: 3 × $50 = $150/month
- 10 pods: 10 × $50 = $500/month
- Spike duration: 8 hours
- Extra cost: ($500 - $150) × 8/730 ≈ $4.38 (negligible)

---

## Scenario 2: Database Becomes Bottleneck

### Symptoms:
```
Latency spike (100ms → 500ms)
Slow query log fills with:
  SELECT * FROM orders WHERE created_at > NOW() - INTERVAL '1 day'
  SELECT * FROM users WHERE email LIKE '%@example.com'
CPU on database: 95%
Disk I/O: saturated
```

### Root Cause Analysis:
```sql
-- Check active queries
SELECT pid, usename, query, query_start 
FROM pg_stat_activity 
WHERE state = 'active'
ORDER BY query_start;

-- Check missing indexes
SELECT schemaname, tablename, indexname 
FROM pg_indexes 
WHERE schemaname = 'public';

-- Check table sizes
SELECT tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables 
WHERE schemaname='public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Solutions (in order):

**1. Add missing indexes (30 minute fix)**
```sql
-- Identify slow queries from pg_stat_statements
SELECT query, calls, mean_exec_time 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC LIMIT 10;

-- Add index (doesn't lock table in PG 14+)
CREATE INDEX CONCURRENTLY idx_orders_created 
ON orders(created_at) 
WHERE status != 'cancelled';

-- Verify index usage
EXPLAIN ANALYZE SELECT * FROM orders 
WHERE created_at > NOW() - INTERVAL '1 day';
```

**2. Add read replicas (1 hour fix)**
```bash
# RDS console: Create read replica in same AZ
# Application: Route SELECT queries to read replica
# Write queries still go to primary

# Cost: $150-300/month per replica
# Benefit: Read load distributed, primary focuses on writes
```

**3. Implement caching (2 hour fix)**
```python
# Redis cache frequently accessed data
def get_user_orders(user_id):
    cache_key = f"user:{user_id}:orders"
    
    # Check cache first (2ms)
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Cache miss, query database (100ms)
    orders = db.query(Order).filter(user_id=user_id).all()
    
    # Store in cache for 1 hour
    redis.setex(cache_key, 3600, json.dumps(orders))
    return orders
```

**4. Optimize slow queries (2-4 hours fix)**
```sql
-- Bad query (full table scan)
SELECT * FROM orders WHERE created_at > NOW() - INTERVAL '1 day'
-- Takes 2000ms (scans all 10M rows)

-- Add index
CREATE INDEX idx_orders_created ON orders(created_at);

-- Same query now takes 50ms (index scan + filter)

-- Even better: Partition table by date (if 100M+ rows)
CREATE TABLE orders_2024_01 PARTITION OF orders
  FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

**5. Vertical scaling (4 hours + cost)**
```
Current: db.t3.medium (2 CPU, 4GB RAM)
Upgrade to: db.r6i.xlarge (4 CPU, 32GB RAM)
Cost: $300 → $1000/month (+$700)
Downtime: 5-10 minutes (RDS maintains replica during upgrade)
```

### Monitoring Added:
```yaml
# Prometheus alerts
- alert: SlowQueries
  expr: rate(pg_stat_statements_mean_exec_time[5m]) > 1000  # >1 second
  
- alert: HighConnections
  expr: pg_stat_activity_count > 80  # >80% of max
  
- alert: ReplicationLag
  expr: pg_replication_lag_seconds > 5
  
- alert: CacheMissRate
  expr: redis_cache_miss_total / redis_cache_total > 0.3  # >30%
```

---

## Scenario 3: Kubernetes Node Fails

### What Happens:

**Second 0:**
```
EC2 instance t3.medium-2 crashes (hardware failure)
Kubelet stops responding to health checks
```

**Second 5:**
```
Master detects node not ready
Pod eviction starts (drain in-flight pods)
Endpoints removed from service
```

**Second 15-30:**
```
Pods start on healthy nodes
- Pod A (API): Starts on node-1 (already has 2 pods)
- Pod B (API): Starts on node-3 (has 1 pod)
Traffic redirected away from crashed node
```

**Minute 1:**
```
All pods healthy on remaining nodes
Load balancer: 2 pods on node-1, 2 pods on node-3
Request latency: Normal (no impact to users)
```

**Minute 5-10:**
```
AWS detects failed instance
Option 1: Replace with new instance (automatic if using ASG)
Option 2: Manual replacement
New node joins cluster
Pods rebalance across 3 nodes again
```

### Why No User Impact:
- ✅ 3 replicas across 3 AZs
- ✅ HPA can scale to 20 (plenty of headroom)
- ✅ Service endpoints updated automatically
- ✅ ALB removed failed node from target group

### Monitoring Alerts:
```yaml
- alert: NodeNotReady
  expr: kube_node_status_condition{condition="Ready"} == 0
  for: 5m  # Alert if node down for 5+ minutes
  
- alert: PodEvictionRate
  expr: rate(kube_pod_evictions_total[5m]) > 1
  
- alert: PendingPods
  expr: kube_pod_status_phase{phase="Pending"} > 0
  for: 5m  # Alert if pod can't schedule
```

---

## Scenario 4: Database Replication Lag Increases

### Symptoms:
```
Read replica latency increasing:
  Minute 1: 100ms lag
  Minute 5: 500ms lag
  Minute 10: 2 second lag
  Minute 15: 30 second lag
```

### Causes:
1. Primary writes very fast
2. Network bandwidth between primary/standby saturated
3. Replica CPU can't keep up (index updates slow)
4. Replica disk I/O bottleneck

### Solutions:

**1. Increase network throughput (immediate)**
```
RDS: Placement group (lower latency between instances)
Cost: No extra charge
Setup: 5 minutes
Benefit: Reduces network latency 10-50ms
```

**2. Optimize replication (30 minutes)**
```sql
-- On replica, tune recovery settings
max_wal_senders = 10  # Allow 10 concurrent replication streams
wal_keep_size = 1GB   # Keep WAL files locally
wal_level = replica   # Include enough info for replication
```

**3. Vertical scale replica (1 hour + cost)**
```
Replica too slow to apply changes
Upgrade from db.t3.medium to db.t3.large
Cost: +$150/month
```

**4. Add another standby (2 hours)**
```
If single standby can't keep up:
  Primary → Standby1 (synchronous)
  Standby1 → Standby2 (asynchronous)
Cost: Extra database instance
```

### Acceptable Lag Thresholds:
- **Primary-Standby**: < 1 second (acceptable)
- **Primary-Read Replica**: < 5 seconds (acceptable)
- **Read Replica-Cache**: < 1 minute (acceptable)

---

## Scenario 5: Certificate Expires (HTTPS Failure)

### Symptoms:
```
Browsers show "Not Secure" warning
Old clients may refuse connection
All traffic to HTTPS endpoint fails
```

### Prevention (Automated):
```yaml
# Use AWS ACM (AWS Certificate Manager)
# - Automatically renews 60 days before expiration
# - Free for AWS resources
# - Handles renewal without downtime

# Renovate bot can check certificate status
kind: Service
metadata:
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    cert-manager.io/issue-temporary-certificate: "true"
spec:
  tls:
  - hosts:
    - api.example.com
    secretName: api-tls
```

### If Cert Expires Anyway:
```bash
# 1. AWS ACM dashboard
# 2. Request new certificate (2-5 minutes)
# 3. Validate domain ownership (email or DNS)
# 4. Update Ingress manifest
# 5. kubectl apply -f ingress.yaml (instant)
```

---

## Scenario 6: Memory Leak in Flask App

### Symptoms:
```
Pod memory usage climbs steadily:
  Hour 1: 400MB
  Hour 2: 650MB
  Hour 3: 950MB (approaching 1GB limit)
  Hour 4: 1050MB → OOMKilled
  Hour 5: Pod restarts automatically
```

### Detection:
```yaml
# Prometheus alert
- alert: PodMemoryGrowth
  expr: |
    (rate(container_memory_working_set_bytes[10m]) > 0)
    and on(pod)
    (container_memory_working_set_bytes > 800e6)  # >800MB
  for: 10m
```

### Root Cause:
```python
# BAD: Memory leak in request handler
user_cache = {}  # Global dict

@app.route('/api/users/<id>')
def get_user(id):
    # Cache grows infinitely
    if id not in user_cache:
        user = db.query(User).get(id)
        user_cache[id] = user  # Never cleared!
    return user_cache[id]

# GOOD: Use Redis with TTL
@app.route('/api/users/<id>')
def get_user(id):
    cached = redis.get(f"user:{id}")
    if cached:
        return json.loads(cached)
    
    user = db.query(User).get(id)
    redis.setex(f"user:{id}", 3600, json.dumps(user))
    return user
```

### Fix Process:
```bash
# 1. Identify memory leak with memory profiler
pip install memory-profiler
python -m memory_profiler app.py

# 2. Fix code (example: remove global cache, use Redis)
git commit -am "Fix: Remove memory leak in user_cache"

# 3. Build new image
docker build -t api:v1.2.0 .
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/api:v1.2.0

# 4. Update deployment
kubectl set image deployment/api api=123456789.dkr.ecr.us-east-1.amazonaws.com/api:v1.2.0

# 5. Monitor new pods
kubectl logs -f deployment/api
kubectl top pods
```

### Prevention:
```yaml
# Set memory limits (kill pod before swap)
resources:
  limits:
    memory: "1Gi"  # Kill if exceeds 1GB
  requests:
    memory: "512Mi"  # Reserve 512MB

# Set restart policy
restartPolicy: Always  # Auto-restart on OOMKill

# Resource limits on node
kubelet config:
  systemReserved:
    memory: "500Mi"  # Reserve for OS
  kubeReserved:
    memory: "500Mi"  # Reserve for kubelet
```

---

## Scenario 7: Cascade Failure (One Component Failure → System Collapse)

### Failure Chain:
```
PostgreSQL primary fails
  ↓
RDS failover to standby (30 seconds)
  ↓
During failover: No master available (connections fail)
  ↓
API pods retry database connections
  ↓
Retry storms cause thundering herd
  ↓
API thread pool exhausted (waiting for DB)
  ↓
API stops accepting new requests
  ↓
ALB health checks fail
  ↓
API pods crash (OOM from queued requests)
  ↓
Users see 502 Bad Gateway
```

### Prevention Measures:

**1. Connection Pooling with Timeout**
```python
# SQLAlchemy connection pool
DATABASE_URL = "postgresql://..."
engine = create_engine(
    DATABASE_URL,
    pool_size=10,           # 10 connections max
    max_overflow=5,         # 5 waiting connections max
    pool_timeout=5,         # Fail after 5 seconds waiting
    pool_recycle=3600,      # Recycle connection every hour
)
```

**2. Circuit Breaker Pattern**
```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
def query_database(sql):
    return db.execute(sql)

# After 5 failures, circuit opens (fast fail)
# Requests fail immediately (no waiting)
# After 60 seconds, circuit tries again (half-open)
```

**3. Request Timeout**
```python
@app.before_request
def timeout():
    # Kill request after 30 seconds
    signal.alarm(30)

@app.errorhandler(signal.SIGALRM)
def timeout_error(signum, frame):
    return {"error": "Request timeout"}, 504
```

**4. Graceful Degradation**
```python
def get_user_profile(user_id):
    # Try to get full profile
    try:
        profile = db.query(UserProfile).get(user_id)
        return profile.to_dict()
    except DatabaseConnectionError:
        # Fall back to cached data if available
        cached = redis.get(f"user:{user_id}:profile")
        if cached:
            return json.loads(cached)
        # Fall back to empty profile
        return {"id": user_id, "name": "Unknown"}
```

### Monitoring During Cascade:
```yaml
- alert: HighDatabaseFailureRate
  expr: rate(db_errors_total[1m]) > 10
  
- alert: HighRetryRate
  expr: rate(flask_retries_total[1m]) > 100
  
- alert: ThreadPoolExhausted
  expr: flask_thread_pool_available == 0
  
- alert: CascadeDetected
  expr: |
    (rate(db_errors_total[1m]) > 10)
    and (rate(flask_http_500_errors_total[1m]) > 5)
    and (container_memory_working_set_bytes > 1000e6)
```

---

## Cost of Scaling

| Scenario | Extra Cost | Duration | Total |
|---|---|---|---|
| **Traffic spike 10x** | +$350/month | 8 hours | $1.36 |
| **Add read replica** | +$150/month | 1 hour | $0.57 |
| **Vertical scale DB** | +$700/month | 1 hour | $2.70 |
| **Multi-region** | +$1200/month | permanent | +$1200 |
| **Add Kubernetes nodes** | +$50/node | 1 hour | $0.19 per node |

**Lesson:** Horizontal scaling costs less than vertical scaling.

---

## Interview Talking Points

**Q: "How would you handle 10x traffic spike?"**
A: "HPA automatically scales pods up to 20. For database, I'd add read replicas and enable caching. If database is bottleneck, add indexes or cache frequently accessed data. Cost impact minimal for short spikes."

**Q: "What breaks first under load?"**
A: "Database connection pool. Applications wait for connections, thread pool gets exhausted, pods crash. Solution: Connection pooling with timeouts, circuit breaker pattern, graceful degradation."

**Q: "How do you prevent cascade failures?"**
A: "Connection pooling with timeouts, circuit breaker pattern, health checks, graceful degradation to cached data, monitoring for early warning signs."

**Q: "What's your RTO/RPO?"**
A: "RTO: 30 seconds (database failover) for infrastructure, < 5 minutes for app issues. RPO: 0 seconds (synchronous replication). Can recover from most failures automatically."
