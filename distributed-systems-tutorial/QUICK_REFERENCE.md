# QUICK_REFERENCE: Glossary & Lookup Tables

## Glossary of Key Terms

### A

**ACID** - Atomicity, Consistency, Isolation, Durability. Properties of traditional database transactions.

**Auto-scaling** - Automatically increasing or decreasing infrastructure capacity based on metrics.

**Availability** - Percentage of time system is operational and responding to requests.

### B

**BASE** - Basically Available, Soft state, Eventually consistent. Model for distributed systems.

**Blue/Green Deployment** - Two identical environments; traffic switched between them for zero-downtime updates.

**Bulkhead Pattern** - Isolating resources (threads, connections) to prevent cascading failures.

### C

**Cache-Aside** - Application checks cache, loads from database on miss, updates cache.

**Canary Deployment** - Deploying to small subset first, gradually increasing traffic.

**CAP Theorem** - Claim that systems can provide at most 2 of: Consistency, Availability, Partition tolerance.

**Circuit Breaker** - Pattern that stops calling failing service, allowing it to recover.

**Consistency** - All nodes see same data at same time (strong) or eventually (eventual).

### D

**Dead-Letter Queue (DLQ)** - Queue for messages that failed processing repeatedly.

**Distributed Lock** - Mechanism for mutual exclusion across multiple servers.

**Distributed Tracing** - Following requests across multiple services with trace IDs.

### E

**Eventual Consistency** - Data eventually converges across replicas, but not immediately consistent.

**Event-Driven Architecture** - Systems based on production and consumption of events.

**Event Sourcing** - Storing immutable stream of events instead of current state.

### H

**Health Check** - Endpoint that reports service health status to load balancers.

**Hotspot** - Shard or server receiving disproportionate load.

### I

**Idempotency** - Operation that produces same result regardless of how many times called.

**Idempotency Key** - Unique identifier that ensures operation runs exactly once despite retries.

### L

**Latency** - Time from request to response (measured in milliseconds).

**Leader-Follower Replication** - One primary accepts writes, followers replicate and handle reads.

**Load Balancer** - Distributes traffic across multiple servers.

### M

**Message Queue** - Persistent buffer holding messages between services.

**Multi-Leader Replication** - Multiple servers accept writes, replicate bidirectionally.

**Multi-Region** - System running in multiple geographic locations.

### P

**Partition** - Network failure dividing system into isolated parts.

**Pub/Sub** - Publish-Subscribe pattern where one producer, many consumers receive message.

### R

**Rate Limiting** - Restricting request rate to prevent overload.

**Replication** - Copying data across multiple servers for durability and availability.

**Replica Lag** - Delay between write on primary and replication to follower.

**RTO** - Recovery Time Objective: how fast to recover from failure.

**RPO** - Recovery Point Objective: how much data loss acceptable.

### S

**Saga** - Distributed transaction using compensating transactions instead of 2PC.

**Scaling** - Increasing capacity (vertical: bigger servers, horizontal: more servers).

**SLA** - Service Level Agreement: commitment to uptime/performance.

**SLI** - Service Level Indicator: measured metric (e.g., 99.9% availability).

**SLO** - Service Level Objective: target for SLI (e.g., 99.9% availability goal).

**Sharding** - Partitioning data across multiple databases by key.

### T

**Throughput** - Requests per second (measured in req/sec).

**Token Bucket** - Rate limiting algorithm using token replenishment.

**Trace ID** - Unique identifier following request across services.

### W

**Write-Behind** - Write to cache immediately, database later.

**Write-Through** - Write to both cache and database synchronously.

---

## Technology Comparison Tables

### Message Queue Systems

| Feature | RabbitMQ | Kafka | AWS SQS |
|---|---|---|---|
| **Throughput** | 50K msg/sec | 1M+ msg/sec | 1M msg/sec |
| **Latency** | <10ms | 100ms-1s | 100ms-30s |
| **Ordering** | Per queue | Per partition | FIFO only |
| **Persistence** | Optional | Always | Always |
| **Operations** | Medium | High | Low (managed) |
| **Cost** | Low | Medium | Low-High |
| **Use Case** | Task queues | Event streams | Serverless |

### Database Replication

| Strategy | Writes | Reads | Consistency | Failover |
|---|---|---|---|---|
| **Leader-Follower** | Single primary | Multiple replicas | Eventual | Manual/auto |
| **Multi-Leader** | Multiple | Multiple | Eventual | Automatic |
| **Leaderless** | Multiple | Multiple | Quorum-based | Automatic |

### Consistency Models

| Model | Latency | Complexity | Use Case |
|---|---|---|---|
| **Strong** | High (sync replication) | Low (simple transactions) | Financial systems |
| **Eventual** | Low (async) | High (handle conflicts) | Social media, caches |
| **Causal** | Medium | Medium | Comment threads |
| **Session** | Low | Low | Web sessions |

### Deployment Strategies

| Strategy | Downtime | Rollback | Infrastructure | Rollout Time |
|---|---|---|---|---|
| **Rolling** | None | Instant | 1x | Hours |
| **Blue/Green** | None | Instant | 2x | Minutes |
| **Canary** | None | Fast | 1.1x | Hours |

### Caching Strategies

| Pattern | Performance | Consistency | Complexity |
|---|---|---|---|
| **Cache-Aside** | High | Eventual | Medium |
| **Write-Through** | Medium | Strong | Low |
| **Write-Behind** | Very High | Eventual | High |

---

## Architecture Checklist

### High Availability

- [ ] Multiple servers (no single point of failure)
- [ ] Load balancer with health checks
- [ ] Database replication (primary + replica minimum)
- [ ] Automatic failover procedures
- [ ] Tested failover (monthly)
- [ ] Multi-region ready (even if not deployed yet)

### Resilience

- [ ] Circuit breakers for external dependencies
- [ ] Timeouts on all network calls
- [ ] Retry with exponential backoff
- [ ] Bulkheads (resource isolation)
- [ ] Graceful degradation (partial failures)
- [ ] Dead-letter queues (failed message handling)

### Performance

- [ ] Caching layer (Redis/Memcached)
- [ ] CDN for static assets
- [ ] Database indexes on query keys
- [ ] Connection pooling
- [ ] Async processing for non-critical operations
- [ ] Monitoring of slow queries

### Observability

- [ ] Structured logging (JSON, trace IDs)
- [ ] Distributed tracing (Jaeger/Zipkin)
- [ ] Metrics collection (Prometheus)
- [ ] Dashboards for service health
- [ ] Alerts for SLO violations
- [ ] Runbooks for common issues

### Security

- [ ] API authentication (JWT, OAuth)
- [ ] Rate limiting per user/API key
- [ ] Input validation
- [ ] Encryption in transit (HTTPS)
- [ ] Encryption at rest
- [ ] Secrets management (no hardcoded credentials)

### Scalability

- [ ] Stateless services (no server affinity)
- [ ] Horizontal scaling tested
- [ ] Auto-scaling policies defined
- [ ] Database sharding plan (if needed)
- [ ] Capacity planning model
- [ ] Load testing at 2x expected peak

---

## Learning Path Recommendations

### For System Design Interviews

**Must Know:**
- Modules 1-3 (Fundamentals, Scalability, Data)
- Module 8 (Microservices)
- Module 9 (Observability basics)

**Should Know:**
- Module 5 (Fault Tolerance)
- Module 10 (Deployment)

**Nice to Know:**
- Module 4 (Messaging)
- Module 6 (Performance)
- Module 7 (Consistency)

### For Backend Engineers

**Foundation (Week 1):**
- Module 1 (Fundamentals)
- START_HERE guide

**Core Skills (Weeks 2-3):**
- Module 2 (Scalability)
- Module 3 (Data)
- Module 5 (Fault Tolerance)

**Advanced (Weeks 4-6):**
- Module 4 (Messaging)
- Module 6 (Performance)
- Module 8 (Microservices)

**Operations (Week 7):**
- Module 9 (Observability)
- Module 10 (Deployment)

### For DevOps/SRE Engineers

**Critical Path:**
- Module 1 (understand systems)
- Module 10 (deployment strategies)
- Module 9 (observability)
- Module 5 (fault tolerance)

**Supporting Knowledge:**
- Module 2 (scaling)
- Module 6 (performance)
- Module 7 (coordination)

---

## Common Pitfalls Checklist

### Architecture Pitfalls

- [ ] Premature microservices (start with monolith)
- [ ] Ignoring network latency
- [ ] Assuming network is reliable
- [ ] Single point of failure
- [ ] No monitoring/observability
- [ ] Distributed transactions (use saga pattern instead)

### Implementation Pitfalls

- [ ] No idempotency keys (duplicate charges)
- [ ] Synchronous call chains (cascading failures)
- [ ] No circuit breakers
- [ ] No timeouts
- [ ] No retries with backoff
- [ ] No DLQ for failed messages
- [ ] Cache invalidation without strategy

### Operational Pitfalls

- [ ] Deploying without runbooks
- [ ] No chaos engineering tests
- [ ] Alerting on every metric (alert fatigue)
- [ ] No SLO defined
- [ ] Underprovisioned for peak load
- [ ] No disaster recovery testing
- [ ] Manual failover only

---

## Quick Decision Tree: When to Use What

### Need to Scale Writes?
- Single DB? → Add replicas (read scaling only)
- Still bottlenecked? → Shard by natural key
- Need ACID? → Use 2PC (expensive) or redesign for eventual consistency
- Can accept eventual? → Use event-driven async

### Communication Between Services?
- Critical path? → Synchronous (REST/gRPC)
- Can be eventual? → Asynchronous (message queue)
- Ordering critical? → Kafka
- Simple pubsub? → Redis, RabbitMQ

### Service Fails?
- Can retry? → Use exponential backoff + circuit breaker
- Can fallback? → Return cached/default value
- Must always respond? → Graceful degradation
- Can reject? → Return 503 Unavailable

### Need Consistency?
- Critical (money)? → ACID, strong consistency
- Nice-to-have? → Eventual consistency
- Between services? → Saga pattern
- Across regions? → Accept eventual

---

## Resource Limits & Sizing

### Typical Server Capacity

```
4 CPU, 8GB RAM:
- CPU-bound workload: 5-10K req/sec
- I/O-bound workload: 1-2K req/sec
- Mixed: 2-5K req/sec

Database:
- Single instance: 10-20K req/sec
- With caching: 50K+ req/sec
- Sharded: 100K+ req/sec

Cache (Redis):
- Single node: 50-100K req/sec
- Cluster: 1M+ req/sec
```

### Cost Estimates (AWS, 2024)

```
100K req/sec system:

Infrastructure:
- App servers (100x t3.medium): ~$10K/month
- Database (2x r6i.2xlarge): ~$5K/month
- Cache (3-node Redis): ~$2K/month
- Load balancer: ~$0.5K/month
- Data transfer (1PB): ~$15K/month

Total: ~$32K/month (~$384K/year)

With Reserved Instances (-30%): ~$268K/year
With Spot Instances (-70%): ~$115K/year
```

---

**Last Updated**: January 2026
**Version**: 1.0
