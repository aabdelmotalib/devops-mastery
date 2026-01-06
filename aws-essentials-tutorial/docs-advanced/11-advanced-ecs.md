# Advanced AWS: ECS & Container Orchestration

## Overview

This module covers **Amazon Elastic Container Service (ECS)**, AWS's container orchestration platform, and how it compares to and complements Kubernetes. You'll learn when to choose ECS, how to manage production container workloads, and integration patterns with other AWS services.

## Mental Model

```
Your Application (Docker Container)
        ↓
    ECS Task
    (Single container instance)
        ↓
    ECS Service
    (Manages multiple task replicas)
        ↓
    ECS Cluster
    (Collection of compute resources: EC2 or Fargate)
        ↓
    Container Registry (ECR)
    (Where images live)
        ↓
    Load Balancer (ALB/NLB)
    (Routes traffic to tasks)
        ↓
    Auto Scaling & Monitoring
    (CloudWatch metrics)
```

Key difference from Kubernetes:
- **ECS:** AWS-native, simpler, less configuration, less flexibility
- **Kubernetes:** Open-source, portable, more configuration options, more flexibility

## What This Module Covers

1. **ECS Fundamentals** - Task definitions, services, clusters
2. **ECS vs Kubernetes** - When to choose each
3. **EC2 vs Fargate Launch Types** - Trade-offs
4. **Production ECS Patterns** - Rolling updates, canary deployments
5. **Integration with AWS Services** - Load balancing, monitoring, scaling
6. **ECS Best Practices** - Security, cost optimization, reliability
7. **Advanced Scenarios** - Multi-AZ deployment, service discovery

## Key Concepts

### ECS Task Definition

A **task definition** is like a Dockerfile but for ECS—it specifies:
- Which Docker image to run
- How much CPU/memory to allocate
- Environment variables
- Volume mounts
- Logging configuration
- IAM role

```yaml
{
  "family": "web-app",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "web-container",
      "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/web-app:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/web-app",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "essential": true
    }
  ],
  "executionRoleArn": "arn:aws:iam::123456789:role/ecsTaskExecutionRole"
}
```

### ECS Task vs Service

**Task:** A single instance of your container. Runs once and stops.
- Use for: Batch jobs, scheduled tasks, one-off operations

**Service:** Manages multiple task replicas, replaces failed tasks, handles updates.
- Use for: Long-running applications, APIs, web services

```bash
# Run a single task (like docker run)
aws ecs run-task \
  --cluster my-cluster \
  --task-definition web-app:1 \
  --launch-type FARGATE \
  --network-configuration awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345]}

# Create a service (manages replicas)
aws ecs create-service \
  --cluster my-cluster \
  --service-name web-app \
  --task-definition web-app:1 \
  --desired-count 3 \
  --launch-type FARGATE
```

### EC2 vs Fargate Launch Types

| Aspect | EC2 | Fargate |
|--------|-----|--------|
| **You manage** | Cluster, instance lifecycle, scaling | Nothing—it's serverless |
| **Cost** | Per instance (even if idle) | Per task (second-level billing) |
| **Control** | Full—customize everything | Limited—pre-configured |
| **Good for** | Stateful, always-on, cost-sensitive | Bursty, predictable, simple workloads |
| **Example** | 24/7 web server on reserved instances | Scheduled batch job, event-driven task |

## Production ECS Pattern

### Complete Example: Web Application with Auto Scaling

```yaml
# Step 1: Create VPC and security groups
aws ec2 create-vpc --cidr-block 10.0.0.0/16
# Create public subnets, private subnets, NAT gateway, etc.

# Step 2: Create ECR repository
aws ecr create-repository --repository-name my-web-app

# Step 3: Build and push Docker image
docker build -t my-web-app:latest .
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com
docker tag my-web-app:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/my-web-app:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/my-web-app:latest

# Step 4: Create ECS task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Step 5: Create ECS cluster
aws ecs create-cluster --cluster-name production

# Step 6: Create ECS service with load balancer
aws ecs create-service \
  --cluster production \
  --service-name web-app \
  --task-definition my-web-app:1 \
  --desired-count 3 \
  --launch-type FARGATE \
  --network-configuration awsvpcConfiguration={subnets=[subnet-public-1,subnet-public-2],securityGroups=[sg-web]} \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789:targetgroup/web-app/1234567890,containerName=web-container,containerPort=8000

# Step 7: Set up auto scaling
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name web-app-asg \
  --cluster production \
  --service-name web-app \
  --max-capacity 10 \
  --min-capacity 1 \
  --target-tracking-scaling-policy-configuration ...
```

## Common Mistakes

**Mistake 1: Task definition with hardcoded environment variables**
```yaml
# ❌ WRONG: Hardcoded secrets
"environment": [
  {"name": "DB_PASSWORD", "value": "super-secret-password"}
]

# ✅ RIGHT: Use Secrets Manager
"secrets": [
  {
    "name": "DB_PASSWORD",
    "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:db-password"
  }
]
```

**Mistake 2: Not setting resource requests/limits**
```yaml
# ❌ WRONG: Task will use whatever it wants
{
  "containerDefinitions": [{"name": "app", "image": "app:latest"}]
}

# ✅ RIGHT: Explicit resource requirements
{
  "family": "app",
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [{"name": "app", "image": "app:latest"}]
}
```

**Mistake 3: Using EC2 for unpredictable workloads**
```
# ❌ WRONG: 24/7 EC2 instances for traffic that spikes 5x/day
$40/month × 24 hours = expensive idle time

# ✅ RIGHT: Use Fargate with auto scaling
Pay only for running tasks + compute time
```

**Mistake 4: Not monitoring task health**
```bash
# ❌ WRONG: No health checks, dead tasks keep running
aws ecs create-service --service-name app ...

# ✅ RIGHT: Enable health checks
aws ecs register-task-definition \
  --health-check "command=[CMD-SHELL, curl -f http://localhost:8000/health || exit 1],interval=30,timeout=5,retries=3"
```

**Mistake 5: Rolling updates without canary deployment**
```bash
# ❌ WRONG: Deploy new version to all tasks immediately
# If new code has a bug, all traffic goes to broken version

# ✅ RIGHT: Canary deployment—test new version first
# Deploy to 1 task, monitor metrics, gradually shift traffic
```

## Production Incident Scenario

### Scenario: "Sudden increase in task failures after deployment"

**Symptoms:**
- ECS service showing "Desired: 5, Running: 2"
- Logs show "OutOfMemory" errors
- Traffic is slow, some requests timeout

**Investigation Steps:**

```bash
# 1. Check task definition for latest version
aws ecs describe-task-definition --task-definition app-name:latest

# 2. Compare memory allocation
# Previous: 512 MB
# New: 256 MB (someone changed it!)

# 3. Check which tasks are failing
aws ecs describe-tasks --cluster production \
  --tasks arn:aws:ecs:...

# 4. Check application logs
aws logs tail /ecs/app-name --follow

# 5. See the error
# "Java heap size exceeded 256MB"
```

**Root Cause:** Task definition memory was reduced from 512MB to 256MB, but application needs more.

**Solution:**

```bash
# 1. Register new task definition with correct memory
# Edit task-definition.json: "memory": "512"

aws ecs register-task-definition --cli-input-json file://task-definition.json

# 2. Update service to use new task definition
aws ecs update-service \
  --cluster production \
  --service app-name \
  --task-definition app-name:2 \
  --force-new-deployment

# 3. Monitor rollout
aws ecs describe-services --cluster production --services app-name

# 4. Verify traffic returns to normal
# Check ALB target group health
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:...
```

**Prevention:**
- Code review all task definition changes
- Monitor memory/CPU utilization before deployment
- Use canary deployments for resource changes
- Alert when task repeatedly fails

## Practice Questions

1. **Scenario:** Your application needs to run a batch job once per day. Should you use ECS Task or Service?
   - Why? Services are for long-running applications. A task is sufficient for one-time jobs.

2. **Decision:** You're deploying a stateless REST API that receives bursty traffic. EC2 or Fargate?
   - Why? Fargate is better for unpredictable workloads. You pay per task, not per instance.

3. **Troubleshooting:** Your ECS tasks keep stopping after 30 seconds. What would you check first?
   - Why? Check task logs and health checks. Tasks stop when they exit or fail health checks.

## Further Reading

- [AWS ECS Best Practices Guide](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/container-considerations.html)
- [ECS vs Kubernetes comparison](https://aws.amazon.com/blogs/compute/amazon-ecs-vs-kubernetes/)
- [Fargate pricing calculator](https://aws.amazon.com/fargate/pricing/)

---

**Next:** Learn about AWS Lambda and serverless patterns in the next advanced module.
