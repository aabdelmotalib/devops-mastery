# Module 6: Cloud-Native Observability with AWS CloudWatch

AWS CloudWatch is the native observability service for AWS. This module covers metrics, logs, alarms, and integration patterns.

## CloudWatch Architecture

```
AWS Resources (EC2, Lambda, RDS, etc)
        ↓
CloudWatch Metrics (Time-series data)
        ↓
CloudWatch Logs (Log aggregation)
        ↓
CloudWatch Alarms (Alerting)
        ↓
Notifications (SNS, Lambda, Auto Scaling)
```

### CloudWatch Metrics

Every AWS service publishes metrics:
- EC2: CPU, network, disk
- RDS: connections, queries, latency
- ELB: request count, latency, errors
- Lambda: invocations, duration, errors
- DynamoDB: throughput, latency, throttles

**Custom metrics**: Applications can publish via API/SDK

### CloudWatch Logs

Log aggregation for AWS services and applications:
- EC2 instance logs via CloudWatch Agent
- Lambda function logs (automatic)
- RDS slow query logs
- Application logs (via SDK/agent)

### CloudWatch Alarms

Monitor metrics and trigger actions:
- Send SNS notifications
- Trigger Lambda functions
- Auto Scaling actions
- EC2 instance actions (reboot, stop)

### CloudWatch Dashboards

Visualize metrics and logs

## Sending Custom Metrics

### From EC2 Instances

**CloudWatch Agent on EC2**:

```bash
# Install agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm

# Configure
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard

# Start
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
```

**Configuration (JSON)**:
```json
{
  "metrics": {
    "namespace": "MyApp",
    "metrics_collected": {
      "cpu": {
        "measurement": [
          {
            "name": "cpu_usage_idle",
            "rename": "CPU_USAGE_IDLE",
            "unit": "Percent"
          }
        ],
        "metrics_collection_interval": 60
      },
      "mem": {
        "measurement": [
          {
            "name": "mem_used_percent",
            "rename": "MEM_USED_PERCENT",
            "unit": "Percent"
          }
        ],
        "metrics_collection_interval": 60
      },
      "disk": {
        "measurement": [
          {
            "name": "used_percent",
            "rename": "DISK_USED_PERCENT",
            "unit": "Percent"
          }
        ],
        "metrics_collection_interval": 60,
        "resources": ["/"]
      }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/application.log",
            "log_group_name": "/aws/ec2/application",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
```

### From Applications (SDK)

**Python example**:
```python
import boto3
from datetime import datetime

cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')

# Put custom metric
cloudwatch.put_metric_data(
    Namespace='MyApplication',
    MetricData=[
        {
            'MetricName': 'ProcessingTime',
            'Value': 254.5,
            'Unit': 'Milliseconds',
            'Timestamp': datetime.utcnow(),
            'Dimensions': [
                {'Name': 'Service', 'Value': 'api'},
                {'Name': 'Environment', 'Value': 'production'}
            ]
        }
    ]
)
```

### From Containers

**ECS Task with CloudWatch Container Insights**:

```json
{
  "containerDefinitions": [
    {
      "name": "app",
      "image": "myapp:latest",
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/myapp",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

## CloudWatch Logs Insights

Powerful log analysis query language:

**Basic query**:
```
fields @timestamp, @message
| filter @message like /ERROR/
| stats count() as error_count
```

**Request latency analysis**:
```
fields @timestamp, @duration
| filter @duration > 1000
| stats avg(@duration), max(@duration), pct(@duration, 95) as p95
```

**Error rate by service**:
```
fields service, @message
| filter @message like /error/
| stats count() as error_count by service
```

**Time-based analysis**:
```
fields @timestamp, @message, response_time
| filter ispresent(response_time)
| stats avg(response_time) as avg_time by bin(5m)
```

## CloudWatch Alarms

### Alarm Configuration

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

# Create alarm for high CPU
cloudwatch.put_metric_alarm(
    AlarmName='HighCPU',
    MetricName='CPUUtilization',
    Namespace='AWS/EC2',
    Statistic='Average',
    Period=300,  # 5 minutes
    EvaluationPeriods=2,  # 2 periods = 10 minutes
    Threshold=80.0,
    ComparisonOperator='GreaterThanThreshold',
    Dimensions=[
        {'Name': 'InstanceId', 'Value': 'i-1234567890abcdef0'}
    ],
    AlarmActions=[
        'arn:aws:sns:us-east-1:123456789012:MyTopic'
    ]
)

# Create composite alarm (combine multiple)
cloudwatch.put_composite_alarm(
    AlarmName='ServiceHealthy',
    AlarmRule='(ALARM(HighCPU) OR ALARM(HighMemory)) AND ALARM(NetworkDown)',
    ActionsEnabled=True,
    AlarmActions=[
        'arn:aws:sns:us-east-1:123456789012:AlertTopic'
    ]
)
```

### Alarm States

- **ALARM**: Threshold breached
- **OK**: Threshold not breached
- **INSUFFICIENT_DATA**: Not enough data to evaluate

## CloudWatch Insights for Application Monitoring

### Application Insights

Detects anomalies and correlates logs with metrics:

```python
# CloudWatch automatically monitors:
- EC2 application error logs
- Performance metrics
- Resource utilization
- Anomalies and correlations
```

### Integration with SNS and Lambda

**SNS for notifications**:
```python
cloudwatch.put_metric_alarm(
    AlarmName='HighErrorRate',
    MetricName='ErrorCount',
    Namespace='MyApp',
    Statistic='Sum',
    Period=60,
    Threshold=10,
    ComparisonOperator='GreaterThanThreshold',
    AlarmActions=[
        'arn:aws:sns:us-east-1:123456789012:alert-topic'
    ]
)
```

**Lambda for custom actions**:
```python
# Alarm triggers Lambda function
# Lambda can auto-remediate, notify teams, etc

def lambda_handler(event, context):
    # Parse CloudWatch alarm notification
    message = json.loads(event['Records'][0]['Sns']['Message'])
    
    if message['NewStateValue'] == 'ALARM':
        # Auto-scaling, auto-healing, etc
        print(f"Alarm triggered: {message['AlarmName']}")
        # Take action...
```

## Multi-Region Monitoring

```python
# Monitor resources across regions
regions = ['us-east-1', 'us-west-2', 'eu-west-1']

for region in regions:
    cw = boto3.client('cloudwatch', region_name=region)
    
    # Get metrics per region
    response = cw.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName='CPUUtilization',
        Dimensions=[...],
        StartTime=datetime.utcnow() - timedelta(hours=1),
        EndTime=datetime.utcnow(),
        Period=300,
        Statistics=['Average']
    )
```

## Cost Optimization

### Log Retention

```python
# Set retention on log group
cloudwatch.put_retention_policy(
    logGroupName='/aws/lambda/myfunction',
    retentionInDays=7  # 7 days instead of infinite
)
```

### Metric Filtering

```python
# Only send important metrics
metric_filter = {
    'logGroupName': '/aws/lambda/myfunction',
    'filterPattern': '[ERROR]',  # Only ERROR logs
    'metricTransformations': [
        {
            'metricName': 'ErrorCount',
            'metricNamespace': 'MyApp',
            'metricValue': '1'
        }
    ]
}
```

## Best Practices

### 1. Dimensions for Filtering

```python
# Always include dimensions
MetricData=[
    {
        'MetricName': 'APILatency',
        'Value': 254,
        'Dimensions': [
            {'Name': 'Service', 'Value': 'api'},
            {'Name': 'Environment', 'Value': 'prod'},
            {'Name': 'Endpoint', 'Value': '/users'},
        ]
    }
]
```

### 2. Alarm Naming

```
Good: "API-Error-Rate-GT-5%-5min-prod"
Bad: "alarm1"

Pattern: {Service}-{Metric}-{Operator}-{Threshold}-{Period}-{Environment}
```

### 3. Composite Alarms

```python
# Better than many separate alarms

# Create atomic alarms first
cpu_alarm = "CPU-High"
memory_alarm = "Memory-High"

# Then combine
composite = "(ALARM(CPU-High) AND ALARM(Memory-High))"
# Fire only when both are true
```

## Exam Questions

1. **What is CloudWatch Container Insights?**
   - A. Container image scanning
   - B. Container cost analysis
   - C. Monitoring metrics from ECS/Kubernetes
   - D. Container network tracing

2. **CloudWatch Logs Insights is used for:**
   - A. Storing logs permanently
   - B. Ad-hoc log analysis and queries
   - C. Real-time log streaming
   - D. Log encryption

3. **What triggers a CloudWatch alarm?**
   - A. Log message contains keyword
   - B. Metric crosses threshold for configured duration
   - C. Manual API call only
   - D. Event from EventBridge

4. **For cost optimization, what should you do with log groups?**
   - A. Keep logs forever
   - B. Set retention policies
   - C. Delete after 1 day
   - D. Archive to S3 immediately

5. **In CloudWatch, what are Dimensions used for?**
   - A. Compress metric data
   - B. Add filtering/grouping to metrics
   - C. Measure performance
   - D. Store custom data

## Hands-On Tasks

### Task 1: Set Up CloudWatch Agent on EC2

Deploy CloudWatch Agent, configure metrics collection, and view in CloudWatch dashboard.

### Task 2: Create CloudWatch Alarms and Notifications

Create composite alarms for service health with SNS notifications.

## Production Incident Scenario

**Scenario**: Lambda functions silently failing, CloudWatch shows no errors

Debug why CloudWatch isn't capturing errors and set up proper monitoring.

---

**Version**: 1.0  
**Time**: 6-8 hours
