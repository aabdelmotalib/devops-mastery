# Interview Preparation Notes

## Portfolio Context

This project demonstrates:
1. **Full-stack DevOps ownership** (not just infrastructure)
2. **Production-grade thinking** (not toy examples)
3. **Decision-making with trade-offs** (not just "best practice")
4. **Scalability & reliability** (the actual job)

---

## 10 Questions You Should Expect

### 1. "Why Flask? Why not FastAPI or Django?"

**What they want to hear:**
- You understand trade-offs
- Flask is the right choice for THIS project
- You considered alternatives

**Answer:**
"Flask is minimal and explicit. For a microservices future, I want lightweight, not batteries-included. FastAPI is faster, but overkill for current load. Django is feature-complete, but harder to decompose later. Flask hits the sweet spot: simple, extensible, easy to debug at every layer. If we had built Django, we'd be stuck."

**Follow-up handling:**
- "When would you use FastAPI?" → "Extreme performance needs, async workloads, automatic API docs critical"
- "When would you use Django?" → "Large monolith, admin panel needed, team lacking DevOps expertise"

---

### 2. "How would you scale this to 10x traffic?"

**What they want to hear:**
- You understand bottlenecks
- You have a scaling strategy
- You can explain database scaling (hardest part)

**Answer:**
"Three steps:
1. Horizontal pod scaling: HPA auto-scales to 20 pods. Tested to handle 10k req/sec easily.
2. Database reads: Add read replicas for analytics queries. Keeps primary for writes only.
3. Caching: More aggressive Redis caching to reduce DB load.

If database becomes bottleneck even with replicas, next step is sharding by tenant_id. But that's a 10x+ growth problem."

**Follow-up handling:**
- "How do you shard data?" → "Partition table by tenant_id, separate schema per shard"
- "Database still bottleneck?" → "DynamoDB if extreme scale (millions ops/sec), or PostgreSQL with logical replication"

---

### 3. "Your database fails. What happens?"

**What they want to hear:**
- You thought about failure modes
- You have a recovery plan
- RTO/RPO numbers

**Answer:**
"Database is Multi-AZ. If primary fails:
- RDS detects failure (30 seconds)
- Automatic failover to standby (synchronous, zero data loss)
- DNS updated (Route 53 refresh, 60 seconds)
- Total RTO: 30-60 seconds
- RPO: 0 (no data loss, synchronous replication)

During failover, API pods retry with exponential backoff. Connection pool resets. Within 2 minutes, system fully recovered."

**Follow-up handling:**
- "What if standby also fails?" → "AWS has another standby in different AZ. Or we restore from backups (RTO 15 minutes, RPO depends on backup frequency)"
- "How do you test this?" → "Chaos engineering: Terminate RDS instance during load test. Verify auto-failover"

---

### 4. "Your API is using too much memory. How do you debug?"

**What they want to hear:**
- You have debugging methodology
- You don't just throw more money at it
- You can identify memory leaks

**Answer:**
"Three approaches:
1. Prometheus metrics: Memory usage per pod, trends over time
2. Memory profiler: Run `python -m memory-profiler` locally
3. Kill largest pod, check what gets freed

Common causes: Global cache growing infinitely, connection leaks, unclosed file handles. Once identified, add circuit breaker or Redis cache with TTL."

**Follow-up handling:**
- "Code uses 512MB when limit is 1GB. Is that a problem?" → "No, but monitor growth. If trending upward, investigate."
- "How do you prevent memory leaks?" → "Code review, test locally, monitoring alerts, OWASP memory best practices"

---

### 5. "How do you deploy without downtime?"

**What they want to hear:**
- You understand blue-green deployment
- You know how to validate new version
- You have a rollback plan

**Answer:**
"Blue-green deployment:
1. New version (green) deployed alongside old (blue)
2. Both handle traffic (10% → green, 90% → blue)
3. Monitor error rate, latency for 2 minutes
4. If good, gradually shift: 50%, then 100%
5. Old version stays running (instant rollback if needed)

Health checks must pass before traffic shift. Smoke tests must succeed. If any alert, rollback automatic."

**Follow-up handling:**
- "How long does deployment take?" → "30-45 minutes total (build + test + gradual rollout)"
- "What if database migration breaks old version?" → "Migrations must be backwards-compatible. Add column in one deploy, use in next deploy"

---

### 6. "Kubernetes cost is too high. How do you reduce?"

**What they want to hear:**
- You understand cost drivers
- You prioritize impact (don't optimize logging if compute 10x worse)
- You know trade-offs

**Answer:**
"Order of impact:
1. Reserve instances (30% savings, baseline load)
2. Use Spot instances (70% cheaper, for burst)
3. Right-size instances (over-provisioned typically)
4. Optimize database (biggest cost usually)

For this project: Reserved instances save $1000/year, Spot for scaling up saves another $500/year. Logging optimization saves $1000/year. Total 42% savings without risk."

**Follow-up handling:**
- "Spot instances interrupted, how do you handle?" → "PodDisruptionBudget ensures graceful drain, requests rerouted"
- "How low can you go?" → "Single-AZ saves cost but risksDowntime. Not recommended."

---

### 7. "Walk me through a request from user to database"

**What they want to hear:**
- You understand every layer
- You can explain caching
- You think about observability

**Answer:**
"Request lifecycle:
1. User (browser) → HTTPS to Route 53 DNS
2. Route 53 returns ALB IP
3. Browser connects to ALB (TLS negotiation)
4. ALB routes to random EKS node
5. Kubernetes Ingress routes to Flask Service
6. Service load-balances to random pod
7. Flask middleware logs request (async)
8. Check Redis cache (usually hit)
9. If cache miss, query PostgreSQL
10. Return JSON, set cache with 1-hour TTL
11. ALB logs response
12. Prometheus scrapes metrics from /metrics endpoint

Latency breakdown: Browser→ALB (50ms), ALB→API (20ms), API→Cache (2ms), Cache miss→DB (50ms), Total ~122ms p99"

**Follow-up handling:**
- "Why async logging?" → "Logging synchronously adds 10ms to every request"
- "How do you cache invalidation?" → "TTL-based (simple, good enough), or event-based (user updates → delete from Redis)"

---

### 8. "Database replication lag spikes. What do you do?"

**What they want to hear:**
- You understand replication mechanics
- You can diagnose root cause
- You have solutions ranked by speed

**Answer:**
"Three-step diagnosis:
1. Check 'SHOW REPLICA STATUS' for seconds behind master
2. Check network bandwidth (AWS Console)
3. Check replica CPU/disk I/O (might be slow applying changes)

Solutions ranked by speed:
1. (5 min) Optimize replica: tune max_wal_senders, wal_keep_size
2. (15 min) Increase network throughput: placement group
3. (1 hr) Vertical scale replica: larger instance type
4. (2 hr) Add another standby: chain replication

For THIS project: Tuning is usually enough. Replica never lags > 1 second in normal operation."

**Follow-up handling:**
- "When does replication lag matter?" → "For read replicas (analytics OK with lag), not for synchronous primary-standby"
- "How do you test replication?" → "Chaos: Simulate network lag (tc command), verify application handles it"

---

### 9. "How do you ensure multi-tenant data isolation?"

**What they want to hear:**
- You think about security
- You enforce it at database level
- You understand least privilege

**Answer:**
"Three layers:
1. Application layer: Always filter by tenant_id in queries
2. Database layer: Row-level security policies enforce tenant_id
3. Network layer: NetworkPolicy limits pod communication

Most important: Database RLS. Even if attacker injects SQL, database enforces: 'SELECT * FROM orders WHERE tenant_id = attacker_tenant_id'. Different tenants never see each other's data.

Every table has tenant_id column. Every policy checks tenant_id."

**Follow-up handling:**
- "How do you test isolation?" → "Chaos engineering: Try to read other tenant's data (should fail)"
- "What if you forget tenant_id filter?" → "RLS prevents the mistake anyway"

---

### 10. "Your logging stack costs $150/month. Too expensive. What do you do?"

**What they want to hear:**
- You understand cost-benefit
- You don't just cut without understanding impact
- You prioritize wisely

**Answer:**
"Step 1: Measure what we're logging. Maybe 90% is noise.

Options:
1. Sample logs (don't log everything): 80% cost reduction
2. Switch to Loki: 70% cost reduction
3. Archive old logs to S3: 80% cost reduction
4. Combination: Error logs in CloudWatch (searchable), warnings to Loki, archives to S3 → 90% reduction

For this project: Loki + S3 archival. Cost: $37/month (vs $152). Most logs still accessible, old logs cheap."

**Follow-up handling:**
- "You need to debug production issue from 6 months ago. Is that still possible?" → "Yes, restored from S3 (cost ~$5 to retrieve)"
- "What if compliance requires 7-year retention?" → "S3 Glacier: $0.004/GB/month for long-term"

---

## How to Answer When You Don't Know

**Pattern:**
1. Admit uncertainty
2. Explain your reasoning process
3. Show what you'd investigate

**Example:**
Q: "How would you migrate to Aurora with zero downtime?"

A: "I haven't done that exact thing, but here's my approach:
1. Create Aurora cluster (same credentials)
2. Setup binary log replication from RDS to Aurora
3. Validate lag is < 5 seconds
4. Update application to read from Aurora
5. Monitor for 1 week
6. Update writes to Aurora

What I'd need to verify: AWS DMS capabilities, compatibility, exact procedure. This is something I'd pair with a senior for first time."

---

## What NOT to Say

❌ "I'm not sure" (without follow-up)
❌ "Everyone just uses Kubernetes" (no thinking)
❌ "DevOps is just Docker and Kubernetes" (reductive)
❌ "We'll optimize later" (no plan)
❌ "Single-AZ is fine" (irresponsible)
❌ "Cost doesn't matter" (not true)
❌ "Security will handle it" (shared responsibility)

---

## Best Practices to Mention

✅ "I always think about failure modes"
✅ "I measure before optimizing"
✅ "I test infrastructure changes (chaos engineering)"
✅ "I automate what repeats"
✅ "I document decisions, not just code"
✅ "I prioritize reliability over features"
✅ "I monitor proactively, not reactively"

---

## Red Flags to Address Proactively

**If you sense the interviewer thinks you overengineered:**
"I started simple (monolithic Flask, single database). Complexity added only when metrics justify it. This is architecture for 100k users. If starting from 0, would be simpler."

**If you sense they think cost doesn't matter:**
"I detailed $3k/year cost, ways to reduce 42%. Even in large orgs, cost discipline matters. It's respect for company resources."

**If you sense they think you over-relied on managed services:**
"RDS Multi-AZ is managed, yes, but I understand replication, failover, backup mechanics. Not a black box. Know how to debug when issues arise."

---

## Questions to Ask Them

These show you're serious:

1. "How many engineers on the platform team?" (Size matters for scope)
2. "What's your current incident response time?" (Shows where they struggle)
3. "Single region or multi-region?" (Strategic choice)
4. "How often do you deploy?" (Culture indicator)
5. "What's your most expensive service?" (Priorities)
6. "What's the biggest operational pain right now?" (Real problems)

---

## The Meta-Interview

They're evaluating:
- **Can you think clearly?** (Not just memorize)
- **Do you understand trade-offs?** (Not dogmatic)
- **Can you explain complex topics simply?** (Communication skill)
- **Would you be safe with production?** (Judgment, not just knowledge)
- **Would you grow into the role?** (Ambition, curiosity)

This project demonstrates all of these.

---

## Common Interviewer Patterns

**The Skeptic:**
"Why so much complexity for 3 replicas?"
→ Answer: Start simple, but built FOR scale. Not over-engineered for current size, engineered FOR future size.

**The Deep Diver:**
"Explain every line of the Kubernetes manifests"
→ Answer: Know your stuff. This is good. Shows you care.

**The Systems Thinker:**
"How does this fit into our broader platform?"
→ Answer: Great question. This is one microservice. With others, would be: service mesh, shared logging, etc.

**The Practical:**
"When would you use this vs just running on Heroku?"
→ Answer: Heroku good for MVP. At scale (100M ARR), cost/control matter. This is "after Heroku" architecture.

---

## Your Competitive Advantages

1. **You wrote production-quality docs** (most people don't)
2. **You explained WHY** (not just WHAT)
3. **You included security/cost** (shows mature thinking)
4. **You acknowledged trade-offs** (not dogmatic)
5. **You have working code** (not just diagrams)

Use these. Be confident.
