# INDEX: Complete Table of Contents

## Quick Navigation

- [README.md](README.md) - Overview and learning paths
- [START_HERE.md](START_HERE.md) - Beginner guide
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Glossary and lookup tables

## The 10 Modules

### Module 1: Distributed Systems Fundamentals
- [docs/01-fundamentals.md](docs/01-fundamentals.md)
- **Topics**: Monolith vs distributed, CAP theorem, latency/throughput, communication patterns
- **Key Concepts**: 
  - CAP theorem (Consistency, Availability, Partition tolerance)
  - Latency percentiles (p50, p95, p99)
  - Synchronous vs asynchronous communication
  - Common distributed system failures

### Module 2: System Scalability
- [docs/02-scalability.md](docs/02-scalability.md)
- **Topics**: Vertical vs horizontal scaling, sharding, load balancing, auto-scaling
- **Key Concepts**:
  - Vertical scaling limits
  - Horizontal scaling challenges
  - Sharding strategies and hotspots
  - Load balancing algorithms
  - Auto-scaling policies

### Module 3: Data Storage & Replication
- [docs/03-data-storage-replication.md](docs/03-data-storage-replication.md)
- **Topics**: Databases, replication strategies, consistency models, caching
- **Key Concepts**:
  - Leader-follower replication
  - Multi-leader and leaderless replication
  - Strong vs eventual consistency
  - Cache-aside, write-through, write-behind patterns
  - Cache invalidation and staleness

### Module 4: Messaging & Event-Driven Architecture
- [docs/04-messaging-event-driven.md](docs/04-messaging-event-driven.md)
- **Topics**: Message queues, pub/sub, event-driven patterns, idempotency
- **Key Concepts**:
  - Message queue vs pub/sub
  - Event sourcing
  - Idempotent operations
  - Retry and backoff strategies
  - Dead-letter queues
  - RabbitMQ, Kafka, SQS comparison

### Module 5: Fault Tolerance & Reliability
- [docs/05-fault-tolerance.md](docs/05-fault-tolerance.md)
- **Topics**: Circuit breakers, health checks, leader election, failover
- **Key Concepts**:
  - Circuit breaker pattern (closed/open/half-open)
  - Bulkhead pattern (resource isolation)
  - Health checks and self-healing
  - Leader election algorithms
  - Distributed locks
  - Multi-region failover

### Module 6: Performance Optimization
- [docs/06-performance-optimization.md](docs/06-performance-optimization.md)
- **Topics**: Profiling, caching, rate limiting, CDN, query optimization
- **Key Concepts**:
  - Performance bottleneck identification
  - Rate limiting algorithms (token bucket)
  - Distributed caching layers
  - CDN integration
  - Database indexing and query optimization
  - Denormalization trade-offs

### Module 7: Consistency, Transactions & Coordination
- [docs/07-consistency-transactions.md](docs/07-consistency-transactions.md)
- **Topics**: ACID vs BASE, distributed transactions, consensus, coordination services
- **Key Concepts**:
  - ACID properties
  - BASE eventually consistent systems
  - Two-phase commit (2PC) problems
  - Saga pattern (distributed transactions alternative)
  - Raft consensus algorithm overview
  - etcd and Zookeeper for coordination
  - Distributed locks and leader election

### Module 8: Microservices Design Patterns
- [docs/08-microservices-patterns.md](docs/08-microservices-patterns.md)
- **Topics**: Service boundaries, API gateway, data consistency, versioning
- **Key Concepts**:
  - Domain-driven design service boundaries
  - API gateway patterns
  - Synchronous vs asynchronous inter-service communication
  - API versioning and contracts
  - Data ownership and consistency
  - Service mesh and sidecars
  - Service decomposition anti-patterns

### Module 9: Observability in Distributed Systems
- [docs/09-observability.md](docs/09-observability.md)
- **Topics**: Metrics, distributed tracing, logging, SLOs, alerting
- **Key Concepts**:
  - Three pillars: metrics, logs, traces
  - RED method (Rate, Errors, Duration)
  - Prometheus and metrics collection
  - Distributed tracing (Jaeger/Zipkin)
  - Trace ID propagation
  - Structured logging
  - SLOs and SLIs
  - Error budgets
  - Alerting strategy and runbooks

### Module 10: Deployment & Scaling Strategies
- [docs/10-deployment-scaling.md](docs/10-deployment-scaling.md)
- **Topics**: Deployment patterns, multi-region, chaos engineering, cost optimization
- **Key Concepts**:
  - Rolling deployment
  - Blue/green deployment
  - Canary deployment
  - Multi-region architecture
  - Failover strategies
  - Chaos engineering
  - Resource quotas and auto-scaling
  - Cost optimization
  - Disaster recovery (RTO, RPO)

## Exam & Practice

- [EXAM_AND_PRACTICE.md](EXAM_AND_PRACTICE.md)
- 50 MCQ questions (5 per module)
- 20 hands-on design tasks (2 per module)
- 10 incident scenarios (1 per module)

## Capstone Project

- [FINAL_PROJECT.md](FINAL_PROJECT.md)
- Design a production-ready distributed system
- Covers: scaling, reliability, observability, deployment

## Quick Lookup

- [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- Glossary of terms
- Technology comparison tables
- Architecture checklists
- Learning path guides

## Examples & Labs

- Examples: `examples/` - Reference implementations (see GitHub repository)
- Labs: `labs/` - Hands-on lab guides
- Reference Configs: `reference-configs/` - Configuration templates

## Learning Paths

### Path 1: System Design Interview Prep (6 weeks)
1. Week 1: Modules 1-2 (Fundamentals, Scalability)
2. Week 2: Modules 3-4 (Data, Messaging)
3. Week 3: Modules 5-6 (Fault tolerance, Performance)
4. Week 4: Modules 7-8 (Consistency, Microservices)
5. Week 5: Modules 9-10 (Observability, Deployment)
6. Week 6: Final Project + Mock interviews

### Path 2: Backend Engineer Transition (4 weeks)
1. Week 1: Modules 1, 2 (Understanding at-scale systems)
2. Week 2: Modules 3, 4, 5 (Building reliable systems)
3. Week 3: Modules 6, 9 (Performance and operations)
4. Week 4: Modules 7, 8, 10 (Advanced patterns, deployment)

### Path 3: DevOps/SRE Focus (5 weeks)
1. Week 1: Module 1 (Fundamentals)
2. Week 2: Module 10 (Deployment), Module 9 (Observability)
3. Week 3: Module 5 (Fault tolerance)
4. Week 4: Modules 2, 6, 7 (Scaling, Performance, Coordination)
5. Week 5: Final Project focused on ops

### Path 4: Deep Dive into Specific Areas
**Caching & Performance Track**:
- Module 3 (Replication & Caching)
- Module 6 (Performance Optimization)
- Examples: Cache implementation patterns

**Messaging Track**:
- Module 4 (Messaging & Event-Driven)
- Module 7 (Consistency & Transactions)
- Examples: Kafka/RabbitMQ setup

**Reliability Track**:
- Module 5 (Fault Tolerance)
- Module 7 (Consensus)
- Module 10 (Deployment strategies)

## Recommended Study Order

1. **Read** the START_HERE guide
2. **Study** modules 1-5 in order (foundational)
3. **Study** modules 6-10 (advanced)
4. **Review** QUICK_REFERENCE for key concepts
5. **Practice** hands-on tasks in EXAM_AND_PRACTICE
6. **Solve** incident scenarios in EXAM_AND_PRACTICE
7. **Complete** FINAL_PROJECT capstone
8. **Mock interview** system design questions

## How Long?

- Reading: ~80 hours (10 hours per module)
- Hands-on practice: ~20 hours
- Final project: ~15 hours
- Total: ~115 hours (3 weeks full-time, 2 months part-time)

## Getting Help

Not understanding a concept?
1. Re-read the section
2. Check QUICK_REFERENCE glossary
3. Look at examples/
4. Check related modules (cross-referenced)

Stuck on a lab?
1. Read the lab description carefully
2. Check hints (if provided)
3. See if related module has similar example
4. Try simpler version first

## Contributing

Found an error? Want to add examples?
This is a living document. Contributions welcome.

---

**Last Updated**: January 2026
**Version**: 1.0
