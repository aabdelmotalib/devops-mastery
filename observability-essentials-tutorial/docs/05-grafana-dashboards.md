# Module 5: Visualization with Grafana

Grafana is the visualization and alerting layer that ties all observability data together. This module covers dashboard design, alerting rules, and best practices.

## Core Concepts

### Grafana Architecture

```
Data Sources (Prometheus, Loki, CloudWatch)
        ↓
Query Engine (Fetch data based on queries)
        ↓
Visualization (Panels: graph, table, gauge, etc)
        ↓
Dashboards (Organized panels with variables)
        ↓
Alerts (Rules that trigger on conditions)
        ↓
Notifications (Slack, Teams, PagerDuty, etc)
```

### Key Components

**Data Sources**: Connect to Prometheus, Loki, CloudWatch, Elasticsearch, etc

**Queries**: PromQL, LogQL, CloudWatch Insights queries

**Panels**: Individual visualizations (timeseries, gauge, table, heatmap, logs)

**Dashboards**: Collections of related panels

**Variables**: Templating for dashboard reusability

**Alerts**: Conditions that trigger notifications

**Folders**: Organize dashboards by team/service

## Dashboard Design

### Golden Signals Dashboard Template

Every service needs:

```
┌─ Service Health ──────────────────────────────────────┐
│                                                        │
│  [Status] [Latency P95] [Error Rate] [Throughput]     │
│                                                        │
├─ Request Metrics ──────────────────────────────────────┤
│                                                        │
│  [Requests/sec (line)]    [Latency Distribution]      │
│  [Error Rate by Endpoint] [Status Code Distribution]  │
│                                                        │
├─ Resource Utilization ─────────────────────────────────┤
│                                                        │
│  [CPU Usage]  [Memory Usage]  [Disk I/O]  [Network]   │
│                                                        │
├─ Dependencies ─────────────────────────────────────────┤
│                                                        │
│  [Database Latency]  [Cache Hit Rate]  [Queue Depth]  │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### Panel Types and Use Cases

**Timeseries**: Metrics over time (CPU, requests/sec)
```
Use for: Trends, patterns, alerting
Example: Request rate, latency, error rate
```

**Gauge**: Single value (0-100%)
```
Use for: Current state, at-a-glance status
Example: CPU usage, memory %, cache hit rate
```

**Table**: Structured data
```
Use for: Rankings, detailed analysis, logs
Example: Top endpoints by latency, error logs
```

**Heatmap**: Distribution over time
```
Use for: Understanding spreads
Example: Latency percentiles over time
```

**Stat**: Large number with sparkline
```
Use for: KPIs, big picture numbers
Example: Total requests today, 24h error count
```

**Logs**: Raw log entries
```
Use for: Debugging, investigation
Example: Error logs, user activity
```

## Dashboard Variables

Variables make dashboards reusable:

```json
{
  "variables": {
    "service": {
      "multi": true,
      "options": "Prometheus query",
      "query": "label_values(up, job)"
    },
    "env": {
      "options": ["dev", "staging", "production"],
      "default": "production"
    },
    "region": {
      "multi": true,
      "query": "label_values(node_info, region)"
    }
  }
}
```

**Using variables in queries**:
```
# Instead of hard-coded:
requests{job="api"}

# Use variables:
requests{job="$service", env="$env"}
```

**Dashboard templating benefits**:
- One dashboard for all services
- Filter by environment
- Multi-select for comparisons

## Alerting Rules

Grafana alerts evaluate conditions and trigger notifications.

### Alert Rule Components

```
Rule name: Too many errors
Data source: Prometheus
Query A: rate(http_requests_total{status=~"5.."}[5m])
Query B: rate(http_requests_total[5m])
Condition: A / B > 0.05  (>5% error rate)
For: 5m (must be true for 5 minutes)
Notify: #alerts-prod channel
```

### Alert States

**Pending**: Condition true but "for" duration not met
**Firing**: Condition true for "for" duration
**Resolved**: Condition false after firing

### Alert Notification Channels

**Slack**:
```
Webhook URL: https://hooks.slack.com/services/...
Template:
{{ .GroupLabels.alertname }}
Status: {{ .Status }}
Value: {{ .CommonAnnotations.value }}
```

**PagerDuty**:
```
Integration key from PagerDuty
Severity: critical for critical alerts
```

**Teams**:
```
Microsoft Teams webhook
Card-based rich formatting
```

**Email**:
```
SMTP configuration
Template support
```

## Best Practices

### 1. Dashboard Organization

```
Folder structure:
├── Platform (infrastructure health)
├── Services
│   ├── API
│   ├── Auth
│   ├── Payment
│   └── Notifications
├── Databases
├── Security
└── Cost
```

### 2. Naming Conventions

```
Good: "API: Request Latency (P95)"
Bad: "Latency"

Good: "Cache: Hit Rate by Instance"
Bad: "Hit Rate"

Include: service name, metric name, aggregation if applicable
```

### 3. Alert Severity

```
Critical: Page on-call immediately
  - Service down
  - Data loss
  - Security breach

Warn: Create ticket, alert team
  - High error rate (but handling)
  - Resource approaching limit
  - Slow degradation

Info: Log and monitor
  - Unusual pattern
  - Optional feature failing
```

### 4. Alert Tuning

```
If alerts fire daily: threshold too sensitive
If alerts never fire: threshold too loose
Goal: Alert should be actionable and rare

Rule: Alert when action is needed, not when monitoring
```

## Exam Questions

1. **What is the primary purpose of dashboard variables?**
   - A. Encrypt sensitive data
   - B. Make dashboards reusable across services/environments
   - C. Improve query performance
   - D. Store long-term data

2. **Which panel type is best for showing top 10 endpoints by error rate?**
   - A. Timeseries
   - B. Gauge
   - C. Table
   - D. Heatmap

3. **In Grafana alerts, what does the "For" parameter control?**
   - A. How long to keep alert history
   - B. How long condition must be true before firing
   - C. When to stop alerting
   - D. How often to re-evaluate

4. **What should a dashboard include to be operationally useful?**
   - A. As many panels as possible
   - B. Golden signals (latency, errors, throughput) + context
   - C. Only critical metrics
   - D. Every metric available

5. **Which is NOT appropriate for critical production alerts?**
   - A. PagerDuty (pages on-call)
   - B. Slack important channel
   - C. Email digest
   - D. SMS

## Hands-On Tasks

### Task 1: Design and Build Service Dashboard

Create a dashboard for a service with:
- Request rate (timeseries)
- Error rate percentage (gauge)
- P95 latency (stat)
- Top errors (table)
- Status by instance (table)
- At least 3 variables (service, env, region)

### Task 2: Create Alert Rules with Notifications

Create alerts for:
1. Error rate > 1% for 5 minutes
2. Latency P95 > 1 second for 10 minutes
3. Service down (up==0) for 2 minutes

Connect to at least one notification channel.

## Production Incident Scenario

**Scenario**: Dashboard shows misleading data causing wrong incident response

- Alerting on wrong metric
- Visualization doesn't match reality
- Variable not updating correctly

Debug and fix the dashboard issues.

---

**Version**: 1.0  
**Time**: 6-8 hours
