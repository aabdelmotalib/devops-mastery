# Quick Reference Guide

Fast lookup for common tasks and commands.

## Prometheus

### Basic Commands

```bash
# Run Prometheus
docker run -d -p 9090:9090 prom/prometheus:latest

# Query HTTP API
curl 'http://localhost:9090/api/v1/query?query=up'

# Query with time range
curl 'http://localhost:9090/api/v1/query_range?query=cpu_usage&start=1609459200&end=1609545600&step=3600'
```

### Common PromQL Queries

```
# Request rate (per second)
rate(http_requests_total[5m])

# Error rate percentage
100 * rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Memory as percentage
(container_memory_usage_bytes / container_memory_limit_bytes) * 100

# Top 10 by rate
topk(10, rate(http_requests_total[5m]))

# Sum by label
sum by (service) (http_requests_total)

# Increase over time
increase(http_requests_total[1h])
```

### Prometheus Configuration

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']
```

## Loki

### Basic Commands

```bash
# Run Loki
docker run -d -p 3100:3100 grafana/loki:latest

# Query HTTP API
curl 'http://localhost:3100/api/prom/query?query={service="api"}'

# Query range
curl 'http://localhost:3100/api/prom/query_range?query={service="api"}&start=0&end=1609545600000000000'
```

### Common LogQL Queries

```
# Logs from service
{service="api"}

# With filter
{service="api"} |= "error"

# Parse JSON
{service="api"} | json

# Count over time
count_over_time({service="api"}[5m])

# Rate of logs
rate({service="api"}[5m])

# By label
sum by (status) (count_over_time({service="api"}[5m]))

# Pattern matching
{service="api"} |~ "timeout|refused"

# Negative filter
{service="api"} != "DEBUG"
```

### Fluent Bit Configuration

```ini
[SERVICE]
    flush           5
    log_level       info

[INPUT]
    name            docker
    tag             docker.*

[FILTER]
    name            modify
    match           *
    add             env production

[OUTPUT]
    name            loki
    match           *
    host            loki
    port            3100
    labels          service=app,env=production
```

## Grafana

### Common HTTP Requests

```bash
# Health check
curl 'http://localhost:3000/api/health'

# List datasources
curl -H "Authorization: Bearer TOKEN" 'http://localhost:3000/api/datasources'

# Create datasource
curl -X POST -H "Authorization: Bearer TOKEN" \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://prometheus:9090",
    "access": "proxy"
  }' \
  'http://localhost:3000/api/datasources'
```

### Alert Rule Syntax

```yaml
alert: HighErrorRate
expr: |
  (sum(rate(http_requests_total{status=~"5.."}[5m])) /
   sum(rate(http_requests_total[5m]))) > 0.05
for: 5m
annotations:
  summary: "Error rate is {{ $value | humanizePercentage }}"
labels:
  severity: critical
```

## Docker / Docker Compose

### Common Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f service_name

# Stop services
docker-compose down

# Check service status
docker-compose ps

# Run command in container
docker exec container_name command
```

## Kubernetes / kubectl

### Common Commands

```bash
# Apply configuration
kubectl apply -f config.yaml

# List resources
kubectl get pods -n monitoring

# View logs
kubectl logs -f pod-name -n monitoring

# Port forward
kubectl port-forward service/grafana 3000:3000 -n monitoring

# Check events
kubectl get events -n monitoring

# Describe resource
kubectl describe pod pod-name -n monitoring
```

## Linux / System Commands

### Disk Space

```bash
# Check disk usage
du -sh /prometheus
df -h

# Find large files
find /prometheus -size +1G
```

### Process Management

```bash
# View running processes
ps aux | grep prometheus

# Check memory usage
free -h

# Monitor in real-time
top
htop
```

### Network

```bash
# Check port connectivity
curl http://localhost:9090/metrics

# Check DNS
nslookup service-name

# Monitor network
netstat -an | grep LISTEN
ss -tlnp
```

## Common Debugging

### Prometheus Issues

**Target down**:
```
1. Check target is running
2. Check firewall allows port
3. Check Prometheus can resolve hostname
4. Check relabel rules don't exclude target
```

**No metrics**:
```
1. Check /metrics endpoint returns data
2. Check scrape interval (may not have run yet)
3. Check metric not dropped by relabel
4. Check metric doesn't exceed cardinality limit
```

### Loki Issues

**Logs not appearing**:
```
1. Check Fluent Bit running and connected
2. Check labels are valid
3. Check no parsing errors in Fluent Bit
4. Check LogQL query is correct
```

**High latency**:
```
1. Check label cardinality (too many unique combinations?)
2. Check query complexity
3. Check storage performance
4. Consider sampling logs
```

### Grafana Issues

**Dashboard slow**:
```
1. Check datasource connection
2. Check query complexity
3. Reduce number of panels
4. Increase aggregation intervals
```

**Alerts not firing**:
```
1. Check alert rule enabled
2. Check threshold
3. Check 'for' duration
4. Check notification channel working
```

## Common Tools

### Send Test Metric to Prometheus

```bash
# Via node_exporter textfile collector
echo 'test_metric 42' > /var/lib/node_exporter/textfile_collector/test.prom

# Via pushgateway
curl -X POST --data-binary @- http://localhost:9091/metrics/job/myjob < /dev/stdin
```

### Test Loki Connectivity

```bash
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"streams":[{"stream":{"job":"test"},"values":[["'$(date +%s000000000)'","test message"]]}]}' \
  http://localhost:3100/loki/api/v1/push
```

### Generate Load for Testing

```bash
# Apache Bench
ab -n 1000 -c 10 http://localhost:8000/api/test

# hey
hey -n 1000 -c 10 http://localhost:8000/api/test

# wrk
wrk -t12 -c400 -d30s http://localhost:8000/api/test
```

## Environment Variables

### Common Configuration

```bash
# Prometheus
PROMETHEUS_OPTS=--config.file=/etc/prometheus/prometheus.yml
PROMETHEUS_OPTS=$PROMETHEUS_OPTS --storage.tsdb.path=/prometheus
PROMETHEUS_OPTS=$PROMETHEUS_OPTS --web.console.libraries=/etc/prometheus/console_libraries
PROMETHEUS_OPTS=$PROMETHEUS_OPTS --web.console.templates=/etc/prometheus/consoles

# Grafana
GF_SECURITY_ADMIN_PASSWORD=admin
GF_SECURITY_ADMIN_USER=admin
GF_USERS_ALLOW_SIGN_UP=false

# Loki
LOKI_CONFIG_PATH=/etc/loki/config.yml

# CloudWatch
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
```

## Port Reference

```
Prometheus:     9090
Grafana:        3000
Loki:           3100
Fluent Bit:     2020 (metrics)
Prometheus PushGateway: 9091
Node Exporter:  9100
cAdvisor:       8080
```

## File Paths

```
Prometheus: /prometheus (data)
Loki: /loki (data)
Fluent Bit: /var/log (input)
Application logs: /var/log/app.log
```

## Performance Tuning

### Prometheus Memory

```
Baseline: 1GB
Per 1M series: +1GB

Solution: Reduce cardinality
- Fewer labels
- Drop high-cardinality labels
- Increase scrape interval
```

### Loki Performance

```
Optimize label strategy:
- Fewer labels
- Lower cardinality values
- Consistent label names

Query optimization:
- Use label filters first
- Parse minimal fields
- Avoid regex on large logs
```

### Grafana Performance

```
- Limit panels per dashboard (< 20)
- Increase aggregation intervals
- Use pre-computed metrics (record rules)
- Cache dashboard queries
```

---

**Reference**: Quick lookup guide for daily operations
