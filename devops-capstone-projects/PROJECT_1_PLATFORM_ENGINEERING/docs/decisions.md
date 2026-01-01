# Architectural Decisions & Trade-offs

## Decision 1: Monolithic Backend vs Microservices

### Decision: Monolithic Flask API (with future microservices path)

**Reasoning:**
- Start simple, scale complexity gradually
- Single codebase easier to debug
- Shared database eliminates distributed transactions initially
- Deployment simpler (one Docker image)

**Trade-offs:**
- ✅ Faster development (one code repo)
- ❌ Harder to scale independent services later
- ❌ All services use same language (Flask)
- ❌ Cannot deploy teams independently

**When this would change:**
- Teams need independent deployment cycles
- Services have vastly different scaling requirements
- Separate tech stacks desired for different services

**Path to Microservices:**
```
Year 1: Monolith (user management + orders + payments)
Year 2: Extract user service (microservice)
Year 3: Extract order service (microservice)
Each service: Own database, own deployment, async communication
```

---

## Decision 2: PostgreSQL (Single Database) vs Database per Service

### Decision: Single PostgreSQL (for now)

**Reasoning:**
- No distributed transaction complexity
- Cross-service joins possible
- ACID guarantees simpler to reason about
- Cost effective (one RDS instance)

**Trade-offs:**
- ✅ Simpler transactions (no 2PC)
- ✅ Referential integrity enforced
- ❌ Database becomes bottleneck at scale
- ❌ Teams compete for schema changes

**Scaling limits:**
- PostgreSQL scales to ~10k TPS with optimization
- After that: Sharding by tenant or feature required

**When to split:**
- Each service has own data model
- Services don't reference each other's data
- Independent scaling needed

---

## Decision 3: Synchronous REST API vs Async/Event-Driven

### Decision: REST API with optional async for non-critical operations

**Reasoning:**
- REST simpler for client applications
- HTTP request/response pattern well-understood
- Easy to debug and test

**Async parts:**
- Logging: Fire-and-forget to CloudWatch
- Email notifications: Queued, processed asynchronously
- Analytics: Batch processed at night

**Trade-offs:**
- ✅ Client code simpler (no event handling)
- ✅ Synchronous guarantees (request completed = work done)
- ❌ Cannot handle peak loads gracefully
- ❌ Database becomes bottleneck for writes

**When to add async:**
- Write throughput exceeds database capacity
- Microservices need loose coupling
- Real-time event processing required

---

## Decision 4: PostgreSQL Replication (Streaming Standby) vs Other HA

### Decision: Streaming Replication to Standby + Read Replica

**Alternatives considered:**
1. **Patroni**: Auto failover orchestration
2. **etcd**: Distributed consensus
3. **PgBouncer**: Connection pooling only

**Why not Patroni:**
- Extra moving part (requires consul/etcd)
- AWS RDS Multi-AZ simpler (managed by AWS)
- RDS handles failover automatically

**Why this choice:**
- RDS Multi-AZ: AWS manages replication, failover
- Synchronous replication: Zero data loss
- Read replica: Scale read-heavy queries
- Cost-benefit: Worth the extra database cost for SaaS

---

## Decision 5: Redis (In-Memory) vs Memcached vs Local Cache

### Decision: Redis Cluster (with persistence)

**Alternatives:**
1. **Memcached**: Pure memory, no persistence
2. **Local cache**: In-app dictionary (Python)
3. **DynamoDB DAX**: Managed caching

**Why Redis:**
- Persistence (RDB + AOF) = reliable cache
- Data structures (hashes, sets, sorted sets)
- Replication built-in
- Pub/Sub for real-time features

**Why not Memcached:**
- No persistence (cache loss on restart)
- No data structures (KV only)
- Harder to implement rate limiting

**Why not local cache:**
- Can't share state across pods
- Memory growth unchecked (OOM)
- No TTL enforcement

---

## Decision 6: JWT (Stateless) vs Session Tokens (Stateful)

### Decision: JWT with Redis blacklist

**Reasoning:**
- JWT stateless (scale without session store)
- But Redis holds JWT to enable revocation
- Best of both worlds

**Token flow:**
```
1. User logs in → Generate JWT (signed with private key)
2. Store JWT hash in Redis with TTL
3. Requests include JWT in Authorization header
4. Verify JWT signature + Redis presence
5. User logout → Remove from Redis (instant revocation)
```

**Why this design:**
- ✅ Stateless for most requests (no Redis hit if cached)
- ✅ Instant logout (Redis deletion)
- ✅ Token expiration automatic (TTL)
- ❌ Requires Redis (small cost)

**Trade-off:**
- Memory: 1 million users × 500 bytes = 500MB (acceptable)

---

## Decision 7: Kubernetes (Self-Managed) vs Managed EKS vs Fargate

### Decision: AWS EKS (managed Kubernetes)

**Why not self-managed K8s:**
- Operational overhead (etcd, control plane)
- Security patches require downtime
- Expert knowledge required

**Why not Fargate (serverless containers):**
- No pod-to-pod networking (cannot run sidecar logging)
- Cannot run DaemonSets (Prometheus node exporter)
- Higher cost for sustained workloads
- Less control over resource allocation

**Why EKS:**
- AWS manages control plane
- Security patches automatic
- Full Kubernetes features
- Cost: $0.10/hour cluster fee reasonable

---

## Decision 8: Prometheus + Grafana vs CloudWatch vs Datadog

### Decision: Prometheus + Grafana (open source)

**Cost comparison:**
- Prometheus: Free
- Grafana: Free (self-hosted)
- CloudWatch: ~$0.30 per metric per month (100 metrics = $30)
- Datadog: ~$15 per host per month

**Why Prometheus:**
- No per-metric billing
- PromQL powerful query language
- Works across clouds
- Industry standard for Kubernetes

**Trade-off:**
- Operational overhead (run Prometheus + Grafana servers)
- No APM (tracing) included
- Custom alerting rules required

**If budget allows:**
- Would add Datadog for APM (expensive but worth it)

---

## Decision 9: Single Region (us-east-1) vs Multi-Region

### Decision: Single region initially, multi-region path documented

**Reasoning:**
- Operational complexity scales with regions
- Most traffic concentrated geographically
- Cost doubles with multi-region

**When to add regions:**
- User base spreads globally
- Latency becomes complaint
- Compliance requires data residency

**Multi-region strategy (future):**
```
Region 1 (us-east-1): Primary, writes
Region 2 (eu-west-1): Read replica, primary failover
Region 3 (ap-southeast-1): Read replica

Route 53: Geolocation routing (route to nearest region)
Data sync: PostgreSQL logical replication between regions
Cost: 3x compute, 2x database, ~$2000/month
```

---

## Decision 10: Log Aggregation (Loki vs ELK vs Splunk)

### Decision: CloudWatch Logs + Loki (dual-stack)

**Reasoning:**
- CloudWatch: Native AWS integration, easy setup
- Loki: Cheaper at scale, Prometheus-like query language

**Why not pure ELK:**
- Operational overhead (Elasticsearch needs tuning)
- Cost: Elasticsearch nodes expensive
- Overkill for initial scale

**Why not pure CloudWatch:**
- Cost at scale (very expensive for high volume)
- No easy Kubernetes integration
- Vendor lock-in

**Dual-stack approach:**
- CloudWatch: Primary logs (compliance, audit trail)
- Loki: Searchable interface (developer experience)
- Cost: ~$100/month for initial volume

---

## Decision 11: Container Registry (ECR vs Docker Hub vs Quay)

### Decision: AWS ECR (Elastic Container Registry)

**Reasoning:**
- Native AWS integration (no credential switching)
- VPC endpoint support (private registry)
- Pull through cache (faster multi-region deployments)
- Cost: ~$0.10/GB storage

**Why not Docker Hub:**
- Rate limiting (100 pulls/6 hours)
- Slower (no regional caching)

**Why not self-hosted:**
- Operational burden
- Registry stability critical (single point of failure)

---

## Decision 12: Secrets Management (AWS Secrets Manager vs Vault vs K8s Secrets)

### Decision: AWS Secrets Manager + Kubernetes Secrets

**Reasoning:**
- Secrets Manager: Rotating credentials (database passwords)
- K8s Secrets: ConfigMaps for non-sensitive data
- Separate concerns: Credentials vs configuration

**Flow:**
```
1. AWS Secrets Manager stores database password
2. Pod retrieves password at startup (via IAM role)
3. Password injected as environment variable
4. Container uses environment variable
5. AWS rotates password (pod pulls new version)
```

**Trade-off:**
- Cost: ~$0.40/secret per month (1 database password = $0.40)
- Complexity: Two secret systems

**Why not HashiCorp Vault:**
- Operational overhead (run Vault cluster)
- AWS Secrets Manager simpler (managed service)

---

## Key Learnings & Red Flags

### What This Project Does Well:
1. ✅ Demonstrates understanding of every layer
2. ✅ Makes explicit trade-off decisions
3. ✅ Uses managed services where appropriate
4. ✅ Plans for scale without over-engineering

### Red Flags Avoided:
1. ❌ Premature microservices (starts monolithic)
2. ❌ Self-managing Kubernetes (use EKS)
3. ❌ Cheap database solutions (uses RDS for reliability)
4. ❌ Over-complicated observability (Prometheus is enough)

### Interview Follow-ups:
- Q: "Why not Microservices from day 1?"
  A: *See Decision 1*
- Q: "How would you scale this 10x?"
  A: *See Decision 9 and horizontal scaling section*
- Q: "What would break first?"
  A: Database (add read replicas), then compute (HPA), then network
