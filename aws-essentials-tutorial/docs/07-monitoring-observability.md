# Module 7: Monitoring & Observability

You can't operate what you can't observe. Monitoring and logging provide visibility into your systems, enabling quick incident response and continuous improvement.

## 7.1 CloudWatch: Metrics and Dashboards

CloudWatch collects metrics from AWS services. You can view, analyze, and alert on metrics.

### Built-in Metrics

AWS services emit metrics automatically:
- EC2: CPU usage, network I/O, disk I/O
- RDS: Database connections, query latency, replication lag
- ELB: Request count, latency, HTTP errors
- DynamoDB: Read/write throughput, throttling

```bash
# Get EC2 CPU metric
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-0123456789abcdef0 \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-15T01:00:00Z \
  --period 300 \
  --statistics Average,Maximum
```

### Custom Metrics

Application metrics (login attempts, shopping cart additions, etc.):

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

# Publish metric
cloudwatch.put_metric_data(
    Namespace='MyApp',
    MetricData=[
        {
            'MetricName': 'LoginAttempts',
            'Value': 150,
            'Unit': 'Count',
            'Timestamp': datetime.utcnow()
        }
    ]
)
```

### Dashboards

```bash
# Create dashboard
aws cloudwatch put-dashboard --dashboard-name myapp-dashboard \
  --dashboard-body '{
    "widgets": [
      {
        "type": "metric",
        "properties": {
          "metrics": [
            ["AWS/EC2", "CPUUtilization", {"stat": "Average"}],
            ["AWS/RDS", "DatabaseConnections"],
            ["AWS/ELB", "TargetResponseTime"]
          ],
          "period": 300,
          "stat": "Average",
          "region": "us-east-1",
          "title": "Application Metrics"
        }
      }
    ]
  }'
```

## 7.2 CloudWatch Logs

Application and system logs sent to CloudWatch Logs. Searchable, analyzable, and retained automatically.

### Log Groups and Streams

Log Group: Collection of logs (e.g., /aws/lambda/my-function)
Log Stream: Logs from single source (e.g., /aws/lambda/my-function/2024-01-15)

```bash
# Create log group
aws logs create-log-group --log-group-name /myapp/requests

# Create log stream
aws logs create-log-stream --log-group-name /myapp/requests \
  --log-stream-name 2024-01-15

# Put logs
aws logs put-log-events --log-group-name /myapp/requests \
  --log-stream-name 2024-01-15 \
  --log-events "timestamp=1705276800000,message='User logged in'"

# Query logs
aws logs start-query --log-group-name /myapp/requests \
  --start-time $(date -d '1 hour ago' +%s) \
  --end-time $(date +%s) \
  --query-string 'fields @timestamp, @message | filter @message like /error/'
```

### Application Logging

Python application logging to CloudWatch:

```python
import boto3
import json
import logging
from datetime import datetime

cloudwatch_logs = boto3.client('logs')

class CloudWatchLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        cloudwatch_logs.put_log_events(
            logGroupName='/myapp/application',
            logStreamName='main',
            logEvents=[{
                'timestamp': int(datetime.utcnow().timestamp() * 1000),
                'message': log_entry
            }]
        )

# Configure logging
handler = CloudWatchLogHandler()
logger = logging.getLogger()
logger.addHandler(handler)

logger.info("Application started")
logger.error("Database connection failed")
```

## 7.3 CloudWatch Alarms

Alarms notify you when metrics exceed thresholds.

```bash
# Alarm: CPU > 80% for 2 periods (10 minutes)
aws cloudwatch put-metric-alarm --alarm-name high-cpu \
  --alarm-description "Alert when EC2 CPU is high" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:ops-alerts

# Alarm: RDS free storage < 5%
aws cloudwatch put-metric-alarm --alarm-name low-disk-space \
  --metric-name FreeStorageSpace \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --threshold 10737418240 \
  --comparison-operator LessThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:ops-alerts
```

### SNS Integration

Alarms trigger SNS notifications:

```bash
# Create SNS topic
aws sns create-topic --name ops-alerts

# Create email subscription
aws sns subscribe --topic-arn arn:aws:sns:us-east-1:123456789012:ops-alerts \
  --protocol email --notification-endpoint alice@example.com

# When alarm triggers, email sent automatically
```

## 7.4 CloudTrail: Audit Logs

CloudTrail logs every API call (who, what, when, where).

```bash
# Enable CloudTrail
aws cloudtrail create-trail --name my-trail \
  --s3-bucket-name cloudtrail-logs

# Start logging
aws cloudtrail start-logging --trail-name my-trail

# Query events
aws cloudtrail lookup-events --lookup-attributes AttributeKey=ResourceName,AttributeValue=mydb
```

CloudTrail reveals:
- Who deleted the database (user, source IP, time)
- Who modified IAM policies
- All RDS modifications
- All S3 bucket changes

## 7.5 Centralized Logging Architecture

Production architecture for logging:

```
Application logs
    ↓
CloudWatch Logs
    ↓
CloudWatch Insights (search/analyze)
    ↓
S3 (long-term retention)
    ↓
Athena (SQL queries on S3 logs)
```

Pipeline:
```bash
# Application sends logs to CloudWatch
# CloudWatch log group → S3 export (daily)
aws logs create-export-task --log-group-name /myapp/requests \
  --from $(date -d 'yesterday' +%s)000 \
  --to $(date +%s)000 \
  --destination my-log-archive

# Query logs in S3 using Athena
aws athena start-query-execution \
  --query-string "SELECT * FROM myapp_logs WHERE error_code = '500'" \
  --query-execution-context Database=logs \
  --result-configuration OutputLocation=s3://my-query-results/
```

## 7.6 X-Ray: Distributed Tracing

X-Ray traces requests through your distributed system, showing latency and bottlenecks.

```python
from aws_xray_sdk.core import xray_recorder

# Instrument AWS SDK
xray_recorder.configure(service='MyApp')

# Wrap database call
@xray_recorder.capture('database_query')
def get_user(user_id):
    return db.query(f"SELECT * FROM users WHERE id = {user_id}")

# Wrap HTTP call
@xray_recorder.capture('external_api')
def call_payment_api():
    return requests.post('https://api.payment.com/charge', ...)

# Request trace shows:
# - Total latency: 500ms
#   ├─ database_query: 200ms
#   ├─ external_api: 250ms
#   └─ JSON serialization: 50ms
```

## 7.7 Common Mistakes

**Mistake 1: Not alerting on important metrics**
If you're not alerted on CPU, disk, database connections, you won't know until users complain.

**Mistake 2: Alert fatigue**
Alert on every metric spike and you'll ignore alerts. Set thresholds high enough to catch real problems.

**Mistake 3: Not retaining logs long enough**
Delete logs after 7 days and you can't debug last week's issue. Retain for at least 30 days (archive after).

**Mistake 4: Logging sensitive data**
Logging passwords, credit cards, SSNs is a security violation. Mask sensitive data before logging.

**Mistake 5: No baseline for normal**
If you don't know normal CPU is 40%, you can't recognize when 80% is abnormal. Establish baselines first.

## Assessment

### Practice Questions

**Q1: EC2 CPU alarm should trigger at 80% for how long before notifying?**
A) 1 minute (too sensitive)
B) 5-10 minutes (reasonable)
C) 1 hour (too delayed)
D) Only when it exceeds 95%

**Q2: You need to query logs from past month using SQL. Use:**
A) CloudWatch Insights
B) Athena on S3 logs
C) CloudTrail
D) X-Ray

**Q3: Database query suddenly takes 2 seconds (normally 200ms). How to diagnose?**
A) CloudWatch metrics only
B) X-Ray traces + CloudWatch metrics
C) CloudTrail (not useful here)
D) System logs only

**Q4: How long does CloudTrail retain events?**
A) 7 days
B) 30 days
C) 90 days (with S3 export for longer)
D) Indefinitely

**Q5: Application logs contain customer passwords. What to do?**
A) Log anyway; Logs are private
B) Filter passwords before logging
C) Use encryption (doesn't help after fact)
D) Don't log sensitive operations

### Hands-On Labs

**Lab 1: CloudWatch Monitoring**

Create EC2 alarm, trigger high CPU, verify alarm notification.

**Lab 2: Centralized Logging**

Set up CloudWatch Logs, export to S3, query with Athena.

### Production Incident Scenario

**Scenario: Slow Database Queries**

Users report "slow website" at 14:00. You have no idea where the bottleneck is.

Without X-Ray:
1. Check CloudWatch
2. EC2 CPU normal
3. Network normal
4. Must manually query database
5. Discover database connection pool exhausted
6. Discover slow query locking tables
7. Time to diagnosis: 45 minutes

With X-Ray:
1. Check X-Ray service map
2. See request → Database call (now 5 seconds!)
3. Check CloudWatch Logs for slow query
4. Identify and kill slow query
5. Time to diagnosis: 5 minutes

Prevention:
- Enable X-Ray from day one
- Set database query alarms (queries > 1 second)
- Monitor connection pool utilization
- Regular query performance analysis

---

Next Module: [Module 8: Security & Compliance](08-security-compliance.md)
