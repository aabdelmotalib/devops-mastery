# Reference Implementations

This directory contains production-ready example code for every module.

## Structure

```
examples/
├── REFERENCE_IMPLEMENTATIONS.md (this file)
├── prometheus-instrumentation/
│   ├── python-flask-example.py
│   ├── go-example.go
│   └── node-js-example.js
├── structured-logging/
│   ├── python-json-logger.py
│   ├── go-structured-logging.go
│   └── node-json-logger.js
├── fluent-bit-configs/
│   ├── docker-input.conf
│   ├── kubernetes-input.conf
│   └── log-parsing.conf
├── grafana-dashboards/
│   ├── system-overview.json
│   ├── api-service.json
│   ├── database-monitoring.json
│   └── business-metrics.json
├── aws-cloudwatch-examples/
│   ├── custom-metrics.py
│   ├── cloudwatch-agent-config.json
│   └── alarm-setup.py
└── alert-rules/
    ├── grafana-alerts.yaml
    ├── prometheus-alerts.yaml
    └── runbook-example.md
```

## Module-by-Module Reference

### Module 1: Observability Fundamentals

No code examples (conceptual module)

### Module 2: Prometheus

**Files**:
- `prometheus-instrumentation/` - Application instrumentation
- `alert-rules/prometheus-alerts.yaml` - Alert rules

**Example**: Flask app with Prometheus metrics
- HTTP request counters
- Request latency histograms
- Active connection gauges
- Database query timing

### Module 3: Logging

**Files**:
- `structured-logging/` - JSON logging implementation

**Example**: Python app with structured logs
- JSON formatter
- Request ID correlation
- Appropriate log levels
- Sensitive data redaction

### Module 4: Log Aggregation

**Files**:
- `fluent-bit-configs/` - Fluent Bit configuration

**Example**: Complete Fluent Bit setup
- Docker input plugin
- JSON parsing
- Kubernetes metadata enrichment
- Loki output configuration

### Module 5: Grafana

**Files**:
- `grafana-dashboards/` - Dashboard JSON exports

**Example Dashboards**:
1. System Overview (golden signals)
2. API Service (request metrics)
3. Database (connections, queries)
4. Business Metrics (from logs)

### Module 6: CloudWatch

**Files**:
- `aws-cloudwatch-examples/` - CloudWatch setup

**Examples**:
- Custom metric publishing
- CloudWatch Agent configuration
- Alarm creation
- SNS integration

### Module 7: Alerting

**Files**:
- `alert-rules/` - Alert definitions and runbooks

**Examples**:
- High error rate alert
- Latency degradation alert
- Service down alert
- Resource exhaustion alert

### Module 8: Advanced Patterns

References across all files showing:
- Multi-service correlation
- Label strategies
- Cost optimization patterns

## Using These Examples

### 1. As Learning Reference

Study examples while working through modules:
- See how concepts translate to code
- Copy and modify for your needs
- Understand best practices

### 2. As Project Templates

Use as starting point for final project:
- Copy Flask example
- Adapt metrics to your service
- Modify dashboards for your system

### 3. As Production Boilerplate

Use code directly in production:
- Production-ready instrumentation
- Best practices built in
- Security considerations included

## File Descriptions

### prometheus-instrumentation/python-flask-example.py

Complete Flask application with:
- Prometheus client library integration
- Request counter (by method, endpoint, status)
- Request latency histogram
- Active request gauge
- Custom business metrics
- /metrics endpoint exposed

Usage:
```python
# Add to your Flask app
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Define metrics
requests_total = Counter(...)
request_duration = Histogram(...)

# Use in routes
@app.route('/api/users/<int:user_id>')
def get_user(user_id):
    with request_duration.time():
        # ... your code ...
        requests_total.labels(...).inc()
```

### structured-logging/python-json-logger.py

Complete logging setup with:
- JSON formatter for structured output
- Correlation ID propagation
- Sensitive data redaction
- Multiple log handlers
- Log level configuration

Usage:
```python
from logging import getLogger
from json_logger import JSONFormatter

logger = getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

logger.info('User action', extra={'user_id': 123, 'action': 'login'})
```

### fluent-bit-configs/docker-input.conf

Complete Fluent Bit configuration for:
- Reading Docker container logs
- JSON parsing
- Kubernetes metadata enrichment
- Log filtering and transformation
- Loki output with labels

Usage:
```ini
[INPUT]
    name docker
    tag docker.*

[FILTER]
    name kubernetes
    match docker.*
    ...
```

### grafana-dashboards/system-overview.json

Pre-built dashboard showing:
- Request rate (timeseries)
- Error rate (gauge)
- Latency p95 (stat)
- CPU/Memory (timeseries)
- Service status (table)
- System logs (panel)

Import into Grafana:
```
Dashboards → Import → Paste JSON → Load
```

### aws-cloudwatch-examples/custom-metrics.py

Python script for:
- Publishing custom metrics
- Setting up CloudWatch Agent
- Creating alarms
- Configuring notifications

Usage:
```python
import boto3

cw = boto3.client('cloudwatch')
cw.put_metric_data(
    Namespace='MyApp',
    MetricData=[{
        'MetricName': 'ProcessingTime',
        'Value': 250,
        'Unit': 'Milliseconds'
    }]
)
```

### alert-rules/prometheus-alerts.yaml

Production alert rules for:
- High error rate
- High latency
- Service down
- Resource utilization
- Database issues

Usage:
```yaml
alert: HighErrorRate
expr: (errors / total) > 0.05
for: 5m
```

## Quick Start Examples

### 1. Add Prometheus to Flask App

```python
# Copy from: prometheus-instrumentation/python-flask-example.py
# Modify: Change metric names and labels for your service
# Deploy: Same container with metrics endpoint
```

### 2. Set Up Structured Logging

```python
# Copy from: structured-logging/python-json-logger.py
# Modify: Add business-relevant fields
# Deploy: Test with `| json` filter
```

### 3. Configure Log Collection

```ini
# Copy from: fluent-bit-configs/docker-input.conf
# Modify: Update service names and labels
# Deploy: Start Fluent Bit container
```

### 4. Create Dashboards

```
# Copy from: grafana-dashboards/system-overview.json
# Modify: Update queries for your metrics
# Import: Use Grafana import feature
```

### 5. Set Up Alerts

```yaml
# Copy from: alert-rules/prometheus-alerts.yaml
# Modify: Adjust thresholds for your services
# Deploy: Add to Prometheus config
```

## Best Practices in Examples

**All examples include**:
- Error handling
- Resource cleanup
- Configuration documentation
- Security considerations
- Production-ready patterns

**Code style**:
- Readable and maintainable
- Follows language conventions
- Well-commented
- DRY (Don't Repeat Yourself)

**Observability aspects**:
- Appropriate metrics
- Useful log messages
- Proper error reporting
- No PII in outputs

## Customization Guide

### For Your Service

1. **Metrics**: Replace endpoint/service names
2. **Labels**: Add labels relevant to your system
3. **Thresholds**: Adjust for your performance baseline
4. **Log Fields**: Add business-relevant fields

### For Your Architecture

1. **Services**: Add examples for your tech stack
2. **Data source**: Modify Loki to your backend
3. **Cloud**: Update CloudWatch examples for regions
4. **Tools**: Replace with your equivalent services

## Common Modifications

### Add New Metric

```python
# Example: Track user signups
user_signups = Counter(
    'user_signups_total',
    'Total user signups',
    ['method']  # Method: email, oauth, etc
)

# Use in code
user_signups.labels(method='oauth').inc()
```

### Add New Log Field

```python
# Example: Track user tier
logger.info(
    'Payment processed',
    extra={
        'user_id': user.id,
        'user_tier': user.tier,
        'amount': amount
    }
)
```

### Add New Alert

```yaml
# Example: Track payment failures
alert: PaymentFailureRate
expr: (payment_failures / payment_attempts) > 0.01
for: 5m
labels:
  severity: critical
```

## Testing Examples

Each example includes:
- Unit tests (where applicable)
- Integration tests
- Load test recommendations

Run tests:
```bash
pytest tests/
```

## Contributing

Found an issue or want to improve examples?
- Examples should be production-ready
- Include error handling
- Document clearly
- Follow code style of language

---

**All examples are meant to be copied, modified, and deployed to production.**
