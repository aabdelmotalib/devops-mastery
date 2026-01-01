# Module 8: Advanced Observability Patterns

This module covers operating observability systems at scale and handling complex scenarios.

## Multi-Cluster Monitoring

### Federated Prometheus Setup

Monitor multiple Kubernetes clusters from central Prometheus:

```yaml
# Central Prometheus
global:
  external_labels:
    cluster: central

scrape_configs:
  # Scrape remote Prometheus instances from each cluster
  - job_name: 'cluster-1'
    static_configs:
      - targets: ['cluster1-prom:9090']
        labels:
          cluster: prod-us-east

  - job_name: 'cluster-2'
    static_configs:
      - targets: ['cluster2-prom:9090']
        labels:
          cluster: prod-eu-west
```

**Metrics deduplication**:
```
metric{cluster="prod-us-east"} = 42
metric{cluster="prod-eu-west"} = 35

Query: sum(metric) = 77
```

### Multi-Environment Monitoring

```
Development: Low retention (7 days), high sampling
Staging: Medium retention (30 days), medium sampling
Production: High retention (90 days), no sampling

Same dashboards, different data sources
Use Grafana variables: env=[dev|staging|prod]
```

## Correlation Patterns

### Metrics + Logs Correlation

```
Metric alert: error_rate > 5%
↓
Find metrics timestamp: 14:32:44
↓
Query logs at same time:
{service="api"} | timestamp >= "2024-01-15T14:32:00" AND timestamp < "2024-01-15T14:33:00"
↓
Find correlating log: "Database connection timeout"
↓
Root cause found
```

### Metrics + Traces Correlation

```
PromQL query: slow_requests (latency > 2s)
↓
Trace ID from metric label
↓
Query tracing backend: traces(trace_id)
↓
See exact span breakdown
↓
Identify slow service in chain
```

## Advanced Label Strategies

### Cardinality Planning

```
Services: 50
Environments: 3 (dev, staging, prod)
Regions: 4 (us, eu, asia, au)
Versions: 5 (rolling deploy)
Instances: 20

Max combinations: 50 × 3 × 4 × 5 × 20 = 300,000 series
If each has 20 metrics: 6M metrics
Safe limit: < 1M metrics per Prometheus

Solution:
- Drop version label (know from git commit)
- Reduce instances label to zone only
- Remove unused label combinations
```

### Label Naming Conventions

```
service=api            (lowercase, no underscores)
env=production        (not 'environment')
region=us-west-2      (standard AWS format)
version=v2.1.0        (for binary/container)

NOT:
SERVICE=api          (mixed case)
Env=production       (inconsistent)
Env_name=production  (redundant)
```

## Cost Optimization at Scale

### Storage Costs

```
100,000 unique time series
15 second scrape interval
Data points: 100k × (86,400 / 15) = 576M per day
Storage: 576M × 1 byte = 576 MB per day
Monthly: 17.3 GB

At $10/GB/month: $173/month

Ways to reduce:
1. Increase scrape interval to 30s → $87/month
2. Drop high-cardinality labels → reduces series
3. Implement sampling → drop low-importance metrics
```

### Sampling Strategies

```
Sample by metric importance:
- Critical metrics: 100% (no sampling)
- High value: 50%
- Low value: 10%
- Info only: 0% (drop)

Sample by time:
- Peak hours: High frequency
- Off-hours: Lower frequency
```

## Observability for Databases

### Key Database Metrics

```
# PostgreSQL
pg_stat_statements: Query performance
pg_stat_database: Connection count, transactions
pg_cache_: Disk vs memory access

# MongoDB
mongod_metrics: Operations, connections
mongod_lock: Lock time, queue depth

# MySQL
mysql_slow_queries: Slow query count
mysql_connections: Active connections
mysql_replication: Replication lag
```

### Database Logging

```
Slow query log:
- Queries taking > 1s
- Generated logs sent to Loki
- Dashboards show slowest queries by pattern

Error logs:
- Connection failures
- Deadlocks
- Replication errors
```

## Observability for Caches

### Redis Monitoring

```
redis_connected_clients       # Active connections
redis_keyspace_hits_total     # Cache hits
redis_keyspace_misses_total   # Cache misses
redis_memory_used_bytes       # Memory consumption
redis_evicted_keys_total      # Eviction count
```

**Useful queries**:
```
# Hit rate
redis_keyspace_hits_total / (redis_keyspace_hits_total + redis_keyspace_misses_total)

# Memory used as percentage
redis_memory_used_bytes / redis_memory_max_bytes * 100

# Eviction rate
rate(redis_evicted_keys_total[5m])
```

## Observability for Message Queues

### Kafka Monitoring

```
kafka_consumer_lag_sum        # Messages behind
kafka_producer_record_send_total   # Messages sent
kafka_consumer_records_lag_max      # Max consumer lag
```

### RabbitMQ Monitoring

```
rabbitmq_queue_messages_unacked
rabbitmq_queue_messages_ready
rabbitmq_channel_created_total
rabbitmq_connection_opened_total
```

## Testing Observability Systems

### Chaos Engineering

```
Test 1: Kill a pod
  - Does alert fire?
  - How long to detect?
  - Logs captured before crash?

Test 2: Cause high latency
  - Does latency alert fire?
  - Do logs show correlating errors?
  - Trace shows chain correctly?

Test 3: Fill disk
  - Are disk metrics correct?
  - Does alert fire before full?
  - Does service degrade gracefully?
```

### Alert Testing

```
# Manually trigger condition
kubectl delete pod database

# Verify:
1. Alert fires within 2 minutes
2. Notification sent to right channel
3. Runbook is accurate
4. Incident commander can take action

# Test monthly
```

## Security in Observability

### Data Access Control

```
API team: Can see API metrics/logs only
Database team: Can see database metrics/logs only
SRE: Can see all metrics/logs
CEO: Can see SLO dashboard only

Implemented via:
- Grafana folder permissions
- Loki label-based RBAC
- CloudWatch resource policies
```

### PII in Observability

```
Never log:
- Credit card numbers
- Social security numbers
- Passwords
- API keys

OK to log:
- user_id (numeric identifier)
- email (if properly stored)
- hashed values

Implement:
- Log redaction rules
- Audit access to sensitive metrics
- Encrypt logs in transit
```

## Exam Questions

1. **Why use federated Prometheus?**
   - A) To increase query speed
   - B) To monitor multiple clusters centrally
   - C) To reduce storage costs
   - D) To add high availability

2. **What is the main challenge with multi-cluster monitoring?**
   - A) Complexity only
   - B) Cost only
   - C) Deduplication and consistency
   - D) Metric compatibility

3. **How does sampling reduce costs?**
   - A) By storing data longer
   - B) By collecting only subset of data
   - C) By increasing compression
   - D) By removing time labels

4. **What should NOT be in logs?**
   - A) Timestamps
   - B) Credit card numbers
   - C) Error messages
   - D) User IDs

5. **How often should you test your alerts?**
   - A) Once a year
   - B) Never (too risky)
   - C) Monthly or quarterly
   - D) Only after changes

## Hands-On Tasks

### Task 1: Set Up Multi-Cluster Monitoring

Create central Prometheus that monitors multiple federated instances.

### Task 2: Test Observability Under Chaos

Kill random pods, fill disks, spike traffic.
Verify:
- Alerts fire correctly
- Logs capture event
- Traces show impact
- Root cause discoverable

## Production Incident Scenario

**Scenario**: Cross-cluster incident where one cluster fails

Debug and respond using observability signals from all clusters simultaneously.

---

**Version**: 1.0  
**Time**: 6-8 hours
