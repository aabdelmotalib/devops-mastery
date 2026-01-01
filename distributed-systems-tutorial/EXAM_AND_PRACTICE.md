# EXAM & PRACTICE: Questions, Tasks, and Scenarios

This file contains all practice materials for the Distributed Systems tutorial.

**Important**: Answers are NOT provided. Use module content to find answers. This forces deeper learning.

---

## Module 1: Distributed Systems Fundamentals

### Multiple Choice Questions

**Q1**: A system handles financial transactions where consistency is critical. Network partitions occasionally occur. According to CAP theorem, which property should be sacrificed?

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

For each component:
- Decide: CP or AP?
- Justify with 1-2 failure scenarios explaining why your choice is better

**Task 2: Latency Budget Allocation**

You have a 1-second SLA for API response time. Your system components:
- Load balancer (5ms)
- Business logic (to be determined)
- Database query (to be determined)
- Response serialization (10ms)
- Network overhead (100ms total, fixed)

Available database options:
- Fast database: 50ms latency, expensive ($10K/month)
- Standard database: 200ms latency, cheap ($2K/month)
- Slow database: 500ms latency, very cheap ($500/month)

Determine:
1. What's your latency budget for business logic and database combined?
2. Which database would you choose? Why?
3. If SLA changes to 500ms, which database becomes viable?

### Incident Scenario

**Title: Cascading Failure During Sale Event**

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

**Answer these questions:**

1. How would you have prevented this?
2. What monitoring would have caught this at T+5min?
3. Design a circuit breaker strategy for this system (thresholds, states)
4. How would you test for this failure before it happens in production?
5. What's the root cause and how do you fix it long-term?

---

## Module 2: System Scalability

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
B) Hysteresis not tuned (different thresholds for up and down)
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

Your deliverables:
1. Choose shard key (justify choice)
2. Explain data distribution
3. How would you handle "get messages for user" query? (cross-shard operation)
4. What's the hotspot risk?
5. How would you reshards if workspace grows 10x?

**Task 2: Auto-Scaling Policy**

You run a streaming platform. Known load patterns:
- Business hours (9-5 PM): 200K req/sec
- Evenings (5 PM-11 PM): 100K req/sec
- Nights (11 PM-9 AM): 10K req/sec

System specifications:
- Each server handles 5K req/sec
- Startup time: 3 minutes
- Shutdown time: 1 minute
- Cost per server: $10/hour

Design:
1. Scheduled scaling plan (different policies for different times)
2. Metric-based scaling for unexpected spikes
3. Calculate estimated cost optimization vs simple fixed capacity
4. How to handle Black Friday (10x normal traffic)?

### Incident Scenario

**Title: Cascading Failures from Hotspot Shard**

You implement sharding by user_id % 16. Everything works fine for 3 months.

Then:
- T+0: Celebrity user joins platform, gains 10M followers
- T+5min: Shard 3 (where celebrity user's data is) hits 95% CPU
- T+6min: Shard 3 starts rejecting queries (overload)
- T+7min: Other shards sending queries to Shard 3 (for relationship data) also fail
- T+8min: Entire system degraded (even users on other shards can't operate)

**Answer these questions:**

1. Why didn't you detect this hotspot earlier?
2. What monitoring would have caught shard imbalance?
3. How do you fix this immediately (emergency)?
4. How do you fix this long-term?
5. Design a system to detect and prevent hotspot shards.

---

## Modules 3-10: Practice Questions Summary

Due to length, here's the pattern (answer all questions across modules):

### Module 3 Hands-on Tasks
- Task 1: Design replica failover system
- Task 2: Cache strategy for e-commerce platform

### Module 4 Hands-on Tasks
- Task 1: Idempotent payment processing
- Task 2: Event-driven order processing

### Module 5 Hands-on Tasks
- Task 1: Circuit breaker policy design
- Task 2: Multi-region failover architecture

### Module 6 Hands-on Tasks
- Task 1: Performance analysis and optimization
- Task 2: Caching strategy design

### Module 7 Hands-on Tasks
- Task 1: Saga design for booking system
- Task 2: Distributed lock implementation

### Module 8 Hands-on Tasks
- Task 1: Microservice decomposition
- Task 2: API gateway design

### Module 9 Hands-on Tasks
- Task 1: SLO definition
- Task 2: Distributed tracing implementation

### Module 10 Hands-on Tasks
- Task 1: Deployment strategy selection
- Task 2: Multi-region failover design

---

## Practice Tips

### How to Use This Document

1. **Work on one module at a time**
   - Complete all questions for Module 1 before Module 2
   - Review module content before answering

2. **Don't peek at answers (they're not provided)**
   - Find answers by reading module content
   - Discuss with colleagues
   - Search for real-world examples

3. **Hands-on tasks should take 2-4 hours each**
   - Draw diagrams
   - Write pseudocode
   - Consider failure modes

4. **Incident scenarios should take 1-2 hours**
   - Root cause analysis
   - Monitoring design
   - Recovery procedures

5. **Retake practice questions after 2 weeks**
   - You'll retain more
   - Spot gaps in understanding

### Self-Assessment

Rate yourself on each concept:
- 1 = Never heard of it
- 2 = Heard of it, don't understand
- 3 = Understand basics
- 4 = Can explain to others
- 5 = Can design systems using this

Before each module, rate yourself 1-5 on:
- Module topic (overall)
- Key concepts (3-5 main concepts)

After module, re-rate. Goal: move 3→5, or 2→4.

---

## Interview Prep

If using this for system design interviews:

1. **Practice explaining design decisions** (not just drawing boxes)
2. **Discuss trade-offs explicitly** (throughput vs latency, consistency vs availability)
3. **Start simple, add complexity** (don't over-engineer upfront)
4. **Ask clarifying questions** (don't assume requirements)
5. **Estimate numbers** (req/sec, data size, costs)

Example:
```
Interviewer: "Design Instagram"
You: "Before I design, let me clarify:
- How many users? (assume 100M)
- How many posts per day? (assume 1B)
- What's latency SLA? (assume <500ms)
- What's availability SLA? (assume 99.9%)
- Geographic distribution needed? (assume yes)"
```

---

## Group Study Guide

Studying with others?

1. **Quiz each other** on MCQs
2. **Design systems together**
   - One person leads, others critique
   - Rotate who leads
3. **Discuss tradeoffs**
   - Why CAP triangle?
   - When to shard?
   - Which deployment strategy?
4. **Mock interviews**
   - 30 min design task
   - 10 min questions
   - Switch roles

---

**Last Updated**: January 2026
**Version**: 1.0

Continue to [FINAL_PROJECT.md](FINAL_PROJECT.md) for capstone project.
