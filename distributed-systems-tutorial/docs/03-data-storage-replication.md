# Module 3: Data Storage & Replication

## Objectives

After completing this module, you will:
- Understand distributed database architectures
- Design replication strategies (leader-follower, multi-leader, peer-to-peer)
- Reason about consistency models (strong, eventual, causal)
- Implement caching strategies (cache-aside, write-through, write-behind)
- Design data partitioning for scale
- Handle cache invalidation in production

## 3.1 Database Replication Strategies

Replication: keeping copies of data on multiple servers.

### Why Replicate?

```
Single database:
- One failure = data loss
- Can't scale reads
- Single geographic location = high latency for far users

Multiple replicas:
- Survive single server failure
- Distribute read load
- Serve from location close to users
- Durability (data in multiple places)
```

### Leader-Follower Replication

One primary database (leader) handles writes, followers (replicas) handle reads.

```
Writes:
User Request
↓
WRITE to Leader
↓
Leader replicates to Followers (asynchronously)
↓
Followers acknowledge

Reads:
User Request
↓
READ from Follower (any one)
↓
Return data immediately
```

#### Implementation

```
Leader (Primary):
- Accepts all writes
- Write-Ahead Log (WAL): logs every transaction
- Sends WAL to followers

Follower (Replica):
- Receives WAL
- Applies transactions in same order
- Stays synchronized
```

#### Write Process

```
Write to Database:
1. Client sends write to leader
2. Leader writes to local storage
3. Leader writes transaction to WAL
4. WAL sent to followers (asynchronously)
5. Followers apply transaction

Client response:
Option A: Respond immediately (leader returns before followers acknowledge)
    - Fast (< 1ms)
    - Risk: data loss if leader crashes before replicating

Option B: Wait for replica acknowledgment (synchronous replication)
    - Slow (10-100ms, network latency to replica)
    - Safe: data on multiple servers
```

#### Followers Lag (Replication Delay)

In asynchronous replication, followers lag behind leader:

```
T+0: Leader receives write: user.balance = 100
T+0: Client reads from Follower
     Follower hasn't replicated yet, returns old value (balance = 90)
     
T+50ms: Follower finally receives write
        New reads from follower return 100

This is replication lag (temporary inconsistency).
```

#### Write-After-Read Consistency

**Problem**: User updates profile, immediately reads it, sees old data.

**Solution**: Always read your own writes from leader.

```python
# After writing to leader
session.set('just_wrote_to_leader', True)

# On reads
if session.get('just_wrote_to_leader'):
    read from leader  # Guaranteed to see your write
else:
    read from follower (distributed)
```

#### Replica Failure

If a replica crashes:

```
Process:
1. Replica disconnects (heartbeat fails)
2. Leader stops replicating to that replica
3. When replica comes back, it's behind
4. Replica requests missing transactions from leader
5. Replica catches up
6. Resume replication

No data loss (everything on leader).
```

#### Leader Failure (More Complex)

```
Normal:
Clients write to Leader
Leader replicates to Followers

Leader crashes:
- Clients can't write
- System unavailable

Recovery (manual):
1. Operator detects failure
2. Chooses a follower to promote to new leader
3. Points clients to new leader
4. New leader replicates to other followers

Time: 15-30 minutes (if lucky) to 1+ hours
```

### Multi-Leader Replication

Multiple leaders, each accepts writes independently.

```
Leader A                    Leader B
Write → Followers           Write → Followers
     ↓                           ↓
     └─────→ Bidirectional ←─────┘
             Replication
```

#### Advantages

1. **Availability**: If one leader down, other continues accepting writes
2. **Lower latency**: Write to nearest leader
3. **Geographic distribution**: Each region has local leader

#### Disadvantages

1. **Conflict resolution**: If both leaders receive writes to same row
2. **Complexity**: Ensuring consistency is hard
3. **Bugs**: Dual-write bugs cause subtle inconsistencies
4. **Replication lag**: Updates reach other leader slowly

#### Conflict Example

```
User in US:
- Connects to Leader A (US)
- Writes: user.name = "Alice"
- Immediately replicates to Leader B (EU)

User in EU:
- Connects to Leader B (EU)
- Reads: user.name (gets "Alice", correct)
- Updates user.name = "Alice Johnson"
- Replicates to Leader A

Meanwhile, Leader A was also processing:
- User updates user.email (simultaneous write)
- Replicates to Leader B

Conflict:
Leader A has: name = "Alice", email = "alice@example.com"
Leader B has: name = "Alice Johnson", email = "alice@example.com"

Which is source of truth? Both are half-right.
```

### Peer-to-Peer (Leaderless) Replication

All nodes are equal, any node accepts writes.

```
Client
   ↓
Request goes to any 3 nodes

Write R = 3:
- Write to node A
- Write to node B
- Write to node C
- Acknowledge when 3 agree

Read R = 3:
- Read from node A
- Read from node B
- Read from node C
- Return most recent (use version numbers)
```

#### Example: DynamoDB, Cassandra

```
3 nodes, write R=3 (all must succeed)
Read R=3 (all must agree)

Write:
Client → Write {id: 123, value: "Alice"}
        → Node 1: stored
        → Node 2: stored
        → Node 3: stored
        → Respond to client (all succeeded)

If any node fails, write fails. Requires all nodes healthy.
```

#### Read Repair

If read finds inconsistent replicas, fix it:

```
Read request hits 3 nodes:
Node 1: {id: 123, version: 1, value: "Alice"}
Node 2: {id: 123, version: 2, value: "Alice Johnson"} ← newest
Node 3: {id: 123, version: 1, value: "Alice"}

Read returns version 2 (newest).
But also writes version 2 to Node 1 and 3 (read repair).
```

## 3.2 Consistency Models

How consistent is your system?

### Strong Consistency

All replicas see same data at same time.

```
Write: balance = 100
Immediately after:
Read from any replica: get 100

Implementation:
- Synchronous replication (wait for all replicas)
- Single leader (serialize all writes)
- Consensus (quorum agreement)

Cost:
- Write latency (must replicate to multiple servers)
- Availability (if replicas down, can't accept writes)
```

### Eventual Consistency

All replicas eventually see same data, but not immediately.

```
Write: balance = 100
Immediately after:
Read from replica 1: might get 90 (lag)
Read from replica 2: might get 100 (already updated)

After replication completes (milliseconds to seconds):
All replicas: 100
```

**Good for:**
- Social media (eventual like counts)
- Analytics (eventual aggregations)
- User profiles (eventual updates)

**Bad for:**
- Financial systems (need immediate consistency)
- Inventory (need to know stock is actually available)

### Causal Consistency

Events that are causally related stay consistent.

```
Example (chat system):
User A writes: "Hello"
User B reads: "Hello"
User B writes: "Hi there"
User A reads: should see both messages in order

Causal consistency: "Hi there" is a response to "Hello",
                  so must maintain this order

Non-causal system: might reorder messages
```

## 3.3 Caching Strategies

Caching: store frequently accessed data in fast storage.

### Cache Placement

```
Client
  ↓
Web Tier (stateless services)
  ↓
Cache Tier (Redis, Memcached)
  ↓
Database (source of truth)
```

Cache hits: 100µs (Redis) vs. 5ms (Database) = 50x faster.

### Cache-Aside Pattern (Lazy Loading)

Application explicitly manages cache:

```python
def get_user(user_id):
    # Check cache first
    user = cache.get(f"user:{user_id}")
    if user is not None:
        return user  # Cache hit
    
    # Cache miss, load from DB
    user = db.query(f"SELECT * FROM users WHERE id = {user_id}")
    
    # Store in cache for future
    cache.set(f"user:{user_id}", user, ttl=3600)
    
    return user
```

**Advantages**: Simple, only cache what's accessed, flexible TTL
**Disadvantages**: Cache miss penalty, cache invalidation challenges

### Write-Through Pattern

Write goes to both cache and database:

```python
def update_user(user_id, data):
    # Update cache
    cache.set(f"user:{user_id}", data)
    
    # Update database
    db.update(f"UPDATE users SET ... WHERE id = {user_id}", data)
    
    return data
```

**Advantages**: Cache always consistent with DB
**Disadvantages**: Slower writes, must maintain both

### Write-Behind Pattern (Write-Back)

Write goes to cache first, database later:

```python
def update_user(user_id, data):
    # Write to cache (fast)
    cache.set(f"user:{user_id}", data)
    
    # Queue database write for later
    queue.publish("db_write", {
        "table": "users",
        "id": user_id,
        "data": data
    })
    
    return data  # Return immediately
```

**Advantages**: Very fast writes, asynchronous DB updates
**Disadvantages**: Risk of data loss (cache crashes before DB writes), complex

## 3.4 Cache Invalidation Challenges

"There are only two hard things in Computer Science: cache invalidation and naming things."

### Problem: Stale Cache

```
Initial: user.email = alice@example.com (in cache)

Another process updates DB: user.email = alice.new@example.com

Stale cache still returns: alice@example.com

How long until user sees new email?
- Never (if TTL not set)
- After TTL expires (could be hours)
```

### Invalidation Strategies

#### Time-Based (TTL)

```
Set cache TTL = 1 hour

user = cache.get("user:123")  # Fresh
... (30 minutes later)
user = cache.get("user:123")  # Still fresh
... (45 minutes later)
user = cache.get("user:123")  # Still fresh, stale for 15 mins
... (75 minutes later)
cache expires, fetch fresh from DB
```

**Advantage**: Simple
**Disadvantage**: Trade-off between staleness and DB load

#### Event-Based Invalidation

When data changes, invalidate cache:

```python
def update_user(user_id, data):
    # Update database
    db.update(user_id, data)
    
    # Invalidate cache
    cache.delete(f"user:{user_id}")
    
    # Next read will reload from DB (miss)
    # Then store in cache again
```

**Advantage**: Cache stays fresh
**Disadvantage**: Must remember to invalidate on every update

#### Pattern: Database Events

Database publishes change events:

```
Application updates user:
1. Update database
2. Database triggers "user_updated" event
3. Event goes to message queue
4. Cache invalidation service reads queue
5. Invalidates cache: user:123

Or use CDC (Change Data Capture):
- Capture all DB changes
- Publish to event stream (Kafka)
- Consumers invalidate cache
```

### Cache Stampede

When cache expires, many requests hit DB simultaneously:

```
user = cache.get("user:123")  # Cache expires at T+3600
Cache miss at T+3600
10,000 concurrent requests all miss cache
All 10,000 query database (thundering herd)
Database overwhelmed

Result: 10x spike in DB load for milliseconds
```

**Solution: Probabilistic Early Expiration**

```python
def get_user(user_id):
    user, ttl_remaining = cache.get_with_ttl(f"user:{user_id}")
    
    if user is None:
        # Cache miss
        user = db.query(user_id)
        cache.set(f"user:{user_id}", user, ttl=3600)
        return user
    
    # Probability of refresh: increases as TTL approaches 0
    if random.random() < (1 - ttl_remaining / 3600):
        # Probabilistically refresh from DB
        new_user = db.query(user_id)
        cache.set(f"user:{user_id}", new_user, ttl=3600)
    
    return user  # Return cached value immediately
```

Now cache refreshes gradually, no thundering herd.

## 3.5 Data Partitioning (Sharding at Data Layer)

Unlike sharding at application layer, database handles partitioning internally.

### Range-Based Partitioning

```
Table: user_orders
Partition by order_date:

Partition 1: dates 2024-01-01 to 2024-01-31 (January)
Partition 2: dates 2024-02-01 to 2024-02-29 (February)
...
Partition 12: dates 2024-12-01 to 2024-12-31 (December)

Query optimization:
"Get orders in March 2024" → Only scan Partition 3
"Get all orders in 2024" → Scan all partitions
```

**Good for**: Time-series data (logs, events, metrics)
**Bad for**: Uneven distribution (if query by region, some regions have more data)

### List-Based Partitioning

```
Table: users_by_region

Partition 1: region IN ('US', 'CA', 'MX')
Partition 2: region IN ('UK', 'DE', 'FR')
Partition 3: region IN ('IN', 'SG', 'JP')
```

**Good for**: Explicit groupings
**Bad for**: Must manually manage partitions

### Hash-Based Partitioning

```
Partition Key: user_id
Partition Count: 16

Partition N = hash(user_id) % 16

user_id 123 → hash → 0x7A → 0x7A % 16 = 10 → Partition 10
user_id 456 → hash → 0x1C → 0x1C % 16 = 3 → Partition 3

Result: Even distribution
```

## 3.6 Production Recommendations

### Replication Setup

**Always replicate**. Single database = unacceptable risk.

```
Minimum:
- 1 primary
- 1 synchronous replica (prevents data loss)
- 1 async replica (geographic distribution)
```

### Cache Naming Convention

```
Consistent naming prevents bugs:

user:{user_id}
user:{user_id}:profile
user:{user_id}:settings

When you update user, know exactly what to invalidate:
cache.delete(f"user:{user_id}:*")
```

### Monitor Cache Health

```
Metrics to track:
- Hit rate (should be >90% for critical caches)
- Eviction rate (if high, cache is too small)
- Average TTL
- Stale reads (if possible to detect)

Alert if hit rate drops below threshold.
```

### Test Failover

Regularly test:
1. Kill primary database → replica takes over
2. Kill replica → primary continues
3. Network partition → system handles split

Don't discover this during incident.

---

## Exam & Practice

### Multiple Choice Questions

**Q1**: You use leader-follower replication with asynchronous replication. What happens if the leader crashes 1 second after accepting a write but before replicating?

A) Data is safe on replica
B) Data is lost
C) Write is partially applied
D) System waits for leader to recover

**Q2**: Your cache has 90% hit rate but users complain of stale data (updates take 10 minutes to appear). What TTL should you set?

A) 1 minute (shorter TTL)
B) 10 minutes (match complaint)
C) 5 minutes (compromise)
D) Need more information

**Q3**: You experience cache stampede (all requests miss simultaneously). Why does this happen?

A) Cache is too small
B) Cache TTL expired for popular key
C) Network failure
D) Database is slow

**Q4**: You partition user data by region (US, EU, Asia). US has 50% of data, others 25% each. What problem occurs?

A) Uneven shard sizes (hotspot)
B) Cache doesn't work
C) Replication is slow
D) Partitioning doesn't help

**Q5**: You implement write-through cache (write to cache and DB). A write to cache succeeds but DB write fails. What happens?

A) Cache and DB consistent
B) Cache has newer data than DB
C) DB has newer data than cache
D) Data lost

### Hands-on Tasks

**Task 1: Replica Failover**

Design a leader-follower replication failover system:
- 1 primary database
- 2 replica databases
- 1 application connecting to primary for writes, replicas for reads

What happens when:
1. Primary crashes (fully)?
2. Primary becomes slow (responds in 10s)?
3. Replica crashes?
4. Network partition between primary and replicas?

Design monitoring and automatic failover where appropriate.

**Task 2: Cache Strategy**

You're building an e-commerce platform:
- User profiles (read-heavy, change infrequently)
- Inventory counts (read-heavy, change frequently)
- Cart contents (read-write, change constantly)

For each, choose: cache-aside, write-through, or write-behind. Justify.
Design TTL strategy. Design invalidation strategy.

### Incident Scenario

**Scenario: Cascade Failure from Stale Cache**

Timeline:
- T+0: Inventory management system updates product stock: 5 → 0 (out of stock)
- T+0: Update goes to database but cache invalidation fails (queue down)
- T+5s: Customer queries cache: "product in stock?" → still shows 5 (stale)
- T+5s: Customer creates order for 3 units
- T+6s: Order service tries to reserve inventory from database
- T+6s: Fails (stock is 0, can only reserve 0)
- T+8s: Order is in inconsistent state (created but can't reserve stock)
- T+10s: Notification service tries to send confirmation (which inventory?)
- T+20s: Customer sees order confirmed but also cancellation notice
- T+1hr: Reconciliation job finds 200 similar orders with inventory mismatches

**Questions:**
1. How do you detect this during incident?
2. What monitoring would have caught it?
3. What's the root cause?
4. How do you fix it (emergency recovery)?
5. How do you prevent recurrence?

---

**Next**: [Module 4: Messaging & Event-Driven Architecture](04-messaging-event-driven.md)
