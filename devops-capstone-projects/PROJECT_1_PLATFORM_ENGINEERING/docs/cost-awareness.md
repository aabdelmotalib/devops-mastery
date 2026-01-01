# Cost Management & Optimization

## Monthly Cost Breakdown

### Infrastructure (AWS)

| Component | Instance Type | Quantity | Monthly Cost | Annual Cost |
|---|---|---|---|---|
| **EKS Cluster** | Managed Control Plane | 1 | $73 | $876 |
| **EC2 Nodes** | t3.medium | 3 | $180 | $2,160 |
| **RDS PostgreSQL** | db.t3.medium Multi-AZ | 1 | $300 | $3,600 |
| **RDS Read Replica** | db.t3.medium (optional) | 0 | $0 | $0 |
| **ElastiCache Redis** | cache.t3.micro Cluster | 1 | $50 | $600 |
| **Application Load Balancer** | ALB + 3 rules | 1 | $22.50 | $270 |
| **NAT Gateway** | Per hour + data transfer | 1 | $45 | $540 |
| **Route 53** | Hosted zone + queries | 1 | $5 | $60 |
| **Data Transfer** | Outbound internet | Variable | $50-100 | $600-1200 |
| **CloudWatch** | Logs + metrics | 1 | $20 | $240 |
| **S3 (backups)** | 100GB storage + archival | 1 | $5-10 | $60-120 |
| **Certificate (ACM)** | SSL/TLS | 1 | $0 | $0 |
| | | | | |
| **TOTAL** | | | **$750-800** | **$9,000-9,600** |

### Estimated Cost at Different Scales

| Metric | Cost | Notes |
|---|---|---|
| **Baseline (3 pods, 1 region)** | $750/month | Minimum production setup |
| **With scaling to 10 pods** | $900/month | During traffic spike |
| **With read replica** | $900/month | Add another database replica |
| **Multi-region (2 regions)** | $1,500/month | Double infrastructure |
| **High availability setup** | $1,200/month | Larger instances + redundancy |

---

## Cost Optimization Strategies

### 1. Use Reserved Instances (30% discount)

**Current:**
```
EC2: 3 × t3.medium on-demand = $180/month
```

**With 1-year reservation:**
```
1-year commitment: 3 × t3.medium × $0.0333/hour × 730 hours = $73/month
Savings: $107/month = $1,284/year
```

**Trade-off:**
- ✅ Huge savings (30%)
- ❌ 1-year commitment
- ❌ Cannot change instance type

**When to use:**
- ✅ Baseline workload (3-5 pods always running)
- ❌ Nodes expected to increase significantly

---

### 2. Use Spot Instances (70% discount)

**Current:**
```
3 pods always running (baseline): t3.medium on-demand
Additional pods during peak: t3.medium on-demand
```

**With Spot instances:**
```
Baseline (reserved): 3 × $0.0333/hour = $0.10/hour
Peak overload (spot): 5 × $0.0099/hour = $0.05/hour

Monthly cost: ($0.10 × 730) + ($0.05 × 4) = $73 + $0.20 = $73.20
Savings: 70% on excess capacity

Risk: Spot instances can be interrupted (2-minute notice)
Solution: Only use for stateless workloads (ok for API)
```

**Kubernetes Spot integration:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 3
  template:
    spec:
      # Reserve node for spot instances
      affinity:
        nodeAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            preference:
              matchExpressions:
              - key: karpenter.sh/capacity-type
                operator: In
                values: ["spot"]
```

---

### 3. Right-size Instances

**Current estimation:**
```
Flask app with 50 requests/sec
Memory: 100MB per pod × 3 = 300MB total
CPU: 50mCPU per pod × 3 = 150mCPU total
```

**Can we use smaller instances?**
```yaml
# Current: t3.medium (2 CPU, 4GB RAM)
# 3 pods use: 300MB RAM, 150mCPU

# Could use: t3.small (2 CPU, 2GB RAM)
# 3 pods use: 300MB RAM, 150mCPU (same)
# Cost: t3.small = $0.023/hour vs t3.medium = $0.0332/hour
# Savings: 30%

# Even better: Use t4g.small (Graviton2 ARM)
# Same performance, 20% cheaper
```

**Measurements:**
```bash
# Check actual usage
kubectl top nodes
# NAME           CPU(cores)  CPU%   MEMORY(Mi)  MEMORY%
# node-1         150m       7%     300Mi        7%
# node-2         140m       7%     290Mi        7%
# node-3         145m       7%     310Mi        7%

# Conclusion: Massively overprovisioned
# Can downsize to t3.small safely
```

---

### 4. Optimize Database Costs

**Current: db.t3.medium Multi-AZ = $300/month**

**Options to reduce:**

```
Option 1: Use db.t3.micro ($30/month)
- Works for development/testing
- Production: Insufficient CPU/memory

Option 2: Single-AZ (not Multi-AZ) = $150/month
- Saves $150/month
- Risk: No automatic failover
- Not recommended for production

Option 3: Use Aurora MySQL (cheaper than PostgreSQL)
- Aurora MySQL: $250/month
- PostgreSQL RDS: $300/month
- Savings: $50/month
- Trade-off: Limited to AWS (less portable)

Option 4: Use RDS Proxy for connection pooling
- Reduces connection overhead
- Better resource utilization
- Cost: $0.30/hour = $220/month
- Savings offset: Reduces need for larger instance
```

**Decision: Keep Multi-AZ (non-negotiable for production)**

---

### 5. Optimize Data Transfer Costs

**Current: ~$50-100/month for outbound internet traffic**

**Optimization:**

```yaml
# 1. Use VPC endpoints (avoid NAT Gateway)
# Current: Data through NAT Gateway = $0.045/GB + $45/month
# With VPC Endpoint: $7.20/month per service

# For S3, DynamoDB, etc.
apiVersion: ec2.amazonaws.com/v1
kind: VPCEndpoint
spec:
  VpcId: vpc-12345
  ServiceName: com.amazonaws.us-east-1.s3
  RouteTableIds:
    - rtb-12345

# Savings: $45 - $7.20 = $37.80/month on NAT

# 2. Use CloudFront (CDN)
# Reduce origin requests
# Edge caching at 200+ locations
# Cheaper data transfer ($0.085/GB vs $0.09 from EC2)
```

**Total data transfer savings: $30-40/month**

---

### 6. Optimize Logging Costs

**Current: CloudWatch Logs**
```
Ingestion: 10GB/day = $5/day = $150/month
Storage: 365 days × 10GB = $2/month
Total: ~$152/month
```

**Optimization options:**

```yaml
# Option 1: Use S3 for long-term storage
# CloudWatch (7 days): $5/day × 7 = $35/month
# S3 (365 days): $0.023/GB × 300GB = $6.90/month
# Savings: $110/month

# Option 2: Use Loki (cheaper for Kubernetes)
# Loki storage: $0.01/GB/month vs $0.03 for CloudWatch
# Loki (365 days): 300GB × $0.01 = $3/month
# Savings: $149/month

# Option 3: Sample logs (don't log everything)
# Log only:
#   - Errors
#   - Auth events
#   - Slow queries
# Reduce volume: 10GB → 1GB/day = 90% savings
```

**Recommended: Loki + S3 archival**
```
Loki (searchable, 7 days): ~$30/month
S3 (archive, 365 days): ~$7/month
Total: ~$37/month
Current CloudWatch: $152/month
Savings: $115/month
```

---

### 7. Optimize Monitoring Costs

**Current: Prometheus + Grafana (self-hosted)**
```
Prometheus storage: 10GB SSD in EBS = $1/month
Grafana: Runs on API pod (included)
Total: ~$1/month
```

**Alternative: Managed monitoring**
```
CloudWatch: 50 metrics × $0.30/month = $15/month
Datadog: $15/host/month × 3 = $45/month
New Relic: $100/month
Prometheus (self-hosted): $1/month
```

**Decision: Keep self-hosted Prometheus**

---

## Cost Reduction: Before & After

| Component | Before | After | Savings |
|---|---|---|---|
| **EC2 (On-demand)** | $180 | $73 (Reserved) | $107/month |
| **Data Transfer** | $100 | $65 (VPC Endpoint) | $35/month |
| **Logging** | $152 | $37 (Loki) | $115/month |
| **Database** | $300 | $300 (keep Multi-AZ) | $0 |
| **Total** | **$732** | **$475** | **$257/month** |

**Annual savings: $3,084 (42% reduction)**

---

## Cost Monitoring & Alerts

### AWS Budgets (Alert on overspending)

```yaml
Name: Monthly Budget
Limit: $500
Alert threshold:
  - 80%: Actual
  - 100%: Projected
Notifications: Email to ops@example.com
```

### Cost Analysis Queries

```sql
-- Monthly spending by service
SELECT service, cost, month
FROM aws_costs
WHERE month = CURRENT_MONTH
GROUP BY service
ORDER BY cost DESC;

-- Forecast next month
SELECT 
  service,
  AVG(daily_cost) * 30 as projected_monthly
FROM aws_costs
WHERE month >= CURRENT_MONTH - 3
GROUP BY service;

-- Find cost anomalies
SELECT date, service, cost
FROM aws_costs
WHERE cost > (
  SELECT AVG(cost) * 1.5
  FROM aws_costs
  WHERE service = 'EC2'
);
```

### Kubernetes Cost Attribution

```yaml
# Add labels for cost tracking
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  labels:
    app: api
    cost-center: "engineering"
    environment: "production"
spec:
  template:
    metadata:
      labels:
        app: api
        team: "backend"
    spec:
      containers:
      - name: api
        resources:
          requests:
            cpu: 500m      # $36/month per core
            memory: 512Mi  # $5/month per GB
          limits:
            cpu: 1000m
            memory: 1Gi

# Cost calculation
# 3 pods × (0.5 CPU × $36 + 0.5GB × $5) = 3 × $19 = $57/month for API
# Plus infrastructure overhead ($300/month) → $357/month total
```

---

## When to Spend More

**Not all cost reductions are good:**

| Cost | Recommendation | Reason |
|---|---|---|
| **Database HA** | Keep Multi-AZ | $150/month worth data safety |
| **Backups** | Keep daily | $5/month for data recovery |
| **Monitoring** | Minimal | $1/month Prometheus sufficient |
| **Logging** | Optimize | Can save $100/month with Loki |
| **Redundancy** | Keep 3+ pods | HA more important than cost |

**Break-even analysis:**
```
Cost of downtime: $10,000/hour
Probability of failure without Multi-AZ: 1% per year
Expected cost of failure: $10,000 × 0.01 × 8 hours = $800
Cost of Multi-AZ: $150/month × 12 = $1,800
Expected loss without Multi-AZ: $800 + $1,800 (downtime not prevented) = $2,600
With Multi-AZ: $1,800 + $0 (prevented failure) = $1,800
Savings: $800/year → Multi-AZ is worth it
```

---

## Interview Points

**Q: "How would you reduce costs by 50%?"**
A: "Reserve instances for baseline (30%), use Spot for burst (70%), optimize logging (Loki instead of CloudWatch), use VPC endpoints. Total: 42% savings. Further: single-AZ (risky), smaller instances (after measuring), serverless (Fargate/Lambda)."

**Q: "When is cost NOT the priority?"**
A: "When reliability is critical: Keep Multi-AZ, redundancy, monitoring. When preventing downtime costs $10k/hour, spending $150/month on HA is 100x ROI."

**Q: "How do you measure if cost optimization broke something?"**
A: "Monitor: Error rate, latency, availability. If error rate increases > 0.1%, revert optimization immediately. Measure cost savings vs risk."

**Q: "What's the single most impactful optimization?"**
A: "Reserve instances for baseline load. 30% savings on compute without changing architecture. Everything else is incremental."
