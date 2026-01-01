# PROJECT 1: Platform Engineering - SaaS Product Backend

**A production-grade platform demonstrating end-to-end DevOps ownership of a multi-tenant SaaS backend.**

---

## 🎯 Problem Statement

### Real-World Context
Many organizations run SaaS platforms that must handle:
- **Multiple customers (tenants)** with isolated data
- **Variable traffic patterns** (morning peaks, off-hours)
- **99.9% uptime SLAs** (not 99%)
- **Rapid feature deployment** without downtime
- **Cost optimization** at scale
- **Compliance requirements** (data isolation, audit logs)

### This Project Solves
Building and operating a **real SaaS backend platform** that:
1. **Isolates tenant data** while sharing infrastructure
2. **Scales horizontally** when load increases
3. **Deploys changes** 100+ times per day safely
4. **Observes everything** to catch issues before customers report them
5. **Costs predictably** even during traffic spikes
6. **Recovers automatically** from failures

### Why This Architecture Matters
This is NOT a simple CRUD app. This demonstrates how **DevOps engineers ensure product reliability**.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Internet Users                          │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐  ┌──────▼──────┐  ┌────▼────┐
    │Route 53 │  │Route 53     │  │Route 53 │
    │(DNS)    │  │(Failover)   │  │(Geo)    │
    └────┬────┘  └──────┬──────┘  └────┬────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐  ┌──────▼──────┐  ┌────▼────┐
    │   ALB   │  │    ALB      │  │   ALB   │
    │(AWS-US)│  │(AWS-EU)     │  │(AWS-AP) │
    └────┬────┘  └──────┬──────┘  └────┬────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
┌───▼─────────┐   ┌──────▼──────┐   ┌────────▼─────┐
│   Nginx      │   │   Nginx     │   │   Nginx      │
│   Ingress    │   │   Ingress   │   │   Ingress    │
│  (K8s)       │   │   (K8s)     │   │   (K8s)      │
└───┬─────────┘   └──────┬──────┘   └────────┬─────┘
    │                    │                    │
    └────────────────────┼────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
    ┌───▼──────┐  ┌──────▼──────┐  ┌────▼──────┐
    │  Flask   │  │    Flask    │  │   Flask   │
    │  Pod 1   │  │    Pod 2    │  │   Pod 3   │
    │(replica) │  │ (replica)   │  │ (replica) │
    └───┬──────┘  └──────┬──────┘  └────┬──────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
    ┌───▼──────┐  ┌──────▼──────┐  ┌────▼──────┐
    │PostgreSQL│  │   Redis     │  │  S3 Logs  │
    │ Primary  │  │   Cluster   │  │ (Archive) │
    │          │  │ (Replication)        │
    └───┬──────┘  └──────┬──────┘  └────┬──────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
            ┌────────────┼────────────┐
            │            │            │
        ┌───▼────┐  ┌────▼─────┐ ┌──▼───┐
        │Prometheus        │CloudWatch│  │Loki│
        │(Metrics)   │(Dashboards)│  │(Logs)
        └───┬────┘  └────┬─────┘ └──┬───┘
            │            │            │
            │            │            │
        ┌───▼────────────▼────────────▼───┐
        │    PagerDuty / Email / Slack     │
        │         (Alerting)               │
        └──────────────────────────────────┘
```

### Component Interaction

1. **Client Request**: DNS routes to nearest region
2. **Load Balancer (ALB)**: Distributes across 3 AZs
3. **Kubernetes Ingress**: Routes to Flask services
4. **Flask Pods**: Handle requests (3+ replicas for HA)
5. **PostgreSQL**: Stores application data, replicates to standby
6. **Redis**: Caches auth tokens, session data, rate limits
7. **Observability**: Prometheus metrics, Loki logs, alerts

### Request Lifecycle

```
User Request 
  ↓
DNS lookup (Route 53) returns ALB IP
  ↓
ALB health checks active backends
  ↓
ALB forwards to Kubernetes Ingress
  ↓
Ingress routes based on hostname/path
  ↓
Flask Pod receives request
  ↓
Authentication: Check Redis cache → PostgreSQL if miss
  ↓
Authorization: Check tenant permissions (cached)
  ↓
Business logic: Query PostgreSQL + Redis
  ↓
Response: JSON + Set-Cookie (if needed)
  ↓
Middleware logs request (async to CloudWatch)
  ↓
Prometheus scrapes metrics endpoint
  ↓
Alerts triggered if thresholds exceeded
```

---

## 🔧 Technology Decisions

### Why Flask (Not FastAPI or Django)?

**Flask Chosen:**
- **Lightweight, explicit control** → Better for learning DevOps patterns
- **Minimal dependencies** → Smaller Docker image (400MB vs 1.5GB for Django)
- **Microservice-friendly** → Easy to split into multiple services later
- **Middleware/extension ecosystem** → Can add features incrementally

**When to Use Flask:**
- Microservices architecture
- Startups optimizing for speed-to-deploy
- Services that don't need ORM complexity
- Learning DevOps (you see every layer)

**When NOT to use Flask:**
- **Django Better**: Large monolith, admin panel needed, rapid development with forms
- **FastAPI Better**: High-performance async APIs, modern Python (3.7+), auto-docs critical
- **Go/Rust Better**: Extreme performance, very small memory footprint

**Trade-offs:**
- Flask: Simpler → Less batteries included
- FastAPI: Faster → Less mature ecosystem
- Django: Feature-complete → Harder to decompose

---

### Why PostgreSQL (Not MongoDB)?

**PostgreSQL Chosen:**
- **ACID transactions** → Data consistency for financial/SaaS operations
- **JSONB support** → Can store semi-structured data (hybrid model)
- **Rich querying** → Complex reports, analytics
- **Replication & HA** → Streaming replication to standby
- **Cost-effective** → RDS multi-AZ still cheaper than NoSQL alternatives at scale

**When to Use PostgreSQL:**
- ✅ SaaS applications (multi-tenant, audit logs, compliance)
- ✅ Financial systems
- ✅ E-commerce (inventory, orders, payments)
- ✅ Analytics/reporting
- ✅ Complex relationships (users → orgs → teams → projects)

**When NOT to use PostgreSQL:**
- **MongoDB Better**: Document-centric (CMS, user profiles with variable fields)
- **DynamoDB Better**: Extreme scale (millions of ops/sec), serverless
- **Elasticsearch Better**: Full-text search, logging, analytics-first
- **Redis Better**: Caching, real-time leaderboards, pub/sub

**Trade-offs:**
- PostgreSQL: Consistency → Slower than NoSQL for unstructured data
- MongoDB: Flexible → No transactions until recently, eventual consistency
- DynamoDB: Managed → Vendor lock-in, limited querying

---

### Why Redis (Not Memcached)?

**Redis Chosen:**
- **Data structures** → Hashes, sets, sorted sets (not just KV)
- **Persistence** → RDB snapshots + AOF logs for durability
- **Replication** → Master-replica for HA
- **Expiration** → Perfect for sessions, rate limits, token caching
- **Pub/Sub** → Real-time event distribution

**When to Use Redis:**
- ✅ Session storage (with expiration)
- ✅ Rate limiting (sliding window counters)
- ✅ Real-time leaderboards (sorted sets)
- ✅ Caching with TTL
- ✅ Job queues (simple pub/sub)

**When NOT to use Redis:**
- **Memcached Better**: Simple KV cache, extreme throughput
- **DynamoDB DAX Better**: Managed, serverless caching
- **RabbitMQ/Kafka Better**: Complex message processing, persistence guarantees

**Trade-offs:**
- Redis: Flexible data types → Requires careful memory management
- Memcached: Simple → Limited to KV pairs
- RabbitMQ: Durable queuing → Slower than Redis pub/sub

---

### Why Docker Compose (For Local Development)?

**Docker Compose Chosen:**
- **One-command setup** → `docker-compose up` → full stack running
- **Service networking** → Services talk via hostnames
- **Volume mounts** → Code changes reflected instantly (no rebuild)
- **Environment files** → Replicate production secrets locally

**When to Use Docker Compose:**
- ✅ Local development
- ✅ Integration testing
- ✅ CI/CD test environments
- ✅ Single-server deployments

**When NOT to use Docker Compose:**
- **Kubernetes Better**: Multi-server, auto-scaling, self-healing
- **ECS Better**: AWS-native, serverless billing
- **Docker Swarm**: Dead project, don't use

---

### Why Kubernetes (Not ECS)?

**Kubernetes Chosen:**
- **Cloud-agnostic** → Run on AWS, GCP, Azure, on-prem
- **Industry standard** → 85% of enterprises use K8s
- **Self-healing** → Dead pods replaced automatically
- **Declarative** → Define desired state, K8s converges
- **CKA marketable** → Most valuable DevOps cert

**When to Use Kubernetes:**
- ✅ Multi-cloud strategy
- ✅ Enterprise standards
- ✅ 50+ microservices
- ✅ On-premises + cloud hybrid
- ✅ Stateless workloads

**When NOT to use Kubernetes:**
- **ECS Better**: AWS-only, simpler API, no YAML learning curve
- **Fargate Better**: Serverless containers, no capacity management
- **Lambda Better**: Functions, not containers
- **Heroku Better**: Tiny teams, rapid prototyping

**Trade-offs:**
- Kubernetes: Powerful → Steep learning curve, operational overhead
- ECS: AWS-native → Locked into AWS, less flexible
- Fargate: Serverless → More expensive for sustained workloads

---

### Why AWS (Not GCP/Azure)?

**AWS Chosen:**
- **Widest service catalog** → 200+ services
- **Market leader** → 32% market share
- **Most job postings** → AWS skills most demanded
- **RDS Aurora** → Best managed database
- **CloudWatch** → Integrated logging/metrics

**When to Use AWS:**
- ✅ Enterprise adoption
- ✅ Complex multi-service architectures
- ✅ Financial/healthcare compliance (lots of solutions)
- ✅ Job market

**When NOT to use AWS:**
- **GCP Better**: Data science, BigQuery, machine learning
- **Azure Better**: Enterprise Microsoft integration (Office 365, Active Directory)
- **Digital Ocean**: Simplicity, predictable pricing

---

### Why Prometheus + Grafana (Not CloudWatch/Datadog)?

**Prometheus + Grafana Chosen:**
- **Open source** → No per-metric billing
- **Scraping model** → Pull metrics (not push = less app code)
- **PromQL** → Powerful query language
- **Alert rules** → Flexible alerting (> 100 requests/sec)
- **Community** → Massive ecosystem

**When to Use Prometheus:**
- ✅ Kubernetes environments
- ✅ Cost-conscious organizations
- ✅ Complex alerting logic
- ✅ Multi-cloud setups

**When NOT to use Prometheus:**
- **CloudWatch Better**: AWS-native, serverless, no infrastructure
- **Datadog Better**: Enterprise support, APM out-of-box
- **New Relic Better**: Managed APM, ease of use

---

## 📋 CI/CD Pipeline Explanation

### Pipeline Stages & Why Each Exists

```
Git Push → Webhook → Jenkins/GitHub Actions
   ↓
1. CHECKOUT (Get code)
   - Why: Can't build without source
   
2. LINT (Code quality)
   - Why: Catch style issues early (cheap)
   - Tools: pylint, black, flake8
   - Fail fast: Yes (no point building bad code)
   
3. UNIT TESTS (Test in isolation)
   - Why: 80% of bugs caught here
   - Coverage: >80% required
   - Run parallel: Yes (fast feedback)
   
4. INTEGRATION TESTS (Services together)
   - Why: Catch component interaction issues
   - Uses: Docker Compose stack
   - Fail fast: Yes (if DB queries fail)

5. SECURITY SCAN (SCA + SAST)
   - Why: Block dependencies with CVEs
   - Tools: Trivy, Snyk, SonarQube
   - Fail on: High severity only

6. BUILD IMAGE (Docker build)
   - Why: Reproducible deployments
   - Base image: python:3.11-slim (minimal)
   - Cache: Use BuildKit for speed
   
7. PUSH IMAGE (To registry)
   - Why: Store version history
   - Registry: ECR (AWS-native)
   - Tag: Git SHA + branch
   
8. DEPLOY TO STAGING (Blue-green)
   - Why: Test in prod-like environment
   - Validation: Smoke tests run
   - Wait for health checks
   
9. SMOKE TESTS (Against staging)
   - Why: Verify deployment health
   - Tests: Health check, login, basic flow
   - Fail fast: Yes (catch deployment issues)
   
10. MANUAL APPROVAL (If needed)
    - Why: Production changes require sign-off
    - For: Major releases, config changes
    - Skip for: Hotfixes (on-call approval)
    
11. DEPLOY TO PRODUCTION (Blue-green)
    - Why: Zero-downtime deployment
    - Strategy: 10% → 50% → 100%
    - Rollback trigger: Error rate > 5%

12. POST-DEPLOY VALIDATION
    - Why: Catch issues in prod immediately
    - Checks: Response time, error rate, latency
    - Alert: Ops team if anomalies
```

### Deployment Strategy: Blue-Green

```
Before deployment:
  Blue (v1.0): Handling 100% traffic
  Green (v1.1): Built, waiting

Step 1: Route 10% traffic to Green
  Blue: 90% traffic
  Green: 10% traffic
  → Monitor metrics for 2 minutes

Step 2: If no errors, route 50% traffic to Green
  Blue: 50% traffic
  Green: 50% traffic
  → Monitor metrics for 5 minutes

Step 3: If no errors, route 100% traffic to Green
  Blue: 0% traffic
  Green: 100% traffic
  → Old Blue pods terminate

Rollback: If error rate spikes, immediately switch back to Blue

This achieves: Zero downtime + instant rollback capability
```

### Why This Specific Pipeline?

1. **Fail fast** → Unit tests before building (waste no resources)
2. **Parallel execution** → Tests, security scans run simultaneously
3. **Immutable artifacts** → Docker image = exact version deployed
4. **Staging validation** → Production == staging (no surprises)
5. **Canary deployment** → Gradual rollout catches issues early
6. **Instant rollback** → Keep old version running until new proves healthy

---

## ☸️ Kubernetes Architecture (CKA-Level)

### Deployment Strategy

```yaml
# Why this matters: Ensures 3+ replicas always running
spec:
  replicas: 3  # High availability across 3 AZs
  
  strategy:
    type: RollingUpdate  # One pod at a time
    rollingUpdate:
      maxSurge: 1        # 4 pods during update
      maxUnavailable: 0  # Always 3+ running
```

### Resource Management (Critical)

```yaml
resources:
  requests:    # Reserved resources (needed for scheduling)
    cpu: "500m"      # 0.5 CPU core
    memory: "512Mi"  # 512MB
  
  limits:      # Hard cap (pod killed if exceeded)
    cpu: "1"         # 1 CPU core max
    memory: "1Gi"    # 1GB max
```

**Why this matters:**
- **Requests**: Kubernetes scheduler uses these to pack pods efficiently
- **Limits**: Prevent runaway pods from killing node
- **Ratio**: Keep requests:limits at 1:2 (buffer for spikes)

### Health Checks (Self-Healing)

```yaml
livenessProbe:    # Is pod alive?
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 10
  periodSeconds: 10
  failureThreshold: 3
  # Kills pod after 30s of failures

readinessProbe:   # Is pod ready to accept traffic?
  httpGet:
    path: /ready
    port: 5000
  initialDelaySeconds: 5
  periodSeconds: 5
  # Removes from load balancer if failing
```

**Why separate probes?**
- **Liveness**: Pod is stuck (restart it)
- **Readiness**: Pod warming up / DB migration (don't send traffic yet)

### Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  
  minReplicas: 3
  maxReplicas: 20
  
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70   # Scale up at 70% CPU
  
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80   # Scale up at 80% memory
  
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100               # Double pods when scaling up
        periodSeconds: 60
    
    scaleDown:
      stabilizationWindowSeconds: 300  # Wait 5 min before scaling down
      policies:
      - type: Pods
        value: 1
        periodSeconds: 120
```

### ConfigMaps & Secrets

```yaml
# ConfigMaps: Non-sensitive config
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-config
data:
  LOG_LEVEL: "info"
  FLASK_ENV: "production"
  DATABASE_POOL_SIZE: "20"

---
# Secrets: Sensitive data (encrypted at rest in etcd)
apiVersion: v1
kind: Secret
metadata:
  name: api-secrets
type: Opaque
data:
  DATABASE_PASSWORD: base64-encoded-password
  JWT_SECRET: base64-encoded-secret
```

### Network Policies (Pod-to-Pod Communication)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-netpol
spec:
  podSelector:
    matchLabels:
      app: api
  
  policyTypes:
  - Ingress
  - Egress
  
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 5000
  
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: databases
    ports:
    - protocol: TCP
      port: 5432  # PostgreSQL
  
  - to:
    - namespaceSelector:
        matchLabels:
          name: cache
    ports:
    - protocol: TCP
      port: 6379  # Redis
  
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 53   # DNS (needed for external calls)
```

### CKA Exam Mapping

This project demonstrates:

| CKA Objective | Implementation |
|---|---|
| **Pod Management** | Deployment with replicas, rolling updates |
| **Services & Networking** | ClusterIP (internal), LoadBalancer (external), NetworkPolicy |
| **Storage** | PersistentVolumes for PostgreSQL, ConfigMaps/Secrets |
| **Scheduling** | Resource requests/limits, node affinity |
| **Security** | RBAC, NetworkPolicy, Pod Security Policies |
| **Monitoring** | Liveness/readiness probes, metrics scraping |
| **Troubleshooting** | Logs, exec, describe, port-forward |

---

## 🌐 AWS Architecture

### Network Design

```
Region: us-east-1

VPC (10.0.0.0/16)
│
├─ Public Subnets (NAT Gateway access)
│  ├─ us-east-1a: 10.0.1.0/24 (ALB)
│  ├─ us-east-1b: 10.0.2.0/24 (ALB)
│  └─ us-east-1c: 10.0.3.0/24 (ALB)
│
├─ Private Subnets (No internet, route via NAT)
│  ├─ us-east-1a: 10.0.11.0/24 (EKS Nodes)
│  ├─ us-east-1b: 10.0.12.0/24 (EKS Nodes)
│  └─ us-east-1c: 10.0.13.0/24 (EKS Nodes)
│
├─ Database Subnets (Encrypted)
│  ├─ us-east-1a: 10.0.21.0/24 (RDS PostgreSQL)
│  ├─ us-east-1b: 10.0.22.0/24 (RDS Standby)
│  └─ us-east-1c: 10.0.23.0/24 (RDS Read Replica)
```

### Compute: EKS vs EC2

| Aspect | EKS | EC2 |
|---|---|---|
| **Management** | AWS manages K8s | You manage everything |
| **Upgrade** | Automatic | Manual |
| **Cost** | $0.10/hour cluster fee | No cluster fee |
| **Complexity** | Medium | High |
| **Scalability** | 1000s of pods | Limited by instance count |
| **Best for** | Microservices | Monoliths, custom OS needs |

**Decision: EKS**
- Reason: Multi-service architecture, self-healing critical
- Cost: Cluster fee offset by reduced operational overhead
- Flexibility: Easy to scale from 3 to 300 pods

### Database: RDS Multi-AZ

```
RDS PostgreSQL 14 (Multi-AZ)
│
├─ Primary (us-east-1a)
│  └─ Accepts reads + writes
│  └─ Automatic backups to S3
│  └─ Replication lag: <1ms
│
├─ Standby (us-east-1b) [Synchronous replication]
│  └─ Hot standby (read-only)
│  └─ Auto-promotion on primary failure
│  └─ Zero data loss
│
└─ Read Replica (us-east-1c) [Asynchronous]
    └─ For analytics queries
    └─ Replication lag: 1-5 seconds acceptable
```

**Why Multi-AZ?**
- Automatic failover to standby (30 seconds)
- Zero data loss (synchronous replication)
- Cost: ~2x single-AZ (acceptable for SaaS)

**RTO / RPO:**
- RTO (Recovery Time Objective): 30 seconds (auto failover)
- RPO (Recovery Point Objective): 0 seconds (synchronous)

### DNS & TLS

```
User Request
  ↓
Route 53 (AWS DNS)
  - Multiple health checks
  - Geolocation routing (US → us-east-1 ALB)
  - Europe → us-west-2 ALB
  
  ↓
ALB (Application Load Balancer)
  - TLS termination (ACM certificate)
  - Cipher suites: TLS 1.3 preferred
  - Redirect HTTP → HTTPS
  
  ↓
Target Group (EKS Nodes)
  - Health check every 30 seconds
  - Deregister unhealthy targets
```

### Cost Optimization

| Component | Cost | Optimization |
|---|---|---|
| **EKS** | $73/month cluster | Fixed cost |
| **EC2 (3 x t3.medium)** | $180/month | Use on-demand (not reserved) |
| **RDS Multi-AZ** | $300/month | db.t3.medium (smallest HA option) |
| **Networking** | $50-100/month | NAT gateway, data transfer |
| **Storage** | $5-10/month | EBS + S3 backups |
| **Total** | **~$600-700/month** | |

**Cost Reduction Strategies:**
1. Reserved Instances (1-year): 30% discount
2. Spot Instances (EKS): 70% discount (non-critical pods)
3. Auto-scaling: Remove pods at night
4. S3 Lifecycle: Move old logs to Glacier

---

## 📊 Observability & Reliability

### Metrics (Prometheus)

Key metrics scraped every 15 seconds:

```yaml
flask_http_requests_total{method="POST", endpoint="/api/users", status="200"}
flask_http_request_duration_seconds{endpoint="/api/orders", quantile="0.99"}
flask_exceptions_total{exception_type="DatabaseError"}
psycopg2_db_pool_connections_open{status="active"}
psycopg2_db_pool_connections_open{status="idle"}
redis_connected_clients
redis_used_memory_bytes
```

### Dashboards (Grafana)

**Dashboard 1: API Health**
- Request rate (requests/sec)
- Latency (p50, p95, p99)
- Error rate (%)
- Status code breakdown (2xx, 4xx, 5xx)

**Dashboard 2: Database Performance**
- Connection pool usage
- Query latency (slow queries > 1 second)
- Replication lag
- Cache hit ratio

**Dashboard 3: Infrastructure**
- Pod CPU usage (% of requests)
- Pod memory usage
- Node disk usage
- Network throughput

### Logging (Loki + CloudWatch)

```
App logs (stdout/stderr)
  ↓
Container runtime captures
  ↓
CloudWatch Agent sends to CloudWatch
  ↓
Loki scrapes CloudWatch (async)
  ↓
Grafana queries Loki
  ↓
Searchable logs with labels
```

**Log Structure (JSON)**
```json
{
  "timestamp": "2026-01-01T12:00:00Z",
  "level": "INFO",
  "service": "api",
  "tenant_id": "cust-123",
  "request_id": "req-abc-def",
  "message": "User login successful",
  "status_code": 200,
  "latency_ms": 45,
  "user_id": "user-456"
}
```

### Alerts (Prometheus Alert Rules)

```yaml
# Alert 1: High error rate
- alert: HighErrorRate
  expr: rate(flask_exceptions_total[5m]) > 1
  for: 5m
  annotations:
    summary: "Error rate > 1/sec for 5 minutes"
    
# Alert 2: Pod restart storm
- alert: PodRestartLoop
  expr: rate(kube_pod_container_status_restarts_total[1h]) > 5
  for: 5m
  
# Alert 3: Database replication lag
- alert: DatabaseReplicationLag
  expr: pg_replication_lag_seconds > 10
  for: 5m
```

### Failure Scenarios & Recovery

| Scenario | Detection | Recovery | RTO |
|---|---|---|---|
| **Pod crashes** | Liveness probe fails | Kubelet restarts pod | <1 min |
| **Database primary fails** | RDS multi-AZ health check | Failover to standby | 30 sec |
| **Network partition** | Readiness probe fails | Drain pod, reschedule | <2 min |
| **Memory leak** | Pod memory crosses limit | OOMKilled, restart | <1 min |
| **Slow database queries** | Query time > threshold | Alert ops, kill query | 10 min |
| **DDoS attack** | Request rate > 10k/sec | ALB rate limiting | Immediate |

---

## 📈 Scaling & Performance

### Horizontal Scaling

**Traffic increase scenario:**
```
Normal: 100 requests/sec (3 pods, 30 req/pod)
  ↓
Spike: 1000 requests/sec detected
  ↓
HPA triggers (CPU > 70%)
  ↓
5 minutes later: 10 pods (100 req/pod)
  ↓
Traffic processes at same latency
```

**Cost impact:** 3 pods × $50/month = $150 → 10 pods × $50/month = $500 (temporary)

### Database Bottleneck

**Symptoms:**
- Query time increases from 50ms to 500ms
- Slow log shows lock waits
- Connection pool exhausted (20/20 connections in use)

**Solutions:**
1. Add read replicas for SELECT queries
2. Cache frequently accessed data (Redis)
3. Add indexes to slow queries
4. Shard data by tenant (advanced)

### Caching Strategy

```
Request for user profile
  ↓
Check Redis (cache hit rate: 85%)
  ↓
If miss, query PostgreSQL
  ↓
Update Redis with TTL = 1 hour
  ↓
Return response (2ms vs 100ms cache miss)
```

### Canary Deployment Performance

```
Before canary: 
  v1.0: 99.5% success rate, 100ms latency

Canary (10% traffic):
  v1.0: 99.5%, 100ms
  v1.1: 99.2%, 95ms (slightly better)

Canary (50% traffic):
  v1.0: 99.5%, 100ms
  v1.1: 99.2%, 95ms (looks good)

Full deployment:
  v1.1: 99.2%, 95ms (rollout complete)
```

---

## 🛡️ Security Posture

### Authentication

```
1. User submits username/password
2. API hashes password using bcrypt (cost=12)
3. Compare hash with stored hash
4. Generate JWT token (RS256 signed)
5. Store JWT in Redis with TTL = 24 hours
6. Return JWT in Authorization header
```

### Authorization

```
Each request includes JWT:
  Header: Authorization: Bearer eyJ...

API validates:
  1. Signature is valid (using public key)
  2. Token hasn't expired
  3. Scopes include requested action
  4. Tenant ID matches (multi-tenancy enforcement)
```

### Data Isolation

```
Query pattern:
  SELECT * FROM orders 
  WHERE tenant_id = $1 AND order_id = $2

Why this matters:
  - Even if SQL injection exists, limited to one tenant
  - Row-level security enforced at DB layer
  - No cross-tenant data leaks possible
```

### Network Security

```
Ingress only from:
  - ALB security group
  - API security group

Egress only to:
  - PostgreSQL security group (port 5432)
  - Redis security group (port 6379)
  - External services (port 443 HTTPS only)

Pod-to-pod: NetworkPolicy enforces
  - API ↔ Database (PostgreSQL)
  - API ↔ Cache (Redis)
  - API ↔ Logging (CloudWatch)
  - No pod-to-pod SSH/sidecar attacks
```

### Image Security

```
Build time:
  1. Scan for vulnerabilities (Trivy)
  2. Non-root user (no sudo)
  3. Minimal base image (python:3.11-slim)
  4. No package manager in production

Runtime:
  1. Immutable container filesystem (read-only)
  2. Resource limits enforced
  3. No privilege escalation
  4. Pod Security Policy prevents bad deployments
```

---

## 📚 Key Files & Locations

- Backend: [backend/app.py](backend/app.py)
- Docker: [docker/Dockerfile](docker/Dockerfile)
- Kubernetes: [kubernetes/api-deployment.yaml](kubernetes/api-deployment.yaml)
- CI/CD: [cicd/.github-workflows-deploy.yml](cicd/.github-workflows-deploy.yml)
- AWS: [aws/infrastructure.md](aws/infrastructure.md)
- Observability: [observability/prometheus-k8s.yaml](observability/prometheus-k8s.yaml)
- Docs: [docs/decisions.md](docs/decisions.md)

See individual directories for implementation details.

---

## 🚀 Quick Start

```bash
# Local development
cd docker
docker-compose up -d

# Run migrations
docker-compose exec api flask db upgrade

# API available at http://localhost:5000
curl http://localhost:5000/health

# Kubernetes deployment
kubectl apply -f kubernetes/

# Check status
kubectl get pods
kubectl get svc
kubectl logs -f deployment/api
```

---

## 📞 Questions This Project Answers

**For Recruiters:**
- ✅ Can you build a real backend system?
- ✅ Do you understand DevOps from first principles?
- ✅ Can you explain every layer of the stack?
- ✅ Do you think about reliability, not just features?

**For Interviewers:**
- ✅ Why is multi-AZ important? (This project shows it)
- ✅ How would you scale this to 10k requests/sec? (HPA, read replicas)
- ✅ What breaks first? (Database, then API, then network)
- ✅ How do you prevent data loss? (Replication, backups, multi-AZ)

**For You:**
- ✅ Deep understanding of production systems
- ✅ Portfolio piece that stands out
- ✅ Ready to discuss architecture with peers
- ✅ Interview confidence
