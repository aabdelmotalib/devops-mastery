# Module 6: Performance Optimization

## Objectives

After completing this module, you will:
- Identify and eliminate bottlenecks using profiling
- Implement distributed caching strategies
- Design rate limiting and throttling
- Integrate CDN for static content
- Optimize database queries at scale
- Understand performance trade-offs

## 6.1 Finding Bottlenecks: Profiling

Can't optimize what you don't measure.

### The Performance Pyramid

```
Bottom-Up Analysis (find actual bottleneck):

1. Measure End-to-End Latency
   "Entire request takes 1000ms"
   
2. Break Down by Component
   Network: 50ms
   Processing: 300ms
   Database: 500ms
   Serialization: 150ms
   
3. Profile the Slowest Component (Database)
   SELECT queries: 400ms
   INSERT queries: 50ms
   JOIN operations: 50ms
   
4. Optimize Slowest Query
   SELECT * FROM orders WHERE user_id = ? AND created_at > ?
   (without index: 500ms)
   (with index: 10ms)

Result: 1000ms → 400ms (60% improvement)
```

### Tools for Profiling

**Application Profiler**:
- Python: cProfile, line_profiler
- Java: JProfiler, async-profiler
- Go: pprof
- Node.js: clinic.js, 0x

**Database Profiler**:
- EXPLAIN (PostgreSQL, MySQL)
- Query log (slow queries)
- pg_stat_statements (PostgreSQL)

**System Profiler**:
- perf (Linux)
- top, htop (CPU, memory)
- iostat (disk I/O)
- netstat (network)

### Real Example: Slow Query

```sql
-- Slow query (10000ms)
SELECT * FROM orders
WHERE user_id = 123
AND status = 'completed'
AND created_at > '2024-01-01'

Reason: No index on (user_id, status, created_at)
Scans: 5M rows to find ~100 matching

-- With index
CREATE INDEX idx_orders_user_status_date 
ON orders(user_id, status, created_at DESC)

Time: 10ms

Improvement: 1000x faster
```

## 6.2 Rate Limiting and Throttling

Protect services from overload.

### Problem: Overload Without Limits

```
API accepts unlimited requests:
100 req/sec, 1000 req/sec, 10000 req/sec, 100000 req/sec

System designed for 10K req/sec:
At 15K: Latency increases
At 20K: Errors start appearing
At 30K: System cascades (database exhausted)

Solution: Reject requests above limit (fail gracefully).
```

### Token Bucket Algorithm

```
Bucket: 1000 tokens
Refill rate: 10 tokens per second

Request arrives:
├─ Has bucket >= 1 token?
│  Yes: Deduct 1, allow request
│  No: Reject request (rate limited)

Implementation:
tokens = 1000
last_refill = now()

def check_rate_limit():
    now = time.time()
    elapsed = now - last_refill
    new_tokens = elapsed * 10  // 10 tokens/sec
    tokens = min(1000, tokens + new_tokens)
    last_refill = now
    
    if tokens >= 1:
        tokens -= 1
        return True  // Allow
    else:
        return False  // Reject
```

### Redis-Based Rate Limiting

```
Per-user rate limit: 100 requests per minute

Redis key: rate_limit:user_123
```python
def check_rate_limit(user_id, limit=100, window=60):
    key = f"rate_limit:{user_id}"
    
    # Increment counter
    current = redis.incr(key)
    
    if current == 1:
        # First request in window, set expiry
        redis.expire(key, window)
    
    if current > limit:
        return False  # Rate limited
    else:
        return True  # Allow
```

### Throttling (Adaptive Rate Limiting)

Not binary (allow/reject), but adaptive based on system state:

```
Light Load (CPU < 50%, DB connections < 50%):
Rate limit: 100 req/sec

Medium Load (CPU 50-70%, DB connections 50-80%):
Rate limit: 75 req/sec

Heavy Load (CPU > 70%, DB connections > 80%):
Rate limit: 50 req/sec

Overload (CPU > 90%, DB connections > 95%):
Rate limit: 25 req/sec

Result: System gracefully sheds load as it approaches limits.
```

## 6.3 Distributed Caching Patterns

Beyond single server cache, caching at multiple layers.

### Layer 1: Browser Cache

```
HTTP Response Headers:
Cache-Control: max-age=3600  // Cache for 1 hour
ETag: "33a64df4245225869b92fc6a40b915bb"

Browser caches response.
Next request: Browser checks cache first.
Result: Zero server load for repeat requests.
```

### Layer 2: CDN Cache

```
Request to S3://bucket/image.jpg

Without CDN:
User in Tokyo → AWS S3 (US) → 300ms latency

With CloudFront:
User in Tokyo → CDN Edge (Tokyo) → 1ms latency
CDN fetches from origin if needed (once).
Subsequent requests: served from edge.
```

### Layer 3: Application Cache

```
Request: GET /api/user/123/profile

Cache-Aside:
1. Check Redis: profile:123
2. If hit: return (1ms)
3. If miss: query DB (100ms)
4. Store in Redis (ttl=1hour)
5. Return to user
```

### Cache Warming

Don't wait for cache misses, proactively populate:

```python
def warmup_cache():
    # Populate most-accessed data
    top_users = db.query("SELECT * FROM users ORDER BY popularity DESC LIMIT 10000")
    for user in top_users:
        cache.set(f"user:{user.id}", user, ttl=3600)
    
    popular_products = db.query("SELECT * FROM products WHERE popularity > threshold")
    for product in popular_products:
        cache.set(f"product:{product.id}", product, ttl=3600)

# Run at service startup
@app.before_first_request
def startup():
    warmup_cache()
```

## 6.4 Database Query Optimization

Queries are often the bottleneck.

### Indexing Strategy

```
Table: orders (100M rows)

Query: SELECT * FROM orders WHERE user_id = 123

No index: Full table scan (100M rows checked) = 5000ms
With index on user_id: Seek + fetch (~1000 rows) = 10ms

Trade-off: Index uses extra space (5-10% of table size)
But dramatically faster queries.
```

### Join Optimization

```
Query 1 (SLOW - N+1 problem):
orders = db.query("SELECT * FROM orders LIMIT 1000")
for order in orders:
    user = db.query("SELECT * FROM users WHERE id = ?", order.user_id)
    // 1 + 1000 queries

Queries: 1001 (one per order)
Latency: 1000 * 5ms = 5000ms

Query 2 (BETTER - JOIN):
SELECT o.*, u.* FROM orders o
JOIN users u ON o.user_id = u.id
LIMIT 1000

Queries: 1 (single join)
Latency: 100ms
```

### Denormalization for Speed

```
Normalized (slow):
user_id → lookup username in users table
username → lookup in comments → join

Denormalized (fast):
Store username directly in comments table
No join needed, single table scan.

Trade-off: Extra storage, must update username in multiple places
Benefit: 10x faster queries
```

## 6.5 CDN and Static Content

Content Delivery Network: serve content from edge locations.

### CDN Architecture

```
User in Tokyo
    ↓
Request for image.jpg
    ↓
Tokyo CDN Edge
├─ Check cache: image.jpg
├─ Hit: serve immediately (1ms)
└─ Miss: fetch from origin (300ms), cache, serve

Next request from Tokyo:
    ↓
Tokyo CDN Edge
├─ Cache hit: serve immediately (1ms)
└─ No origin fetch
```

### CDN Cache Headers

```
Static content (images, CSS, JavaScript):
Cache-Control: public, max-age=31536000  // 1 year
ETag: "v1-hash"

Semi-static (rarely changes):
Cache-Control: public, max-age=86400  // 1 day

Dynamic content:
Cache-Control: private, no-cache
Or: Set-Cookie (not cached by CDN)
```

## 6.6 Production Recommendations

### Performance Monitoring

```
Track key metrics:
- Request latency (p50, p95, p99)
- Database query time
- Cache hit rate
- CPU/Memory utilization
- Network I/O

Alert on:
- p99 latency increase > 20%
- Cache hit rate drop
- Query time > SLA
- CPU > 80%
```

### Optimization Priority

```
Order of optimization (biggest impact first):

1. Database queries (often 50-70% of latency)
   - Add indexes
   - Eliminate N+1
   - Denormalize if needed

2. Caching (often 30-40% latency reduction)
   - Cache frequently accessed data
   - CDN for static content

3. Application code (often 10-20% of latency)
   - Profile and optimize hot paths
   - Parallelization

4. Infrastructure scaling (last resort)
   - Vertical scaling
   - Horizontal scaling
```

---

## Exam & Practice

### Multiple Choice Questions

**Q1**: Query takes 500ms. Breakdown: DB 400ms, processing 50ms, network 50ms. What should you optimize first?

A) Processing code (50% optimization)
B) Database query (80% optimization)
C) Network (might reduce round trips)
D) Cache (prevent query altogether)

**Q2**: Rate limit is 1000 req/sec. Peak load is 900 req/sec normally, spike to 2000 req/sec. What happens?

A) Requests queued (wait)
B) 1100 requests rejected (graceful degradation)
C) System crashes
D) Depends on throttling policy

**Q3**: Cache hit rate is 95% for user profiles. Should you increase cache TTL from 1 hour to 24 hours?

A) Yes (more hits)
B) No (more stale data)
C) Need more information (what's staleness tolerance?)
D) Makes no difference

**Q4**: Database index uses 10GB of extra disk. Reduces query from 1000ms to 10ms. Is it worth it?

A) No (too much disk)
B) Yes (100x speedup worth 10GB)
C) Maybe (depends on storage cost vs benefit)
D) Depends on how many queries

**Q5**: User complaint: "Images load slow from Europe". Your origin is US. How do you fix?

A) Optimize image compression
B) Add CDN with edge in Europe
C) Upgrade database
D) Add more app servers

### Hands-on Tasks

**Task 1: Performance Analysis**

Given this system:
- API response time: 800ms average
- Database query: 600ms average
- Processing: 100ms average
- Network: 100ms average

1. Calculate bottleneck percentage
2. Suggest top 3 optimizations
3. Estimate impact of each optimization
4. Which optimization gives best ROI?

**Task 2: Caching Strategy**

You have:
- User data (1M users, read-heavy, changes infrequent)
- Session data (10M sessions, high turnover, critical)
- Product catalog (100K products, read-heavy, changes daily)
- User feed (dynamic, varies by user, changes constantly)

For each, specify:
- Cache or not?
- Cache type (L1, L2, CDN)?
- TTL strategy
- Invalidation strategy

### Incident Scenario

**Scenario: Performance Degradation from Missing Index**

Timeline:
- T+0: System running normally (100ms avg latency)
- T+0: Feature launch: new report generating complex query
- T+0: Query scans 50M rows (no index), takes 15 seconds
- T+10min: 100 users run report → query queue fills
- T+15min: Database connection pool exhausted
- T+20min: Other queries timeout
- T+25min: Entire system slow (cascading)
- T+40min: Alert fires
- T+50min: Team adds index, query now 100ms

**Questions:**
1. How would you detect the new query before production?
2. What monitoring would have caught the degradation?
3. How would you reproduce this locally?
4. Design testing to prevent this in future?
5. What emergency actions (while waiting for index)?

---

**Next**: [Module 7: Consistency, Transactions & Coordination](07-consistency-transactions.md)
