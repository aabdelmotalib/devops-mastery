# Module 5: Networking & Content Delivery

Network architecture determines how users reach your application, how your application reaches databases, and how data flows securely. Poor networking design leads to latency, security vulnerabilities, and scalability limits.

## 5.1 VPC: Virtual Private Cloud

A VPC is your isolated network in AWS. Everything runs in a VPC.

### VPC Basics

```bash
# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16

# Create public subnet
aws ec2 create-subnet --vpc-id vpc-12345 \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a

# Create private subnet
aws ec2 create-subnet --vpc-id vpc-12345 \
  --cidr-block 10.0.10.0/24 \
  --availability-zone us-east-1a
```

Architecture:
```
VPC 10.0.0.0/16
├── Public Subnet 10.0.1.0/24 (us-east-1a)
│   └── Internet Gateway (entry/exit point)
├── Public Subnet 10.0.2.0/24 (us-east-1b)
│   └── Internet Gateway
├── Private Subnet 10.0.10.0/24 (us-east-1a)
│   └── NAT Gateway (outbound internet)
└── Private Subnet 10.0.11.0/24 (us-east-1b)
    └── NAT Gateway
```

Public subnets: Route to internet directly (load balancers, NAT gateways)
Private subnets: No direct internet; only internal communication

### Route Tables

Route tables determine where traffic goes:

```bash
# Create public route table
aws ec2 create-route-table --vpc-id vpc-12345

# Add default route to internet gateway
aws ec2 create-route --route-table-id rtb-12345 \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id igw-12345

# Associate with public subnet
aws ec2 associate-route-table --subnet-id subnet-12345 \
  --route-table-id rtb-12345
```

Traffic destined for 0.0.0.0/0 (any IP) goes to the internet gateway.

## 5.2 Security Groups vs. NACLs

### Security Groups

Stateful firewall at instance level. Only "allow" rules.

```bash
# Create security group
aws ec2 create-security-group --group-name web-sg \
  --description "Web server security group" \
  --vpc-id vpc-12345

# Allow HTTP from anyone
aws ec2 authorize-security-group-ingress --group-id sg-12345 \
  --protocol tcp --port 80 --cidr 0.0.0.0/0

# Allow HTTPS from anyone
aws ec2 authorize-security-group-ingress --group-id sg-12345 \
  --protocol tcp --port 443 --cidr 0.0.0.0/0

# Allow SSH from office IP only
aws ec2 authorize-security-group-ingress --group-id sg-12345 \
  --protocol tcp --port 22 --cidr 203.0.113.0/24
```

Stateful: If you send a request on port 80, response on port 80 is automatically allowed (you don't need an explicit ingress rule for responses).

### NACLs

Stateless firewall at subnet level. Rules are processed in order (first match wins).

```bash
# Create NACL
aws ec2 create-network-acl --vpc-id vpc-12345

# Add inbound rule for HTTP
aws ec2 create-network-acl-entry --network-acl-id acl-12345 \
  --rule-number 100 --protocol tcp --port-range From=80,To=80 \
  --cidr-block 0.0.0.0/0 --ingress

# Add outbound rule for HTTP response
aws ec2 create-network-acl-entry --network-acl-id acl-12345 \
  --rule-number 100 --protocol tcp --port-range From=1024,To=65535 \
  --cidr-block 0.0.0.0/0 --egress
```

**Production practice**: Use security groups. Avoid NACLs unless you have specific regulatory requirements. Security groups are simpler and sufficient for 99% of use cases.

## 5.3 Elastic Load Balancer (ELB)

ELB distributes traffic across multiple targets (EC2 instances, Lambda, IP addresses). Critical for high availability.

### ALB: Application Load Balancer

Layer 7 (application) load balancing. Understands HTTP/HTTPS, can route by hostname, path, or headers.

```bash
# Create ALB
aws elbv2 create-load-balancer --name web-alb \
  --subnets subnet-12345 subnet-67890 \
  --security-groups sg-12345 \
  --scheme internet-facing

# Create target group
aws elbv2 create-target-group --name web-targets \
  --protocol HTTP --port 80 --vpc-id vpc-12345

# Create listener (HTTP requests on port 80)
aws elbv2 create-listener --load-balancer-arn arn:aws:elasticloadbalancing:... \
  --protocol HTTP --port 80 \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...

# Register targets (EC2 instances)
aws elbv2 register-targets --target-group-arn arn:aws:elasticloadbalancing:... \
  --targets Id=i-0123456789abcdef0 Id=i-0abcdef0123456789
```

Routing examples:
- Route /api/* to api-server targets
- Route /admin/* to admin-server targets
- Route requests to api.example.com to api-targets
- Route requests to www.example.com to web-targets

### NLB: Network Load Balancer

Layer 4 (transport) load balancing. Ultra-high performance, low latency.

Use NLB for:
- Extreme performance (millions of requests/sec)
- Non-HTTP protocols (TCP, UDP, TLS)
- Latency-sensitive applications

### Health Checks

Load balancers check target health. Unhealthy targets are removed.

```bash
# Configure health check
aws elbv2 modify-target-group --target-group-arn arn:aws:elasticloadbalancing:... \
  --health-check-path /health \
  --health-check-protocol HTTP \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3 \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 10
```

Targets must return HTTP 200-399 to /health endpoint.

## 5.4 Route 53: DNS

Route 53 provides DNS and traffic routing. Aliases traffic based on health, geography, or latency.

### Simple Routing

Map domain to single resource:

```bash
# Create hosted zone
aws route53 create-hosted-zone --name example.com --caller-reference 2024-01-15

# Create A record
aws route53 change-resource-record-sets --hosted-zone-id Z12345 \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "example.com",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [{"Value": "203.0.113.1"}]
      }
    }]
  }'
```

### Alias Records

AWS-specific feature: Map domain to AWS resource directly. No additional cost.

```bash
# Alias to ALB
aws route53 change-resource-record-sets --hosted-zone-id Z12345 \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "www.example.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z35SXDOTRQ7X7K",
          "DNSName": "web-alb-123456.us-east-1.elb.amazonaws.com",
          "EvaluateTargetHealth": true
        }
      }
    }]
  }'
```

EvaluateTargetHealth: Only return IP if ALB is healthy.

### Failover Routing

Route 53 can failover to secondary resource if primary is unhealthy:

```
example.com (primary in us-east-1)
    ↓ (if unhealthy, Route 53 returns)
example.com (secondary in us-west-2)
```

## 5.5 CloudFront: Content Delivery Network

CloudFront caches content at edge locations globally. Serves content from the location closest to the user.

Benefits:
- Reduced latency (content closer to users)
- Reduced origin load (cache hits reduce database queries)
- DDoS protection (AWS manages)
- HTTPS everywhere

### CloudFront Distribution

```bash
# Create distribution
aws cloudfront create-distribution --distribution-config '{
  "CallerReference": "2024-01-15",
  "Origins": [{
    "Id": "myOrigin",
    "DomainName": "example.com",
    "CustomOriginConfig": {
      "HTTPPort": 80,
      "OriginProtocolPolicy": "https-only"
    }
  }],
  "DefaultCacheBehavior": {
    "TargetOriginId": "myOrigin",
    "ViewerProtocolPolicy": "redirect-to-https",
    "TrustedSigners": {
      "Enabled": false,
      "Quantity": 0
    },
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {"Forward": "none"}
    },
    "MinTTL": 0
  },
  "Comment": "CDN for example.com",
  "Enabled": true
}'
```

First request: User → CloudFront edge → Origin
Second request from same user: User → CloudFront edge (cached)

## 5.6 VPC Endpoints

VPC endpoints allow private access to AWS services without internet gateway.

Use case: Access S3 from private subnet without NAT gateway.

```bash
# Create S3 endpoint
aws ec2 create-vpc-endpoint --vpc-id vpc-12345 \
  --service-name com.amazonaws.us-east-1.s3 \
  --route-table-ids rtb-12345

# EC2 in private subnet can now access S3 without internet
aws s3 cp s3://my-bucket/file.txt ./file.txt
```

Benefits:
- No internet gateway needed
- Lower data transfer costs (no NAT charges)
- More secure (traffic stays in AWS)

## 5.7 Network Architecture Example

Production three-tier application network design:

```
Route 53 (DNS resolution)
    ↓
CloudFront Distribution (global edge caching)
    ↓
ALB (multi-AZ load balancing)
    ├─ AZ us-east-1a
    │  ├─ Web EC2 (security group: allow 80, 443)
    │  ├─ App EC2
    │  └─ Private Subnet 10.0.10.0/24
    │     ├─ RDS primary (security group: allow 5432 from app sg)
    │     └─ ElastiCache (security group: allow 6379 from app sg)
    └─ AZ us-east-1b
       ├─ Web EC2
       ├─ App EC2
       └─ Private Subnet 10.0.11.0/24
          ├─ RDS standby (Multi-AZ)
          └─ ElastiCache replica
    ↓
VPC Endpoints (S3, DynamoDB access without internet gateway)
    ↓
NAT Gateway (private instances outbound internet for updates)
```

Data flow:
1. User requests www.example.com
2. Route 53 returns ALB IP
3. User connects to CloudFront edge (closest to them)
4. CloudFront checks if content is cached
5. If cache miss, CloudFront proxies to ALB in us-east-1
6. ALB forwards to healthy EC2 instance
7. Application queries RDS (same AZ for low latency)
8. Response cached in CloudFront
9. Next request from nearby user hits CloudFront cache

## 5.8 Common Mistakes

**Mistake 1: Putting databases in public subnets**
Databases should never be internet-accessible. Always use private subnets.

**Mistake 2: Using 0.0.0.0/0 (allow anyone) for SSH**
SSH access should be restricted to your office/VPN IP. Use 0.0.0.0/0 only if you're OK with brute force attacks.

**Mistake 3: Not configuring health checks**
Without health checks, load balancers send traffic to failed instances. Always configure health checks.

**Mistake 4: CloudFront caching everything**
CloudFront caches based on URL. If your application has session cookies, caching breaks sessions. Use cache invalidation or disable caching for pages with sessions.

**Mistake 5: Ignoring TTL**
Low TTL (30 seconds) means DNS lookups every 30 seconds. High TTL (3600 seconds) means 1 hour to DNS propagation. Choose based on change frequency.

## Assessment

### Practice Questions

**Q1: You need to route traffic to different targets based on URL path. Use:**
A) Network Load Balancer
B) Classic Load Balancer
C) Application Load Balancer
D) Route 53 failover

**Q2: Database in private subnet needs to download security patches. How?**
A) Add route to internet gateway
B) Use NAT gateway in public subnet
C) Use VPC endpoint
D) Disable private subnet restriction

**Q3: Route 53 health check on ALB fails. What happens?**
A) Route 53 stops returning ALB IP
B) ALB automatically scales
C) CloudFront fails
D) Nothing; Route 53 ignores health

**Q4: CloudFront caches content for 1 hour. How to serve updated content immediately?**
A) Wait 1 hour
B) Invalidate cache
C) Add ?v=123 query parameter
D) Change domain name

**Q5: Security group allows port 443 (HTTPS). Traffic on port 80 (HTTP)?**
A) Allowed automatically (stateful)
B) Blocked; only 443 is allowed
C) Depends on NACLs
D) Allowed only from security group itself

### Hands-On Labs

**Lab 1: VPC and Security Groups**

Create VPC with public/private subnets, launch EC2 in each, configure security groups.

**Lab 2: Load Balancer and Route 53**

Create ALB, register targets, create Route 53 DNS record, verify traffic distribution.

### Production Incident Scenario

**Scenario: Region-Wide DDoS Attack**

Your application in us-east-1 gets hit with 1 million requests/second. CloudFront edge locations are overwhelmed. Users in Europe experience slowness.

Root cause: No geographic distribution. All traffic routed to us-east-1 region.

Solution:
- Deploy application in multiple regions (us-east-1, eu-west-1, ap-southeast-1)
- Use Route 53 latency-based routing
- Route 53 returns closest region based on user geography
- Each region absorbs 1/3 of traffic
- Total capacity: 3 million requests/second

Recovery:
1. Activate secondary regions immediately
2. Update Route 53 routing policy
3. Test failover
4. Monitor per-region traffic

Prevention:
- Design for multi-region from day one
- Test regional failover monthly
- Use AWS Shield for DDoS protection

---

Next Module: [Module 6: CI/CD & DevOps Integration](06-cicd-devops-integration.md)
