# Module 10: Deployment & Scaling Strategies

## Objectives

After completing this module, you will:
- Understand rolling, blue/green, and canary deployment patterns
- Design multi-region deployment strategies
- Implement chaos engineering for testing
- Manage resource quotas and auto-scaling
- Optimize costs at scale
- Design disaster recovery

## 10.1 Deployment Strategies

### Rolling Deployment

Gradually replace old instances with new ones.

```
Initial state:
Server 1 (v1.0)
Server 2 (v1.0)
Server 3 (v1.0)
Server 4 (v1.0)
All serving traffic

Step 1:
Server 1 (v1.1) ← updated
Server 2 (v1.0)
Server 3 (v1.0)
Server 4 (v1.0)
75% on old, 25% on new

Step 2:
Server 1 (v1.1)
Server 2 (v1.1) ← updated
Server 3 (v1.0)
Server 4 (v1.0)
50% on old, 50% on new

Step 3:
Server 1 (v1.1)
Server 2 (v1.1)
Server 3 (v1.1) ← updated
Server 4 (v1.0)
25% on old, 75% on new

Step 4:
Server 1 (v1.1)
Server 2 (v1.1)
Server 3 (v1.1)
Server 4 (v1.1) ← updated
0% on old, 100% on new
```

**Advantages**:
- No capacity loss (old and new both serving)
- Easy rollback (keep old version running)
- Gradual traffic shift (testing in production)

**Disadvantages**:
- Database migrations complex (both versions must handle schema)
- Long deployment time (if 100 servers, takes hours)
- Stateful services harder to migrate

### Blue/Green Deployment

Two identical environments, switch traffic between them.

```
Blue Environment (v1.0):
├─ Load Balancer (receives 100% traffic)
├─ 10 App Servers
├─ Database + replicas
└─ Cache cluster

Green Environment (v1.1):
├─ Load Balancer (receives 0% traffic)
├─ 10 App Servers (new version)
├─ Database + replicas (copy from blue)
└─ Cache cluster (synced)

Deployment:
1. Test green environment thoroughly
2. Copy data from blue to green
3. Switch load balancer: blue → green (instant)
4. If issue: switch back (instant rollback)
```

**Advantages**:
- Instant deployment (no gradual process)
- Instant rollback (keep blue running)
- Can test thoroughly before switch
- Zero downtime

**Disadvantages**:
- Double infrastructure cost (2 environments)
- Database sync complexity
- Must handle diverging state (users still using blue during sync)

### Canary Deployment

Deploy to small subset first, gradually increase traffic.

```
Version 1.0 (99% traffic):
├─ Server 1-98 (serve v1.0)
├─ 99K requests/sec

Version 1.1 (1% traffic - canary):
├─ Server 99-100 (serve v1.1)
├─ 1K requests/sec (1% of traffic)

Monitor metrics for v1.1:
├─ Error rate (compare to v1.0)
├─ Latency (compare to v1.0)
├─ Business metrics (conversion rate, etc.)

If v1.1 looks good:
├─ 2% traffic (2K req/sec)
├─ 5% traffic (5K req/sec)
├─ 50% traffic (50K req/sec)
├─ 100% traffic (all traffic)

If v1.1 has issues:
├─ Rollback to v1.0 (only 1% affected)
```

**Advantages**:
- Risk mitigation (small blast radius)
- Real production metrics (better than testing)
- Easy rollback (affected few users)

**Disadvantages**:
- Requires sophisticated monitoring (detecting issues in 1% of traffic)
- Longer deployment time (gradual ramp)
- Complex infrastructure (multiple versions simultaneously)

### Choosing Deployment Strategy

```
Rolling Deployment:
- Use when: Stateless services, compatible schema changes
- Not when: Stateful services, database migrations
- Rollback time: Instant

Blue/Green:
- Use when: Zero downtime critical, frequent deployments
- Not when: Database size huge (expensive to duplicate)
- Cost: 2x infrastructure

Canary:
- Use when: High-traffic production, risk-averse
- Not when: Team doesn't have monitoring expertise
- Best for: Critical services, novel versions
```

## 10.2 Multi-Region Deployment

Serving users globally while handling failures.

### Multi-Region Architecture

```
US-East (Primary):
├─ 100 app servers
├─ Database primary
└─ Load capacity: 100K req/sec

US-West (Secondary):
├─ 20 app servers
├─ Database replica
└─ Load capacity: 20K req/sec

EU-West (Tertiary):
├─ 10 app servers
├─ Database replica
└─ Load capacity: 10K req/sec

DNS/Global Load Balancer:
├─ 60% traffic → US-East (closest for most)
├─ 25% traffic → US-West
├─ 15% traffic → EU-West

Data Replication:
US-East (primary)
  ├─ Synchronous to US-West (low latency, low lag)
  └─ Asynchronous to EU-West (high latency, acceptable lag)
```

### Failover Scenarios

```
Scenario 1: US-East datacenter lost
├─ DNS detects (health checks fail)
├─ Shifts 60% traffic to other regions
├─ US-West: 20K → needs to handle ~60K (overload)
├─ Auto-scaling: add 40 more servers (5-10 minutes)
├─ EU-West: 10K → handle ~30K (overload)
├─ Auto-scaling: add 20 more servers
└─ Result: Degraded service for 5-10 minutes, then recovery

Scenario 2: US-East primary database lost
├─ Promote US-West replica to primary
├─ Stop accepting writes to EU replica (prevent divergence)
├─ All writes go to new primary (US-West)
├─ Eventually replicate to EU
└─ Result: Service continues, possible loss of last few seconds

Scenario 3: All US regions lost
├─ EU-West becomes primary
├─ Capacity: 10K req/sec (need 100K req/sec) → heavily degraded
├─ Manual failover of data
├─ Spin up capacity in new US region
├─ Hours-long recovery process
```

## 10.3 Chaos Engineering

Testing system reliability by introducing controlled failures.

### Failure Injection

```
Chaos Engineering Test: What if database latency spikes?

Normal state:
- Database latency: 10ms
- Request latency: 100ms
- Success rate: 99.9%

Inject failure:
- Add 500ms latency to 10% of database queries
- Start test at 10 AM (production traffic)

Observe:
- Request latency: 100ms → 120ms (p95)
- Success rate: 99.9% → 99.7% (some timeouts)
- Error rate: 0.1% → 0.3%

Verdict:
- System handles gracefully (no cascading)
- Circuit breaker activates (stops hammering DB)
- Graceful degradation works
```

### Common Chaos Tests

```
Test 1: Database becomes unavailable
├─ Drop all connections to database
├─ Observe: Services failover to replica (or fail appropriately)

Test 2: Network partition
├─ Drop network between Region A and Region B
├─ Observe: Services handle split-brain correctly

Test 3: CPU exhaustion
├─ Consume 90% of CPU on one server
├─ Observe: Load balancer sheds load, system continues

Test 4: Memory leak
├─ Gradually leak memory, monitor behavior
├─ Observe: Service restarts before OOM

Test 5: Cascading failure
├─ Kill primary service
├─ Observe: Failover works, load distributes
```

### Tools

```
Kubernetes-native:
- Chaos Toolkit (open source)
- Gremlin (commercial)
- LitmusChaos (Kubernetes-specific)

Network:
- Toxiproxy (proxy that injects failures)

Application:
- Hystrix simulator (testing circuit breakers)
```

## 10.4 Resource Management and Auto-Scaling

### Resource Quotas

Kubernetes example:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production

---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: prod-quota
  namespace: production
spec:
  hard:
    requests.cpu: "1000"      # Max 1000 CPU cores
    requests.memory: "2000Gi"  # Max 2000 GB memory
    pods: "500"               # Max 500 pods
    limits.cpu: "2000"        # Max 2000 CPU cores
    limits.memory: "4000Gi"   # Max 4000 GB memory
```

Result: No single deployment can consume all resources.

### Auto-Scaling Policies

```
Metric-Based:
- Scale up if CPU > 70% for 5 minutes
- Scale down if CPU < 30% for 10 minutes

Scheduled:
- 9 AM - 5 PM weekdays: 100 pods
- Nights and weekends: 20 pods
- Black Friday (Nov 25): 500 pods

Custom Metrics:
- Scale based on business metric (active users, queue depth)
- Scale up if queue > 1000 messages
```

## 10.5 Cost Optimization at Scale

### Cost Analysis

```
Monthly cost breakdown (100 app servers):

Compute (instances): $50,000
  - EC2 instances: 100 * $0.20/hr * 730 hrs = $14,600
  - Reserved instances (discount): -$5,000
  - Subtotal: $9,600

Data Transfer: $15,000
  - Outbound traffic: 1PB/month * $0.05/GB = $51,200
  - But: CloudFront caching reduces by 70%
  - Actual: $15,360

Database: $20,000
  - RDS instances: $15,000
  - Backups: $3,000
  - Data transfer: $2,000

Storage: $5,000
  - S3 for backups: $2,000
  - EBS volumes: $3,000

Monitoring: $3,000
  - CloudWatch: $2,000
  - Third-party tools: $1,000

Total: ~$48,000/month ($576K/year)
```

### Cost Optimization Strategies

```
1. Right-sizing instances
   ├─ Profile actual usage (not worst-case)
   ├─ Move from t3.large to t3.medium
   ├─ Savings: 20-30%

2. Reserved instances
   ├─ 1-year commitment: 30-40% discount
   ├─ 3-year commitment: 50-60% discount
   ├─ Savings: $30-50K/year

3. Spot instances
   ├─ Use excess cloud capacity (70-90% discount)
   ├─ Can be terminated anytime
   ├─ Good for: batch jobs, non-critical services
   ├─ Savings: $20K/month for right workloads

4. Caching and CDN
   ├─ Reduce database load (less compute)
   ├─ Serve from edge (less data transfer)
   ├─ Savings: $5-10K/month

5. Database optimization
   ├─ Proper indexing (fewer slow queries)
   ├─ Denormalization (less joins)
   ├─ Savings: $3-5K/month
```

## 10.6 Disaster Recovery

### RTO and RPO

```
RTO (Recovery Time Objective): How fast to recover?
├─ Critical: < 1 hour
├─ Important: < 4 hours
├─ Non-critical: < 24 hours

RPO (Recovery Point Objective): How much data loss acceptable?
├─ Critical: < 5 minutes (lose at most 5 min of data)
├─ Important: < 1 hour
├─ Non-critical: < 1 day

Examples:
- Payment system: RTO=15min, RPO=1min
- Analytics: RTO=24hr, RPO=1hr
- Recommendations: RTO=4hr, RPO=1day
```

### Disaster Recovery Plan

```
Scenario: Entire primary region (US-East) lost

Recovery steps:
1. Detect failure (2 minutes)
   └─ Health checks detect region down
   
2. Promote secondary to primary (5 minutes)
   └─ Secondary (US-West) becomes read-write
   └─ Tertiary (EU-West) stops as replica
   
3. Point DNS to secondary (10 minutes)
   └─ Users routed to secondary
   
4. Scale secondary (20 minutes)
   └─ Add capacity to handle all traffic
   
5. Spin up new primary (60 minutes)
   └─ Launch new infrastructure in US-East
   
6. Replicate data back (ongoing)
   └─ New US-East replicates from US-West
   
Total RTO: 60-90 minutes
Data loss: Last 1-5 minutes (depends on replication lag)

Test this monthly (don't wait for real disaster).
```

## 10.7 Production Recommendations

### Deployment Checklist

Before deploying:
- [ ] All tests passing locally
- [ ] Integration tests passing
- [ ] Staged deployment plan ready
- [ ] Rollback procedure documented
- [ ] Monitoring dashboards ready
- [ ] On-call engineer available
- [ ] Runbook updated

### Gradual Rollout

```
100 services, rolling deployment:
├─ Hour 1: Deploy to 10 services (least critical)
├─ Hour 2: Deploy to 20 services
├─ Hour 3: Deploy to 30 services
├─ Hour 4: Deploy to 40 services (most critical)

Benefit: If issue found in hour 1, only 10 services affected
Catch problems early before affecting critical systems.
```

---

## Exam & Practice

### Multiple Choice Questions

**Q1**: You deploy version 1.1 to 1% of users (canary). Error rate in canary: 5% vs 0.5% normal. Action?

A) Continue rollout (1% is acceptable loss)
B) Pause and investigate
C) Rollback canary
D) Increase to 5% and monitor

**Q2**: Blue/Green deployment requires 2x infrastructure. When is it worth cost?

A) Never (always use rolling)
B) High-traffic services (downtime = revenue loss)
C) Critical services (uptime > cost)
D) Always (best practice)

**Q3**: Database replication lag is 30 seconds. Primary region fails. Expected data loss?

A) 0 seconds (no loss)
B) 30 seconds (replication lag)
C) Entire database (lost)
D) Depends on RTO

**Q4**: Chaos test: Kill database, system should failover. What's the issue?

A) Test is destructive
B) Not a real failure mode
C) Should test with replicas, not primary
D) Good test

**Q5**: Cost optimization: Move from t3.large ($0.10/hr) to t3.medium ($0.05/hr). Savings?

A) 50% on compute
B) Not much (other costs remain)
C) Depends on utilization
D) Zero if underutilized

### Hands-on Tasks

**Task 1: Deployment Strategy Selection**

You're deploying a new feature to order service:
- 50 servers handling 10K req/sec
- 99.9% SLA required
- New feature uses different database schema
- Team size: 3 engineers

Design:
- Deployment strategy (rolling/blue-green/canary)
- Timeline
- Rollback procedure
- Monitoring plan

**Task 2: Multi-Region Failover**

Design failover for system:
- Primary: 50K req/sec capacity
- Secondary: 20K req/sec capacity
- Tertiary: 5K req/sec capacity

Handle:
- Primary region complete failure
- Primary database failure
- Network partition between regions
- Cost optimization (don't keep tertiary fully staffed)

### Incident Scenario

**Scenario: Deployment-Induced Cascading Failure**

Timeline:
- T+0: Deploy v1.1 to 10% of users (canary)
- T+5min: All metrics look good
- T+15min: Increase to 25% (standard canary progression)
- T+20min: Increase to 50%
- T+25min: Alert fires: HighDatabaseLoad
- T+27min: Database latency increases (replication lag)
- T+30min: Increase to 100% (no issues detected)
- T+35min: Alert fires: HighErrorRate (affects all users now)
- T+40min: Alert fires: DatabaseReplicationLag
- T+50min: Full rollback to v1.0 initiated
- T+60min: System recovers

**Post-mortem investigation discovers:**
- v1.1 made many more database queries (N+1)
- Low in canary didn't show up (small traffic)
- At 50%+, it became visible but too late

**Questions:**
1. What monitoring would catch this during canary?
2. Should you have paused at 25% or 50%?
3. How to detect N+1 query issue before production?
4. Design better metrics for canary (not just error rate)?
5. When is full rollback vs emergency fix better?

---

**Next Steps**:
- [EXAM_AND_PRACTICE.md](../EXAM_AND_PRACTICE.md) - All practice questions and scenarios
- [FINAL_PROJECT.md](../FINAL_PROJECT.md) - Capstone design project
- [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) - Glossary and lookup table

---

**Congratulations!** You've completed all 10 modules of the Distributed Systems tutorial.

What you've learned:
- How to design systems that scale to millions of users
- How to build reliability into systems
- How to reason about trade-offs
- How to operate systems in production
- How to respond to failures

Where to go next:
- Build distributed systems (apply knowledge)
- Interview preparation (system design questions)
- Deep dive into specific areas (Kubernetes, Kafka, databases)
- Contribute to open-source distributed systems projects
