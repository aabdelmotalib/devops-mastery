# FINAL PROJECT: Design a Production-Ready Distributed System

This is your capstone project, integrating all 10 modules into a single, cohesive system design.

---

## Project Overview

You're hired to architect the backend system for **TravelFlow**, a global ride-sharing platform competing with Uber/Lyft.

### Requirements

**Business Requirements:**
- Support 100 million active users worldwide
- 2 million concurrent rides per day (peak: 50K concurrent)
- 500K new users per day
- Available in 50+ countries
- 99.99% uptime SLA (production must survive region failure)
- Sub-second driver assignment

**Scale Numbers:**
- Average requests per second: 50,000
- Peak requests per second: 200,000
- Expected growth: 50% annually for 5 years

**Key Features:**
1. User authentication and profile management
2. Driver and rider matching (real-time, sub-second)
3. Payment processing and billing
4. GPS tracking and navigation
5. Push notifications to users and drivers
6. Ride history and analytics
7. Rating and review system
8. Customer support and dispute resolution

---

## Phase 1: High-Level Architecture

### 1.1 Define Service Boundaries

Design 8-12 microservices using domain-driven design.

For each service, specify:
- **Name and responsibility**: What does it own?
- **Data ownership**: What data does it store (no other service writes)?
- **Key operations**: Main use cases (create, read, update, delete)
- **Scale**: Estimated requests/sec and data size
- **Technology**: Database type, why?

**Example:**
```
User Service:
- Owns: User profiles, authentication
- Operations: register, login, get profile, update profile
- Scale: 10K req/sec, 100M users
- Tech: PostgreSQL (relational, strong consistency needed for auth)
```

**Deliverable:**
- Service inventory (table of all services)
- Service dependency diagram
- Data ownership matrix

### 1.2 Communication Patterns

For each pair of services that needs to communicate:

1. **Synchronous or Asynchronous?**
   - Justify choice

2. **Interface:**
   - REST, gRPC, or message queue?
   - Request/response format
   - Error codes and handling

3. **Resilience:**
   - Timeouts, retries, circuit breakers
   - Fallback behavior

**Critical Paths (synchronous):**
- User login
- Driver assignment
- Payment authorization

**Non-Critical Paths (async):**
- Notification sending
- Analytics logging
- Email confirmation

**Deliverable:**
- Communication matrix (which services call which)
- 3-5 key API specifications (full request/response)

### 1.3 Data Layer Design

For each service's database:

1. **Database choice:** PostgreSQL, MongoDB, Redis, etc. (justify)
2. **Replication strategy:** Leader-follower, multi-leader, or denormalization
3. **Sharding strategy:** If needed, what's the shard key?
4. **Consistency model:** ACID, eventual, or causal?
5. **Caching layer:** What to cache? TTL strategy?

**Example (Ride Service):**
```
Primary DB: PostgreSQL
- Owns: ride_id, driver_id, rider_id, status, created_at
- Shard key: driver_id (distribute driver's rides across shards)
- Replication: Leader + 1 follower (synchronous) + 1 replica (async, other region)

Cache: Redis cluster
- Key: ride:{ride_id} (active rides only)
- TTL: Expires when ride ends
- Invalidation: When status changes

Read replica for analytics:
- Eventual consistency OK
- Replicated with 30-second lag
```

**Deliverable:**
- Database design for each service (schema outline)
- Replication and caching strategy
- Data consistency guarantees

---

## Phase 2: Reliability and Resilience

### 2.1 Failure Scenarios

Design for these failure modes:

1. **Single service crashes**
   - Which services depend on it?
   - Graceful degradation strategy?
   - Fallback behavior?

2. **Database replica lag**
   - Service calls replica, reads stale data
   - Application handles stale data?
   - When is this unacceptable?

3. **Entire region fails**
   - Primary region: US-East
   - Secondary region: US-West
   - Plan: Failover procedure, data loss acceptable?

4. **Cascading failures**
   - Payment Service becomes slow
   - What happens? Circuit breaker? Timeout?
   - Prevent cascade to Ride Service, User Service?

5. **Network partition**
   - Two regions can't communicate
   - Each assumes other is dead
   - Prevents split-brain?

**For each scenario:**
- Detection mechanism (how to know it happened?)
- Recovery procedure (steps to restore service)
- Data loss acceptable? (RPO)
- Downtime acceptable? (RTO)

**Deliverable:**
- Failure mode analysis (table: scenario, detection, recovery, impact)
- Multi-region architecture (diagram)
- High availability checklist (what to implement)

### 2.2 Resilience Patterns

For top 5 critical service-to-service calls:

1. **Service A** → **Service B**
   - Timeout (seconds): _____
   - Retries: How many? Backoff strategy?
   - Circuit breaker: Failure threshold? Recovery timeout?
   - Fallback: If B unavailable, what happens?

**Example:**
```
Ride Service → Payment Service

Normal: 100ms average latency
Timeout: 5 seconds (fail fast if Payment slow)
Retries: 3 attempts with exponential backoff (1s, 2s, 4s)
Circuit breaker: 5 failures → open, 60s recovery
Fallback: Payment unavailable → queue payment, continue
```

**Deliverable:**
- Resilience design for critical paths
- Circuit breaker configuration
- Timeout and retry strategies

---

## Phase 3: Scaling and Performance

### 3.1 Load Testing

Estimate load per service (at 50K req/sec):

```
User Service:
- Login: 5K req/sec (5 million unique users/day, 80% in 12 hours)
- Get profile: 10K req/sec (users check profile frequently)
- Update profile: 1K req/sec

Ride Service:
- Create ride (request): 15K req/sec (main load)
- Get active rides: 20K req/sec (drivers polling)
- Update ride status: 5K req/sec
```

For each service, estimate:
1. **Queries per request** (SQL/NoSQL calls)
2. **Database load** (total queries/sec across system)
3. **Server capacity** (req/sec per server, assume 1000 req/sec typical)
4. **Servers needed** (load / capacity)

**Load calculation example:**
```
Ride Service: 15K req/sec to create ride
- Per request: 1 insert to rides table + 1 update to driver_state = 2 writes
- Database load: 15K * 2 = 30K writes/sec
- Database capacity: 5K writes/sec per server
- Servers needed: 30K / 5K = 6 database servers (for rides)
```

**Deliverable:**
- Load estimate per service
- Database capacity planning
- Number of servers/instances needed

### 3.2 Caching Strategy

For highest-load services, design caching:

1. **What to cache:** Top 5 queries/operations
   - User profiles? (read-heavy, infrequently changes)
   - Driver availability? (changes frequently, maybe don't cache)
   - Active rides? (medium, temporary)

2. **Cache hit rate target:** Aim for >90% for popular queries

3. **Cache invalidation:** When to refresh?
   - TTL-based? (e.g., 1 hour for user profiles)
   - Event-based? (invalidate when profile changes)
   - Both?

4. **Cache sizing:** How much data?
   - User profiles: 100M users, 1KB each = 100GB
   - Redis capacity: 256GB cluster enough? Yes.
   - Cost: ~$50K/month for large Redis cluster

**Deliverable:**
- Caching strategy (what, when, how)
- Expected hit rates
- Cache sizing and cost

### 3.3 Database Optimization

For database-heavy services:

1. **Query optimization:**
   - Add index on (driver_id, created_at desc) for ride history
   - Join optimization: prevent N+1
   - Connection pooling: 100 connections per server

2. **Denormalization:**
   - Ride status cached in driver's profile (eventual consistency OK)
   - Reduces joins for common queries

3. **Sharding:**
   - Rides sharded by driver_id (distribute load)
   - Users sharded by user_id
   - Avoid cross-shard queries (use cache for lookups)

**Deliverable:**
- Schema with indexes
- Query optimization plan
- Denormalization strategy

---

## Phase 4: Observability

### 4.1 Metrics and Monitoring

Define 15-20 key metrics:

```
RED Metrics (per service):
- Request rate (req/sec)
- Error rate (%)
- Latency (p50, p95, p99)

Business Metrics:
- Active riders online
- Active drivers online
- Rides started per minute
- Revenue per hour
- Payment success rate

Infrastructure:
- CPU utilization (%)
- Memory usage (%)
- Database connections
- Cache hit rate (%)
- Network I/O
```

For each metric:
- **Normal range:** What's healthy?
- **Alert threshold:** When to alert?
- **Severity:** Critical, warning, or info?

**Example:**
```
Metric: Payment Service Error Rate
Normal: < 0.1% (1 in 1000 succeed)
Warning: > 1% (alert but don't page)
Critical: > 5% (page on-call)
```

**Deliverable:**
- Metrics list (table)
- Alert thresholds for each
- Dashboard layout (wireframe)

### 4.2 Distributed Tracing

Design tracing for critical request:

**User creates a ride request**

Request flow:
1. Rider submits: GET /api/rides/request
2. API Gateway (validate, auth)
3. Ride Service (create ride, mark as "searching")
4. Matching Service (find nearby drivers)
5. Notification Service (notify drivers)
6. Update Ride Service (assign driver)
7. Return response

Each step should:
- Have unique trace ID
- Log entry/exit
- Log any external calls
- Record latency

**For matching service (most complex):**
- Trace: Find drivers within 2 miles
- Queries: Location index lookup, filtering by availability
- External call: Maps API for ETA
- Decision: Assign best driver

**Deliverable:**
- Trace design (format, propagation)
- What to log at each service
- How to correlate logs

### 4.3 SLOs and Error Budgets

Define SLOs:

```
Ride Creation SLO: 99.9% of requests complete < 2 seconds
  - Error budget: 0.1% = 8 hours/month failures acceptable
  - If at 99.5% this month: Used 4 hours, 4 hours left
  
Payment Processing SLO: 99.95% success rate
  - Error budget: 0.05% = 2 hours/month acceptable failures
  
Driver Assignment SLO: 99% within 30 seconds
  - Error budget: 1% = 36 hours/month acceptable delays
```

**Deliverable:**
- SLO table (target, error budget)
- How to calculate and report
- Alert rules based on error budget

---

## Phase 5: Deployment and Operations

### 5.1 Deployment Strategy

How to deploy new versions safely?

1. **Gradual rollout:**
   - Canary: 1% traffic for 30 minutes
   - Ramp: 5%, 25%, 50%, 100%
   - Total time: 3-4 hours

2. **Rollback:**
   - Automatic if error rate > 1%
   - Manual rollback available
   - Time to rollback: < 5 minutes

3. **Testing before deploy:**
   - Unit tests
   - Integration tests
   - Load test (at 50K req/sec)
   - Canary environment (same as production)

**Deliverable:**
- Deployment checklist
- Canary launch procedure
- Rollback procedure

### 5.2 Multi-Region Operations

How to operate across US-East, US-West, EU-West?

1. **Data replication:**
   - US-East primary
   - US-West sync replica (low latency, low lag)
   - EU-West async replica

2. **Failover:**
   - Auto-failover if primary region unavailable (health checks)
   - Promote US-West to primary
   - Time: 5-10 minutes

3. **Traffic routing:**
   - DNS-based: Serve users from closest region
   - 60% US-East, 25% US-West, 15% EU-West
   - Adjust based on region capacity

**Deliverable:**
- Multi-region architecture diagram
- Data replication strategy
- Failover automation procedure

### 5.3 Disaster Recovery

Prepare for catastrophic failure:

**Scenario: US-East datacenter burns down**

Recovery steps:
1. **Detect:** Health checks fail (2 min)
2. **Failover:** Promote US-West (10 min)
3. **Scale:** Auto-scale US-West to handle all traffic (10 min)
4. **Route:** DNS change to US-West as primary (1 min, TTL)
5. **Recovery:** Launch new infrastructure in new US location (2 hours)
6. **Rebalance:** Rebalance traffic across 3 regions

**RTO:** 30-60 minutes
**RPO:** Last 5 minutes (replication lag)

**Monthly test:** Simulate this failure monthly (not in production)

**Deliverable:**
- Disaster recovery plan
- RTO and RPO specifications
- Testing schedule

---

## Phase 6: Cost Analysis

### 6.1 Infrastructure Costs

Estimate annual cost for 50K req/sec system:

```
Compute (App Servers):
- 200 servers (stateless, horizontally scaled)
- t3.large instances: $0.083/hr
- Cost: 200 * $0.083 * 730 = $12,100/month = $145K/year
- Reserved instances (-40%): $87K/year

Database:
- Primary: r6i.4xlarge: $2.00/hr = $14.6K/month
- Replicas (2x): 2 * $0.50/hr = $7.3K/month
- Backups: $2K/month
- Cost: $24K/month = $288K/year

Caching:
- Redis cluster (256GB): $15K/month = $180K/year

Message Queues:
- Kafka cluster: $5K/month = $60K/year

Data Transfer:
- Outbound: 1PB/month * $0.05/GB = $51K/month
- With CDN (-70%): $15K/month = $180K/year

Monitoring and Logs:
- Prometheus, Grafana, ELK: $3K/month = $36K/year

CDN:
- For static assets: $5K/month = $60K/year

Total: ~$60K/month = $720K/year
```

### 6.2 Cost Optimization

Savings opportunities:

1. **Reserved instances** (-30-40%): $50K/year
2. **Spot instances for non-critical** (-70%): $30K/year
3. **Database right-sizing** (-20%): $60K/year
4. **Caching efficiency** (-15%): $30K/year
5. **CDN optimization** (-30%): $20K/year

**Total optimization: $190K/year → $530K/year total cost**

**Deliverable:**
- Cost breakdown (compute, storage, network, etc.)
- Annual infrastructure cost estimate
- Cost optimization opportunities

---

## Evaluation Criteria

Your design will be evaluated on:

### Technical Correctness (40%)
- [ ] Service boundaries well-designed (clear ownership)
- [ ] Scalability to 50K req/sec
- [ ] Reliability (handles failures)
- [ ] Consistency model appropriate
- [ ] Caching strategy sound

### Operational Readiness (30%)
- [ ] Monitoring and observability comprehensive
- [ ] Deployment strategy clear and safe
- [ ] Multi-region failover planned
- [ ] Disaster recovery documented
- [ ] Cost-conscious design

### Trade-off Awareness (20%)
- [ ] Acknowledges CAP/latency/cost tradeoffs
- [ ] Explains why technology choices
- [ ] Compares alternatives
- [ ] Balances simplicity vs features

### Completeness (10%)
- [ ] All sections addressed
- [ ] Diagrams included
- [ ] Concrete numbers (servers, latency, cost)
- [ ] Actionable recommendations

---

## Deliverables

### Phase 1: Architecture
- [ ] Service boundaries (table, diagram)
- [ ] Communication patterns (matrix, APIs)
- [ ] Data layer design (schema, replication)

### Phase 2: Reliability
- [ ] Failure scenario analysis (table)
- [ ] Multi-region architecture (diagram)
- [ ] Resilience patterns (circuit breakers, etc.)

### Phase 3: Scalability
- [ ] Load estimates (per service)
- [ ] Capacity planning (servers needed)
- [ ] Caching strategy (what, when, TTL)
- [ ] Database optimization (indexes, denormalization)

### Phase 4: Observability
- [ ] Metrics and alerts (table)
- [ ] Dashboard wireframe
- [ ] Distributed tracing design
- [ ] SLOs and error budgets

### Phase 5: Operations
- [ ] Deployment procedure (steps, timeline)
- [ ] Multi-region operations (failover)
- [ ] Disaster recovery plan (RTO, RPO)

### Phase 6: Cost
- [ ] Cost breakdown (annual)
- [ ] Cost optimization opportunities
- [ ] Cost per user/per ride estimate

---

## Final Presentation

Prepare a 20-minute presentation covering:
1. System architecture (5 min)
2. Reliability/failover (5 min)
3. Scalability/performance (5 min)
4. Observability/operations (5 min)

Be ready for questions:
- "What if payment service is down?"
- "How do you scale to 200K req/sec?"
- "What if your shard hotspots?"
- "How do you deploy safely?"

---

## Next Steps After Completion

1. **Compare with others:** See different approaches
2. **Research real systems:** Read how Uber, Lyft, etc. design systems
3. **Build a prototype:** Implement key services (at smaller scale)
4. **Interview practice:** Use this design for mock interviews
5. **Deep dives:** Focus on areas you want to specialize in

---

**Good luck! This is a comprehensive, production-grade system design.**

Remember: There are no "perfect" answers. Focus on:
- Clear thinking
- Sound trade-offs
- Operational awareness
- Scalability mindset

---

**Last Updated**: January 2026
**Version**: 1.0
