# Module 10: Failure & Recovery

## Architecture: Assume Everything Fails

Murphy's Law applies to CI/CD: "Anything that can go wrong will go wrong."

Your system must:
1. Detect failures quickly
2. Alert the right people
3. Enable fast recovery
4. Learn from the failure

```
Failure happens
    ↓
System detects (monitoring)
    ↓
Team is alerted
    ↓
Team responds
    ↓
System recovered
    ↓
Incident analyzed
    ↓
Process improved
```

## Types of Failures

### Failure 1: Build Failures

Code is broken (doesn't compile, syntax error, missing dependency).

```
Developer pushes code
    ↓
CI: Try to compile
    ↓
FAIL: Syntax error in src/auth.py
    ↓
Developer is notified
    ↓
Developer fixes
    ↓
CI passes
```

**Recovery:** Developer must fix code. Pipeline caught it (working as designed).

**Time to recovery:** 5-30 minutes (depends on dev availability)

### Failure 2: Test Failures

Code compiles but tests fail.

```
Code compiles successfully
    ↓
CI: Run unit tests
    ↓
FAIL: test_password_validation fails
    ↓
Developer is notified
    ↓
Developer debugs (wrong regex in validator)
    ↓
Developer fixes
    ↓
Tests pass
```

**Recovery:** Developer debugs and fixes.

**Time to recovery:** 15 minutes to 1 hour (depends on test clarity)

### Failure 3: Flaky Tests

Tests pass sometimes, fail sometimes (non-deterministic).

```
CI Run 1: All tests pass
CI Run 2: Integration test times out
CI Run 3: All tests pass
CI Run 4: Same integration test times out

Pattern: Database query sometimes slow
Root: Test database isn't isolated, other tests run in parallel
```

**Recovery:** Fix test (make deterministic) or increase timeout with investigation.

**Time to recovery:** 1-3 hours (takes debugging to understand)

**Risk:** Team starts ignoring test failures ("it's just flaky again")

### Failure 4: Artifact Build Failures

Tests pass, but artifact building fails.

```
Tests: PASS
    ↓
Docker build: FAIL
Error: Cannot find base image (registry down?)
    ↓
Artifact not created
    ↓
Can't deploy
```

**Recovery:** Wait for registry to recover, retry build.

**Time to recovery:** 5-30 minutes (depends on external service)

### Failure 5: Deployment Failures

Artifact is good, but deployment fails.

```
Artifact created: myapp:abc123d
    ↓
Deploy to staging: Start pulling image
    ↓
FAIL: Kubernetes cluster is down
    ↓
Or: Image corrupted, pull fails
    ↓
Or: Database migration fails
```

**Recovery:** Fix underlying issue, retry deployment.

**Time to recovery:** 15 minutes to hours (depends on complexity)

### Failure 6: Post-Deployment Failures

Deployment succeeds but application fails.

```
Deployment completes
    ↓
Smoke tests pass
    ↓
5 minutes later: Application crashes
    ↓
Error: Memory leak, OOM after 5 min under load
    ↓
Production is down
```

**Recovery:** Rollback to previous version immediately.

**Time to recovery:** 2-5 minutes (automated rollback)

### Failure 7: Infrastructure Failures

Infrastructure breaks or changes unexpectedly.

```
Terraform code: database is db.t3.micro
Actual AWS: db.r5.large (manually changed)
Terraform apply reverts to t3.micro
Database is undersized
Application crashes
```

**Recovery:** Fix infrastructure (either accept the manual change or revert to code)

**Time to recovery:** 5-15 minutes (depends on drift detection)

### Failure 8: Security Breaches

Code has vulnerability or secrets are exposed.

```
Code deployed to production with SQL injection
Attacker discovers and exploits
Data breached
```

Or:

```
Database password hardcoded in code
Code pushed to public GitHub
Attacker accesses database
```

**Recovery:** Hotfix + deploy (fast) + rotate credentials + audit

**Time to recovery:** 15 minutes to hours (depends on detection speed)

## Failure Detection

### Real-Time Monitoring

```
Application running
    ↓
Metrics collected continuously:
  - Error rate (# errors / total requests)
  - Latency (how long requests take)
  - CPU usage
  - Memory usage
  - Disk space
    ↓
Alerts defined:
  - Error rate > 1% → alert
  - Latency p95 > 500ms → alert
  - CPU > 80% → alert
    ↓
Error rate spikes to 5%
    ↓
Alert triggered immediately
    ↓
Team notified (Slack, PagerDuty)
```

### Health Checks

Automated checks that application is healthy:

```bash
# Simple HTTP check
curl https://api.example.com/health
# Expected: 200 OK

# Database check
curl https://api.example.com/health/db
# Expected: 200 OK (database is responsive)

# Cache check
curl https://api.example.com/health/cache
# Expected: 200 OK (cache is responsive)

# If any check fails → alert
```

### Log Analysis

Automated analysis of logs for error patterns:

```
Logs scanned continuously:
  - "OutOfMemoryError" → alert
  - "Database connection timeout" × 10 in 1 minute → alert
  - "Authentication failure" × 100 in 1 minute → alert (brute force?)
  - Stack trace patterns → alert
```

## Rollback

When deployment fails, rollback to previous version.

### Instant Rollback (Blue-Green)

```
Green (v1.1) has bug
    ↓
Switch traffic back to Blue (v1.0)
    ↓
Time: <1 minute
```

### Artifact Rollback

```
Current: myapp:v1.1 (bad)
    ↓
Get previous artifact: myapp:v1.0
    ↓
Pull artifact, start containers
    ↓
Verify health
    ↓
Time: 2-5 minutes
```

### Database Rollback

If code doesn't work, sometimes data is also corrupted.

```
Code deploys v1.1
Database migration runs
Migration has bug (loses data)
Rollback code to v1.0
But data is already changed

Problem: Rolling back code doesn't roll back data
```

**Solution:** Database migrations must be reversible.

```sql
-- Forward migration (up)
CREATE TABLE users (id INT, name VARCHAR(255));

-- Reverse migration (down)
DROP TABLE users;
```

When you rollback:
1. Rollback code
2. Run database rollback script
3. Data and code are now consistent

### Zero-Loss Rollback Pattern

Design migrations so rollback never loses data:

```sql
-- Deploy v1.1: Add new column (backward compatible)
ALTER TABLE users ADD COLUMN email VARCHAR(255);

-- App can use old code OR new code (both work)
-- No data loss

-- Deploy v1.2: Populate new column
UPDATE users SET email = ...;

-- Now email is filled

-- If we rollback to v1.0 (before email), old code just ignores email column
-- No data loss
```

vs

```sql
-- Bad: Remove column immediately
ALTER TABLE users DROP COLUMN username;  -- Old code expects this!

-- Rollback: Column is gone, can't restore
-- Data loss
```

## Incident Response

When production fails, follow a procedure:

### Phase 1: Detect (0-5 minutes)

Monitoring detects failure.
Alert is sent to team.

### Phase 2: Respond (5-15 minutes)

On-call engineer:
1. Receives alert
2. Understands what's broken
3. Decides: Is rollback needed?

```
If obvious bad deployment:
  → Immediate rollback

If unclear:
  → Page senior engineer
  → Investigate logs
  → Decide action
```

### Phase 3: Recover (5-30 minutes)

Execute recovery:

```
Option A: Rollback
  - Click "rollback"
  - Wait for deployment
  - Verify health
  - Time: 5 minutes

Option B: Hotfix
  - Write fix
  - CI/CD builds and tests
  - Deploy fix
  - Verify health
  - Time: 15-30 minutes

Option A is faster (usually chosen)
Option B chosen only if rollback isn't possible
```

### Phase 4: Stabilize (30-60 minutes)

Ensure system is stable:

```
1. Monitor metrics (error rate, latency, CPU)
2. Wait 15 minutes to confirm stability
3. Declare incident resolved
4. Notify stakeholders
```

### Phase 5: Investigate (1-24 hours)

Conduct incident post-mortem:

```
Questions:
  - What happened?
  - Why did it happen?
  - Why wasn't it caught by CI/CD?
  - How do we prevent next time?

Example answers:
  - Code had edge case bug (only manifests under load)
  - Staging didn't have same load as production
  - Monitoring didn't alert early enough
  - Rollback was manual instead of automated

Actions:
  - Add test for edge case
  - Improve load testing in staging
  - Add metric alerts
  - Automate rollback
```

## Disaster Recovery

Worst case: Production data is corrupted or lost.

### Backup Strategy

```
Backups taken:
  - Hourly (keep 24 hours)
  - Daily (keep 30 days)
  - Weekly (keep 1 year)

Backup locations:
  - Primary region (local)
  - Secondary region (geographic redundancy)
  - Off-site storage (for compliance)

Backup testing:
  - Monthly: Restore backup to staging
  - Verify data integrity
  - Verify restore process works

Recovery time objective (RTO): 4 hours
Recovery point objective (RPO): 1 hour (accept up to 1 hour of data loss)
```

### Disaster Scenario

```
Data corruption: Random data gets deleted
    ↓
Discovered: "Users are missing from database"
    ↓
Immediate action:
  1. Stop accepting writes
  2. Create backup (snapshot current state)
  3. Identify corruption time (when did it start?)
    ↓
  4. Restore backup from before corruption
  5. Restore data to t=corruption_time - 1 hour
    ↓
  6. Accept data loss from last hour
  7. Notify affected users
  8. Restart accepting writes
    ↓
Recovery time: 2 hours
Data loss: 1 hour of changes
```

## Common Failures and Prevention

### Failure 1: Flaky Tests

**Symptom:** Tests pass/fail randomly

**Prevention:**
- Tests must be deterministic
- Isolate test data (no shared state)
- Use timeouts appropriately
- Mock external services

### Failure 2: Slow Pipeline

**Symptom:** Pipeline takes 45+ minutes

**Prevention:**
- Parallelize stages
- Optimize tests (remove slow tests, mock I/O)
- Cache dependencies
- Use efficient build tools

### Failure 3: Failed Deployments

**Symptom:** Code doesn't start after deployment

**Prevention:**
- Smoke tests after deployment
- Health checks in application
- Gradual rollout (canary, blue-green)
- Automated rollback on failure

### Failure 4: Secrets Exposed

**Symptom:** Database password in logs or Git

**Prevention:**
- Secret scanning in CI
- Never log secrets
- Store secrets in secure manager
- Rotate secrets regularly
- Audit secret access

### Failure 5: Infrastructure Drift

**Symptom:** Code says t3.micro, actual is t3.large

**Prevention:**
- Daily drift detection
- Enforce Infrastructure as Code
- Version control infrastructure changes
- Code review for infrastructure

## Common Mistakes

### Mistake 1: No Rollback Plan

Wrong: "We've never had to rollback, so we don't need a plan"

Problem:
- When failure happens, rollback is ad-hoc
- Takes hours instead of minutes
- Errors during rollback

Right: Practice rollback monthly

### Mistake 2: Ignoring Warnings

Wrong: "CPU is at 75%, but it's been fine before"

Problem:
- Next spike, CPU hits 100% and crashes
- Could have prevented by scaling

Right: Alert at 75%, investigate, plan scaling

### Mistake 3: Manual Rollback

Wrong: "On-call engineer manually deletes pods, restarts services"

Problem:
- Slow (5+ minutes)
- Error-prone
- Depends on engineer expertise

Right: Automated rollback (click button, it happens)

### Mistake 4: No Incident Post-Mortem

Wrong: "We fixed it, let's move on"

Problem:
- Same issue happens again
- Team doesn't learn
- No systemic improvement

Right: Every incident → post-mortem → action items

### Mistake 5: Untested Disaster Recovery

Wrong: "We have backup procedures documented"

Problem:
- Disaster happens: procedures don't work
- Backups are corrupted
- Data loss

Right: Monthly: Test backup restore fully

## Example: Real Incident

**Timeline**

```
2024-01-15 14:00
  Deploy v1.5.0 to production (canary: 5%)

14:05
  Monitoring alerts: error rate 2% (normal is 0.1%)
  Wait 5 minutes to see if passes

14:10
  Error rate still 2%
  Check logs: "Database connection timeout"

14:12
  Investigate: v1.5.0 creates 10x more DB connections
  Code change: Added connection pooling (buggy)

14:13
  Decision: Rollback immediately
  Execute: docker switch --from v1.5.0 --to v1.4.9

14:15
  New version running: error rate drops to 0.1%
  Production healthy

14:20
  Post-mortem begins:
    - Bug: Connection pooling misconfigured
    - Why not caught: No load testing in staging
    - Why not detected earlier: Only 5% in canary (too few users to trigger)
    - How to prevent:
      1. Add connection pool load test
      2. Increase canary to 20% (more users = faster detection)
      3. Add alert for DB connections

14:30
  Post-mortem ends
  Action items created (fix, test, deploy)

Next day:
  Connection pool bug fixed
  Load test added to CI
  Code review approval: pass
  Deployed in new canary (20% now)
  Monitors closely, gradually to 100%

Result:
  - Incident duration: 15 minutes
  - Data loss: 0
  - User impact: ~1000 affected (5% of users, 15 min)
  - Cost: ~$5,000 in lost revenue
  - Prevention: $0 (just code fixes + tests)

Lesson: The 15-minute incident saved us from repeated 15-minute incidents.
```

---

## Practice

### Multiple Choice Questions (NO ANSWERS - Test Yourself)

1. What's the first action when production is failing?
   - a) Investigate logs
   - b) Alert the team
   - c) Decide: rollback or hotfix?
   - d) Deploy a fix immediately

2. Why is rollback faster than hotfix?
   - a) Rollback doesn't need testing
   - b) Rollback uses already-tested artifact
   - c) Rollback requires no human code review
   - d) All of the above

3. When should you test disaster recovery?
   - a) Only when disaster happens
   - b) Before production
   - c) Monthly (practice drill)
   - d) Annual compliance requirement

4. What's a post-mortem?
   - a) After-incident blame assignment
   - b) Root cause analysis + action items
   - c) A time to yell at engineers
   - d) Optional documentation

5. Why are flaky tests dangerous?
   - a) They slow down CI
   - b) Team ignores failures (safety signal is broken)
   - c) Hard to debug
   - d) Both a and c

### Pipeline Design Tasks

**Task 1: Design Incident Response**
Production deployment fails. Design the response:

1. How is failure detected?
2. Who is alerted and how?
3. What's the first decision tree?
4. How do you rollback?
5. What's the post-incident process?

**Task 2: Design Disaster Recovery**
You have 1 million users, database is 500GB, in AWS.

Design recovery plan:
1. Where are backups stored?
2. How often are they taken?
3. How long to restore?
4. How much data loss is acceptable?
5. How often do you test?

### Failure Scenario

**Scenario: Cascading Failures**

Timeline:
- 14:00: Deploy v1.5.0 to 10% (canary)
- 14:03: No alerts (canary users don't trigger bug)
- 14:05: Expand to 50%
- 14:07: Database crashes (overload from buggy code)
- 14:08: Database recovery takes 10 minutes
- 14:18: Database is back, but 50% of production is on broken code
- 14:19: Data corruption detected (bad data written during crash)

Now you must:
1. Rollback broken code (5 min)
2. Restore database from backup (15 min)

But options are:
- Restore to 14:00 (lose 20 min of data)
- Restore to 14:07 (corrupted data partially applied)

Questions:
1. What went wrong (multi-part failure)?
2. How was each step preventable?
3. What monitoring would have helped?
4. What's the actual recovery plan?
5. How do you communicate to users?

---

Next: [Final Project: Build a Production CI/CD System](final-project.md)
