# Advanced AWS: Fargate & Managed Container Services

## Overview

This module covers **AWS Fargate**, AWS's fully managed container execution platform, and how it differs from EC2-based container orchestration. You'll learn when Fargate makes sense, cost modeling, and production patterns.

## Mental Model

```
Traditional EC2:
You launch instance → manage OS → manage networking → run container → scale instances
(You manage compute)

Fargate:
You define container spec → AWS handles everything else → focus on application
(AWS manages compute)

         Container Code
                ↓
         Task Definition
                ↓
          Fargate (managed)
                ↓
         Automatic Scaling
                ↓
         Automatic Networking
```

## Key Insight

Fargate is **not cheaper**, but it's **simpler**. Choose based on:
- **Use Fargate if:** Unpredictable load, startup/shutdown quickly, don't need custom OS
- **Use EC2 if:** Predictable baseline, always-on workloads, need full OS control

## Cost Model Deep Dive

### EC2 Launch Type

```
Fixed cost: m5.large instance = $0.096/hour = ~$70/month
            (even if empty)

Variable: Depends on utilization
          CPU + Memory allocated to tasks

Example: Single m5.large instance
- 2 vCPU, 8GB RAM
- Run 1 task (2 vCPU, 4GB) = $70/month
- Run 4 tasks (0.5 vCPU, 1GB each) = $70/month
✅ Better for steady-state workloads
```

### Fargate Launch Type

```
No fixed cost—pay per task execution

Pricing per task:
= (GB-hours × $0.04746) + (vCPU-hours × $0.04556)

Example: 0.25 vCPU, 512MB RAM, 24/7
= (730 hours × 0.512GB × $0.04746) + (730 × 0.25 × $0.04556)
= $17.89 + $8.34 = $26.23/month

✅ Better for bursty workloads
```

## When NOT to Use Fargate

```
❌ GPU workloads (not available on Fargate)
❌ Require >4 vCPU (Fargate max) and high RAM
❌ Need direct instance access (no SSH into Fargate)
❌ Domain-specific hardware accelerators
❌ Cost-sensitive always-on workloads (EC2 reserved instances cheaper)
```

## Production Pattern: Fargate with Auto Scaling

```bash
# Step 1: Create task definition (remember: CPU in 256 increments)
aws ecs register-task-definition \
  --family web-api \
  --requires-compatibilities FARGATE \
  --network-mode awsvpc \
  --cpu 512 \
  --memory 1024 \
  --container-definitions '[{
    "name": "api",
    "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/api:latest",
    "portMappings": [{"containerPort": 8000}],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/api",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "ecs"
      }
    }
  }]'

# Step 2: Create Fargate service
aws ecs create-service \
  --cluster production \
  --service-name api \
  --task-definition web-api \
  --desired-count 3 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-1,subnet-2],securityGroups=[sg-fargate],assignPublicIp=DISABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=api,containerPort=8000" \
  --service-registries "registryArn=arn:aws:servicediscovery:..."

# Step 3: Set up auto scaling policy
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/production/api \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 20

# CPU-based scaling
aws application-autoscaling put-scaling-policy \
  --policy-name cpu-scaling \
  --service-namespace ecs \
  --resource-id service/production/api \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration "TargetValue=70,PredefinedMetricSpecification={PredefinedMetricType=ECSServiceAverageCPUUtilization},ScaleOutCooldown=60,ScaleInCooldown=300"

# Memory-based scaling
aws application-autoscaling put-scaling-policy \
  --policy-name memory-scaling \
  --service-namespace ecs \
  --resource-id service/production/api \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration "TargetValue=80,PredefinedMetricSpecification={PredefinedMetricType=ECSServiceAverageMemoryUtilization},ScaleOutCooldown=60,ScaleInCooldown=300"

# Step 4: Monitor
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=api \
  --start-time 2025-01-06T00:00:00Z \
  --end-time 2025-01-06T23:59:59Z \
  --period 300 \
  --statistics Average,Maximum
```

## Networking in Fargate

Fargate requires **awsvpc network mode**:

```
Each task gets its own ENI (Elastic Network Interface)
with its own IP address, security group, network rules

┌────────────────────────┐
│  VPC (10.0.0.0/16)     │
│  ┌──────────────────┐  │
│  │  Public Subnet   │  │
│  │  10.0.1.0/24     │  │
│  │                  │  │
│  │  Task 1: ENI     │  │
│  │  Task 2: ENI     │  │
│  │  Task 3: ENI     │  │
│  └──────────────────┘  │
│  ┌──────────────────┐  │
│  │  Private Subnet  │  │
│  │  10.0.2.0/24     │  │
│  │  (RDS, cache)    │  │
│  └──────────────────┘  │
└────────────────────────┘
```

**Best practice:** Run tasks in private subnets, use NAT gateway for outbound traffic

```bash
# Security group for Fargate tasks
aws ec2 create-security-group \
  --group-name fargate-tasks \
  --description "Fargate task security group" \
  --vpc-id vpc-12345

# Allow inbound from ALB
aws ec2 authorize-security-group-ingress \
  --group-id sg-fargate \
  --protocol tcp \
  --port 8000 \
  --source-security-group-id sg-alb

# Allow outbound to RDS
aws ec2 authorize-security-group-egress \
  --group-id sg-fargate \
  --protocol tcp \
  --port 5432 \
  --destination-security-group-id sg-rds
```

## Logging in Fargate

Fargate automatically sends logs to CloudWatch:

```python
# Your code just prints to stdout
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler():
    logger.info("Starting processing...")  # Goes to CloudWatch
    process_data()
    logger.info("Complete")

# CloudWatch log group: /ecs/{task-family}
# CloudWatch log stream: {task-family}/{task-id}
```

## Common Mistakes

**Mistake 1: Wrong CPU/memory combination**
```bash
# ❌ WRONG: Invalid combination (CPU must be 256, 512, 1024, 2048, 4096)
aws ecs register-task-definition \
  --cpu 500 \
  --memory 512

# ✅ RIGHT: Valid combinations
CPU 256:  512MB, 1GB, 2GB
CPU 512:  1GB, 2GB, 3GB, 4GB
CPU 1024: 2GB-8GB (in 1GB increments)
CPU 2048: 4GB-16GB (in 1GB increments)
```

**Mistake 2: Tasks in public subnet with public IP**
```bash
# ❌ WRONG: Directly exposed to internet
aws ecs create-service \
  --network-configuration "awsvpcConfiguration={subnets=[public-subnet],assignPublicIp=ENABLED}"

# ✅ RIGHT: Private subnet, behind ALB
aws ecs create-service \
  --network-configuration "awsvpcConfiguration={subnets=[private-subnet],securityGroups=[sg-fargate],assignPublicIp=DISABLED}"
```

**Mistake 3: No health check defined**
```bash
# ❌ WRONG: ALB doesn't know if task is healthy
aws ecs create-service --service-name api --load-balancers ...

# ✅ RIGHT: Define health check path
aws elbv2 modify-target-group \
  --target-group-arn arn:... \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3
```

**Mistake 4: Scaling on wrong metric**
```bash
# ❌ WRONG: Scale on CPU when memory is bottleneck
aws application-autoscaling put-scaling-policy \
  --target-tracking-scaling-policy-configuration "{PredefinedMetricSpecification={PredefinedMetricType=ECSServiceAverageCPUUtilization},TargetValue=70}"

# ✅ RIGHT: Monitor both, scale on the actual bottleneck
# Use CloudWatch metrics to identify: Is it CPU or memory?
# Scale on whichever hits limit first
```

**Mistake 5: No resource requests in ECS service**
```bash
# ❌ WRONG: No constraints on task resource requirements
aws ecs register-task-definition \
  --container-definitions '[{"name":"app","image":"app:latest"}]'

# ✅ RIGHT: Explicit resource requests
aws ecs register-task-definition \
  --cpu 512 \
  --memory 1024 \
  --container-definitions '[{"name":"app","image":"app:latest","memory":1024}]'
```

## Production Incident Scenario

### Scenario: "Fargate tasks failing after scaling up"

**Symptoms:**
- Service scaled from 3 to 20 tasks
- New tasks stuck in "PROVISIONING" state
- After 1 minute, status changes to "STOPPED"
- CloudWatch logs: "InsufficientMemory"

**Investigation:**

```bash
# 1. Check task status
aws ecs describe-tasks \
  --cluster production \
  --tasks arn:aws:ecs:... \
  | grep lastStatus

# Result: "STOPPED" with stopCode: "InsufficientMemory"

# 2. Check subnet IP availability
aws ec2 describe-subnets \
  --subnet-ids subnet-1 subnet-2 \
  --query 'Subnets[].{Subnet:SubnetId,AvailableIPs:AvailableIpAddressCount}'

# Result: subnet-1 has 0 available IPs!
# Each Fargate task needs an IP address
```

**Root Cause:** Subnets ran out of IP addresses. With 20 tasks × 3 subnets, needed 60 IPs, but subnets only had /28 (16 IPs).

**Solution:**

```bash
# 1. Expand subnet CIDR (requires recreating subnet - disruptive)
# Better: Expand VPC CIDR and add more subnets

# 2. Temporarily scale down
aws ecs update-service \
  --cluster production \
  --service api \
  --desired-count 10

# 3. Create larger subnet
aws ec2 create-subnet \
  --vpc-id vpc-12345 \
  --cidr-block 10.0.4.0/24  # /24 = 256 IPs

# 4. Add to ECS task placement
aws ecs update-service \
  --cluster production \
  --service api \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-1,subnet-2,subnet-3,subnet-new]}" \
  --desired-count 20

# 5. Monitor
aws ecs describe-services --cluster production --services api
```

**Prevention:**
- Plan IP address space before scaling
- Use /24 subnets (256 IPs) for production
- Monitor available IPs in CloudWatch
- Calculate: max_tasks × 1 IP/task ≤ available IPs

## Practice Questions

1. **Cost calculation:** 100 always-on Fargate tasks at 512 CPU, 1GB RAM. Monthly cost?
   - Each task: (730 × 1GB × $0.04746) + (730 × 0.5 vCPU × $0.04556) = $51.88/month
   - 100 tasks = $5,188/month

2. **Comparison:** Same 100 tasks on 50 × m5.large instances (2 vCPU, 8GB each).
   - Instance cost: 50 × $0.096/hour × 730 = $3,504/month
   - Fargate is more expensive for steady workloads!

3. **Networking:** Why run Fargate tasks in private subnets?
   - Security isolation, no direct internet exposure, use NAT for outbound

## Further Reading

- [Fargate best practices](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html)
- [Fargate networking deep dive](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-networking.html)
- [Cost optimization guide](https://aws.amazon.com/blogs/compute/optimizing-fargate-costs/)

---

**Next:** These three advanced AWS modules give you the depth to handle enterprise container workloads.
