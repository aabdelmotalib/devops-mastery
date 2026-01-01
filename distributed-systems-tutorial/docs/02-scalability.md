# Module 2: System Scalability

## Objectives

After completing this module, you will:
- Understand horizontal vs. vertical scaling and their trade-offs
- Design sharding and partitioning strategies
- Implement load balancing patterns
- Design for stateless service scaling
- Understand auto-scaling and capacity planning
- Know scaling limits and when sharding becomes necessary

## 2.1 Vertical vs. Horizontal Scaling

Two fundamental approaches to handling more load:

### Vertical Scaling (Bigger Server)

Use a more powerful server instead of adding more servers.

```
Current: 4 CPU, 8GB RAM → 1,000 req/sec
Upgrade: 8 CPU, 32GB RAM → ~1,800 req/sec
Problem: Still limited by single machine capacity
```

#### Vertical Scaling Advantages

1. **Simplicity**: No architectural changes needed
2. **No coordination**: Single server, no distributed logic
3. **Better cache locality**: More data in server memory
4. **Lower operational overhead**: Fewer machines to manage
5. **Simpler debugging**: Single point of failure (ironically simple to debug)

#### Vertical Scaling Disadvantages

1. **Ceiling limit**: Can't buy server bigger than what exists (~128 CPU cores, 4TB RAM)
2. **Cost exponential**: Doubling capacity costs 5-10x more (premium hardware tax)
3. **No redundancy**: Server fails = entire service down
4. **Maintenance window**: Upgrades require downtime
5. **Single point of failure**: All load on one machine

#### Vertical Scaling Real Numbers

```
AWS Instance Sizes (per hour):
t3.small (1 CPU, 2GB RAM): $0.02/hr → 100 req/sec
r6i.2xlarge (8 CPU, 64GB RAM): $0.50/hr → 800 req/sec
r6i.12xlarge (48 CPU, 384GB RAM): $3.00/hr → 4,800 req/sec

Observation: Price grows faster than capacity
- 48x more CPUs costs 150x more
- Efficiency decreases at high end
```

### Horizontal Scaling (More Servers)

Add more commodity servers and distribute load.

```
Current: 1 server @ 1,000 req/sec
Add 9 more: 10 servers @ 10,000 req/sec (linear)
Problem: Database becomes bottleneck
```

#### Horizontal Scaling Advantages

1. **Linear cost**: 10 servers = 10x cost
2. **High availability**: Server fails, others cover
3. **No ceiling**: Theoretically unlimited scaling
4. **Gradual upgrade**: Add servers as needed (no downtime)
5. **Flexibility**: Use commodity hardware (cheap)

#### Horizontal Scaling Disadvantages

1. **Complexity**: Coordination, distributed state
2. **Database bottleneck**: More servers → more DB load
3. **Network overhead**: Inter-server communication
4. **Debugging difficulty**: Requests spread across servers
5. **Consistency challenges**: Multiple servers with same data

### Hybrid Approach (Production)

Use both strategically:

```
Stage 1: Single server (vertical)
- 1x r5.2xlarge (8 CPU, 64GB)

Stage 2: Separate database (vertical)
- 1x r5.2xlarge (app) + 1x r5.4xlarge (db)

Stage 3: Multiple app servers + read replicas (horizontal + vertical)
- 3x r5.xlarge (app, horizontal)
- 1x r5.4xlarge (db primary, vertical)
- 2x r5.2xlarge (db replicas, vertical)

Stage 4: Sharded database (horizontal on data layer)
- 10x r5.xlarge (app)
- 4x r5.2xlarge (database shards)

Conclusion: Use vertical for components that can't be sharded (databases),
use horizontal for stateless components (app servers).
```

## 2.2 Load Balancing Patterns

Load balancers distribute incoming traffic across multiple servers.

### Load Balancer Placement

```
Internet
↓
DNS → resolver returns multiple IPs OR single LB IP
↓
Load Balancer (Layer 4 or Layer 7)
├→ Server 1
├→ Server 2
├→ Server 3
└→ Server 4
```

### Load Balancing Algorithms

#### Round Robin

Send requests to servers in sequence.

```
Request 1 → Server 1
Request 2 → Server 2
Request 3 → Server 3
Request 4 → Server 4
Request 5 → Server 1
...
```

**Good for**: Identical servers, identical request sizes
**Problem**: If one server is slow, all requests still get distributed equally

#### Least Connections

Send request to server handling fewest active connections.

```
Server 1: 5 active connections
Server 2: 2 active connections ← Next request goes here
Server 3: 8 active connections
```

**Good for**: Long-lived connections, uneven request durations
**Problem**: Doesn't account for request complexity

#### Weighted Round Robin

Give more traffic to better servers.

```
Server 1 (powerful): weight 4
Server 2 (weak): weight 1

Distribution: 4 to Server 1, then 1 to Server 2
SSSS-2-SSSS-2-SSSS-2...
```

**Good for**: Mixed server sizes
**Problem**: Requires manual weight configuration

#### IP Hash / Sticky Sessions

Same client → same server (based on source IP).

```
Hash(client_ip) % num_servers = server_id

Benefit: Session affinity (no sharing session between servers)
Problem: Server dies → hashed traffic goes to wrong server
```

### Health Checking

Load balancer must know which servers are healthy:

```
Every 5 seconds:
LB → Server: GET /health
     Server: HTTP 200 OK

If Server doesn't respond:
- Mark unhealthy
- Stop sending new connections
- Route traffic elsewhere

Server recovers:
- Responds to health check
- Mark healthy after N consecutive successes
- Resume traffic
```

### Load Balancer Failures

Problem: Load balancer itself can fail.

**Solution 1: Multiple Load Balancers**
```
DNS → Multiple IPs
├→ LB 1 (active)
├→ LB 2 (active)

Both receive traffic via DNS round-robin.
If LB 1 dies, DNS still resolves to LB 2.
But takes minutes for DNS TTL to expire.
```

**Solution 2: Dedicated High-Availability LB**
```
Virtual IP (VIP)
↓
Active LB (main)
Passive LB (backup)

Active monitors heartbeat to Passive.
If Active dies, Passive takes VIP immediately (seconds).
```

## 2.3 Sharding Strategy

When vertical and horizontal scaling of single database hit limits, shard the data.

### Sharding Concept

Split data across multiple database instances by key.

```
All Users Database
├→ User IDs 1-1M → Database Shard 1
├→ User IDs 1M-2M → Database Shard 2
├→ User IDs 2M-3M → Database Shard 3
└→ User IDs 3M-4M → Database Shard 4

Queries now:
- "Get user 123" → Shard 1 (hash(123) % 4 = 0)
- "Get user 1M+1" → Shard 2 (hash(1M+1) % 4 = 1)

Each shard handles 1/4 the data and queries.
```

### Shard Key Selection

Shard key determines which shard a record goes to.

#### Good Shard Keys

**User ID (high cardinality, uniform distribution)**
```
hash(user_id) % num_shards
- High cardinality: millions of distinct values
- Uniform: each shard gets equal data
- Result: Even distribution
```

**Tenant ID (for multi-tenant systems)**
```
hash(tenant_id) % num_shards
- All one tenant's data in same shard
- Easier to manage, backup, migrate one tenant
```

#### Bad Shard Keys

**Geographic region (low cardinality)**
```
US → Shard 1
Europe → Shard 2
Asia → Shard 3

Problem: US gets 40% traffic, others 10-20%
Result: Shard 1 overloaded, others idle (hotspot)
```

**Timestamp (monotonically increasing)**
```
hash(created_at) → Always same recent shard
All new records go to Shard N.
Result: Newest data on one shard (hotspot)
```

### Sharding Tradeoffs

#### Advantages

1. **Horizontal scaling**: Add more shards as data grows
2. **Load distribution**: Each shard handles portion of load
3. **Smaller datasets**: Each shard scans less data
4. **Independent operation**: Backup/maintain shards separately

#### Disadvantages

1. **Complex queries**: Cross-shard queries expensive
2. **Transaction challenges**: Distributed transactions hard
3. **Resharding**: Moving data between shards during growth
4. **Hotspots**: Bad shard key causes uneven load
5. **Operational complexity**: More databases to manage

### Cross-Shard Operations

Most queries are single-shard (fast). But some need multiple shards.

#### Inefficient: Scatter-Gather

```
Query: "Get all users with status='active'"
(no shard key specified)

Solution: Query all shards
├→ Shard 1: users with status active
├→ Shard 2: users with status active
├→ Shard 3: users with status active
└→ Shard 4: users with status active

Combine results.

Problem: Queries all databases, slow and expensive
Latency: max(shard 1 latency, shard 2, shard 3, shard 4)
If one shard slow: entire query slow
```

#### Better: Denormalization

```
Keep cached view of data by alternative key
Original: User → Shard by user_id
Alternative: UsersByStatus → Pre-computed in cache
             Status='active' → Cached list

Cost: Extra memory, must keep cache updated
Benefit: Fast queries by status without scatter-gather
```

### Resharding (Adding More Shards)

When shards get too full, add more shards.

```
Current: 4 shards (users distributed 0-4M users/shard)
Growing: System now has 8M users per shard (too much)

New plan: 8 shards

Resharding plan:
Old hash: hash(user_id) % 4
New hash: hash(user_id) % 8

Problem: All data moves!
```

**Migration process:**
1. Add new shards (empty)
2. Read from old shards, write to both old + new (dual write)
3. Copy data from old shards to new
4. Verify consistency
5. Switch reads to new shards
6. Remove dual write
7. Decommission old shards

**Pain points:**
- Takes hours/days (for big systems, weeks)
- Risky (dual write bugs can corrupt data)
- Requires maintenance window
- If resharding fails, have to roll back

## 2.4 Stateless Service Scaling

Services that don't store state can scale horizontally easily.

### Stateless vs. Stateful

#### Stateless Service

```
Service = f(input)
No memory between requests.

Request 1: GET /user/123 → returns {"id": 123, "name": "Alice"}
Request 2: GET /user/456 → returns {"id": 456, "name": "Bob"}

Server doesn't remember request 1.
Each request is independent.
```

**Advantages**:
- Linearly scalable (add 10 servers = 10x capacity)
- Can kill/start servers anytime
- Easy load balancing (any server can handle any request)
- Easy to upgrade code (rolling restart without data loss)

#### Stateful Service

```
Service has in-memory state that affects requests.

Server: User Sessions Dictionary
request 1: GET /login with (user, password) → creates session in memory
request 2: GET /profile → reads from session in memory

If request 2 goes to different server:
Server 2 doesn't have session → "unauthorized"
```

**Disadvantages**:
- Must route same client to same server (sticky sessions)
- Can't kill server (loses in-memory data)
- Harder load balancing
- Bottleneck when scaling

### Making Services Stateless

Move state out of server memory:

**Before (Stateful)**:
```python
app = Flask(__name__)
sessions = {}  # In-memory session store

@app.route('/login', methods=['POST'])
def login():
    user = request.json['user']
    password = request.json['password']
    if verify(user, password):
        session_id = generate_id()
        sessions[session_id] = {'user': user}  # Store in memory
        return {'session_id': session_id}

@app.route('/profile')
def get_profile():
    session_id = request.headers['X-Session-Id']
    user = sessions[session_id]['user']  # Need to be on same server
    return {'user': user}
```

**After (Stateless)**:
```python
import redis

cache = redis.Redis()
app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    user = request.json['user']
    password = request.json['password']
    if verify(user, password):
        session_id = generate_id()
        cache.setex(session_id, 3600, json.dumps({'user': user}))
        return {'session_id': session_id}

@app.route('/profile')
def get_profile():
    session_id = request.headers['X-Session-Id']
    session = cache.get(session_id)  # Any server can read
    user = json.loads(session)['user']
    return {'user': user}
```

Now both servers can handle any request (any client can go to any server).

## 2.5 Auto-Scaling

Automatically add/remove servers based on load.

### Auto-Scaling Metrics

Decide when to scale up/down:

```
CPU Utilization: Scale up if avg CPU > 70%
Memory Usage: Scale up if memory > 80%
Request Latency: Scale up if p95 latency > 500ms
Queue Depth: Scale up if message queue > 1000 messages
Custom: Scale based on business metric (active user count)
```

### Auto-Scaling Policies

#### Target-Based Scaling

```
Target: 70% CPU utilization

Current: 10 servers at 80% CPU
Desired: scale to 10 * (80/70) = ~11-12 servers
Action: Add 2 servers

New: 12 servers at ~67% CPU (meets target)
```

#### Step Scaling

```
If CPU > 80%: Add 20% servers (aggressive)
If CPU > 60% but < 80%: Add 10% servers
If CPU < 40%: Remove 10% servers (conservative)
If CPU < 20%: Remove 20% servers
```

#### Scheduled Scaling

```
Every weekday 9-5 PM: 100 servers
Every weekday 6 PM-8 AM: 20 servers
Weekends: 30 servers (predictable pattern)
```

### Auto-Scaling Dangers

#### Thrashing (Flapping)

```
Metric is at threshold, constantly oscillating:
- CPU at 70% threshold
- Adds server (one more server)
- CPU drops to 60% (remove server flag triggered)
- Removes server
- CPU rises to 75%
- Adds server again

System constantly churning. Inefficient.

Fix: Use hysteresis (different thresholds for up and down)
- Scale up if CPU > 70%
- Scale down if CPU < 50% (not 70%)
```

#### Slow Scaling During Traffic Spike

```
Sudden spike: 1M to 10M requests/sec

Auto-scaling takes 3 minutes to add servers:
- T+0: Spike detected
- T+1min: New servers starting
- T+2min: New servers initializing
- T+3min: New servers in service

But you've already lost users at T+30sec.
```

**Fix**: Predictive scaling (scale before spike if you see trend), capacity buffers.

## 2.6 Production Recommendations

### Capacity Planning

Always maintain headroom:

```
Peak load: 100K req/sec
Design capacity: 150K req/sec (50% headroom)
Why? For auto-scaling latency, unexpected spikes, failing servers
```

### Gradual Rollout of Sharding

```
Don't shard from day 1 (complexity without necessity)

Timeline:
Month 1-3: Single database, scale vertically
Month 3-6: Add read replicas
Month 6-12: Monitor growth, plan sharding
Month 12+: Implement sharding if data grows 2-3x
```

### Health Check Best Practices

```
GET /health

Should check:
- Application is responding
- Can reach database
- Can reach critical dependencies (cache, queue)
- No degraded state (not restarting, not disk full)

Response:
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "cache": "ok",
    "queue": "ok"
  }
}
```

### Monitor Scaling Events

```
Always log when servers are added/removed:
"Added 2 servers due to CPU > 70%"
"Removed 1 server, CPU dropped to 45%"

Analyze later: Did scaling help? Was there a spike?
Tune thresholds based on real events.
```

---

## Exam & Practice

### Multiple Choice Questions

**Q1**: You have a database shard strategy using user_id % 4. Suddenly, one user becomes viral, getting 40% of all requests. What happens?

A) The system scales automatically
B) One shard becomes hotspot, bottleneck
C) Load balancer detects hotspot, redistributes
D) Sharding prevents hotspots

**Q2**: Your stateless services are at 90% CPU, you scale up by 50% servers. Database is at 50% CPU. What's the bottleneck?

A) Compute (stateless services)
B) Database
C) Network between services and database
D) Not enough information

**Q3**: Auto-scaling policy: "Add servers if CPU > 70%, remove if CPU < 40%". You experience thrashing (constant scaling). Which problem is this?

A) Threshold too high
B) Hysteresis not tuned
C) Auto-scaling is broken
D) Servers starting too slowly

**Q4**: You're resharding from 4 to 8 shards. During migration, you dual-write (new and old). What risk do you take?

A) Data loss
B) Inconsistency between old/new shards
C) Downtime
D) Performance degradation

**Q5**: A user session is stored in a single server's memory (stateful). How do you make it scalable?

A) Add more servers
B) Use sticky session routing
C) Move sessions to Redis (stateless)
D) Use IP hashing

### Hands-on Tasks

**Task 1: Shard Key Design**

Design a sharding strategy for a messaging system (like Slack):
- 100 million users
- 10 million workspaces (groups of users)
- Users send 5 billion messages per day
- Queries are: "get messages for workspace", "get messages for user"

Choose shard key. Justify trade-offs. How would you handle the "get messages for user" query?

**Task 2: Auto-Scaling Policy**

You run a streaming platform. Peak load:
- Business hours (9-5 PM): 200K req/sec
- Evenings: 100K req/sec
- Nights: 10K req/sec

Each server handles 5K req/sec.
Startup time: 3 minutes.
Cost per server: $10/hour.

Design auto-scaling policy (thresholds, targets, scheduled scaling).

### Incident Scenario

**Scenario: Cascading Failures from Hotspot**

You implement sharding by user_id % 16. Everything works fine for 3 months.

Then:
- T+0: Celebrity user joins platform, gains 10M followers
- T+5min: Shard 3 (where celebrity user's data is) hits 95% CPU
- T+6min: Shard 3 starts rejecting queries (overload)
- T+7min: Other shards sending queries to Shard 3 (for relationship data) also fail
- T+8min: Entire system degraded (even users on other shards can't operate)

**Questions:**
1. Why didn't you detect this earlier?
2. What monitoring would have helped?
3. How do you fix this immediately (emergency)?
4. How do you fix this long-term?
5. Design a system to prevent hotspot shards.

---

**Next**: [Module 3: Data Storage & Replication](03-data-storage-replication.md)
