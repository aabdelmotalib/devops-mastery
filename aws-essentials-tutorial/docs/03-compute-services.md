# Module 3: Compute Services

Compute is where your applications run. AWS provides multiple options: EC2 (full control), ECS (container orchestration), EKS (Kubernetes), Lambda (serverless), and Elastic Beanstalk (platform). Choosing the right compute service depends on your application architecture, team skills, and operational requirements.

## 3.1 EC2: Elastic Compute Cloud

EC2 provides virtual machines (instances) on AWS infrastructure. You choose OS, instance type, storage, and network. EC2 is IaaS: AWS manages hardware, you manage OS and above.

### Instance Types

EC2 offers instance types optimized for different workloads:

| Family | Use Case | Example | vCPU | Memory | Network |
|--------|----------|---------|------|--------|---------|
| t3 | General purpose, burstable | t3.medium | 2 | 4 GB | Moderate |
| m5 | General purpose, balanced | m5.large | 2 | 8 GB | Gigabit |
| c5 | Compute optimized | c5.xlarge | 4 | 8 GB | Gigabit |
| r5 | Memory optimized | r5.xlarge | 4 | 32 GB | Gigabit |
| i3 | Storage optimized (NVMe) | i3.large | 2 | 16 GB + SSD | Gigabit |
| g4 | GPU for ML/graphics | g4dn.xlarge | 4 | 16 GB + GPU | 10 Gigabit |
| p3 | GPU for HPC | p3.2xlarge | 8 | 61 GB + GPU | 10 Gigabit |

**Selection factors**:
- **CPU**: Compute-heavy? Use c5. General? Use m5 or t3.
- **Memory**: Cache, database? Use r5.
- **Storage**: High throughput reads? Use i3.
- **Network**: Low-latency requirements? Use enhanced networking.

### Instance Lifecycle

```
Pending → Running → Stopping → Stopped → Terminating → Terminated
```

- **Running**: You're charged per hour (or per second for recent instances)
- **Stopped**: EBS volume persists, but you're not charged for compute (charged for storage)
- **Terminated**: Instance and EBS deleted (unless configured otherwise); no charges

### Launch Template

Instead of clicking the console, define instances in code. Launch templates are reusable configuration.

```bash
# Create launch template
aws ec2 create-launch-template --launch-template-name web-server \
  --launch-template-data '{
    "ImageId": "ami-0c55b159cbfafe1f0",
    "InstanceType": "t3.micro",
    "KeyName": "my-keypair",
    "SecurityGroupIds": ["sg-0123456789abcdef0"],
    "UserData": "IyEvYmluL2Jhc2gKYXB0IHVwZGF0ZQphcHQgaW5zdGFsbCAteSBuZ2lueA==",
    "TagSpecifications": [{
      "ResourceType": "instance",
      "Tags": [{"Key": "Name", "Value": "web-server"}]
    }]
  }'

# Launch instances from template
aws ec2 run-instances --launch-template LaunchTemplateName=web-server --count 2
```

### EC2 Pricing Models

**On-Demand**: Pay per hour, no commitment. Highest per-unit cost.
```
t3.micro: $0.0116/hour = $8.47/month
m5.large: $0.096/hour = $70/month
```

**Reserved Instances (RI)**: Commit 1-3 years, pay upfront, 30-70% discount.
```
t3.micro reserved (1-year, all-upfront): $0.0036/hour = $2.62/month
Savings: 69% vs. on-demand
```

**Spot Instances**: Use unused capacity, 70-90% discount, can be interrupted.
```
t3.micro spot: $0.0035/hour (70% off)
Risk: 2-minute termination notice if capacity needed
Use case: Batch jobs, CI/CD builds, non-critical stateless workloads
```

**Savings Plans**: Commit to compute usage (not instance type), 20-50% discount.
```
Compute Savings Plan: $0.01/hour discount on any instance type/region
Example: t3.micro: $0.0116 - $0.01 = $0.0016/hour after savings plan
```

**Production decision**: Use on-demand for development. Use reserved or savings plans for predictable 24/7 production workloads. Use spot for batch and CI/CD.

### Autoscaling

Autoscaling automatically adjusts instance count based on demand. Critical for handling traffic spikes.

```bash
# Create autoscaling group
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name web-servers \
  --launch-template LaunchTemplateName=web-server \
  --min-size 2 \
  --desired-capacity 2 \
  --max-size 10 \
  --availability-zones us-east-1a us-east-1b \
  --load-balancer-names web-alb

# Set scaling policy (scale up when CPU > 70%)
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name web-servers \
  --policy-name scale-up-policy \
  --adjustment-type PercentChangeInCapacity \
  --adjustment-type 20 \
  --cooldown 300

# Set scaling policy (scale down when CPU < 30%)
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name web-servers \
  --policy-name scale-down-policy \
  --adjustment-type PercentChangeInCapacity \
  --scaling-adjustment -10 \
  --cooldown 300
```

Traffic spikes to 100 users:
1. Load on 2 instances increases to 85% CPU
2. Autoscaling detects > 70% threshold
3. Adds 1-2 new instances (20% increase = 0.4 → 1 new instance)
4. Traffic distributed across 3-4 instances
5. CPU drops to acceptable levels

## 3.2 Container Orchestration: ECS vs EKS

Containers provide OS-level isolation. Applications run in containers instead of directly on instances. ECS and EKS both orchestrate containers, but EKS is Kubernetes (industry standard).

### ECS (Elastic Container Service)

ECS is AWS's proprietary container orchestration. Simpler than Kubernetes, but less flexible.

Components:
- **Task**: Single container or group of containers running together
- **Service**: Long-running task, replicated across instances
- **Cluster**: Collection of EC2 instances or Fargate capacity

Example: Deploy a Docker web server on ECS

```bash
# Create cluster
aws ecs create-cluster --cluster-name web-app

# Create task definition (Docker image configuration)
aws ecs register-task-definition --family web-server \
  --container-definitions '[{
    "name": "web-server",
    "image": "nginx:latest",
    "memory": 512,
    "cpu": 256,
    "portMappings": [{
      "containerPort": 80,
      "hostPort": 80
    }]
  }]'

# Create service (run tasks continuously)
aws ecs create-service --cluster web-app \
  --service-name web-service \
  --task-definition web-server \
  --desired-count 3
```

### EKS (Elastic Kubernetes Service)

EKS is managed Kubernetes on AWS. Kubernetes is the industry standard for container orchestration.

Pros: Industry standard, portable (run same config on any Kubernetes)
Cons: More complex, higher learning curve

Example: Deploy a container on EKS

```bash
# Create cluster
aws eks create-cluster --name my-cluster \
  --version 1.24 \
  --role-arn arn:aws:iam::123456789012:role/eks-cluster-role \
  --resources-vpc-config subnetIds=subnet-12345,subnet-67890

# Add node group (EC2 instances running containers)
aws eks create-nodegroup --cluster-name my-cluster \
  --nodegroup-name my-nodes \
  --scaling-config minSize=2,maxSize=10,desiredSize=2 \
  --subnets subnet-12345 subnet-67890 \
  --node-role arn:aws:iam::123456789012:role/eks-node-role

# Deploy application using kubectl (Kubernetes client)
kubectl create deployment web-server --image=nginx:latest --replicas=3
```

### ECS vs EKS Decision Matrix

| Aspect | ECS | EKS |
|--------|-----|-----|
| Learning curve | Easier | Steeper (Kubernetes) |
| Portability | AWS-specific | Industry standard |
| Flexibility | Lower (AWS opinionated) | Higher (full Kubernetes) |
| Cost | Lower (no Kubernetes overhead) | Higher (control plane + nodes) |
| Community | AWS-focused | Large Kubernetes ecosystem |
| Best for | AWS-only shops | Multi-cloud, large teams |

**Production recommendation**: If you're AWS-only and want simplicity, use ECS or Elastic Beanstalk. If you need portability or large-scale Kubernetes expertise, use EKS.

## 3.3 AWS Fargate

Fargate is serverless containers. You define container images and memory; AWS handles EC2 management automatically.

Without Fargate (manual EC2 management):
1. Launch EC2 instances
2. Install Docker runtime
3. Manage OS patching
4. Monitor CPU/memory
5. Scale instances up/down

With Fargate:
1. Define container image and memory
2. Fargate runs container
3. Auto-scales, handles patching, monitoring

```bash
# Launch task on Fargate (ECS)
aws ecs run-task --cluster web-app \
  --task-definition web-server \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345]}"
```

Trade-offs:
- **Pros**: No server management, auto-scaling, pay per container second
- **Cons**: Less flexibility, costs more per container than EC2

**Use Fargate for**: Bursty workloads, microservices, applications you don't want to manage.

## 3.4 AWS Lambda

Lambda is serverless functions: You provide code, AWS handles everything else. You pay per execution (0.0000002$ per request + $0.0000166667 per GB-second).

Use case: Event-driven, short-running tasks, API endpoints.

```bash
# Create IAM role for Lambda
aws iam create-role --role-name lambda-execution-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Create function
aws lambda create-function --function-name hello-world \
  --runtime python3.11 \
  --role arn:aws:iam::123456789012:role/lambda-execution-role \
  --handler index.handler \
  --zip-file fileb://function.zip

# Invoke function
aws lambda invoke --function-name hello-world \
  --payload '{"name":"Alice"}' \
  response.json
```

Lambda Python handler (index.py):
```python
def handler(event, context):
    name = event.get('name', 'World')
    return {
        'statusCode': 200,
        'body': f'Hello, {name}!'
    }
```

**Production note**: Lambda is excellent for:
- API endpoints (via API Gateway)
- Scheduled tasks (via CloudWatch Events)
- Event processors (S3 uploads, DynamoDB changes)

Avoid for: Long-running processes, stateful applications, compute-heavy workloads.

## 3.5 Elastic Beanstalk

Elastic Beanstalk is a managed platform for deploying applications. You provide code, Beanstalk provisions EC2, load balancers, and scaling automatically.

Supported languages: Python, Node.js, Java, Go, .NET, Ruby, PHP.

```bash
# Install EB CLI
pip install awsebcli

# Initialize application
eb init my-app --platform python-3.11

# Create environment
eb create production

# Deploy code
eb deploy

# View logs
eb logs

# Scale
eb scale 4  # Run on 4 instances
```

Beanstalk handles:
- EC2 instance provisioning
- Load balancer creation
- Autoscaling configuration
- Health monitoring
- Deployment strategies (rolling, all-at-once)

You manage:
- Application code
- Database connection strings
- Environment variables
- Deployment lifecycle

**Beanstalk vs. Fargate**: Beanstalk manages full application stack (OS, runtime). Fargate is just containers. Choose Beanstalk for traditional applications, Fargate for containerized microservices.

## 3.6 Production Compute Architecture

A typical production architecture uses multiple compute services:

```
Route 53 (DNS)
    ↓
CloudFront (CDN for static content)
    ↓
ALB (Load balancer)
    ├─ ECS Fargate service (API, microservice A)
    ├─ ECS Fargate service (microservice B)
    ├─ Elastic Beanstalk environment (web app)
    └─ Lambda (background jobs)
    ↓
RDS (shared database)
```

- **API endpoints**: Lambda (low latency, auto-scaling)
- **Web application**: Elastic Beanstalk or ECS (traditional apps)
- **Microservices**: ECS/EKS Fargate (containerized)
- **Background jobs**: Lambda (event-driven) or EC2 (long-running)

## 3.7 Common Mistakes

**Mistake 1: Over-provisioning**
Launching t3.2xlarge (8 vCPU, 32 GB) for a development environment wastes money. t3.micro costs 1/20th as much and is sufficient.

**Mistake 2: Not using autoscaling**
Manually scaling instances leads to two problems: Over-capacity (costs money) or under-capacity (service degrades). Autoscaling handles both.

**Mistake 3: Ignoring instance metadata**
EC2 instances have metadata available at http://169.254.169.254/latest/meta-data/. You can query this for instance ID, IAM role, availability zone, etc.

**Mistake 4: Not using managed services**
Running your own database on EC2 means patching, backups, replication—all your responsibility. Use RDS.

**Mistake 5: Choosing wrong compute service**
Trying to run Lambda for long-running jobs (> 15 minutes) is impossible. Trying to run EC2 for 1-second API responses is expensive. Match compute service to workload.

## 3.8 Production Notes

### Health Checks

Autoscaling groups check instance health. Unhealthy instances are replaced.

```bash
# Configure health check
aws autoscaling update-auto-scaling-group \
  --auto-scaling-group-name web-servers \
  --health-check-type ELB \
  --health-check-grace-period 300
```

Health check types:
- **EC2**: Uses EC2 status checks (simple)
- **ELB**: Uses load balancer health checks (application-level)

Use ELB health checks: They verify your application responds correctly, not just that the OS is running.

### Deployment Strategies

**Blue-green**: Run two environments (blue and green). Deploy to green, test, switch traffic.

Benefits: Zero-downtime, instant rollback
Cost: 2x resources during deployment

**Rolling**: Gradually replace instances during deployment.

Benefits: Lower cost
Trade-offs: Brief inconsistency, slightly longer deployment

**Canary**: Deploy to 10% of instances, monitor, then 100%.

Benefits: Early detection of issues
Trade-offs: Complex, longer deployment

## Assessment

### Practice Questions

**Q1: You need to run a database on EC2. Is this recommended?**
A) Yes, EC2 is flexible
B) No, use RDS (managed, automated backups)
C) Only if you have database expertise
D) EC2 and RDS cost the same

**Q2: Your Lambda function times out after 15 seconds. What's the maximum duration?**
A) 15 seconds
B) 5 minutes
C) 15 minutes
D) No limit

**Q3: You want autoscaling based on custom metrics (not CPU). What's the best approach?**
A) CloudWatch custom metrics + scaling policy
B) CloudWatch dashboard
C) Manual scaling
D) Not possible

**Q4: An EC2 instance with on-demand pricing costs $0.10/hour. Using spot, it costs $0.02/hour. What's the risk?**
A) No risk, always use spot
B) Spot can be terminated with 2 minutes notice
C) Spot is less reliable
D) Spot has worse performance

**Q5: You're deploying a containerized application. Should you use ECS or EKS?**
A) ECS (simpler)
B) EKS (industry standard)
C) It depends on whether you need portability/scale
D) Both cost the same

### Hands-On Labs

**Lab 1: Launch EC2 with Autoscaling**

Objective: Deploy autoscaled web servers.

Tasks:
1. Create launch template with nginx
2. Create autoscaling group (min 2, desired 2, max 5)
3. Create ALB in two AZs
4. Attach autoscaling group to ALB
5. Create CloudWatch alarm (CPU > 70%)
6. Create scaling policy (add 2 instances on alarm)
7. Test by hitting load balancer: Watch instances increase

Success criteria: Instances launch/terminate based on demand

**Lab 2: Deploy to Elastic Beanstalk**

Objective: Deploy application without managing servers.

Tasks:
1. Create simple Flask app
2. Create requirements.txt
3. Initialize EB: `eb init`
4. Create environment: `eb create`
5. Deploy: `eb deploy`
6. Monitor health: `eb status`
7. Scale: `eb scale 3`
8. Clean up: `eb terminate`

Success criteria: App deployed and accessible

### Production Incident Scenario

**Scenario: Uncontrolled Autoscaling Costs**

At 2:00 AM, a database query bug causes your application to respond slowly. Autoscaling detects high CPU and launches 50 new instances. By 6:00 AM, 200 instances are running (normally 5). AWS bill for that month will exceed $20,000 (normally $2,000).

Root causes:
- Autoscaling policy too aggressive (adds 50% per 5 minutes)
- No max instance limit
- No automated alerting on instance count
- Bug in application query not caught before production

Recovery:
1. Manually reduce desired capacity: `aws autoscaling update-auto-scaling-group --desired-capacity 5`
2. Review autoscaling events to find the trigger
3. Fix database query
4. Reduce instance count and terminate

Prevention:
- Smaller scaling increments (add 1-2 at a time)
- Set hard max limits (e.g., max 10 instances)
- Alert when instance count crosses thresholds
- Test scaling policies with load generation
- Use CloudWatch dashboards to spot anomalies

---

Next Module: [Module 4: Storage & Databases](04-storage-databases.md)
