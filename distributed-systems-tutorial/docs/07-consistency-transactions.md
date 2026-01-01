# Module 7: Consistency, Transactions & Coordination

## Objectives

After completing this module, you will:
- Understand ACID vs BASE trade-offs
- Design distributed transactions and their limitations
- Understand consensus algorithms (Raft, Paxos)
- Use coordination services (etcd, Zookeeper)
- Implement saga pattern for distributed transactions
- Handle distributed locks and coordination

## 7.1 ACID vs BASE

### ACID (Traditional Databases)

ACID: Atomicity, Consistency, Isolation, Durability

```
Atomicity: Transaction all-or-nothing
├─ BEGIN TRANSACTION
├─ Deduct $100 from account A
├─ Add $100 to account B
├─ COMMIT

If any operation fails: rollback entire transaction
Result: Both operations succeed or both fail (no partial state)

Consistency: Data valid after transaction
├─ Before: A=$500, B=$400, total=$900
├─ After: A=$400, B=$500, total=$900
├─ Invariant (total) preserved

Isolation: Concurrent transactions don't interfere
├─ Transaction 1: Transfer A→B
├─ Transaction 2: Transfer B→C
├─ Locks ensure proper ordering

Durability: Committed data survives failures
├─ After COMMIT returns
├─ Data persisted to disk
├─ Even if server crashes
```

**Cost**:
- Write operations slower (must await commit confirmation)
- Locking reduces concurrency
- Harder to scale across servers (distributed transactions expensive)

**Good for**: Financial systems, critical data

### BASE (Distributed Systems)

BASE: Basically Available, Soft state, Eventually consistent

```
Basically Available:
├─ System responds even if some parts fail
├─ May serve stale data or incomplete results
├─ Priority: availability over consistency

Soft State:
├─ Data might be inconsistent temporarily
├─ Inconsistency auto-resolves over time
├─ No need for synchronous consistency

Eventually Consistent:
├─ All replicas converge to same state
├─ Takes seconds to minutes
├─ Not immediately consistent
```

**Cost**:
- Eventual inconsistency (stale reads)
- Complex conflict resolution
- Application must handle conflicts

**Good for**: Social media, analytics, recommendations

### Decision Tree

```
Choose ACID if:
├─ Data integrity critical (financial, medical)
├─ Consistency worth slower performance
└─ Single region or can afford distributed transactions

Choose BASE if:
├─ Availability more important than consistency
├─ Can tolerate eventual inconsistency (seconds)
└─ Geographic distribution important
```

## 7.2 Distributed Transactions

Coordinating updates across multiple databases.

### Two-Phase Commit (2PC)

Coordinator ensures atomicity across multiple servers:

```
Phase 1 (Prepare):
├─ Coordinator asks each participant: "Can you commit?"
├─ Each participant:
│  ├─ Locks resources
│  ├─ Performs operation
│  ├─ Tests constraint
│  └─ Responds: YES or NO (can't undo yet)

Phase 2 (Commit/Abort):
├─ If all say YES:
│  └─ Coordinator: COMMIT (all participants commit)
├─ If any say NO:
│  └─ Coordinator: ABORT (all rollback, release locks)

Result: All-or-nothing atomicity across databases
```

### 2PC Problems

```
Distributed failure scenarios:

Scenario 1: Participant fails after YES vote (before COMMIT)
├─ Participant has locked resources
├─ Can't proceed or rollback
├─ Resources locked indefinitely

Scenario 2: Network partition
├─ Coordinator can't reach participant
├─ Participant waiting for decision
├─ Deadlock (both waiting)

Scenario 3: Coordinator fails
├─ Participants locked
├─ No one to tell them to commit or rollback
├─ Manual intervention required

Result: 2PC is blocking and not partition-tolerant.
```

### Why 2PC Fails in Modern Distributed Systems

```
2PC requires:
- All participants available (no failures during transaction)
- Synchronous communication (can wait forever)
- Coordination server available (single point of failure)

Network reality:
- Failures are frequent
- Latency is unpredictable
- Partitions do happen

Result: 2PC is impractical for cloud systems.
```

### Saga Pattern (Distributed Transaction Alternative)

Use compensating transactions instead of 2PC:

```
Transfer $100: A → B

Saga (orchestrated):
1. Deduct $100 from A → SUCCESS
2. Add $100 to B → FAILS (invalid account)

Compensation:
3. Add $100 back to A (undo deduct)

Result: A and B end up consistent (A has original amount)
No need for 2PC, each operation independent.
```

### Saga Implementation

```python
class TransferSaga:
    def __init__(self, account_a, account_b, amount):
        self.account_a = account_a
        self.account_b = account_b
        self.amount = amount
        self.state = "PENDING"
    
    def execute(self):
        try:
            # Step 1: Deduct from A
            self.deduct_from_a()
            
            # Step 2: Add to B
            self.add_to_b()
            
            self.state = "COMMITTED"
        
        except Exception as e:
            # Compensation: undo changes
            self.compensate()
            self.state = "ABORTED"
            raise
    
    def deduct_from_a(self):
        db.execute(
            f"UPDATE accounts SET balance = balance - {self.amount} WHERE id = {self.account_a}"
        )
        db.execute(
            f"INSERT INTO saga_log VALUES ('{self.state}', 'deduct_a', {self.account_a}, {self.amount})"
        )
    
    def add_to_b(self):
        db.execute(
            f"UPDATE accounts SET balance = balance + {self.amount} WHERE id = {self.account_b}"
        )
        db.execute(
            f"INSERT INTO saga_log VALUES ('{self.state}', 'add_b', {self.account_b}, {self.amount})"
        )
    
    def compensate(self):
        # Undo: add back to A
        db.execute(
            f"UPDATE accounts SET balance = balance + {self.amount} WHERE id = {self.account_a}"
        )
        db.execute(
            f"INSERT INTO saga_log VALUES ('{self.state}', 'compensate_a', {self.account_a}, {self.amount})"
        )
```

## 7.3 Consensus Algorithms

How servers agree on state in presence of failures.

### Raft Overview (Simplified)

Three states: Follower, Candidate, Leader

```
Initialization:
All servers start as Followers.

Election:
- Followers don't hear from leader
- Follower times out (150-300ms), becomes Candidate
- Candidate requests votes from other servers
- If gets majority (N/2 + 1), becomes Leader
- Leader sends heartbeat every 50ms

Leader failure:
- Followers stop receiving heartbeats
- Follower times out, becomes Candidate
- New leader elected

Log replication:
- Client sends command to Leader
- Leader appends to log, sends to Followers
- Followers append to log
- Once majority acknowledged, Leader commits
- Leaders later tell Followers to commit
```

### Consensus Cost

```
Strong consistency (Raft):
- Requires majority agreement
- Write latency: at least N/2 round-trips (milliseconds)
- Leader failure: 150-300ms until new leader elected

Trade-off:
- Guaranteed consistency (all nodes same state)
- Cost: latency and complexity
```

## 7.4 Coordination Services

Use external services for coordination: etcd, Zookeeper, Consul

### Example: Distributed Configuration with etcd

```python
import etcd3

client = etcd3.client()

# Leader election
lease = client.lease(60)  # 60 second lease

try:
    client.put('/service/leader', hostname, lease=lease)
    print("I'm the leader!")
except etcd3.exceptions.DuplicateKeyError:
    print("Someone else is leader")

# Watch for leader changes
watch_id = client.watch('/service/leader')
for event in client.get_watch_response(watch_id):
    if event.key == '/service/leader':
        print(f"Leader changed to {event.value}")
```

### Service Discovery with etcd

```python
# Register service
client.put('/services/payment-service/server1', 'http://server1:8080', lease=60)
client.put('/services/payment-service/server2', 'http://server2:8080', lease=60)

# Discover services
services = []
for key, value in client.get_prefix('/services/payment-service/'):
    services.append(value)

# Load balance
next_service = load_balancer.select(services)
```

## 7.5 Distributed Locks

Prevent multiple servers from executing same operation.

### Mutex Pattern with etcd

```python
def acquire_lock(lock_name, ttl=60):
    """
    Acquire distributed lock. Returns immediately if acquired.
    Blocks if lock held by someone else.
    """
    while True:
        try:
            # Try to create lock key (fails if exists)
            client.put(f'/locks/{lock_name}', hostname, lease=ttl)
            return True  # Lock acquired
        except etcd3.exceptions.DuplicateKeyError:
            # Lock held by someone else, wait and retry
            time.sleep(0.1)

def release_lock(lock_name):
    """Release distributed lock"""
    client.delete(f'/locks/{lock_name}')

# Usage
def batch_job():
    if acquire_lock('batch_processor'):
        try:
            process_batch()
        finally:
            release_lock('batch_processor')
    else:
        print("Another instance running")
```

## 7.6 Production Recommendations

### When to Use ACID

Only when:
- Data corruption is unacceptable (financial, medical)
- Single region / low-latency coordination possible
- Can afford transaction overhead

### When to Accept Eventual Consistency

For most systems:
- User data: OK to be eventual
- Inventory: 100% accurate (but eventual OK)
- Analytics: Eventual is standard
- Recommendations: Eventual is fine

### Saga vs Distributed Transaction

```
Use Saga if:
- Services are independent
- Each step can be compensated
- Latency matters (saga is faster)

Use Distributed Transaction if:
- Consistency critical
- All participants available
- Can afford latency/complexity
```

---

## Exam & Practice

### Multiple Choice Questions

**Q1**: You implement 2PC for distributed transaction. Network partition occurs mid-transaction. What happens?

A) Automatic rollback
B) Deadlock (participants waiting for decision)
C) Automatic retry
D) System detects and recovers

**Q2**: Saga pattern handles failure by compensating. What's a compensation for "transfer A→B"?

A) Retry transfer again
B) Add amount back to A (undo)
C) Fail the entire saga
D) Manually intervene

**Q3**: Raft consensus requires majority agreement. 5 servers, 2 failed. Can system still operate?

A) No (2 out of 5 not quorum)
B) Yes (3 out of 5 is quorum)
C) Depends on which 2 failed
D) Yes if primary is alive

**Q4**: etcd lease expires (TTL=60s, no renewal). What happens to lock?

A) Lock held permanently
B) Lock automatically released
C) Requires manual cleanup
D) Next server gets lock

**Q5**: Service writes to 3 replicas (asynchronous). One replica crashes. Consistency status?

A) Strongly consistent (others have data)
B) Eventually consistent (replica will catch up)
C) Broken (data loss)
D) Depends on which replica

### Hands-on Tasks

**Task 1: Saga Design**

Design saga for booking system:
1. Reserve seat
2. Charge payment
3. Send confirmation email

Handle failures:
- Charge fails → release seat
- Email fails → ??? (compensation?)

Specify:
- Order of operations
- Compensation steps
- Idempotency strategy

**Task 2: Distributed Lock**

Design distributed lock for batch job:
- Only one instance should run at a time
- If instance crashes, lock should auto-release
- Multiple regions calling same job

Specify:
- TTL strategy
- Failure handling
- Multi-region strategy

### Incident Scenario

**Scenario: Saga Partial Failure Recovery Failure**

Timeline:
- T+0: Booking saga starts (reserve → charge → email)
- T+0: Step 1 succeeds (seat reserved)
- T+1: Step 2 fails (payment declined)
- T+2: Compensation should refund seat
- T+3: Compensation runs (delete reservation)
- T+4: But delete query fails (database connection timeout)
- T+5: Saga ends (marked FAILED)
- T+10: Problem: Seat still reserved (compensation never completed)
- T+100: Another customer tries to book same seat
- T+101: Failure: "Already reserved"

**Questions:**
1. How do you prevent partial saga compensation?
2. Should failed compensation retry automatically?
3. What monitoring would catch unreleased resources?
4. Design compensate-the-compensate strategy
5. How do you test saga failures?

---

**Next**: [Module 8: Microservices Design Patterns](08-microservices-patterns.md)
