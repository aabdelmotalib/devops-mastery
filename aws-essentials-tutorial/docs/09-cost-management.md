# Module 9: Cost Management & Optimization

AWS billing grows quietly. A misconfigured job can cost $1000/day before you notice. Cost optimization isn't an afterthought; it's ongoing operations.

## 9.1 Cost Structure

AWS charges for:
- **Compute**: Per instance per hour (or per second)
- **Storage**: Per GB per month
- **Data transfer**: Per GB out (inter-region, to internet)
- **Database**: Per instance per hour or per request
- **Services**: Per function call, per API request, etc.

### Monthly Bill Estimate

Typical three-tier app:
- 2 EC2 t3.medium on-demand: $0.0416/hour × 730 = $60.36
- 1 RDS db.t3.micro multi-AZ: $0.054/hour × 730 = $39.42
- 100 GB S3: $2.30
- 100 GB data transfer (outbound): $9.00/month
- Total: ~$110/month

Multiply by 12 months: $1,320/year

## 9.2 Cost Explorer

Visualize spending by service, linked account, tag, etc.

```bash
# Get current month cost by service
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --group-by Type=DIMENSION,Key=SERVICE
```

Console:
1. Open Cost Explorer
2. Select date range
3. Group by Service, Linked Account, or Tag
4. Identify which services cost most

## 9.3 Right-Sizing Recommendations

AWS provides right-sizing recommendations (available in Cost Anomaly Detection).

### Identify Overprovisioned Resources

```bash
# EC2 instances with < 5% CPU average (likely oversized)
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-0123456789abcdef0 \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-31T23:59:59Z \
  --period 86400 \
  --statistics Average

# If average < 10%, downsize
# t3.xlarge running at 5% CPU → resize to t3.medium
```

Savings example:
- t3.xlarge: $0.1664/hour = $121/month
- t3.medium: $0.0416/hour = $30/month
- Savings: $91/month ($1,092/year) for same workload

## 9.4 Pricing Models

### On-Demand: Highest Flexibility, Highest Cost

Best for:
- Development/testing (turn off when not in use)
- Unpredictable workloads
- Short-term projects

Cost: Full hourly rate

### Reserved Instances (RI): 1-3 Year Commitment

Best for:
- Production workloads (24/7 running)
- Predictable capacity

Options:
- **All Upfront**: Largest discount (40% for 1-year, 60% for 3-year), pay entire cost at purchase
- **Partial Upfront**: Medium discount (35% for 1-year), pay portion upfront, hourly for remainder
- **No Upfront**: Smallest discount (25% for 1-year), hourly rate reduced

Cost example (t3.micro):
- On-demand: $0.0116/hour × 730 = $8.47/month
- 1-year RI (all upfront): $67/year = $5.58/month (34% savings)
- 3-year RI (all upfront): $124/year = $3.44/month (59% savings)

Strategy: Use RIs for predictable production. Don't reserve development (turn off at 5 PM).

### Spot Instances: 70-90% Discount, Interruptible

Best for:
- Batch jobs (can be interrupted and retried)
- CI/CD build servers (can resume)
- Non-critical background tasks

Risk: AWS can terminate with 2-minute notice if capacity needed.

Cost example:
- On-demand t3.micro: $8.47/month
- Spot t3.micro: $1.70/month (80% savings)

Strategy: Use spot for everything that can handle interruption.

### Savings Plans: Commit to Compute Usage

Best for:
- Flexibility across instance types
- Multi-region deployments

Compute Savings Plans: Discount applies across t3, m5, c5, r5 instance types globally.

Cost example:
- Instance Savings Plan (t3.medium reserved): $0.0298/hour
- Compute Savings Plan: $0.01/hour discount on any instance type
- Switching to t3.small: $0.0104/hour - $0.01 = $0.0004/hour (essentially free)

## 9.5 Cost Anomaly Detection

CloudWatch detects unexpected cost spikes automatically.

```bash
# Enable anomaly detection on Cost and Usage Report
aws ce create-anomaly-monitor --anomaly-monitor '{
  "MonitorName": "daily-spend-anomaly",
  "MonitorType": "DIMENSIONAL",
  "MonitorDimension": "SERVICE",
  "MonitorSpecification": {
    "Dimensions": ["SERVICE"]
  }
}'

# Alert when actual spend > expected by 50%
aws ce create-anomaly-subscription --subscription-name alert-large-spend \
  --threshold 50 \
  --frequency DAILY
```

Common anomalies:
- Misconfigured NAT gateway (high data transfer)
- Runaway autoscaling (too many instances)
- DataSync job continuously running
- Old snapshots accumulating

## 9.6 Cost Optimization Checklist

- [ ] Right-size EC2 instances (check CPU usage)
- [ ] Terminate unused EC2 instances and RDS databases
- [ ] Use reserved instances for predictable 24/7 workloads
- [ ] Use spot instances for batch/CI/CD
- [ ] Delete old EBS snapshots (retain only 30 days)
- [ ] Delete old RDS snapshots
- [ ] Enable S3 lifecycle (move old data to Glacier)
- [ ] Disable unnecessary CloudWatch logs (retain 30 days minimum)
- [ ] Enable detailed monitoring only where needed (standard monitoring is cheaper)
- [ ] Use VPC endpoints instead of NAT gateways (save on data transfer)
- [ ] Consolidate EC2 instances across regions
- [ ] Use DynamoDB on-demand for unpredictable workloads
- [ ] Review data transfer costs (often 20-30% of bill)
- [ ] Use S3 intelligent-tiering for unknown access patterns
- [ ] Terminate unused RDS read replicas

## 9.7 Common Mistakes

**Mistake 1: Not setting billing alerts**
You don't notice $10,000 bill until month-end invoice. Set budget alert: if spend > $500/day, notify.

```bash
aws budgets create-budget --account-id 123456789012 \
  --budget BudgetName=monthly-limit,BudgetLimit='{Amount=5000,Unit=USD}' \
  --notifications-with-subscribers '[{
    "Notification": {"NotificationType": "ACTUAL", "ComparisonOperator": "GREATER_THAN", "Threshold": 100},
    "Subscribers": [{"SubscriptionType": "SNS", "Address": "alerts@example.com"}]
  }]'
```

**Mistake 2: Running on-demand when predictable**
Predictable production workload should use reserved instances. Savings: 40-60%.

**Mistake 3: Leaving resources running after testing**
Launch EC2 for testing, forget to terminate. Costs $0.10/day × 365 = $37/year per instance.

**Mistake 4: High data transfer costs**
Each GB of data transferred out costs $0.09. Moving 1 TB = $90. Use CloudFront caching to reduce.

**Mistake 5: Not deleting old snapshots**
RDS snapshots are charged per GB per month. 100 GB snapshot costs $23/month. Delete after 30 days unless needed for compliance.

## 9.8 Production Notes

### Cost Monitoring Dashboard

Create custom dashboard:
```
Daily Spend Trend
├─ EC2: $X
├─ RDS: $Y
├─ Data Transfer: $Z
└─ Other: $W

Monthly Projection
└─ If trend continues: $TOTAL/month
```

Review daily. If projection > budget, investigate why.

### Cost Allocation Tags

Tag all resources by cost center, team, project:

```bash
# Tag EC2
aws ec2 create-tags --resources i-0123456789abcdef0 \
  --tags Key=CostCenter,Value=engineering Key=Team,Value=backend

# Tag RDS
aws rds add-tags-to-resource --resource-name arn:aws:rds:us-east-1:123456789012:db:mydb \
  --tags Key=CostCenter,Value=engineering Key=Team,Value=backend
```

In Cost Explorer, group by CostCenter tag to see who's spending how much.

## Assessment

### Practice Questions

**Q1: Predictable workload running 24/7. Best pricing?**
A) On-demand (most flexible)
B) 1-year Reserved Instance (40% savings)
C) 3-year Reserved Instance (60% savings)
D) Spot (80% savings)

**Q2: Batch job that can be interrupted. Best pricing?**
A) On-demand
B) Reserved Instance
C) Spot Instance (80% discount)
D) Savings Plan

**Q3: EC2 showing 5% CPU average. Right-sizing action?**
A) Downsize to smaller instance type
B) Upgrade to larger instance
C) Launch more instances
D) No change

**Q4: How much does 1 GB of data transfer out cost?**
A) Free
B) $0.01
C) $0.09
D) $0.50

**Q5: What's the best way to reduce data transfer costs?**
A) Use reserved instances
B) CloudFront caching
C) Right-sizing
D) Delete old logs

### Hands-On Labs

**Lab 1: Cost Explorer Analysis**

View spending by service, identify top 3 cost drivers, calculate monthly projection.

**Lab 2: Right-Sizing Exercise**

Identify overprovisioned instances, calculate savings from downsizing.

### Production Incident Scenario

**Scenario: Unexpected $15,000 Bill**

Month-end AWS bill is $15,000 (normally $500). Investigation reveals:
- Data transfer: $12,000 (normally $50)
- EC2: $2,500 (normally $100)
- RDS: $500 (normal)

Root cause: DataSync job misconfigured, copying 500 GB/day between regions (uncompressed).

Timeline:
- Day 1: Job runs, 50 GB transferred = $4.50
- Day 2: 100 GB = $9
- Day 3: 200 GB = $18
- ...
- Day 30: 500 GB = $45/day × 30 days = $1,350

Plus 100 EC2 instances launched for some batch job left running.

Recovery:
1. Identify the DataSync job (CloudTrail shows creation 30 days ago)
2. Disable the job
3. Terminate rogue EC2 instances
4. Request credit for obvious misconfiguration

Prevention:
- Cost anomaly alerts (would detect 10x normal spend on day 2)
- CloudTrail alerts on large resource creation
- Daily cost review
- Budget alarms

---

Next Module: [Module 10: Advanced Services Overview](10-advanced-services.md)
