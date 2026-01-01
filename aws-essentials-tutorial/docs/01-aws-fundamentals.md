# Module 1: AWS Fundamentals

This module establishes the foundational concepts underpinning all AWS architecture. You must understand these concepts deeply before proceeding to compute, storage, or network modules.

## 1.1 Cloud Computing Essentials

Cloud computing shifts computing responsibility from capital expenditure (buying servers) to operational expenditure (paying for usage). AWS offers this through several models:

### IaaS (Infrastructure as a Service)

AWS provides raw compute, storage, and networking resources. You are responsible for the operating system, middleware, runtime, applications, and data. EC2 is the primary IaaS offering.

Use case: Running existing applications with full control over the OS. Ideal for legacy systems or specialized configurations.

Example: Launch an Ubuntu EC2 instance and install your own database, web server, and application.

```bash
# Launch an EC2 instance (you'll configure this in Module 3)
aws ec2 run-instances --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.micro --region us-east-1
```

### PaaS (Platform as a Service)

AWS manages infrastructure, OS, and middleware. You provide the application code and data. RDS, Elastic Beanstalk, and App Runner are PaaS offerings.

Use case: Running applications without managing database servers or OS patching. You deploy code and focus on features.

Example: Deploy a Flask app to AWS Elastic Beanstalk. AWS handles the EC2 instances, load balancing, and scaling.

```bash
# Deploy app using Elastic Beanstalk (demonstrated in Module 3)
eb init my-app
eb create my-env
eb deploy
```

### SaaS (Software as a Service)

AWS (and other vendors) provides fully managed applications accessible via the internet. You consume the service. Amazon Workmail, AWS Compliance, and third-party tools like Slack integration are SaaS.

Use case: Using managed services without building or deploying anything. Pay per user or per transaction.

Example: Using Amazon Workmail for email instead of running your own mail server.

### Production Decision Matrix

| Service Type | Control | Operational Burden | Scaling | Cost Predictability | Best For |
|--------------|---------|-------------------|---------|-------------------|----------|
| IaaS (EC2) | High | High | Manual or via autoscaling | Medium | Custom apps, legacy systems |
| PaaS (RDS, Beanstalk) | Medium | Low | Automatic (most) | Medium-High | Standard applications |
| SaaS (Workmail) | Low | Very Low | N/A | High | Non-core services |

**Production Note**: Most companies use all three. Run databases in RDS (PaaS), applications on EC2 (IaaS) or Beanstalk (PaaS), and use Workmail (SaaS) for email.

## 1.2 Regions and Availability Zones

### AWS Regions

An AWS Region is a geographically isolated area containing multiple data centers. Currently, AWS operates in 30+ regions worldwide. Examples: us-east-1 (N. Virginia), eu-west-1 (Ireland), ap-southeast-1 (Singapore).

Why regions matter:
- **Compliance**: Data residency requirements (GDPR in EU requires eu-* regions)
- **Latency**: Serving European customers from us-east-1 adds 100ms+ latency
- **Cost**: Some regions cost 2-3x more than others
- **Feature availability**: New AWS features roll out to regions on different timelines

### Availability Zones (AZs)

Each region contains 2-4 Availability Zones. Each AZ is a separate data center with independent infrastructure, power, and network connectivity. AZs are connected by high-bandwidth, low-latency fiber.

Why AZs matter:
- **Fault isolation**: An AZ outage affects services in that AZ only
- **Durability**: Multi-AZ deployments survive AZ failures
- **Performance**: Inter-AZ latency is < 5ms, acceptable for databases

### Architecture Across AZs

```
Region: us-east-1
├── AZ us-east-1a
│   └── EC2 Instance (Web Server)
│   └── EBS Volume
├── AZ us-east-1b
│   └── EC2 Instance (Web Server)
│   └── RDS Multi-AZ Standby
└── AZ us-east-1c
    └── S3 (regional, all AZs)
```

**Production Pattern**: Always deploy compute in multiple AZs. Database with Multi-AZ failover. Load balance across AZs.

### Regional Service vs. AZ Service

Some services are regional (one instance across all AZs):
- S3, DynamoDB, Route 53 (regional redundancy automatic)

Some services are per-AZ (you must deploy multiple times):
- EC2, EBS, RDS (you choose single or multi-AZ)

Check the [AWS documentation](https://docs.aws.amazon.com/general/latest/gr/rande.html) for service availability.

## 1.3 Shared Responsibility Model

This is critical for security, compliance, and architecture decisions.

AWS is responsible for:
- Physical data center security
- Network infrastructure
- Hypervisor and virtualization
- Managed service internals

You are responsible for:
- OS updates and patching (on EC2)
- Application security
- Network ACLs and security groups
- IAM policies and access control
- Data encryption (both at-rest and in-transit)
- Credential management
- Disaster recovery and backups

```
You Handle          AWS Handles
├─ Applications     ├─ Physical Security
├─ OS Patching      ├─ Network Infrastructure
├─ Credentials      ├─ Hypervisor
├─ Encryption Keys  └─ Hardware Failures
└─ Network ACLs
```

### Service-Specific Responsibility

The split changes by service type:

| Service | AWS Manages | You Manage |
|---------|------------|-----------|
| EC2 | Hardware, hypervisor | OS, patches, app, security group |
| RDS | Hardware, DB engine, OS, backups | DB users, access control, data model |
| S3 | Hardware, durability, availability | Bucket policy, encryption keys, versioning |
| Lambda | Runtime, scaling, infrastructure | Code, environment variables, IAM role |

**Common Mistake**: Assuming AWS handles OS patching on EC2. You must patch EC2 instances. AWS handles patching for RDS, Lambda, and other managed services.

## 1.4 AWS Service Categories (Cloud Mental Model)

Understanding service categories is essential for architecture. Services stack in layers:

### Layer 1: Network Foundation

Services that enable connectivity:
- **Route 53**: DNS service
- **VPC (Virtual Private Cloud)**: Networking, subnets, routing
- **CloudFront**: Content delivery and edge caching

These connect users to your infrastructure.

### Layer 2: Load Balancing

Services that distribute traffic:
- **Elastic Load Balancer (ELB)**: Classic, Application (ALB), Network (NLB)
- **Auto Scaling**: Automatically scales compute based on demand

These ensure no single server becomes a bottleneck.

### Layer 3: Compute

Services that run your code:
- **EC2**: Virtual machines (IaaS)
- **ECS**: Container orchestration
- **EKS**: Kubernetes service
- **Lambda**: Serverless functions
- **Elastic Beanstalk**: Managed platform (PaaS)

These execute your applications.

### Layer 4: Databases & Caching

Services that persist data:
- **RDS**: Managed relational databases (MySQL, PostgreSQL, MariaDB, SQL Server, Oracle)
- **DynamoDB**: NoSQL database
- **ElastiCache**: In-memory caching (Redis, Memcached)

These store and retrieve application data.

### Layer 5: Storage

Services that store files and objects:
- **S3**: Object storage for files, backups, static assets
- **EFS**: Network file system
- **FSx**: Managed file servers

These handle long-term, high-volume data.

### Layer 6: Monitoring & Security

Services that observe and protect:
- **CloudWatch**: Metrics, logs, alarms
- **CloudTrail**: Audit trails
- **IAM**: Access control
- **KMS**: Encryption key management

These ensure visibility and security across all layers.

### Typical Production Request Flow

```
1. User submits HTTP request
   ↓
2. Route 53 resolves domain to ALB IP
   ↓
3. ALB routes to healthy EC2 (in multiple AZs)
   ↓
4. EC2 instance processes request
   ↓
5. Application queries RDS for user data
   ↓
6. RDS returns data from Multi-AZ replica
   ↓
7. Application caches hot data in ElastiCache
   ↓
8. Large files stored in S3
   ↓
9. CloudWatch monitors all layers
   ↓
10. Response sent back to user
```

Every production system traverses these layers. Understanding them prevents poor architectural decisions.

## 1.5 AWS Cost Model

AWS uses pay-as-you-go pricing. You pay only for resources you use, not for capacity you own.

### Pricing Models

**On-Demand**: Pay hourly for instances you use. No upfront cost, highest per-unit cost. Best for variable workloads.

```
t3.micro on-demand: $0.0116/hour
Running 730 hours/month: $8.47/month
```

**Reserved Instances (RI)**: Commit to 1-3 years, pay upfront, receive 30-70% discount.

```
t3.micro reserved (1-year): $0.0036/hour
Running 730 hours/month: $2.62/month
Savings vs. on-demand: 69% less
```

**Spot Instances**: Unused AWS capacity at 70-90% discount. Can terminate with 2-minute notice.

```
t3.micro spot: $0.0035/hour (70% off)
Risk: AWS can terminate if capacity is needed
Use case: Batch jobs, CI/CD builds, non-critical workloads
```

**Savings Plans**: Commit to compute usage (not instance type), get 20-50% discount. More flexible than RIs.

```
Compute Savings Plan: Discount applies across instance types
Example: $0.01/hour discount across t3, m5, c5 instances
```

### Pricing Example: Web Application

Simple three-tier web app:
- 2x EC2 t3.medium on-demand: $0.0416/hour each = $0.0832/hour
- 1x RDS db.t3.micro multi-AZ: $0.054/hour
- 10 GB S3 storage: $0.23/month
- 100 GB data transfer out: $9.00/month

Monthly estimate: ($0.1372 * 730) + $0.23 + $9.00 = $109.25

Using reserved instances: ($0.0372 * 730) + savings = $40-50/month

**Production Note**: Cost scales with customer growth. The same application serving 100x more users costs maybe 5x more in compute because of autoscaling efficiency, but your total billing grows. Monitor costs obsessively from day one.

### Free Tier

AWS offers free tier for 12 months:
- 750 hours of t2.micro EC2
- 20 GB RDS database
- 5 GB S3 storage
- 15 GB data transfer per month

Most lab exercises fit within free tier. Always monitor billing to stay within limits.

## 1.6 AWS Networking Fundamentals

### IP Addressing

AWS uses RFC 1918 private IP ranges for VPCs:
- 10.0.0.0/8
- 172.16.0.0/12
- 192.168.0.0/16

Resources get both private IPs (internal communication) and optionally public IPs (internet-facing).

Example: An EC2 instance might have:
- Private IP: 10.0.1.42 (internal to VPC)
- Public IP: 203.0.113.42 (internet-accessible, assigned by ELB)

### VPC Basics

A VPC is your isolated network in AWS. Think of it as your own data center inside AWS.

Components:
- **Subnets**: Subdivisions of the VPC's IP range, mapped to AZs
- **Route tables**: Rules determining where traffic flows
- **Internet Gateway**: Entry/exit point to the public internet
- **NAT Gateway**: Allows private resources to initiate outbound internet connections

Example VPC structure:

```
VPC: 10.0.0.0/16
├── Public Subnet us-east-1a: 10.0.1.0/24 (has route to Internet Gateway)
│   └── EC2 with public IP (accessible from internet)
├── Public Subnet us-east-1b: 10.0.2.0/24
│   └── EC2 with public IP
├── Private Subnet us-east-1a: 10.0.10.0/24 (no direct internet access)
│   └── RDS instance
└── NAT Gateway in public subnet
    (allows private resources to download updates)
```

### Security Groups vs. NACLs

**Security Groups** (stateful firewall at instance level):
- Allow rules only (no explicit deny)
- Stateful (response traffic automatically allowed)
- Applied to ENI (network interface)

Example: Allow HTTP and HTTPS inbound

```
Inbound Rules:
- Protocol: TCP, Port: 80, Source: 0.0.0.0/0 (anyone)
- Protocol: TCP, Port: 443, Source: 0.0.0.0/0 (anyone)
- Protocol: TCP, Port: 3306, Source: 10.0.10.0/24 (RDS subnet only)
```

**NACLs** (stateless firewall at subnet level):
- Allow and deny rules
- Stateless (response traffic requires explicit rule)
- Applied to subnet

Example: More restrictive, but rarely used in modern designs.

**Production Pattern**: Use security groups for instance-level control. Use NACLs sparingly; they add complexity.

## 1.7 Production Architecture Example

Putting it all together, a production three-tier web application:

```
Route 53 (DNS)
    ↓
CloudFront (CDN for static assets)
    ↓
ALB in public subnets (us-east-1a, us-east-1b)
    ├─ AZ us-east-1a
    │  └─ Auto Scaling Group (2-10 EC2 t3.small)
    │     └─ Security group: Allow port 80, 443
    └─ AZ us-east-1b
       └─ Auto Scaling Group (2-10 EC2 t3.small)
          └─ Security group: Allow port 80, 443
    ↓
RDS Multi-AZ (Primary us-east-1a, Standby us-east-1b)
    └─ Security group: Allow port 5432 from app security group only
    ↓
S3 (static assets, backups)
    └─ Lifecycle: Move old backups to Glacier after 30 days
    ↓
ElastiCache Redis (in private subnets)
    └─ Cache hot data (user sessions, product catalog)
    ↓
CloudWatch (logs, metrics, alarms)
IAM (roles for EC2, RDS, S3 access)
```

Data flow:
1. User requests app.example.com
2. Route 53 returns CloudFront distribution IP
3. CloudFront serves static assets, proxies dynamic requests to ALB
4. ALB routes to healthy EC2 in multiple AZs
5. EC2 queries RDS (Multi-AZ ensures availability)
6. Redis caches frequently accessed data
7. S3 stores user uploads, database backups
8. CloudWatch monitors all components
9. Auto scaling adds/removes EC2 based on load

This design provides:
- Availability: Multi-AZ, load balancing
- Scalability: Auto scaling, CDN caching
- Durability: RDS backups, S3 versioning
- Security: VPC isolation, security groups, IAM roles
- Observability: Comprehensive logging and monitoring

## 1.8 Common Mistakes

**Mistake 1: Choosing the wrong region for cost**
Not all regions cost the same. us-east-1 is cheapest. If cost matters, use us-east-1 unless compliance requires otherwise.

**Mistake 2: Treating availability zones as redundant**
AZs have independent infrastructure, but they're in the same region. A region-wide issue (AWS maintenance, natural disaster) affects all AZs. For disaster recovery, use multiple regions.

**Mistake 3: Not understanding shared responsibility**
Assuming AWS patches your EC2 OS is a security disaster. AWS patches RDS, Lambda, and managed services, but not EC2.

**Mistake 4: Over-complicating the network**
Most workloads need:
- Public subnets for load balancers
- Private subnets for databases and app servers
- One internet gateway per VPC
- One NAT gateway for outbound traffic from private subnets
Anything more is over-engineering.

**Mistake 5: Ignoring costs from day one**
Add cost alerts in billing preferences immediately. Review actual spend weekly. A misconfigured job can cost thousands per day.

## 1.9 Production Notes

### Building for Availability

Availability is not about zero downtime; it's about graceful degradation. Your system should continue functioning (possibly in degraded mode) when components fail.

Design principle: Every single component should be redundant across multiple AZs.

- Load balancer: Multi-AZ (ALB automatically spans AZs)
- Compute: Multiple AZ-specific auto scaling groups
- Database: Multi-AZ RDS with automatic failover
- Caching: Replicated Redis cluster
- Storage: S3 region-level redundancy

When one AZ fails, the other handles traffic. Users experience no interruption.

### Thinking About Blast Radius

Blast radius is the scope of impact from a single failure.

Good design:
- EC2 instance failure: 1/10 capacity lost, others handle traffic (small blast radius)
- Database failure: Automatic RDS failover (seconds of interruption, controlled blast radius)
- Region failure: Only affects customers in that region, activate regional failover

Bad design:
- Single EC2 running the application: Instance failure = total outage
- Unencrypted database: Breach = all customer data exposed
- No backups: Data loss = unrecoverable

### Cost Optimization Starting Points

1. Use t3.micro or t3.small for development/staging
2. Use autoscaling to match capacity to demand
3. Use reserved instances for predictable, 24/7 workloads
4. Use spot instances for non-critical batch jobs
5. Delete non-production resources immediately (dev environments cost real money)
6. Monitor data transfer costs (most underestimated AWS cost)

## Assessment

### Practice Questions

**Q1: Which AWS service provides the highest customer responsibility for OS patching?**
A) RDS MySQL
B) EC2 t3.micro
C) Lambda
D) Elastic Beanstalk

**Q2: Your application runs in us-east-1a. An AZ failure occurs. What happens?**
A) Entire region becomes unavailable
B) Only us-east-1a is affected; us-east-1b continues serving traffic
C) Application auto-failover to us-west-2
D) AWS immediately restores all data from backup

**Q3: You need to serve users in EU with < 50ms latency. What region should you use?**
A) us-east-1 (cheapest)
B) eu-west-1 (Ireland)
C) ap-southeast-1
D) Any region; CloudFront eliminates latency

**Q4: A misconfigured NAT gateway costs you $100/day in data transfer charges. What shared responsibility issue occurred?**
A) AWS didn't warn you
B) You didn't implement billing alerts
C) This is a shared cost both parties must monitor
D) AWS should have prevented the misconfiguration

**Q5: You launch an EC2 instance with a public IP. Security group allows port 22 (SSH). What can someone do?**
A) SSH into the instance (if they have the key)
B) See the instance's existence (anyone can scan)
C) Directly access your RDS database
D) Access your S3 buckets

### Hands-On Labs

**Lab 1: AWS Account Setup and CLI Configuration**

Objective: Verify AWS account setup and CLI functionality.

Tasks:
1. Create an AWS account and enable billing alerts
2. Create an IAM user (don't use root)
3. Install AWS CLI v2
4. Configure CLI with IAM user credentials
5. Verify access: `aws sts get-caller-identity`
6. List EC2 instances: `aws ec2 describe-instances --region us-east-1`
7. Check your AWS account ID and username

Success criteria:
- CLI returns your AWS account ID and IAM user ARN
- No EC2 instances exist yet (empty list)
- Billing alerts are enabled in AWS console

**Lab 2: Exploring Regions and Availability Zones**

Objective: Understand regional architecture.

Tasks:
1. Use AWS CLI to list all regions: `aws ec2 describe-regions`
2. For each major region, list AZs:
   ```bash
   aws ec2 describe-availability-zones --region us-east-1 --query 'AvailabilityZones[*].[ZoneName,State]' --output table
   ```
3. Calculate the "closest" region to your actual location by latency
4. Note region pricing differences:
   ```bash
   aws pricing get-products --service-code AmazonEC2 --filters "Type=TERM_MATCH,Field=instanceType,Value=t3.micro" --region us-east-1
   ```
5. Document which regions support which services you care about (check [AWS docs](https://docs.aws.amazon.com/general/latest/gr/rande.html))

Success criteria:
- Can list all 30+ regions and AZs
- Understand latency implications of region choice
- Know pricing varies by region

### Production Incident Scenario

**Scenario: Regional Outage**

Your application serves users globally from a single us-east-1 region. At 14:00 UTC, us-east-1 experiences a widespread outage affecting all services. Your RDS database, load balancer, and EC2 instances are all unavailable.

Impact:
- 100% downtime for all users
- 4 hours until AWS repairs infrastructure
- Customer data is safe (RDS backups exist), but unavailable
- Incident costs: Lost revenue + emergency engineering time

Questions:
1. What architectural decisions led to this single point of failure?
2. How would you design for regional failures?
3. What's the minimum deployment for regional redundancy?
4. How would you test regional failover without waiting for an actual outage?

Recommended Response:
- Active-active deployment in two regions (us-east-1 and us-west-2)
- Route 53 health checks and failover routing
- RDS read replicas in secondary region
- S3 cross-region replication
- Cost is higher, but downtime is 5-10 minutes instead of 4 hours

---

Next Module: [Module 2: Identity & Access Management](02-identity-access-management.md)
