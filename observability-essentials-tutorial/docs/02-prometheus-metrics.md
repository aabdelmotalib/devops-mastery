# Module 2: Metrics Collection with Prometheus

In this module, you'll learn how Prometheus collects, stores, and enables you to query metrics from applications and infrastructure. This is the foundation for observability.

## Table of Contents

- [Prometheus Architecture](#prometheus-architecture)
- [Core Components](#core-components)
- [Metric Types](#metric-types)
- [Exporters and Instrumentation](#exporters-and-instrumentation)
- [Scrape Configuration](#scrape-configuration)
- [PromQL Basics](#promql-basics)
- [Data Storage and Retention](#data-storage-and-retention)
- [Best Practices](#best-practices)
- [Common Pitfalls](#common-pitfalls)
- [Real-World Example](#real-world-example)
- [Exam Questions](#exam-questions)
- [Hands-On Tasks](#hands-on-tasks)
- [Production Incident Scenario](#production-incident-scenario)

## Prometheus Architecture

Prometheus is a pull-based metrics system. Unlike push-based systems (InfluxDB, Datadog), Prometheus actively scrapes metrics from targets.

### Architecture Diagram

```
┌──────────────────────┐
│  Target Services     │
│  (Flask, Node.js,    │
│   Go with exporter)  │
└──────────────┬───────┘
               │ (exposes /metrics endpoint)
               ▼
┌──────────────────────────────────────┐
│   Prometheus Server (central)        │
│  ┌──────────────────────────────┐   │
│  │ Scraper                      │   │
│  │ Runs on scrape_interval      │   │
│  │ (default 15s)               │   │
│  └────────────┬─────────────────┘   │
│               │                      │
│  ┌────────────▼─────────────────┐   │
│  │ Time Series Database (TSDB)  │   │
│  │ Stores metrics with labels   │   │
│  │ Compacts data over time      │   │
│  └────────────┬─────────────────┘   │
│               │                      │
│  ┌────────────▼─────────────────┐   │
│  │ Query Engine                 │   │
│  │ Evaluates PromQL queries     │   │
│  └─────────────────────────────┘   │
└──────────────┬───────────────────────┘
               │ (HTTP API :9090)
               ▼
        ┌──────────────┐
        │   Grafana    │
        │ (Dashboards) │
        └──────────────┘
```

### Key Principle: Pull vs Push

**Pull-based** (Prometheus):
- Prometheus scrapes targets at intervals
- Targets must expose metrics endpoint
- Prometheus controls collection rate
- Easier to manage which targets to scrape

**Advantages**:
- Scales better (one server scrapes many targets)
- Can scrape instantly (no client buffer)
- Target failures visible immediately
- Duplicate detection easy

**Disadvantages**:
- Short-lived jobs can be missed
- Targets must be accessible to Prometheus
- Harder to scrape across firewalls

## Core Components

### 1. Prometheus Server

The central component that scrapes, stores, and serves metrics.

**Key responsibilities**:
- Scrape targets according to config
- Store metrics in TSDB
- Evaluate alerting rules
- Provide HTTP API for queries
- No distributed setup (single instance design)

**Resource requirements**:
- Memory: 2GB baseline + 1GB per 1M active series
- CPU: Single core baseline, scales with scrape frequency
- Disk: 15 bytes per sample (highly variable)

For 1M metrics at 15s intervals, daily: ~5.8GB

### 2. Exporters

Services that expose metrics in Prometheus format. They translate system/app metrics to Prometheus format.

**Common exporters**:
- **Node Exporter**: System metrics (CPU, memory, disk, network)
- **cAdvisor**: Container metrics
- **PostgreSQL Exporter**: Database metrics
- **Redis Exporter**: Cache metrics
- **Nginx Exporter**: Web server metrics

**How exporters work**:
```
System/App State → Exporter → Prometheus format → /metrics endpoint
```

### 3. TSDB (Time Series Database)

Prometheus includes its own TSDB. Not a separate component, but critical to understand.

**Key characteristics**:
- Column-oriented storage (optimized for time series)
- Each metric+labels = unique time series
- Samples stored as (timestamp, value) pairs
- Compacted into blocks (2-hour default)
- Retention policy enforced

**Storage layout** (simplified):
```
/prometheus/
├── wal/                    (write-ahead log, uncompressed)
│   ├── 000000
│   ├── 000001
│   └── checkpoint-latest
├── chunks_head/            (current samples)
└── metrics.txt             (cardinality index)
```

### 4. Service Discovery

Prometheus needs to know what to scrape. Service discovery automates target discovery.

**Methods**:
- **Static**: Fixed targets in config
- **Kubernetes**: Discover pods/services via API
- **DNS**: Look up A records
- **Consul**: Service catalog
- **EC2**: Auto-discover instances

**Example (Kubernetes)**:
```yaml
scrape_configs:
- job_name: 'kubernetes-pods'
  kubernetes_sd_configs:
  - role: pod
```

Prometheus automatically finds all pods and scrapes their metrics.

## Metric Types

### Counter

Always increases or resets. Never decreases.

**Definition**:
```python
# Flask example
from prometheus_client import Counter

requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Increment when request completes
requests_total.labels(method='GET', endpoint='/api/users', status=200).inc()
```

**Scrape output**:
```
http_requests_total{method="GET",endpoint="/api/users",status="200"} 15432
http_requests_total{method="GET",endpoint="/api/users",status="404"} 12
http_requests_total{method="POST",endpoint="/api/users",status="201"} 342
```

**PromQL operations**:
```
# Per-second rate over 5 minutes
rate(http_requests_total[5m])

# Absolute increase
increase(http_requests_total[1h])

# Look for resets (useful for detecting crashes)
resets(http_requests_total[24h])
```

### Gauge

Can increase or decrease. Represents current value.

**Definition**:
```python
from prometheus_client import Gauge

memory_bytes = Gauge(
    'process_memory_bytes',
    'Process memory in bytes'
)

memory_bytes.set(104857600)  # 100MB
```

**Scrape output**:
```
process_memory_bytes 104857600
```

**PromQL operations**:
```
# Current value
process_memory_bytes

# Average over time
avg_over_time(process_memory_bytes[5m])

# Max value seen
max_over_time(process_memory_bytes[1h])
```

### Histogram

Distribution of observations in predefined buckets. Useful for latency.

**Definition**:
```python
from prometheus_client import Histogram

request_latency = Histogram(
    'request_latency_seconds',
    'Request latency in seconds',
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

start = time.time()
# ... handle request ...
latency = time.time() - start
request_latency.observe(latency)
```

**Scrape output**:
```
request_latency_seconds_bucket{le="0.01"} 10
request_latency_seconds_bucket{le="0.025"} 25
request_latency_seconds_bucket{le="0.05"} 45
request_latency_seconds_bucket{le="0.1"} 95
request_latency_seconds_bucket{le="+Inf"} 100
request_latency_seconds_count 100
request_latency_seconds_sum 15.432
```

**PromQL operations**:
```
# 95th percentile latency
histogram_quantile(0.95, request_latency_seconds_bucket)

# Average latency
request_latency_seconds_sum / request_latency_seconds_count

# Requests faster than 100ms
request_latency_seconds_bucket{le="0.1"}
```

### Summary

Similar to Histogram but percentiles calculated on client side.

**Definition**:
```python
from prometheus_client import Summary

request_latency = Summary(
    'request_latency_seconds',
    'Request latency in seconds',
    objectives=[0.5, 0.9, 0.99]  # Desired quantiles
)

request_latency.observe(0.234)
```

**Scrape output**:
```
request_latency_seconds{quantile="0.5"} 0.15
request_latency_seconds{quantile="0.9"} 0.45
request_latency_seconds{quantile="0.99"} 0.98
request_latency_seconds_count 100
request_latency_seconds_sum 15.432
```

**Differences from Histogram**:
- Percentiles computed on client, not server
- No buckets exposed
- Cannot aggregate across instances
- Lower cardinality

**When to use**:
- Histogram: Multi-instance aggregation (distributed system)
- Summary: Single-instance percentiles (within one process)

## Exporters and Instrumentation

### Exporter Categories

**Language-specific** (integrate into your code):
- prometheus_client (Python)
- prom/client (Go)
- prometheus (Node.js/JavaScript)
- prometheus (Java/JVM)

**Standalone** (external process):
- Node Exporter (system metrics)
- cAdvisor (container metrics)
- PostgreSQL Exporter (database metrics)

**Application-specific** (tailored to a service):
- Nginx metrics
- Redis metrics
- Elasticsearch metrics

### Instrumentation Philosophy

Every service should expose metrics. Three approaches:

**1. Direct instrumentation** (Recommended):
Embed Prometheus client library in your code.

```python
from prometheus_client import Counter, Histogram, start_http_server

# Create metrics
requests_total = Counter('http_requests_total', 'Total requests', ['method', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'Request duration')

# Start metrics server
start_http_server(8000)  # Exposes /metrics on port 8000

# Your Flask app
@app.route('/api/users')
def get_users():
    with request_duration.time():
        users = db.query(User).all()
        requests_total.labels(method='GET', status=200).inc()
        return jsonify(users)
```

**2. Exporter bridge** (Limited flexibility):
Use an exporter that translates another metric format.

```
App → StatsD format → StatsD exporter → Prometheus
```

**3. Polling exporter** (No app changes):
External tool scrapes application state.

```
External exporter → App REST API → Prometheus
```

**Recommendation**: Use direct instrumentation when possible.

### High-Cardinality Metrics: The Danger

High cardinality means too many unique label combinations.

**Bad example**:
```python
# DON'T DO THIS
request_duration = Histogram(
    'http_request_duration_seconds',
    'Request duration',
    ['user_id', 'product_id', 'timestamp', 'ip_address']  # HIGH CARDINALITY!
)

# With millions of users/products, creates millions of unique time series
# Storage explodes, queries become slow
```

**Good example**:
```python
# DO THIS
request_duration = Histogram(
    'http_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint', 'status']  # 10-100 combinations max
)

# If user-specific tracking needed, use logs not metrics
```

**Rule of thumb**:
- Cardinality < 10: Very safe
- Cardinality 10-100: Fine, monitor growth
- Cardinality 100-1,000: Potential issues
- Cardinality > 1,000: Will cause problems

## Scrape Configuration

Prometheus learns what to scrape from its configuration file.

### Basic Configuration

```yaml
global:
  scrape_interval: 15s       # How often to scrape targets
  evaluation_interval: 15s   # How often to evaluate rules
  external_labels:
    cluster: production      # Added to all metrics

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node-exporter'
    scrape_interval: 10s     # Override global
    static_configs:
      - targets:
        - 'host1:9100'
        - 'host2:9100'
        - 'host3:9100'
        labels:
          env: production

  - job_name: 'flask-api'
    static_configs:
      - targets:
        - 'api1:8000'
        - 'api2:8000'
        - 'api3:8000'
        labels:
          service: api
```

### Kubernetes Service Discovery

```yaml
scrape_configs:
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      # Only scrape pods with prometheus=true label
      - source_labels: [__meta_kubernetes_pod_label_prometheus]
        action: keep
        regex: true
      # Use pod's own port for metrics
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_port]
        action: replace
        target_label: __param_target
      # Set job label from pod name
      - source_labels: [__meta_kubernetes_pod_name]
        action: replace
        target_label: job
```

### Relabel Configuration (Advanced)

Relabel rules modify labels before/after scrape.

```yaml
relabel_configs:
  # Keep only certain instances
  - source_labels: [__address__]
    regex: 'prod-.*'
    action: keep

  # Rename label
  - source_labels: [__meta_kubernetes_pod_label_app]
    action: replace
    target_label: application

  # Create composite label
  - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_pod_name]
    regex: '([^;]+);([^;]+)'
    action: replace
    target_label: pod_full_name
    replacement: '$1/$2'

  # Drop metrics before scraping (metric_path)
  - source_labels: [__metrics_path__]
    regex: '.*/excluded_metrics'
    action: drop
```

### Scrape Timing Details

```
t0: Scrape starts (measure duration)
    ↓ HTTP request to /metrics
t1: Target responds (measure response time)
    ↓ Parse metrics
t2: Write to TSDB
t3: Record scrape took (t2-t0)
t4: Schedule next scrape at t0 + scrape_interval
```

Key point: If scrape takes 5 seconds with 15s interval, next starts at t0+15s, not t2+15s.

## PromQL Basics

PromQL is Prometheus Query Language. It's how you retrieve and analyze metrics.

### Instant Vector

Evaluates to a set of time series at a specific point in time.

```
# All http_requests_total time series (current value)
http_requests_total

# Filter by label
http_requests_total{job="flask-api"}

# Multiple label matches
http_requests_total{job="flask-api", status="200"}

# Label matching operators
http_requests_total{status=~"2.."}  # 2xx status codes
http_requests_total{status!~"5.."}  # NOT 5xx status codes
```

### Range Vector

Returns samples over a time window.

```
# Last 5 minutes of data
http_requests_total[5m]

# Last 1 hour
http_requests_total[1h]

# Last 7 days
http_requests_total[7d]
```

**Important**: Range vectors are rarely used directly. Usually wrapped in functions.

### Functions: Rate and Increase

**rate()**: Per-second rate of increase

```
# Requests per second over last 5 minutes
rate(http_requests_total[5m])

# Bytes received per second
rate(node_network_receive_bytes_total[5m])

# Error rate (errors per second)
rate(http_requests_total{status=~"5.."}[5m])
```

**increase()**: Total increase (absolute, not per-second)

```
# Total requests in last hour
increase(http_requests_total[1h])

# Used for: absolute growth numbers
```

### Functions: Aggregation

```
# Sum all time series
sum(http_requests_total)

# Sum by label
sum by (status) (http_requests_total)
# Result: one time series per status value

# Average across instances
avg(process_memory_bytes)

# Max value seen
max(http_request_duration_seconds)

# 95th percentile
histogram_quantile(0.95, http_request_duration_seconds_bucket)
```

### Functions: Arithmetic

```
# Percentage (0-100)
(memory_used / memory_total) * 100

# Ratio
requests_success / requests_total

# Combine metrics
cpu_usage / cpu_cores
```

### Time Functions

```
# How long ago (in seconds)
time() - timestamp(http_requests_total)

# Format timestamp
strftime(time(), "%Y-%m-%d")
```

### Real PromQL Examples

**Error rate over 5 minutes**:
```
sum(rate(http_requests_total{status=~"5.."}[5m])) / 
sum(rate(http_requests_total[5m]))
```

**P99 latency by endpoint**:
```
histogram_quantile(0.99, sum by (le, endpoint) (rate(http_request_duration_seconds_bucket[5m])))
```

**Memory usage as percentage of limit**:
```
(container_memory_usage_bytes / container_spec_memory_limit_bytes) * 100
```

**Query count per database**:
```
sum by (database) (rate(mysql_queries_total[5m]))
```

## Data Storage and Retention

### How Prometheus Stores Data

**Write process** (on each scrape):
1. Metrics received at /metrics endpoint
2. Sample timestamped and labeled
3. Appended to WAL (Write-Ahead Log)
4. Added to in-memory head
5. Every 2 hours: compacted into block
6. Old blocks compressed and archived

**TSDB structure** (on disk):
```
prometheus/
├── wal/                      # Current write-ahead log
│   ├── 000000 (uncompressed)
│   ├── 000001
│   └── checkpoint-latest
├── chunks_head/              # In-memory samples
└── blocks/                   # Compacted 2-hour blocks
    ├── 01AN1JXZ0RNF0KZM0V5S/
    ├── 01AN1JXZ0RNF0KZM0V5T/
    └── ... (thousands for high-cardinality)
```

**Retention policy**:
```yaml
global:
  retention:
    time: 30d           # Keep data 30 days
    size: 50GB          # OR stop at 50GB (whichever first)
```

### Storage Calculation

**Formula**: 
```
Daily bytes = (metrics_count) × (samples_per_day) × (bytes_per_sample)
```

**Example**:
```
Metrics: 10,000 unique time series
Scrape interval: 15 seconds
Samples per time series per day: 86,400 / 15 = 5,760
Bytes per sample: 15 (average)

Daily: 10,000 × 5,760 × 15 = 864MB/day
Monthly: 864MB × 30 = 25.9GB/month
Yearly: 25.9GB × 12 = 310GB/year
```

### Storage Optimization

**1. Reduce cardinality**:
```
Remove high-cardinality labels
Track user_id in logs, not metrics
```

**2. Increase scrape interval**:
```yaml
scrape_configs:
  - job_name: 'slow-changing'
    scrape_interval: 60s  # Instead of 15s
```

**3. Drop unnecessary metrics** (at scrape time):
```yaml
metric_relabel_configs:
  - source_labels: [__name__]
    regex: 'go_.*'
    action: drop  # Don't store Go runtime metrics
```

**4. Use shorter retention for non-critical data**:
```yaml
# Keep high-volume metrics shorter
metric_relabel_configs:
  - source_labels: [__name__]
    regex: 'node_network_.*'
    action: replace
    target_label: __tmp_retention
    replacement: '7d'

# Keep critical metrics longer (30d default)
```

### Long-Term Storage

Prometheus is designed for recent data (weeks-months). For long-term:

**Option 1: Prometheus remote storage**
```yaml
remote_write:
  - url: http://cortex:9009/api/prom/push
    write_relabel_configs:
      - source_labels: [job]
        regex: 'prod-.*'
        action: keep
```

**Option 2: Export and archive**
```bash
# Export data to S3 weekly
prometheus-backup save --backup.location s3://bucket/prometheus
```

**Option 3: Use managed service** (Grafana Cloud, AWS Managed Prometheus)

## Best Practices

### 1. Label Naming

**Use snake_case**:
```
Good: http_requests_total
Bad: httpRequestsTotal
```

**Be specific**:
```
Good: request_latency_seconds
Bad: latency
```

**Consistent labels across metrics**:
```
All metrics have: job, instance, service, env
```

### 2. Metric Naming

**Format**: `<namespace>_<subsystem>_<name>_<unit>`

```
http_requests_total        # Counter
http_request_duration_seconds  # Histogram
process_memory_bytes       # Gauge
mysql_connections_active   # Gauge
redis_operation_duration_seconds  # Histogram
```

**Rules**:
- Use seconds for time (not ms or us)
- Use bytes for size (not kb, gb)
- Avoid abbreviations
- Counters end in _total

### 3. Scrape Interval Tuning

**Fast-changing metrics**: 10-15 seconds
- Request latency
- Error rates
- Active connections

**Stable metrics**: 30-60 seconds
- Disk usage
- CPU temperature
- Configuration changes

**Slow metrics**: 5 minutes
- System boot time
- License expirations

**Rule of thumb**: Scrape at 2x the frequency you need to observe changes.

### 4. Target Health Monitoring

Monitor Prometheus itself:
```
# At localhost:9090/metrics

up{job="flask-api",instance="host1"}           # 1 = up, 0 = down
scrape_duration_seconds{job="flask-api"}       # How long scrape took
scrape_samples_post_metric_relabeling{job}     # Metrics accepted
```

Use these for alerting:
```
# Alert if target is down
alert: TargetDown
expr: up{job="flask-api"} == 0
for: 5m
```

### 5. Use Prometheus Recording Rules

Pre-compute expensive queries and store as new metrics.

```yaml
groups:
  - name: requests
    interval: 15s
    rules:
      # Record per-second error rate
      - record: instance:http_requests_error_rate:rate5m
        expr: >
          sum(rate(http_requests_total{status=~"5.."}[5m])) by (instance)
          /
          sum(rate(http_requests_total[5m])) by (instance)

      # Record p99 latency
      - record: instance:http_request_duration_p99:rate5m
        expr: >
          histogram_quantile(0.99, 
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le, instance))
```

Then query the pre-computed metric:
```
instance:http_requests_error_rate:rate5m
```

Much faster than computing on query time.

## Common Pitfalls

### Pitfall 1: High Cardinality Explosion

**Problem**: Using unique values as labels
```python
# DON'T
requests = Counter('requests', ['user_id', 'product_id'])

# With 1M users and 10k products: 10B combinations possible
# Storage explodes, queries slow
```

**Solution**: Use low-cardinality labels
```python
# DO
requests = Counter('requests', ['endpoint', 'status'])

# Maybe 50-100 combinations
```

### Pitfall 2: Missing Metrics Means Zero

**Problem**: If metric doesn't exist, graph shows nothing (not zero)
```
# If some instances don't have the metric:
memory_bytes{instance="host1"} 1024
# host2 has no data
# Graph shows host1 data only, looks like host2 has 0
```

**Solution**: Use `or vector(0)` to fill gaps
```
memory_bytes or vector(0)
```

### Pitfall 3: Scrape Configuration Too Aggressive

**Problem**: Scraping every 5 seconds with 1000 targets
```yaml
scrape_interval: 5s
# 1000 targets × (4 samples per metric × 10 metrics) = 40,000 samples/sec
# Prometheus can't keep up, data loss occurs
```

**Solution**: Use reasonable intervals
```yaml
scrape_interval: 15s  # Standard
# 1000 targets × 40 samples = 66k/sec (manageable)
```

### Pitfall 4: Labels with Timestamps

**Problem**: Adding timestamp to labels
```python
# DON'T
metric = Gauge('jobs_running', ['job_name', 'started_at'])
# started_at values change constantly = high cardinality
```

**Solution**: Use timestamps as metric values
```python
# DO
job_start_timestamp = Gauge('job_start_timestamp', ['job_name'])
job_start_timestamp.labels(job_name='backup').set(1705335164)
```

### Pitfall 5: Relying Only on Metrics

**Problem**: Assuming metrics tell the complete story
```
Metric shows: memory_bytes = 1024MB
Question: Why did memory spike?
Can't answer with just the metric value.
```

**Solution**: Combine with logs
```
Metric shows: memory spike at 14:32
Logs show: "CacheLoader: Loaded 1M items into memory"
Now you understand why.
```

## Real-World Example

### Flask Application Instrumentation

**Service**: User API that queries database and caches results

```python
# Flask app with Prometheus instrumentation

from flask import Flask, jsonify
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
import redis

app = Flask(__name__)
cache = redis.Redis(host='localhost', port=6379)

# Metrics
requests_total = Counter(
    'flask_requests_total',
    'Total Flask requests',
    ['method', 'endpoint', 'status'],
    registry=prometheus_registry
)

request_duration = Histogram(
    'flask_request_duration_seconds',
    'Flask request duration',
    ['endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
    registry=prometheus_registry
)

cache_hits = Counter(
    'cache_hits_total',
    'Cache hits',
    ['endpoint'],
    registry=prometheus_registry
)

cache_misses = Counter(
    'cache_misses_total',
    'Cache misses',
    ['endpoint'],
    registry=prometheus_registry
)

db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type'],
    buckets=(0.001, 0.01, 0.05, 0.1, 0.5),
    registry=prometheus_registry
)

active_requests = Gauge(
    'flask_requests_active',
    'Active Flask requests',
    ['endpoint'],
    registry=prometheus_registry
)

@app.before_request
def before_request():
    request.start_time = time.time()
    active_requests.labels(endpoint=request.endpoint).inc()

@app.after_request
def after_request(response):
    duration = time.time() - request.start_time
    active_requests.labels(endpoint=request.endpoint).dec()
    request_duration.labels(endpoint=request.endpoint).observe(duration)
    requests_total.labels(
        method=request.method,
        endpoint=request.endpoint,
        status=response.status_code
    ).inc()
    return response

@app.route('/api/users/<int:user_id>')
def get_user(user_id):
    endpoint = '/api/users/<int:user_id>'
    
    # Check cache first
    cache_key = f'user:{user_id}'
    cached = cache.get(cache_key)
    
    if cached:
        cache_hits.labels(endpoint=endpoint).inc()
        return jsonify(json.loads(cached))
    
    cache_misses.labels(endpoint=endpoint).inc()
    
    # Query database
    start = time.time()
    user = db.query(User).filter_by(id=user_id).first()
    duration = time.time() - start
    db_query_duration.labels(query_type='select_user').observe(duration)
    
    if not user:
        return jsonify({'error': 'Not found'}), 404
    
    # Cache result
    cache.setex(cache_key, 3600, json.dumps(user.to_dict()))
    
    return jsonify(user.to_dict())

# Start metrics server on port 8001
start_http_server(8001)

if __name__ == '__main__':
    app.run(port=8000)
```

**Prometheus configuration**:
```yaml
scrape_configs:
  - job_name: 'flask-api'
    static_configs:
      - targets: ['localhost:8001']
        labels:
          service: user-api
          env: production
```

**Useful queries**:
```
# Request rate
rate(flask_requests_total[5m])

# Error rate
rate(flask_requests_total{status=~"5.."}[5m]) / rate(flask_requests_total[5m])

# P95 latency
histogram_quantile(0.95, flask_request_duration_seconds_bucket)

# Cache hit ratio
cache_hits_total / (cache_hits_total + cache_misses_total)

# Active requests
flask_requests_active
```

## Exam Questions

1. **What is a key advantage of Prometheus's pull-based metrics collection?**
   - A. Targets can push metrics from behind firewalls
   - B. The server controls scrape timing and can verify target health
   - C. It eliminates the need for exporters
   - D. It stores data for unlimited duration

2. **In Prometheus, what does a single "time series" consist of?**
   - A. A metric name only
   - B. A metric name with a specific set of label values
   - C. All samples for a metric across all time
   - D. A snapshot of the system at one moment

3. **Which metric type should you use for tracking "number of items processed"?**
   - A. Gauge
   - B. Counter
   - C. Histogram
   - D. Summary

4. **What does the expression `rate(http_requests_total[5m])` calculate?**
   - A. Total requests in the last 5 minutes
   - B. Per-second rate of requests over the last 5 minutes
   - C. Maximum requests seen in the last 5 minutes
   - D. Current requests per second

5. **How does Prometheus store data over time to manage disk space?**
   - A. By deleting old samples immediately
   - B. By compressing metrics into 2-hour blocks and enforcing retention policies
   - C. By never storing historical data
   - D. By uploading data to cloud storage automatically

## Hands-On Tasks

### Task 1: Deploy Prometheus and Configure Scrape Targets

**Objective**: Get Prometheus running and scrape metrics from multiple targets

**Steps**:
1. Start Prometheus in Docker:
```bash
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v /path/to/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus \
  --config.file=/etc/prometheus/prometheus.yml
```

2. Create a `prometheus.yml` with:
   - Prometheus itself as a scrape target
   - Add Node Exporter as a target (start it in separate container)
   - Set scrape_interval to 15s

3. Verify metrics are being scraped:
   - Visit http://localhost:9090/targets
   - Confirm all targets show "UP"
   - Check http://localhost:9090/graph and query `prometheus_build_info`

4. Query metrics:
   - `up{job="node"}` - should return 1 if Node Exporter is running
   - `rate(prometheus_tsdb_symbol_table_size_bytes[5m])`
   - Create a dashboard query for requests per second (use any metric available)

**Acceptance criteria**:
- Prometheus accessible at http://localhost:9090
- At least 2 scrape targets showing "UP"
- Successful metric queries showing data
- Screenshot showing targets and a working query

### Task 2: Instrument a Simple Application

**Objective**: Add Prometheus metrics to a basic application

**Requirements**:
- Create a simple HTTP server (Flask, Go, Node.js - your choice)
- Add 3 metrics:
  1. Counter for total requests
  2. Histogram for request latency
  3. Gauge for active connections
- Expose /metrics endpoint
- Scrape with Prometheus and verify metrics appear

**Example starter (Python)**:
```python
from flask import Flask
from prometheus_client import Counter, Histogram, Gauge, start_http_server

app = Flask(__name__)
requests_total = Counter('app_requests_total', 'Total requests', ['endpoint'])
request_duration = Histogram('app_request_duration_seconds', 'Request duration')
active = Gauge('app_active_requests', 'Active requests')

@app.route('/hello')
def hello():
    with request_duration.time():
        active.inc()
        requests_total.labels(endpoint='/hello').inc()
        active.dec()
        return 'Hello'

start_http_server(8001)
app.run(port=8000)
```

**Acceptance criteria**:
- Application running on port 8000
- /metrics endpoint returning Prometheus format
- All 3 metric types present
- Prometheus scraping successfully
- Metrics updated on each request

## Production Incident Scenario

### Scenario: Unexpected Storage Explosion

**Background**:
Your Prometheus server has run out of disk space overnight. The /prometheus directory has grown from 50GB to 250GB in 6 hours.

**Context**:
- Prometheus was working fine yesterday
- No new services added to scrape
- No configuration changes known
- Alerting on disk space would have helped

**Your Task**:

1. **Identify the cause**: What could cause 4x growth?
   - List 5 possible causes
   - How would you investigate each?

2. **Write diagnostic queries**: What PromQL queries would help identify the issue?
   - Query cardinality
   - Query which metrics consume most space
   - Check label growth

3. **Implement immediate fix**: How would you reduce space without losing data?

4. **Prevention**: What monitoring would you add?

5. **Recovery**: How would you clean up?

**Example investigation approach**:
```
1. Check disk usage per scrape job
   count by (job) (prometheus_tsdb_metric_chunks_created_total)

2. Check cardinality
   count(count by (__name__, job) (prometheus_tsdb_metric_chunks_created_total))

3. Identify high-cardinality metrics
   topk(10, count by (__name__) (prometheus_tsdb_metric_chunks_created_total))

4. Look for new labels being added
   timestamp(scrape_series_added) - check for recent changes

5. Review relabel rules - did any labels become high-cardinality?
```

**Deliverables**:
- Root cause analysis (200-300 words)
- List of diagnostic queries used
- Immediate remediation steps (with commands)
- Proposed preventive monitoring (3-5 metrics/alerts)
- Post-incident action items

---

**Next Module**: [Module 3: Logging Fundamentals](03-logging-fundamentals.md)

---

**Version**: 1.0  
**Time to Complete**: 6-8 hours  
**Key Concepts**: Prometheus architecture, metric types, scraping, PromQL, TSDB, retention
