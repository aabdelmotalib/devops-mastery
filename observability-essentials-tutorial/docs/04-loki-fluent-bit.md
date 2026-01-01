# Module 4: Log Aggregation with Loki & Fluent Bit

Loki is a log aggregation system designed for Kubernetes and cloud-native environments. Fluent Bit is a lightweight log processor and forwarder. Together, they form a scalable, cost-effective logging solution.

## Table of Contents

- [Loki Architecture](#loki-architecture)
- [LogQL Query Language](#logql-query-language)
- [Fluent Bit Overview](#fluent-bit-overview)
- [Docker Integration](#docker-integration)
- [Kubernetes Integration](#kubernetes-integration)
- [Indexing Strategy](#indexing-strategy)
- [Best Practices](#best-practices)
- [Common Pitfalls](#common-pitfalls)
- [Real-World Example](#real-world-example)
- [Exam Questions](#exam-questions)
- [Hands-On Tasks](#hands-on-tasks)
- [Production Incident Scenario](#production-incident-scenario)

## Loki Architecture

Loki is fundamentally different from traditional log systems like ELK. Instead of indexing all fields, it indexes only labels.

### Design Principle: Labels Not Full-Text

Traditional systems (Elasticsearch):
```
Index every field: timestamp, level, service, user_id, message, ...
Result: High cardinality, large index, expensive storage
```

Loki approach:
```
Index only labels: {service="api", level="error", env="prod"}
Store full content unindexed
Parse on query time if needed
Result: Lower cardinality, smaller index, cheaper
```

**Key insight**: Fewer labels = cheaper queries = better scalability

### Architecture Components

```
┌─────────────────────┐
│  Log Sources        │
│  (Fluent Bit, apps) │
└────────────┬────────┘
             │ (HTTP push to /loki/api/v1/push)
             ▼
┌─────────────────────────────────────┐
│   Loki Distributor                  │
│   (Write path, validation)          │
└────────────┬────────────────────────┘
             │
       ┌─────┴─────┬──────────┐
       ▼           ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│ Ingester │ │ Ingester │ │ Ingester │
│ (in-mem) │ │ (in-mem) │ │ (in-mem) │
└─────┬────┘ └─────┬────┘ └─────┬────┘
      │            │            │
      └────────┬───┴────────┬───┘
               │ (WAL to disk)
               ▼
        ┌──────────────────┐
        │ Object Storage   │
        │ (S3, GCS, etc)   │
        └──────────────────┘
```

### Write Path

```
1. Fluent Bit sends logs to Loki /push endpoint
2. Distributor receives, validates labels
3. Distributor routes to appropriate Ingester (by stream hash)
4. Ingester stores in memory (ring buffer)
5. Periodically flushes to object storage (S3, GCS, Cassandra)
6. Write-ahead log (WAL) ensures no data loss
```

### Read Path

```
1. Query comes to Loki query frontend
2. Frontend may cache results
3. Query splits into chunks by time
4. Querier reads from Ingesters (recent) and Storage (historical)
5. Results aggregated and returned
```

### Storage Tiers

Loki uses three types of storage:

**Ingester (Hot)**: 
- In-memory, fast access
- Last 15-30 minutes of data
- No persistence (WAL backed)

**Object Storage (Warm/Cold)**:
- S3, GCS, or compatible
- Hours to years of data
- Cost-effective
- Slower access

**Index**:
- Small, separate index storage
- Only labels indexed (not content)
- Cassandra, BoltDB, or in-memory

## LogQL Query Language

LogQL is Loki's query language. Similar to PromQL but for logs.

### Log Stream Selection

Basic syntax:
```
{label="value"}
```

Examples:
```
# Logs from api service in production
{service="api", env="production"}

# Logs from error level
{level="error"}

# Multiple label values
{status=~"5.."}  # 500-599 errors
{status!="200"}  # Any status except 200

# Contains operator
{service=~"api|cache|db"}
```

### Text Filtering

After selecting streams, filter by content:

```
# Contains word "error"
{service="api"} |= "error"

# Does NOT contain word
{service="api"} != "error"

# Regex match
{service="api"} |~ "timeout|refused"

# Case-insensitive
{service="api"} |i "ERROR"
```

### Parsing

Extract fields from log line:

```
# JSON parsing
{service="api"} | json

# Extract specific field from JSON
{service="api"} | json user_id

# Label extraction
{service="api"} | pattern `<level> <message>`

# Regex extraction
{service="api"} | regexp "duration=(?P<dur>\\d+)"
```

### Aggregation Functions

Similar to PromQL:

```
# Count logs
count_over_time({service="api"}[5m])

# Rate of logs
rate({service="api"}[5m])

# Count by label
sum by (status) (count_over_time({service="api"}[5m]))

# Bytes per second
bytes_over_time({service="api"}[5m])
```

### Example Queries

**Error rate by service**:
```
sum by (service) (rate({level="error"}[5m])) / sum by (service) (rate({level=~"(info|warn|error)"}[5m]))
```

**Response time distribution** (requires parsed field):
```
quantile_over_time(0.95, {service="api"} | json duration_ms [5m])
```

**User activity over time**:
```
sum by (user_id) (count_over_time({service="api"} | json user_id [1h]))
```

## Fluent Bit Overview

Fluent Bit is a lightweight (5MB) log processor and forwarder. It's the heart of distributed logging.

### Why Fluent Bit?

**Lightweight**: 5MB vs 100MB+ for other agents
**Fast**: C-based, low overhead
**Flexible**: Parse, filter, transform logs
**Cloud-native**: Built for containers and Kubernetes
**Multi-destination**: Send to Loki, S3, Kafka, etc.

### Architecture

```
Input Plugins → Parser → Filter → Output Plugins
  │
  └─ Read logs (files, syslog, etc)
      └─ Parse (JSON, regex, etc)
          └─ Filter (transform, enrich)
              └─ Send (Loki, S3, etc)
```

### Configuration Structure

Fluent Bit configuration is INI-style:

```ini
[SERVICE]
    # Global options
    flush        5
    daemon       Off
    log_level    info

[INPUT]
    # What to read
    name         docker
    path         /var/lib/docker/containers/*/config.v2.json
    tag          docker.*

[PARSER]
    # How to parse logs
    name         json
    format       json
    time_key     timestamp
    time_format  %Y-%m-%dT%H:%M:%S.%LZ

[FILTER]
    # Transform logs
    name         record_modifier
    match        docker.*
    record       environment production

[OUTPUT]
    # Where to send
    name         loki
    match        docker.*
    host         loki
    port         3100
    labels       service=myapp,env=production
```

### Common Input Plugins

**Docker**: Read container logs
```ini
[INPUT]
    name       docker
    tag        docker.*
```

**Kubernetes**: Read pod logs
```ini
[INPUT]
    name       systemd
    tag        kube.*
    path       /var/log/containers/
```

**Syslog**: Read syslog messages
```ini
[INPUT]
    name       syslog
    tag        syslog.*
    listen     0.0.0.0
    port       514
```

**Tail**: Read log files
```ini
[INPUT]
    name       tail
    path       /var/log/app/*.log
    tag        app.*
```

## Docker Integration

### Reading Docker Container Logs

Fluent Bit can automatically discover and read logs from running containers.

**Docker Compose Example**:
```yaml
version: '3'

services:
  fluent-bit:
    image: fluent/fluent-bit:latest
    volumes:
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./fluent-bit.conf:/fluent-bit/etc/fluent-bit.conf
    ports:
      - "2020:2020"  # Metrics

  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - ./loki-config.yaml:/etc/loki/local-config.yaml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

**Fluent Bit config for Docker**:
```ini
[SERVICE]
    flush           5
    daemon          Off
    log_level       info

[INPUT]
    name            docker
    tag             docker.*
    read_from_head  true

[FILTER]
    name            record_modifier
    match           docker.*
    record          environment production
    record          datacenter us-west

[OUTPUT]
    name            loki
    match           docker.*
    host            loki
    port            3100
    labels          service=docker,env=production
```

### Container Labels as Loki Labels

Use Docker labels to add metadata:

```yaml
services:
  api:
    image: myapp:latest
    labels:
      observability.loki: "true"
      service: api-server
      env: production
```

Fluent Bit reads these labels and sends as Loki labels:

```ini
[FILTER]
    name         docker
    match        docker.*
    labels       service,env
```

Result in Loki: `{service="api-server", env="production", container_name="api"}`

## Kubernetes Integration

### DaemonSet Deployment

Deploy Fluent Bit as DaemonSet to collect logs from all nodes:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
data:
  fluent-bit.conf: |
    [SERVICE]
        flush        5
        log_level    info

    [INPUT]
        name              systemd
        tag               kube.*
        path              /var/log/containers/
        parser            docker
        db                /var/log/flb_kube.db

    [FILTER]
        name                kubernetes
        match               kube.*
        kube_url            https://kubernetes.default.svc:443
        kube_ca_file        /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        kube_token_file     /var/run/secrets/kubernetes.io/serviceaccount/token
        kube_tag_prefix     kube.var.log.containers.
        merge_log           On
        keep_log            Off
        k8s_logging_parser  On
        k8s_logging_exclude On

    [FILTER]
        name                modify
        match               kube.*
        add                 cluster production
        add                 environment prod

    [OUTPUT]
        name   loki
        match  kube.*
        host   loki.monitoring
        port   3100
        labels job=kubernetes,cluster=production
```

Full DaemonSet:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluent-bit
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: fluent-bit
  template:
    metadata:
      labels:
        app: fluent-bit
    spec:
      serviceAccountName: fluent-bit
      containers:
      - name: fluent-bit
        image: fluent/fluent-bit:latest
        resources:
          limits:
            memory: 256Mi
            cpu: 200m
          requests:
            memory: 128Mi
            cpu: 100m
        volumeMounts:
        - name: varlog
          mountPath: /var/log
          readOnly: true
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
        - name: config
          mountPath: /fluent-bit/etc/
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
      - name: config
        configMap:
          name: fluent-bit-config
```

### Log Parsing in Kubernetes

Logs from containers often need parsing:

```ini
[PARSER]
    name        docker
    format      json
    time_key    timestamp
    time_format %Y-%m-%dT%H:%M:%S.%LZ
    time_keep   On

[PARSER]
    name        syslog
    format      regex
    regex       ^\<(?<pri>[0-9]+)\>(?<time>[^ ]* {1,2}[^ ]* [^ ]*) (?<host>[^ ]*) (?<ident>[a-zA-Z0-9_\/\.\-]*)(?:\[(?<pid>[0-9]+)\])?(?:[^\:]*\:)? *(?<message>.*)$
    time_key    time
    time_format %b %d %H:%M:%S

[FILTER]
    name    parser
    match   kube.*
    key_name  log
    parser    docker
    parser    syslog
    preserve_key On
```

## Indexing Strategy

Loki's power comes from smart labeling. Bad labels destroy performance.

### Golden Signals as Labels

Label what matters for observability:

```
{service="api",      # Which service
 env="production",   # Which environment
 level="error",      # Log level
 region="us-west"}   # Where it runs
```

Each combination creates a stream. Streams are stored and indexed separately.

### High Cardinality Danger

**BAD**: Using unique values as labels
```
{service="api", user_id="john", request_id="abc123"}
# Millions of unique combinations = millions of streams
# Loki becomes slow, expensive
```

**GOOD**: High-cardinality in the log content, not labels
```
{service="api"} | json user_id="john"
# 1 stream, content queried at read time
# Loki stays fast, cheap
```

### Recommended Labels

Limited set (rule of thumb):
- **service**: Which service generated logs (required)
- **env**: production, staging, dev (required)
- **level**: error, warn, info, debug (recommended)
- **region**: Which region/zone (if multi-region)
- **job**: Job/pod name (auto from Kubernetes)

**Maximum cardinality per label**:
- service: 100s
- env: 3-5
- level: 5
- region: 10-20
- job: 1000s

Rule: (service) × (env) × (level) × (region) × (job) < 100,000 streams

## Best Practices

### 1. Label Strategy

```
Good labels:
- Fixed values (service, env)
- Low cardinality (< 100 unique values)
- Relevant for filtering (level, region)

Bad labels:
- Unique per request (user_id, request_id, timestamp)
- Unbounded (any user input)
- Not useful for filtering
```

### 2. Buffer and Batching

Fluent Bit should batch logs:

```ini
[OUTPUT]
    name   loki
    match  *
    host   loki
    port   3100
    
    # Batching
    batch_size  1000      # Flush after 1000 logs
    batch_wait  5         # Or wait max 5 seconds
```

### 3. Retention Policy

```yaml
# Loki local config
limits_config:
  retention_period: 30d   # Keep 30 days
  
schema_config:
  configs:
    - from: 2024-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h
```

### 4. Query Optimization

```
Slow query: {service="api"} | json_parser | error != ""
            # Parses ALL logs then filters

Fast query: {service="api", level="error"}
            # Filters by label first, minimal parsing
```

## Common Pitfalls

### Pitfall 1: Too Many Labels

Creates stream explosion:

```
Bad:
{service, env, level, user_id, request_id, endpoint, method, status}
# 10 services × 3 envs × 5 levels × 1M users = 150M streams!

Fix:
{service, env, level}
# 10 × 3 × 5 = 150 streams
# Put user_id, request_id in log content
```

### Pitfall 2: Not Setting Job Labels

Kubernetes should auto-set job:

```ini
[FILTER]
    name                kubernetes
    match               kube.*
    labels              job,namespace,pod_name
```

Enables filtering by pod, namespace automatically.

### Pitfall 3: Parsing on Write

Parsing should happen on read:

```
Bad:
[FILTER]
    name   parser
    match  *
    key_name log
    parser json
    # Parse every log as it comes

Good:
# Don't parse on write
# Parse on query: | json key1
```

### Pitfall 4: No Log Sampling

All logs = infinite costs:

```python
# Sample by level
if level in ['ERROR', 'CRITICAL']:
    sample = 1.0  # Always log
elif level == 'WARN':
    sample = 0.5  # 50% of warnings
else:
    sample = 0.1  # 10% of info/debug

if random.random() < sample:
    logger.log(...)
```

## Real-World Example

### Microservices Logging Pipeline

**Services**: API (Python), Cache (Redis), Database (PostgreSQL), Worker (Go)

**Loki Config**:
```yaml
auth_enabled: false

ingester:
  chunk_idle_period: 3m
  max_chunk_age: 1h
  max_streams_limit_utilisation: 0.9
  
limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h
  retention_period: 30d

schema_config:
  configs:
    - from: 2024-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

server:
  http_listen_port: 3100
  log_level: info
```

**Fluent Bit Config**:
```ini
[SERVICE]
    flush           5
    daemon          Off
    log_level       info

# Docker input
[INPUT]
    name            docker
    tag             docker.*
    read_from_head  true

# Kubernetes input
[INPUT]
    name            systemd
    tag             kube.*
    path            /var/log/containers/

# Parser for Python JSON logs
[PARSER]
    name            json
    format          json
    time_key        timestamp
    time_format     %Y-%m-%dT%H:%M:%S.%fZ

# Kubernetes filter
[FILTER]
    name                kubernetes
    match               kube.*
    kube_url            https://kubernetes.default.svc:443
    kube_tag_prefix     kube.var.log.containers.
    merge_log           On
    keep_log            Off

# Modify records
[FILTER]
    name         modify
    match        *
    add          cluster production
    add          region us-west-2

# Send to Loki
[OUTPUT]
    name   loki
    match  *
    host   loki.monitoring
    port   3100
    labels service=$service,env=$env,level=$level
```

**Query examples**:
```
# All errors in last hour
{level="error", cluster="production"} | json | error != ""

# API latency over time
{service="api"} | json | duration_ms > 500 | rate([5m])

# Worker job failures
{service="worker"} | json status="failed"
```

## Exam Questions

1. **What is Loki's primary indexing strategy?**
   - A. Full-text indexing of all fields
   - B. Label-based indexing, content parsed on query
   - C. Keyword indexing with machine learning
   - D. No indexing, sequential scan

2. **Which is NOT recommended as a Loki label?**
   - A. service
   - B. environment
   - C. user_id
   - D. region

3. **What does Fluent Bit do in a logging pipeline?**
   - A. Stores logs (like Loki)
   - B. Visualizes logs (like Grafana)
   - C. Collects and forwards logs to aggregators
   - D. Queries logs using LogQL

4. **In LogQL, what does `|=` operator do?**
   - A. Extract fields from logs
   - B. Filter logs containing a string
   - C. Count logs per label
   - D. Change log format

5. **What is a major advantage of Loki vs Elasticsearch?**
   - A. Loki has better full-text search
   - B. Loki is more expensive
   - C. Loki uses label-based indexing, lower cost and simpler
   - D. Loki doesn't need storage

## Hands-On Tasks

### Task 1: Deploy Loki and Fluent Bit Stack

**Objective**: Set up complete log aggregation with Loki, Fluent Bit, and Grafana

**Steps**:
1. Start Loki server
2. Deploy Fluent Bit with Docker input
3. Connect Grafana as Loki data source
4. Send logs from application
5. Query logs in Grafana

**Acceptance**:
- Loki running on port 3100
- Fluent Bit collecting container logs
- Grafana connected to Loki
- Can query logs with LogQL

### Task 2: Log Correlation with Request IDs

**Objective**: Trace request through multiple services using logs

**Requirements**:
- 3 services (can be simple Flask apps)
- All logs in JSON format
- request_id propagated through services
- Show complete trace using LogQL

**Acceptance**:
- request_id in all logs
- LogQL query returns complete request trace
- Can correlate logs across services

## Production Incident Scenario

### Scenario: Log Pipeline Backlog

Your Fluent Bit instances are falling behind. Logs are delayed by 10+ minutes. Dashboards and alerts are stale.

**Constraints**: 
- Can't change application code
- Need to fix in 30 minutes
- Storage is not the issue

**Your task**: 
1. Identify what causes backup
2. Show diagnostic queries
3. Propose fixes with specific config changes

---

**Next Module**: [Module 5: Grafana Dashboards](05-grafana-dashboards.md)

---

**Version**: 1.0  
**Time**: 6-8 hours
