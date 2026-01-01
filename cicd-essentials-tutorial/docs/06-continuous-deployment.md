# Module 06: Continuous Deployment

## Architecture: Deployment Strategies

Deployment is where code moves to production. It's the riskiest step. A bad deployment causes downtime, data loss, or security breach.

```
Artifact ready
    ↓
Deployment strategy choice
    ↓
Deploy to production
    ↓
Verify
    ↓
Success or Rollback
```

There are several deployment strategies. Each has trade-offs.

## Strategy 1: Big Bang Deployment

Deploy all-at-once. Old version → new version instantly.

```
Users ─ Old Service v1.0
        ↓ (deploy)
Users ─ New Service v1.1
```

**Timeline:**
- t=0: Deploy artifact
- t=5 min: Rollout complete
- t=5+ min: Any bugs appear to all users

**Pros:**
- Fast
- Simple

**Cons:**
- Any bug affects 100% of users
- High blast radius
- No recovery path (must rollback, takes time)

**Risk: HIGH**

Not recommended for production. Too risky.

## Strategy 2: Blue-Green Deployment

Run two identical production environments. Switch traffic between them.

```
Blue (v1.0):    Users ──→ Blue Service v1.0 (production)
Green (v1.1):   (idle)   Green Service v1.1 (staging-like)

Deploy v1.1 to Green
Test Green fully
Verify Green is healthy
  ↓
Switch traffic (one command)
  ↓
Users ──→ Green Service v1.1 (now production)
Blue (v1.0 stays running, ready for rollback)
```

**Timeline:**
- t=0: Deploy to green, run full tests
- t=15 min: Green verified healthy
- t=15+ min: Switch traffic (instantaneous)
- t=16 min: v1.1 in production, v1.0 still running

**Pros:**
- Instant rollback (switch traffic back to blue)
- Full environment verification before production
- No downtime
- Can keep both versions running for gradual cutover

**Cons:**
- Need 2x infrastructure (cost)
- Need to synchronize database/state between blue/green
- Must manage traffic switch

**Risk: MEDIUM**

Good for critical systems. Gold standard for zero-downtime deploys.

## Strategy 3: Canary Deployment

Deploy new version to small percentage of users first. Monitor. Gradually increase.

```
Users split:
  90% → Old Service v1.0
  10% → New Service v1.1 (canary)

Monitor metrics:
  Errors: v1.0 = 0.1%, v1.1 = 0.5% (higher!)
  Latency: v1.0 = 50ms, v1.1 = 45ms (good)

Decision: Continue, but monitor closely

  50% → v1.0
  50% → v1.1

Wait 10 minutes, check metrics

  10% → v1.0
  90% → v1.1

If any issues appear, rollback to 100% v1.0
```

**Timeline:**
- t=0: Deploy v1.1 to 10% of users
- t=5 min: Monitor, no issues
- t=10 min: 50% traffic shift
- t=20 min: 100% on v1.1

**Pros:**
- Limited blast radius (bug hits 10%, not 100%)
- Real user metrics (not synthetic tests)
- Rollback available at any step
- Gradual traffic shift catches edge cases

**Cons:**
- Slower (takes 20-30 minutes)
- Need sophisticated traffic routing
- Must have monitoring (can't rollback blind)

**Risk: LOW**

Best for large-scale systems. Catches issues that staging testing misses.

## Strategy 4: Rolling Deployment

Gradually replace old instances with new ones.

```
Version v1.0: Instance 1, 2, 3, 4

Deploy v1.1:
  Stop instance 1 → Start instance 1 (v1.1)
  Wait for health check
  Stop instance 2 → Start instance 2 (v1.1)
  Wait for health check
  ...

Eventually:
  All instances running v1.1
  Old version gone
  Users experienced no downtime (routed to other instances)
```

**Timeline:**
- Instance 1 deployed: 2 min
- Instance 2 deployed: 2 min
- Instance 3 deployed: 2 min
- Instance 4 deployed: 2 min
- Total: 8 minutes for full rollout

**Pros:**
- Gradual rollout
- Always have capacity (don't stop all at once)
- Works well with auto-scaling

**Cons:**
- Slow (one instance at a time)
- If bug exists, you gradually roll it to all instances
- Can't do instant rollback (old code is gone)

**Risk: MEDIUM**

Good for microservices. Works well with Kubernetes.

## Strategy 5: Feature Flags / Dark Deployments

Deploy code to production, but disable new feature with a flag.

```
Code deployed: v1.1 (has new feature, feature-disabled)
  Old UI path: uses old code path (works)
  New UI path: feature disabled (shows old version)

Enable feature flag for internal staff first:
  Internal tests (feature enabled)

If good, enable for 10% users:
  10% see new feature

If metrics good, enable for 100%:
  Feature is live
```

**Timeline:**
- t=0: Deploy code with flag off
- t=5 min: Internal testing
- t=20 min: Rollout to 10%
- t=40 min: Rollout to 100%

**Pros:**
- Deploy code without releasing feature
- Easy to toggle on/off
- No infrastructure duplication needed
- Fastest iteration

**Cons:**
- Requires feature flag infrastructure (complexity)
- Must maintain old code paths alongside new
- Flag cleanup (technical debt)

**Risk: LOW**

Modern approach. Used by tech companies at scale.

## Environment Promotion

Code flows through environments before production.

```
Development
    ↓
Staging
    ↓
Production
```

**Development:**
- Write code
- Unit tests
- Local testing

**Staging:**
- Same as production (same config, database type, etc.)
- Integration tests against real-like systems
- Performance testing
- Manual testing
- Security scanning
- Smoke tests

**Production:**
- Real users
- Real data
- Real load

### Staging vs Production Parity

Staging MUST match production. Otherwise staging tests don't apply.

```
Bad (staging != production):
  Staging: single server
  Production: 50 servers with load balancing
  Result: Code works in staging, fails under load in production

Good (staging = production):
  Staging: 2 servers with load balancing, same config
  Production: 50 servers with load balancing, same config
  Result: If code works in staging, it works in production
```

### Approval Gates

Between environments, add approval gates.

```
Code passes CI
    ↓
Deploy to staging
    ↓
Run staging tests
    ↓
Manual approval (product/engineering)
    ↓
Deploy to production
```

Approval might be:
- Automatic (if all tests pass)
- Manual (human click button)
- Time-based (deploy during business hours only)

## Rollback

When something goes wrong, rollback to previous version.

### Instant Rollback (Blue-Green)

```
Green (v1.1) with bug
    ↓
Switch traffic back to Blue (v1.0)
    ↓
Issue resolved (instant)
```

Time: <1 minute

### Artifact-Based Rollback

```
Current: myapp:v1.1 (has bug)
    ↓
Deploy: myapp:v1.0 (previous version)
    ↓
Issue resolved
```

Time: 2-5 minutes (rebuild might be needed)

### Data Rollback

Sometimes code is fine, but data is corrupted.

```
Corrupted data
    ↓
Restore backup
    ↓
Replay transactions (if possible)
    ↓
Data consistent
```

Time: 15 minutes to hours (depends on backup size)

### Important: Test Rollback

You must practice rollback. It shouldn't be a surprise.

```
Every month, actually rollback to previous version.
Verify it works.
Rollback again to current version.
```

This tests:
- Your rollback procedure works
- Data migrations are reversible
- Backup/restore works

Never trust untested rollback.

## Monitoring and Validation

After deployment, you MUST validate it worked.

### Smoke Tests

Quick tests that basic functionality works.

```bash
# After deployment to production
curl https://api.example.com/health
# Should return 200 OK

curl -X POST https://api.example.com/api/users \
  -d '{"name":"test"}' \
  -H "Content-Type: application/json"
# Should return 201

curl https://api.example.com/api/users
# Should return list of users
```

### Metrics Validation

Does the new version behave correctly under real load?

```
Metrics before deployment (baseline):
  Error rate: 0.05%
  Latency p95: 150ms
  CPU: 45%

After deployment:
  Error rate: 0.08% (slightly higher, but acceptable)
  Latency p95: 140ms (better)
  CPU: 50% (slightly higher, acceptable)

Result: Deployment is good, metrics are acceptable
```

vs

```
After deployment:
  Error rate: 2% (CRITICAL - 40x higher)
  → Rollback immediately
```

### Alerting

Alert on anomalies after deployment.

```
Alert: Error rate > 1% (5x baseline)
Alert: Latency p95 > 500ms (3x baseline)
Alert: CPU > 80%
Alert: Memory > 90%
Alert: Database connections exhausted
```

## Common Mistakes

### Mistake 1: No Rollback Plan

Wrong: "We've never had to rollback, so we don't plan for it"

Problem:
- When disaster happens, rollback is ad-hoc
- Takes 2+ hours to recover
- Errors during rollback make it worse

Right: Rollback procedure is tested monthly

### Mistake 2: Staging Doesn't Match Production

Wrong: Staging is a single server, production is 50 servers

Problem:
- Staging tests don't apply to production
- Load-related bugs aren't caught
- Crashes in production but not staging

Right: Staging is smaller but architecturally identical

### Mistake 3: Deploying Without Validation

Wrong: Deploy code, assume it works

Problem:
- Bugs reach real users
- No data to rollback decision
- Slow detection (users report issues)

Right: Deploy, run smoke tests, monitor metrics

### Mistake 4: No Approval Gate for Production

Wrong: Code in staging automatically deploys to production

Problem:
- No human oversight
- Untested code reaches users
- Compliance failure (regulated industries need approval)

Right: Manual approval between staging and production

### Mistake 5: Deploying During Peak Traffic

Wrong: Deploy at 2 PM on Monday (peak traffic)

Problem:
- New version immediately under load
- Bugs amplified by high load
- Blast radius larger (more users affected)

Right: Deploy during low-traffic window (midnight, weekend)

## Example: Production Deployment

**Scenario:** Deploying payment service v2.1.0

```
Friday 11 PM (low traffic)

1. Deploy to canary (5% users)
   docker run paymentapp:v2.1.0 --traffic=5%
   
2. Monitor for 5 minutes
   Errors: 0.1% (normal)
   Latency: 120ms (normal)
   
3. Expand to 50%
   docker run paymentapp:v2.1.0 --traffic=50%
   
4. Monitor for 10 minutes
   Errors: 0.08% (normal)
   Latency: 125ms (normal)
   
5. Expand to 100%
   docker run paymentapp:v2.1.0 --traffic=100%
   
6. Monitor for 15 minutes
   All metrics normal
   
7. Declare success
   v2.1.0 is now production
   Old version v2.0.9 kept for rollback
   
   If something goes wrong:
   docker run paymentapp:v2.0.9 --traffic=100%
   (instant rollback)
```

---

## Practice

### Multiple Choice Questions (NO ANSWERS - Test Yourself)

1. You need to deploy new code to production with zero downtime. Which strategy?
   - a) Big bang deployment
   - b) Blue-green deployment
   - c) Rolling deployment
   - d) Both b and c

2. Blue-green deployment requires what?
   - a) Two identical production environments
   - b) Traffic router (load balancer)
   - c) Quick rollback capability
   - d) All of the above

3. Canary deployment deploys to what percentage initially?
   - a) 1%
   - b) 5-10%
   - c) 50%
   - d) 100%

4. What's the purpose of smoke tests after deployment?
   - a) Verify basic functionality works
   - b) Ensure it's safe to keep deployment
   - c) Catch obvious bugs before users find them
   - d) All of the above

5. When should you rollback a deployment?
   - a) If any test fails
   - b) If error rate doubles
   - c) If metrics show problems
   - d) Only if user reports issues

### Pipeline Design Tasks

**Task 1: Design Deployment Strategy**
You're deploying a customer-facing API. Downtime costs $10,000/minute. Choose deployment strategy:

1. What strategy would you use?
2. How long does rollout take?
3. What's the blast radius if bug is found?
4. How do you validate each stage?

**Task 2: Staging Environment Design**
You're designing staging for a microservices system:
- 10 microservices
- Each has different scaling needs
- Peak production load is 1000 req/sec

Design staging:
1. How many replicas of each service?
2. Should staging have same load as production?
3. What database setup?
4. How do you verify production parity?

### Failure Scenario

**Scenario: The Canary That Wasn't**

You deploy v1.5.0 using canary strategy:
- 5% to canary
- Monitor 5 minutes
- Expand to 50%
- Monitor 10 minutes
- Expand to 100%

At t=3 minutes (canary stage), metrics look normal. Expand to 50%.

At t=18 minutes (50% deployed):
- Edge case bug manifests (only under 50%+ load)
- Error rate spikes to 15%
- But you already deployed to half the users

Questions:
1. Why didn't canary (5%) catch this?
2. What would have caught it?
3. How long to rollback now?
4. How do you prevent this?
5. Is canary deployment a good strategy or bad design?

---

Next: [Module 07: Infrastructure as Code](07-infrastructure-as-code.md)
