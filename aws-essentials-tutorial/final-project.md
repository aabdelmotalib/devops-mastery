# Final Project: Production-Ready AWS Deployment

This final project synthesizes everything learned in Modules 1-10. You'll design and deploy a complete, production-grade backend system on AWS.

## Project Overview

Deploy a multi-tier e-commerce backend with:
- User registration and authentication
- Product catalog
- Shopping cart and order management
- Payment processing (mock)
- Admin dashboard
- Full monitoring and logging
- Automated deployment pipeline

### Architecture Diagram

```
Users/Clients
    ↓
Route 53 (DNS)
    ↓
CloudFront (CDN)
    ↓
ALB (Load Balancer)
    ├─ AZ us-east-1a
    │  ├─ API Server (ECS Fargate)
    │  ├─ Admin Server (ECS Fargate)
    │  └─ Lambda Functions
    └─ AZ us-east-1b
       ├─ API Server (ECS Fargate)
       ├─ Admin Server (ECS Fargate)
       └─ Lambda Functions
    ↓
Databases
├─ RDS PostgreSQL (users, orders, products)
├─ DynamoDB (sessions, real-time data)
└─ ElastiCache Redis (caching)
    ↓
Storage
├─ S3 (product images, backups)
└─ SQS/SNS (asynchronous tasks)
    ↓
Monitoring
├─ CloudWatch (logs, metrics, alarms)
├─ CloudTrail (audit)
└─ X-Ray (tracing)
```

## Phase 1: Infrastructure Setup (4 hours)

### 1.1 VPC and Networking

Create VPC with public and private subnets across two AZs:

```bash
#!/bin/bash

# Create VPC
VPC_ID=$(aws ec2 create-vpc --cidr-block 10.0.0.0/16 --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=ecommerce-vpc}]' --query 'Vpc.VpcId' --output text)

# Create Internet Gateway
IGW_ID=$(aws ec2 create-internet-gateway --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=ecommerce-igw}]' --query 'InternetGateway.InternetGatewayId' --output text)
aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID

# Public Subnets (for ALB, NAT Gateway)
PUBLIC_SUBNET_AZ1=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.1.0/24 --availability-zone us-east-1a --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=public-1a}]' --query 'Subnet.SubnetId' --output text)
PUBLIC_SUBNET_AZ2=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.2.0/24 --availability-zone us-east-1b --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=public-1b}]' --query 'Subnet.SubnetId' --output text)

# Private Subnets (for RDS, ECS, Lambda)
PRIVATE_SUBNET_AZ1=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.10.0/24 --availability-zone us-east-1a --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=private-1a}]' --query 'Subnet.SubnetId' --output text)
PRIVATE_SUBNET_AZ2=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.11.0/24 --availability-zone us-east-1b --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=private-1b}]' --query 'Subnet.SubnetId' --output text)

# Create public route table
PUBLIC_RTB=$(aws ec2 create-route-table --vpc-id $VPC_ID --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=public-rtb}]' --query 'RouteTable.RouteTableId' --output text)
aws ec2 create-route --route-table-id $PUBLIC_RTB --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID
aws ec2 associate-route-table --subnet-id $PUBLIC_SUBNET_AZ1 --route-table-id $PUBLIC_RTB
aws ec2 associate-route-table --subnet-id $PUBLIC_SUBNET_AZ2 --route-table-id $PUBLIC_RTB

# Create NAT Gateway (allows private subnets outbound internet)
EIP=$(aws ec2 allocate-address --domain vpc --tag-specifications 'ResourceType=elastic-ip,Tags=[{Key=Name,Value=nat-eip}]' --query 'PublicIp' --output text)
NAT_GW=$(aws ec2 create-nat-gateway --subnet-id $PUBLIC_SUBNET_AZ1 --allocation-id $(aws ec2 describe-addresses --public-ips $EIP --query 'Addresses[0].AllocationId' --output text) --tag-specifications 'ResourceType=nat-gateway,Tags=[{Key=Name,Value=nat-gateway}]' --query 'NatGateway.NatGatewayId' --output text)

# Private route table (routes through NAT)
PRIVATE_RTB=$(aws ec2 create-route-table --vpc-id $VPC_ID --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=private-rtb}]' --query 'RouteTable.RouteTableId' --output text)
aws ec2 create-route --route-table-id $PRIVATE_RTB --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT_GW
aws ec2 associate-route-table --subnet-id $PRIVATE_SUBNET_AZ1 --route-table-id $PRIVATE_RTB
aws ec2 associate-route-table --subnet-id $PRIVATE_SUBNET_AZ2 --route-table-id $PRIVATE_RTB

echo "VPC Setup Complete"
echo "VPC: $VPC_ID"
echo "Public Subnets: $PUBLIC_SUBNET_AZ1, $PUBLIC_SUBNET_AZ2"
echo "Private Subnets: $PRIVATE_SUBNET_AZ1, $PRIVATE_SUBNET_AZ2"
```

### 1.2 Security Groups

```bash
# ALB Security Group (allows HTTP/HTTPS from internet)
ALB_SG=$(aws ec2 create-security-group --group-name alb-sg --description "ALB security group" --vpc-id $VPC_ID --query 'GroupId' --output text)
aws ec2 authorize-security-group-ingress --group-id $ALB_SG --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $ALB_SG --protocol tcp --port 443 --cidr 0.0.0.0/0

# App Security Group (allows traffic from ALB only)
APP_SG=$(aws ec2 create-security-group --group-name app-sg --description "App security group" --vpc-id $VPC_ID --query 'GroupId' --output text)
aws ec2 authorize-security-group-ingress --group-id $APP_SG --protocol tcp --port 80 --source-group $ALB_SG
aws ec2 authorize-security-group-ingress --group-id $APP_SG --protocol tcp --port 443 --source-group $ALB_SG

# Database Security Group (allows traffic from app only)
DB_SG=$(aws ec2 create-security-group --group-name db-sg --description "Database security group" --vpc-id $VPC_ID --query 'GroupId' --output text)
aws ec2 authorize-security-group-ingress --group-id $DB_SG --protocol tcp --port 5432 --source-group $APP_SG
aws ec2 authorize-security-group-ingress --group-id $DB_SG --protocol tcp --port 6379 --source-group $APP_SG  # Redis
```

### 1.3 Load Balancer

```bash
# Create ALB
ALB=$(aws elbv2 create-load-balancer --name ecommerce-alb \
  --subnets $PUBLIC_SUBNET_AZ1 $PUBLIC_SUBNET_AZ2 \
  --security-groups $ALB_SG \
  --scheme internet-facing \
  --type application \
  --query 'LoadBalancers[0].LoadBalancerArn' --output text)

# Create target group
TG=$(aws elbv2 create-target-group --name api-targets \
  --protocol HTTP --port 80 --vpc-id $VPC_ID \
  --target-type ip \
  --health-check-path /health \
  --query 'TargetGroups[0].TargetGroupArn' --output text)

# Create listener
aws elbv2 create-listener --load-balancer-arn $ALB \
  --protocol HTTP --port 80 \
  --default-actions Type=forward,TargetGroupArn=$TG
```

## Phase 2: Database Setup (2 hours)

### 2.1 RDS PostgreSQL

```bash
# Create RDS instance
RDS_INSTANCE=$(aws rds create-db-instance \
  --db-instance-identifier ecommerce-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username admin \
  --master-user-password $(openssl rand -base64 32) \
  --allocated-storage 20 \
  --vpc-security-group-ids $DB_SG \
  --db-subnet-group-name default \
  --multi-az \
  --backup-retention-period 7 \
  --enable-cloudwatch-logs-exports postgresql \
  --query 'DBInstance.DBInstanceIdentifier' --output text)

# Wait for creation (takes 5-10 minutes)
aws rds wait db-instance-available --db-instance-identifier ecommerce-db

# Get endpoint
RDS_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier ecommerce-db \
  --query 'DBInstances[0].Endpoint.Address' --output text)

# Initialize database
psql -h $RDS_ENDPOINT -U admin -d postgres << EOF
CREATE DATABASE ecommerce;
\c ecommerce
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  name VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  price DECIMAL(10,2),
  image_url VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  total DECIMAL(10,2),
  status VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
EOF
```

### 2.2 ElastiCache Redis

```bash
# Create Redis cluster
ELASTICACHE=$(aws elasticache create-cache-cluster \
  --cache-cluster-id ecommerce-cache \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1 \
  --security-group-ids $DB_SG \
  --query 'CacheCluster.CacheNodes[0].Endpoint.Address' --output text)
```

## Phase 3: Application Development (4 hours)

### 3.1 Flask Backend API

```python
# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import redis
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Database connection
db_conn = psycopg2.connect(
    host=os.environ['DB_HOST'],
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
    database='ecommerce'
)

# Redis cache
cache = redis.Redis(
    host=os.environ['CACHE_HOST'],
    port=6379,
    decode_responses=True
)

# Health check
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

# User registration
@app.route('/api/users/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    cursor = db_conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (email, password_hash, name) VALUES (%s, %s, %s)",
            (email, hash_password(password), data.get('name'))
        )
        db_conn.commit()
        return jsonify({'status': 'registered'}), 201
    except Exception as e:
        db_conn.rollback()
        return jsonify({'error': str(e)}), 400

# Get products (cached)
@app.route('/api/products', methods=['GET'])
def get_products():
    # Try cache first
    cached = cache.get('products')
    if cached:
        return json.loads(cached), 200
    
    # Query database
    cursor = db_conn.cursor()
    cursor.execute("SELECT id, name, price, image_url FROM products")
    products = [{'id': row[0], 'name': row[1], 'price': float(row[2]), 'image': row[3]} for row in cursor.fetchall()]
    
    # Cache for 1 hour
    cache.setex('products', 3600, json.dumps(products))
    
    return jsonify(products), 200

# Create order
@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.json
    user_id = data.get('user_id')
    items = data.get('items')  # List of {product_id, quantity}
    
    total = 0
    for item in items:
        cursor = db_conn.cursor()
        cursor.execute("SELECT price FROM products WHERE id = %s", (item['product_id'],))
        price = cursor.fetchone()[0]
        total += price * item['quantity']
    
    cursor = db_conn.cursor()
    cursor.execute(
        "INSERT INTO orders (user_id, total, status) VALUES (%s, %s, %s) RETURNING id",
        (user_id, total, 'pending')
    )
    order_id = cursor.fetchone()[0]
    db_conn.commit()
    
    # Publish event for payment processing
    publish_to_sqs('OrderCreated', {'order_id': order_id, 'user_id': user_id, 'amount': total})
    
    return jsonify({'order_id': order_id, 'status': 'pending'}), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
```

### 3.2 Docker Configuration

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .

ENV FLASK_APP=app.py
ENV DB_HOST=ecommerce-db.xxxxx.us-east-1.rds.amazonaws.com
ENV DB_USER=admin
ENV CACHE_HOST=ecommerce-cache.xxxxx.ng.0001.use1.cache.amazonaws.com

CMD ["python", "app.py"]
```

## Phase 4: Containerization & Deployment (3 hours)

### 4.1 Push Docker Image to ECR

```bash
# Create ECR repository
aws ecr create-repository --repository-name ecommerce-api

# Build and push image
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGISTRY=$ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $REGISTRY

docker build -t ecommerce-api:latest .
docker tag ecommerce-api:latest $REGISTRY/ecommerce-api:latest
docker push $REGISTRY/ecommerce-api:latest
```

### 4.2 ECS Task Definition

```json
{
  "family": "ecommerce-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/ecommerce-api:latest",
      "portMappings": [
        {
          "containerPort": 80,
          "protocol": "tcp"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ecommerce-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "environment": [
        {
          "name": "DB_HOST",
          "value": "ecommerce-db.xxxxx.us-east-1.rds.amazonaws.com"
        }
      ]
    }
  ]
}
```

### 4.3 ECS Service

```bash
# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create ECS cluster
aws ecs create-cluster --cluster-name ecommerce

# Create service (run 2 tasks across 2 AZs)
aws ecs create-service \
  --cluster ecommerce \
  --service-name api-service \
  --task-definition ecommerce-api:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$PRIVATE_SUBNET_AZ1,$PRIVATE_SUBNET_AZ2],securityGroups=[$APP_SG],assignPublicIp=DISABLED}" \
  --load-balancers targetGroupArn=$TG,containerName=api,containerPort=80
```

## Phase 5: CI/CD Pipeline (2 hours)

### 5.1 CodePipeline

```bash
# Create CodeBuild project for testing
aws codebuild create-project --name ecommerce-test \
  --source type=GITHUB,location=https://github.com/yourorg/ecommerce.git \
  --artifacts type=S3,location=pipeline-artifacts \
  --environment type=LINUX_CONTAINER,image=aws/codebuild/standard:5.0,computeType=BUILD_GENERAL1_SMALL \
  --service-role arn:aws:iam::$ACCOUNT_ID:role/codebuild-role

# Create CodePipeline
aws codepipeline create-pipeline --cli-input-json '{
  "pipeline": {
    "name": "ecommerce-pipeline",
    "roleArn": "arn:aws:iam::'$ACCOUNT_ID':role/codepipeline-role",
    "artifactStore": {"type": "S3", "location": "pipeline-artifacts"},
    "stages": [
      {
        "name": "Source",
        "actions": [{
          "name": "GitHub",
          "actionTypeId": {"category": "Source", "owner": "ThirdParty", "provider": "GitHub", "version": "1"},
          "configuration": {"Owner": "yourorg", "Repo": "ecommerce", "Branch": "main"},
          "outputArtifacts": [{"name": "SourceOutput"}]
        }]
      },
      {
        "name": "Build",
        "actions": [{
          "name": "BuildAndTest",
          "actionTypeId": {"category": "Build", "owner": "AWS", "provider": "CodeBuild", "version": "1"},
          "configuration": {"ProjectName": "ecommerce-test"},
          "inputArtifacts": [{"name": "SourceOutput"}],
          "outputArtifacts": [{"name": "BuildOutput"}]
        }]
      },
      {
        "name": "Deploy",
        "actions": [{
          "name": "DeployToECS",
          "actionTypeId": {"category": "Deploy", "owner": "AWS", "provider": "ECS", "version": "1"},
          "configuration": {"ClusterName": "ecommerce", "ServiceName": "api-service", "FileName": "imagedefinitions.json"},
          "inputArtifacts": [{"name": "BuildOutput"}]
        }]
      }
    ]
  }
}'
```

## Phase 6: Monitoring & Logging (3 hours)

### 6.1 CloudWatch

```bash
# Create log groups
aws logs create-log-group --log-group-name /ecs/ecommerce-api
aws logs create-log-group --log-group-name /aws/rds/ecommerce

# Create CloudWatch dashboard
aws cloudwatch put-dashboard --dashboard-name ecommerce \
  --dashboard-body '{
    "widgets": [
      {
        "type": "metric",
        "properties": {
          "metrics": [
            ["AWS/ECS", "CPUUtilization", {"stat": "Average"}],
            ["AWS/ECS", "MemoryUtilization"],
            ["AWS/ApplicationELB", "TargetResponseTime"],
            ["AWS/RDS", "DatabaseConnections"],
            ["AWS/ElastiCache", "CacheHits"]
          ],
          "period": 300,
          "stat": "Average",
          "region": "us-east-1",
          "title": "Ecommerce Application Metrics"
        }
      }
    ]
  }'

# Create alarms
aws cloudwatch put-metric-alarm --alarm-name ecommerce-cpu-high \
  --alarm-description "Alert when CPU is high" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-east-1:$ACCOUNT_ID:alerts
```

### 6.2 Enable CloudTrail

```bash
aws cloudtrail create-trail --name ecommerce-trail \
  --s3-bucket-name ecommerce-cloudtrail

aws cloudtrail start-logging --trail-name ecommerce-trail

aws cloudtrail put-event-selectors --trail-name ecommerce-trail \
  --event-selectors ReadWriteType=All,IncludeManagementEvents=true
```

## Phase 7: Security & Backup (2 hours)

### 7.1 Secrets Manager

```bash
# Store database password
aws secretsmanager create-secret --name ecommerce/db-password \
  --secret-string "$(openssl rand -base64 32)"

# Configure automatic rotation
aws secretsmanager rotate-secret --secret-id ecommerce/db-password \
  --rotation-rules AutomaticallyAfterDays=30
```

### 7.2 RDS Backups

```bash
# Automated backups are enabled (7-day retention)
# Create manual snapshot for major releases
aws rds create-db-snapshot \
  --db-instance-identifier ecommerce-db \
  --db-snapshot-identifier ecommerce-db-backup-2024-01-15
```

## Phase 8: Deployment & Testing (2 hours)

### 8.1 DNS and CDN

```bash
# Create Route 53 hosted zone
aws route53 create-hosted-zone --name ecommerce.example.com \
  --caller-reference 2024-01-15

# Create A record alias to ALB
aws route53 change-resource-record-sets --hosted-zone-id Z123 \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "api.ecommerce.example.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z35SXDOTRQ7X7K",
          "DNSName": "ecommerce-alb-123456.us-east-1.elb.amazonaws.com",
          "EvaluateTargetHealth": true
        }
      }
    }]
  }'

# Create CloudFront distribution
aws cloudfront create-distribution --distribution-config '{
  "CallerReference": "ecommerce-2024-01-15",
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [{
      "Id": "myOrigin",
      "DomainName": "api.ecommerce.example.com",
      "CustomOriginConfig": {
        "HTTPPort": 80,
        "OriginProtocolPolicy": "http-only"
      }
    }]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "myOrigin",
    "ViewerProtocolPolicy": "redirect-to-https",
    "TrustedSigners": {"Enabled": false, "Quantity": 0},
    "ForwardedValues": {"QueryString": false, "Cookies": {"Forward": "none"}},
    "MinTTL": 0
  },
  "Comment": "Ecommerce CDN",
  "Enabled": true
}'
```

### 8.2 Load Testing

```bash
# Use Apache Bench to test
ab -n 1000 -c 10 http://api.ecommerce.example.com/api/products

# Monitor CloudWatch metrics during test
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average,Maximum
```

## Success Criteria

✓ VPC with public and private subnets across 2 AZs
✓ RDS PostgreSQL multi-AZ with automated backups
✓ ElastiCache Redis for caching
✓ ALB distributing traffic to 2+ ECS tasks
✓ Containerized API in ECR
✓ CI/CD pipeline from GitHub to ECS
✓ CloudWatch monitoring and alarms
✓ CloudTrail audit logging
✓ Secrets Manager for credentials
✓ Route 53 DNS routing
✓ CloudFront CDN
✓ Health checks passing
✓ API responding to HTTP requests
✓ Database persisting data
✓ Autoscaling functional (can scale ECS tasks)
✓ All traffic encrypted (HTTPS)
✓ Logs aggregated in CloudWatch

## Estimated Costs

- ALB: $16/month
- ECS Fargate: $15/month (2 tasks)
- RDS db.t3.micro: $30/month
- ElastiCache cache.t3.micro: $17/month
- NAT Gateway: $32/month (data transfer)
- Route 53: $0.50/month (1 hosted zone)
- CloudFront: $2-10/month (minimal traffic)

**Total: ~$110-130/month**

## Production Checklist

- [ ] Multi-region failover tested
- [ ] Disaster recovery (restore from backup) tested
- [ ] Load testing completed, baseline established
- [ ] Security groups tested (only necessary ports open)
- [ ] Database backups automated and tested
- [ ] Logs retained for 30+ days
- [ ] Alarms configured and tested
- [ ] CloudTrail recording all API calls
- [ ] IAM roles follow least privilege
- [ ] Secrets Manager configured with rotation
- [ ] HTTPS enforced everywhere
- [ ] CORS properly configured
- [ ] API rate limiting implemented
- [ ] Error handling robust (500 errors don't crash app)
- [ ] Rollback procedure tested
- [ ] On-call escalation path documented

---

**Congratulations!** You've deployed a production-grade AWS system. This architecture handles:
- High availability (multi-AZ)
- Scalability (autoscaling, caching, CDN)
- Durability (Multi-AZ RDS, automated backups)
- Security (VPC isolation, IAM, encryption, audit logs)
- Observability (comprehensive monitoring, logging, tracing)
- Operational excellence (CI/CD, Infrastructure as Code, automated deployment)

Now apply these patterns to your own applications.
