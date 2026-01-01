# Module 08: Pipeline Observability

## Architecture: Know What Your Pipeline Is Doing

Observability means you can see what happened, why it happened, and how to prevent it next time.

Without observability:
- Pipeline fails: "CI pipeline failed" (no details)
- You don't know why
- Takes 2 hours to debug
- Can't learn to prevent

With observability:
- Pipeline fails: Detailed logs, metrics, timestamps
- Root cause clear in 2 minutes
- Can fix immediately
- Prevent next time

## Three Pillars of Observability

### Pillar 1: Logs

Logs are detailed records of what happened.

```
[2024-01-15 10:05:30] Starting CI pipeline
[2024-01-15 10:05:32] Checking out code from abc123d
[2024-01-15 10:05:35] Installing dependencies (pip install)
[2024-01-15 10:05:45] Running linting
[2024-01-15 10:06:15] Linting found 3 issues in src/auth.py
[2024-01-15 10:06:15] Running unit tests
[2024-01-15 10:06:45] Tests passed (123 passed, 0 failed)
[2024-01-15 10:06:45] Running integration tests
[2024-01-15 10:07:20] Database connection failed: timeout
[2024-01-15 10:07:20] Integration tests failed
[2024-01-15 10:07:20] Pipeline failed
```

Logs answer: What happened, when, and in what order?

#### Log Levels

- **DEBUG**: Detailed information (only for debugging)
- **INFO**: General information (normal operation)
- **WARN**: Something unusual but not fatal
- **ERROR**: Something failed
- **CRITICAL**: System is broken

```
INFO: Starting test suite
DEBUG: Test 1: test_password_hash... running
DEBUG: Test 1: test_password_hash... passed
INFO: Tests completed (450 passed, 0 failed)
```

#### Log Storage

Logs must be persistent (stored after pipeline finishes).

```
CI completes → Logs saved to:
  - File storage (S3, Azure Blob)
  - Log aggregation (ELK stack, Datadog, CloudWatch)
  - Pipeline storage (GitHub/GitLab keeps logs)

Later, review logs:
  - Debugging
  - Compliance audit
  - Incident analysis
```

Retention: Keep logs for 90 days minimum, 2 years recommended.

### Pillar 2: Metrics

Metrics are numbers that measure behavior.

```
Metrics from CI pipeline:
  - Pipeline duration (5 minutes)
  - Test pass rate (450/450 passed, 100%)
  - Code coverage (84%)
  - Lines changed (250)
  - Number of stages (6)
  - Artifact size (45 MB)

Metrics from deployment:
  - Deployment duration (2 minutes)
  - Error rate after deploy (0.1%)
  - Latency p95 after deploy (120ms)
  - Instance count after deploy (3)
```

#### Tracking Metrics Over Time

```
Week 1: Pipeline duration: 5 min, coverage: 84%
Week 2: Pipeline duration: 7 min, coverage: 84%
Week 3: Pipeline duration: 8 min, coverage: 82%  (degrading)
Week 4: Pipeline duration: 10 min, coverage: 80%  (alert!)

Question: Why is pipeline getting slower and coverage dropping?
Answer: Check logs and code changes
```

#### Important Pipeline Metrics

```
1. Pipeline Duration
   - How long does the pipeline take?
   - Slow = developers wait (velocity impact)
   - Target: < 5 minutes

2. Success Rate
   - What percentage of pipelines pass?
   - Low = unstable
   - Target: > 99%

3. Test Coverage
   - What % of code is tested?
   - Low = untested code reaches production
   - Target: > 80%

4. Deployment Frequency
   - How often do you deploy?
   - High = fast iteration
   - Low = bottleneck somewhere
   - Target: Daily (or multiple times)

5. MTTR (Mean Time To Recovery)
   - When deployment breaks, how long to fix?
   - High = bad monitoring or rollback process
   - Target: < 15 minutes

6. Change Failure Rate
   - What % of changes cause incidents?
   - High = insufficient testing
   - Target: < 15%
```

### Pillar 3: Traces

Traces follow a request through the entire system.

```
Developer pushes code
  ↓ [trace ID: abc-xyz-123]
  ├── Git webhook received (log: received push)
  ├── CI pipeline started (log: pipeline begun)
  │   ├── Checkout code (duration: 5s)
  │   ├── Build (duration: 30s)
  │   ├── Unit tests (duration: 150s)
  │   ├── Integration tests (duration: 200s)
  │   └── Artifact built (log: artifact created)
  ├── Artifact pushed to registry (log: pushed)
  ├── CD deployment started (log: deployment begun)
  │   ├── Pull artifact (duration: 15s)
  │   ├── Health check (status: passing)
  │   └── Traffic switched (log: switched)
  └── Deployment complete (log: success)

Total time: 10 minutes
[trace complete]
```

Traces answer: How did this code move through the entire system?

## Audit Trails

For compliance and incident investigation, you need audit trails.

### What to Audit

```
Who changed what, when, and why?

Audit log entry:
  Timestamp: 2024-01-15 15:30:00 UTC
  User: alice@company.com
  Action: Merged pull request #1234
  Change: Added TOTP authentication
  Approval: bob@company.com approved at 15:29:30
  Reason: Reviewed and approved

Later entry:
  Timestamp: 2024-01-15 15:35:00 UTC
  User: (automation) CD system
  Action: Deployed code to production
  Version: myapp:abc123d
  Environment: production
  Approval: alice@company.com approved at 15:34:00
  Duration: 2 minutes
  Result: Success
```

Audit trails prove:
- Code was reviewed (compliance)
- Deployment was approved (governance)
- Who did what (accountability)

### Audit Storage

Must be immutable (can't be changed after creation).

```
Audit log written to:
  - AWS CloudTrail (immutable, encrypted)
  - Azure Audit Logs
  - Kubernetes audit logs
  - Git repository (commits are immutable)
  - Separate audit database

Never writable, never deletable
```

Retention: 7 years minimum (compliance).

## Monitoring Pipeline Health

### Key Indicators

```
Green (healthy):
  - Last 10 pipelines all passed
  - Pipeline duration stable
  - No security warnings
  - Test coverage stable

Yellow (warning):
  - Last pipeline failed
  - Pipeline duration increasing
  - Test coverage dropping
  - One flaky test

Red (critical):
  - Last 5 pipelines all failed
  - High failure rate
  - Security vulnerabilities found
  - Coverage dropped significantly
```

### Alerting

Alert when something goes wrong.

```
Alert rules:
  - Pipeline success rate < 90% (too many failures)
  - Pipeline duration > 15 minutes (too slow)
  - Code coverage < 75% (dropping)
  - Test failure rate > 5% (flaky tests)
  - Security scan found critical vulnerability
  - Deployment failed
  - Artifact push failed
```

Alert recipients:
- Engineering team (Slack, email)
- On-call engineer (PagerDuty for critical)
- Compliance team (for security alerts)

## Common Mistakes

### Mistake 1: No Logging

Wrong: Pipeline runs silently, no details

Problem:
- Pipeline fails: "Job failed" (no context)
- Takes hours to debug
- Can't improve

Right: Detailed logs at every stage

### Mistake 2: Logging Secrets

Wrong: Logs contain database passwords or API keys

Problem:
- Security breach
- Logs must be treated as public (they leak)

Right: Explicitly exclude secrets from logs

```bash
# BAD:
echo "Connecting to postgres://user:password@host"

# GOOD:
echo "Connecting to postgres://user:***@host"
```

### Mistake 3: No Metrics Baseline

Wrong: Pipeline takes 10 minutes, is that good or bad?

Problem:
- No way to detect degradation
- No data for optimization

Right: Track metrics over time

```
Pipeline duration:
  Week 1: 5 min (baseline)
  Week 2: 5.2 min (normal variance)
  Week 3: 6 min (slightly slower, investigate)
  Week 4: 8 min (alert! something changed)
```

### Mistake 4: Ignoring Audit Trails

Wrong: No one knows who deployed what when

Problem:
- Compliance failure (can't prove code was reviewed)
- Incident investigation is slow
- Accountability is unclear

Right: Every action logged with who/what/when/why

### Mistake 5: Logs Not Retained

Wrong: Logs deleted after 7 days

Problem:
- Can't investigate incidents from 2 weeks ago
- Compliance failure (required to keep 7 years)
- Can't learn from history

Right: Long-term log storage

## Example: Observability Stack

```
┌─ CI/CD System (GitHub Actions, GitLab CI, Jenkins)
│   └─ Logs
│   └─ Metrics
│   └─ Traces
│
├─ Log Aggregation (ELK, Datadog, CloudWatch)
│   (centralizes all logs)
│   └─ Search
│   └─ Analysis
│
├─ Metrics Storage (Prometheus, Datadog, CloudWatch)
│   (stores time-series data)
│   └─ Dashboards
│   └─ Alerting
│
├─ Tracing Backend (Jaeger, Datadog APM)
│   (tracks requests through system)
│   └─ Latency analysis
│   └─ Dependency visualization
│
├─ Audit Log Storage (S3, CloudTrail, immutable)
│   └─ Compliance queries
│   └─ Incident investigation
│
└─ Dashboard / Alerting
    (single pane of glass)
    └─ Pipeline health
    └─ Deployment status
    └─ Security alerts
```

## Example: Pipeline Observability in Practice

```yaml
name: Observable Pipeline

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Tests
        run: |
          # Start timing
          start_time=$(date +%s%N)
          
          # Run tests with detailed output
          pytest tests/ -v --tb=short
          test_result=$?
          
          # End timing
          end_time=$(date +%s%N)
          duration_ms=$((($end_time - $start_time) / 1000000))
          
          # Log metrics
          echo "METRIC test_duration_ms=$duration_ms"
          echo "METRIC test_result=$test_result"
          
          exit $test_result
      
      - name: Upload Logs
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: pipeline-logs
          path: logs/
          retention-days: 90
      
      - name: Report Metrics
        if: always()
        run: |
          # Extract metrics from step output
          # Push to monitoring system (Datadog, Prometheus, etc.)
          curl -X POST https://metrics.example.com/api/v1/metrics \
            -H "Authorization: Bearer ${{ secrets.METRICS_TOKEN }}" \
            -d '{
              "pipeline_id": "${{ github.run_id }}",
              "status": "success",
              "duration_ms": 5000,
              "commit": "${{ github.sha }}",
              "branch": "${{ github.ref }}"
            }'
      
      - name: Audit Trail
        if: always()
        run: |
          # Log audit entry
          cat > audit.json << EOF
          {
            "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
            "actor": "${{ github.actor }}",
            "action": "deployment",
            "status": "success",
            "commit": "${{ github.sha }}",
            "branch": "${{ github.ref }}",
            "details": "Deployed myapp:${{ github.sha }}"
          }
          EOF
          
          # Send to audit log storage
          aws s3 cp audit.json s3://company-audit-logs/${{ github.run_id }}/
```

---

## Practice

### Multiple Choice Questions (NO ANSWERS - Test Yourself)

1. What's the primary purpose of logging in CI/CD?
   - a) Store data for long term
   - b) Allow debugging when failures occur
   - c) Comply with regulations
   - d) All of the above

2. A metric shows pipeline duration increasing from 5 min to 12 min. What's the first step?
   - a) Optimize the slowest stage
   - b) Check logs to find what changed
   - c) Blame the test suite
   - d) Increase resources

3. Why should secrets NOT be logged?
   - a) Logs become too large
   - b) Logs might leak (are not confidential)
   - c) Secrets are slow to write
   - d) Logs are unencrypted

4. What's an audit trail?
   - a) Record of who did what, when, where, why
   - b) Automatic monitoring
   - c) Security scanning
   - d) Failure notification

5. What retention period for pipeline logs is reasonable?
   - a) 7 days
   - b) 3 months
   - c) 2 years
   - d) 7 years (compliance requirement)

### Pipeline Design Tasks

**Task 1: Design Pipeline Monitoring**
Your CI/CD has become black box. Team doesn't know:
- Why pipelines fail
- How long they take
- If coverage is improving
- If security improved

Design observability:
1. What metrics should you track?
2. What should be logged?
3. What audit information is needed?
4. How do you visualize pipeline health?

**Task 2: Create Audit Trail**
Design audit trail for this scenario:

```
Developer alice commits code
Engineer bob reviews and approves
Code is deployed to production
```

1. What audit entries would you record?
2. What information is captured?
3. Who should have access?
4. Retention period?

### Failure Scenario

**Scenario: Silent Pipeline Failure**

Your pipeline runs daily at midnight. It's automated (no human monitoring).

Pipeline fails (database connection timeout), but:
- No logs are sent to monitoring
- No alert is triggered
- No one notices

24 hours later, team discovers code never deployed.

Meanwhile:
- Code changes weren't in production
- Bugs weren't fixed in production
- Security patches weren't applied

Questions:
1. How could this failure be prevented?
2. What observability was missing?
3. What alert should have fired?
4. How do you detect silent failures?
5. How would audit logs help?

---

Next: [Module 09: CI/CD Tools Comparison](09-cicd-tools-comparison.md)
