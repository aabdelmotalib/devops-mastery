# Module 7: Alerting & Incident Response

Alerts bridge observability and action. This module covers defining alerts, responding to incidents, and improving response workflows.

## SLO/SLI Framework

### Defining Service Level Objectives (SLO)

An SLO is a target for how well a service should perform:

```
API Service SLO:
- Availability: 99.9% (9 hours downtime per month allowed)
- Latency: p95 < 500ms
- Error rate: < 0.1%
```

### Service Level Indicators (SLI)

Measurements that show if SLO is met:

```
SLI for Availability:
(successful_requests) / (total_requests) >= 0.999

SLI for Latency:
percentile(request_duration, 95) < 500ms

SLI for Error Rate:
(failed_requests) / (total_requests) < 0.001
```

### Error Budget

If SLO is 99.9%, you get an error budget:

```
30-day month: 43,200 minutes
SLO: 99.9%
Allowed downtime: 43,200 × 0.1% = 43.2 minutes

Actual incidents this month:
- 2024-01-05: 15 minutes (database failover)
- 2024-01-12: 10 minutes (deployment issue)
- 2024-01-20: 5 minutes (cache failure)
Total: 30 minutes

Remaining budget: 43.2 - 30 = 13.2 minutes

Can take ONE more incident before SLO breach
→ Be conservative with changes near end of month
```

## Alert Design

### Designing Good Alerts

**Must be**:
- Actionable (tells operator what to do)
- Timely (fires when action matters)
- Reliable (low false positive rate)
- Specific (identifies root cause clearly)

**Example**:
```
Good: "API latency p95 > 2s for 5 minutes → Check database query logs"
Bad: "API slow"

Good: "Payment processor 500 errors > 10/min → Check payment API status"
Bad: "High error rate"
```

### Alert Severity Levels

**P1 (Critical)**: Service unavailable or data loss
- Action: Page on-call immediately
- Target response: < 5 minutes
- Example: API returns 500 errors

**P2 (High)**: Significant degradation
- Action: Alert team, start mitigation
- Target response: < 15 minutes
- Example: Error rate 5%, latency spiking

**P3 (Medium)**: Minor issues
- Action: Create ticket
- Target response: < 1 hour
- Example: One non-critical feature broken

**P4 (Low)**: Information only
- Action: Log for analysis
- No immediate response required
- Example: Unusual pattern detected

### Alert Thresholds

```
Critical threshold:
error_rate > 5%         # Service severely broken
availability < 95%      # Continuous failures
latency_p95 > 5s        # Very slow

Warning threshold:
error_rate > 1%         # Unusual
availability < 99.5%    # Minor issues
latency_p95 > 2s        # Slower than normal

Info threshold:
error_rate > 0.1%       # Track anomalies
availability < 99.9%    # Monitor
latency_p95 > 1s        # Baseline
```

## Alert Fatigue Prevention

### Root Cause Alerts (not Symptom Alerts)

**Bad**: Alert on symptom
```
Condition: Latency > 1s for 1 minute
Result: Fires 100x per day (noisy)
```

**Good**: Alert on root cause
```
Conditions: 
  - Slow database query + Database query time > 1s
  - And database utilization > 80%
Result: Fires when action matters (root cause clear)
```

### Composite Alerts

```
APIHealth = (error_rate < 1%) AND (latency_p95 < 500ms)

Only alert when API is actually unhealthy,
not just on individual metrics drifting
```

### Alert Deduplication

Don't alert multiple times for same issue:

```
Alert: DatabaseDown
Fires at 14:32 → Page on-call
At 14:35: Still down → DON'T alert again
At 14:42: Recovered → Send "Resolved" notification

Deduplicate within 15 minute window
```

## Incident Response Workflow

### Incident Severity Classification

```
Severity 1: Complete outage
  - Customer impact: All users
  - Page: All on-call staff
  - Target resolution: < 15 minutes

Severity 2: Partial degradation
  - Customer impact: Some users
  - Page: Primary on-call
  - Target resolution: < 1 hour

Severity 3: Minor issue
  - Customer impact: Few users
  - Notify: Team slack channel
  - Target resolution: < 4 hours

Severity 4: Bug, no immediate impact
  - Create ticket only
  - Schedule for next sprint
```

### Incident Command Structure

```
Incident Commander: Coordinates response
  ├─ Engineering Lead: Investigates root cause
  ├─ Operations Lead: Executes remediation
  └─ Communications Lead: Updates status page
```

### Incident Timeline Template

```
14:32 - Alert fires: "API error rate > 5%"
14:33 - On-call engineer assigned
14:35 - Initial investigation: "Database connection pool exhausted"
14:40 - Root cause found: "New deployment has connection leak"
14:42 - Remediation: Rolled back deployment
14:43 - Service recovered, error rate returning to normal
14:45 - Incident resolved, all metrics normal

Post-incident: Review tomorrow at 10am
```

## Creating Runbooks

Every alert should have a runbook:

```markdown
# Alert: Database Connection Pool Exhausted

## Symptoms
- API returns "database unavailable" errors
- Database connection count > 90% of max
- Alert fires: db_connections > 450

## Immediate Actions (First 5 minutes)
1. Check current connection count: `SELECT count(*) FROM pg_stat_activity;`
2. Check slow queries: `SELECT pid, query, query_start FROM pg_stat_activity WHERE state != 'idle';`
3. Kill idle connections: `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND query_start < now() - '10 minutes'::interval;`

## Root Cause Investigation
- [ ] Check application logs for connection pool errors
- [ ] Check for recent code deployments
- [ ] Check database slow query log
- [ ] Check for unusual traffic spike

## Mitigation Options (in order of preference)
1. Increase application connection pool size (config change, no restart)
2. Increase database max_connections (requires restart)
3. Kill non-essential connections
4. Redirect traffic to standby database

## Prevention
- Monitor connection pool usage continuously
- Set alert at 70% utilization (early warning)
- Load test before major deployments
- Review connection pool settings quarterly
```

## Alerting Tools Integration

### Grafana Alerting

```yaml
groups:
  - name: api_alerts
    interval: 1m
    rules:
      - alert: HighErrorRate
        expr: |
          (sum by (job) (rate(http_requests_total{status=~"5.."}[5m])) /
           sum by (job) (rate(http_requests_total[5m]))) > 0.05
        for: 5m
        annotations:
          summary: "High error rate on {{ $labels.job }}"
          description: "Error rate is {{ $value | humanizePercentage }}"
        labels:
          severity: critical
```

### Slack Integration

```python
import requests

def send_slack_alert(channel, title, message, severity):
    color = {'critical': 'danger', 'warning': 'warning', 'info': 'good'}[severity]
    
    payload = {
        'channel': channel,
        'attachments': [{
            'color': color,
            'title': title,
            'text': message,
            'fields': [
                {'title': 'Severity', 'value': severity},
                {'title': 'Timestamp', 'value': datetime.utcnow().isoformat()}
            ]
        }]
    }
    
    requests.post(SLACK_WEBHOOK_URL, json=payload)

# On alert
send_slack_alert('#alerts-prod', 'API Error Rate High', 
                'Error rate 8% for 5 minutes. Check database.', 'critical')
```

### PagerDuty Integration

```python
from pdpyras import APISession

session = APISession(token=PAGERDUTY_TOKEN)

incident = session.post('/incidents', json={
    'incident': {
        'type': 'incident',
        'title': 'API Error Rate Critical',
        'body': {
            'type': 'incident_body',
            'description': 'Error rate exceeded 5% threshold'
        },
        'escalation_policy': {
            'id': ESCALATION_POLICY_ID,
            'type': 'escalation_policy_reference'
        },
        'urgency': 'high'
    }
})
```

## Post-Incident Review

Every incident needs analysis:

```markdown
# Incident Review: Database Connection Exhaustion

## Summary
Deployment with connection pool leak caused database unavailability.
Duration: 13 minutes
Severity: P1 (Complete outage)

## Timeline
- 14:32: Alert fires
- 14:40: Root cause identified (connection leak in new code)
- 14:42: Deployment rolled back
- 14:45: Recovered

## Root Cause Analysis
Application code opened database connections but didn't properly close them.
New code added in deployment but not tested under load.

## Contributing Factors
1. No load testing before deploy to production
2. Connection leak not detected in staging (low traffic)
3. Alert only fires when already critical (< 5 min margin)

## Action Items
1. Add connection pool monitoring dashboard (SRE)
2. Implement load testing in CI/CD pipeline (Dev)
3. Alert at 70% connection usage instead of 90% (SRE)
4. Code review checklist item: "Close all resources" (Team)
5. Post-deploy monitoring procedure update (Ops)

## Lessons Learned
- Staging doesn't replicate production conditions
- Need earlier warning signals
- Incident response was excellent (13 min resolution)
```

## Exam Questions

1. **What is the primary difference between SLO and SLI?**
   - A. SLO is promise to customers, SLI is measurement
   - B. SLI is promise, SLO is measurement
   - C. They mean the same thing
   - D. SLO is AWS only, SLI is open source

2. **An alert should be triggered when:**
   - A. Any unusual metric value appears
   - B. When immediate action is needed
   - C. Continuously for monitoring
   - D. Only on critical errors

3. **What is error budget?**
   - A. How much money to spend on monitoring
   - B. Allowed downtime/failures within SLO
   - C. Budget for incident response
   - D. Cost of logging

4. **Alert fatigue causes:**
   - A. People respond faster
   - B. Better incident response
   - C. Alerts ignored, real issues missed
   - D. Servers to fail

5. **Why is a runbook important?**
   - A. Only for new employees
   - B. Reduces incident response time and improves consistency
   - C) Takes too much time to write
   - D) Not needed if monitoring is good

## Hands-On Tasks

### Task 1: Design SLOs for a Service

Define SLOs and SLIs for an API service with alerts at various levels.

### Task 2: Create Complete Alert System

Set up alerts with:
- Alert rules (Grafana, CloudWatch, or Prometheus)
- Notification channels (Slack, email)
- Runbooks
- Severity classification

## Production Incident Scenario

**Scenario**: Frequent false alarms causing alert fatigue, engineers ignore alerts

- Analyze alert firing patterns
- Identify which alerts are noisy
- Redesign alert thresholds and rules
- Implement composite alerts

---

**Version**: 1.0  
**Time**: 6-8 hours
