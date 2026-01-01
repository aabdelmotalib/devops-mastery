# Reference Implementations

This file contains complete, copy-paste-ready example code for common AWS patterns covered in the tutorial.

## Terraform: Complete VPC and Network Stack

```hcl
# main.tf

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "ecommerce-vpc"
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "public-subnet-${count.index + 1}"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "private-subnet-${count.index + 1}"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "ecommerce-igw"
  }
}

# NAT Gateway
resource "aws_eip" "nat" {
  domain = "vpc"
  tags = {
    Name = "nat-eip"
  }
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name = "nat-gateway"
  }

  depends_on = [aws_internet_gateway.main]
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block      = "0.0.0.0/0"
    gateway_id      = aws_internet_gateway.main.id
  }

  tags = {
    Name = "public-rtb"
  }
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }

  tags = {
    Name = "private-rtb"
  }
}

resource "aws_route_table_association" "private" {
  count          = 2
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# Security Groups
resource "aws_security_group" "alb" {
  name   = "alb-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "alb-sg"
  }
}

resource "aws_security_group" "app" {
  name   = "app-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "app-sg"
  }
}

resource "aws_security_group" "db" {
  name   = "db-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "db-sg"
  }
}

# ALB
resource "aws_lb" "main" {
  name               = "ecommerce-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  tags = {
    Name = "ecommerce-alb"
  }
}

resource "aws_lb_target_group" "app" {
  name        = "app-targets"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 10
    interval            = 30
    path                = "/health"
    matcher             = "200"
  }

  tags = {
    Name = "app-targets"
  }
}

resource "aws_lb_listener" "app" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

# Data source for AZs
data "aws_availability_zones" "available" {
  state = "available"
}

# Outputs
output "alb_dns" {
  value       = aws_lb.main.dns_name
  description = "ALB DNS name"
}

output "vpc_id" {
  value       = aws_vpc.main.id
  description = "VPC ID"
}

output "private_subnet_ids" {
  value       = aws_subnet.private[*].id
  description = "Private subnet IDs"
}
```

## CloudFormation: RDS and ElastiCache

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'RDS PostgreSQL and ElastiCache Redis stack'

Parameters:
  VpcId:
    Type: AWS::EC2::VPC::Id
    Description: VPC ID
  
  PrivateSubnetIds:
    Type: List<AWS::EC2::Subnet::Id>
    Description: Private subnet IDs
  
  DBSecurityGroupId:
    Type: AWS::EC2::SecurityGroup::Id
    Description: Database security group

Resources:
  DBSubnetGroup:
    Type: AWS::RDS::DBSubnetGroup
    Properties:
      DBSubnetGroupDescription: Subnet group for RDS
      SubnetIds: !Ref PrivateSubnetIds
      Tags:
        - Key: Name
          Value: db-subnet-group

  RDSInstance:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceIdentifier: ecommerce-db
      DBInstanceClass: db.t3.micro
      Engine: postgres
      EngineVersion: '15.1'
      MasterUsername: admin
      MasterUserPassword: !Sub '{{resolve:secretsmanager:ecommerce/db-password:SecretString:password}}'
      AllocatedStorage: 20
      StorageType: gp3
      StorageEncrypted: true
      VPCSecurityGroups:
        - !Ref DBSecurityGroupId
      DBSubnetGroupName: !Ref DBSubnetGroup
      MultiAZ: true
      BackupRetentionPeriod: 7
      PreferredBackupWindow: '03:00-04:00'
      PreferredMaintenanceWindow: 'sun:04:00-sun:05:00'
      EnableCloudwatchLogsExports:
        - postgresql
      EnableIAMDatabaseAuthentication: false
      Tags:
        - Key: Name
          Value: ecommerce-db

  ElastiCacheSubnetGroup:
    Type: AWS::ElastiCache::SubnetGroup
    Properties:
      Description: Subnet group for ElastiCache
      SubnetIds: !Ref PrivateSubnetIds
      Tags:
        - Key: Name
          Value: cache-subnet-group

  ElastiCacheCluster:
    Type: AWS::ElastiCache::CacheCluster
    Properties:
      CacheClusterId: ecommerce-cache
      CacheNodeType: cache.t3.micro
      Engine: redis
      EngineVersion: '7.0'
      NumCacheNodes: 1
      CacheSubnetGroupName: !Ref ElastiCacheSubnetGroup
      VpcSecurityGroupIds:
        - !Ref DBSecurityGroupId
      AutomaticFailoverEnabled: false
      Tags:
        - Key: Name
          Value: ecommerce-cache

Outputs:
  RDSEndpoint:
    Description: RDS database endpoint
    Value: !GetAtt RDSInstance.Endpoint.Address
  
  ElastiCacheEndpoint:
    Description: ElastiCache cluster endpoint
    Value: !GetAtt ElastiCacheCluster.RedisEndpoint.Address
```

## Flask Application with AWS Integration

```python
# app.py
import os
import json
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import redis
import boto3
from datetime import datetime
from functools import wraps
import jwt

# Initialize Flask
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS clients
s3 = boto3.client('s3')
sns = boto3.client('sns')
sqs = boto3.client('sqs')
cloudwatch = boto3.client('cloudwatch')

# Database connection
def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ['DB_HOST'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        database='ecommerce',
        cursor_factory=psycopg2.extras.RealDictCursor
    )
    return conn

# Redis cache
cache = redis.Redis(
    host=os.environ.get('CACHE_HOST', 'localhost'),
    port=6379,
    decode_responses=True,
    socket_connect_timeout=5
)

# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    try:
        cache.ping()
        conn = get_db_connection()
        conn.close()
        return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503

# Register user
@app.route('/api/users/register', methods=['POST'])
def register():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO users (email, password_hash, name) VALUES (%s, %s, %s) RETURNING id",
                (email, hash(password), name)  # NOTE: Use bcrypt in production
            )
            user_id = cursor.fetchone()['id']
            conn.commit()
            
            # Log to CloudWatch
            cloudwatch.put_metric_data(
                Namespace='Ecommerce',
                MetricData=[
                    {
                        'MetricName': 'UserRegistrations',
                        'Value': 1,
                        'Unit': 'Count'
                    }
                ]
            )
            
            return jsonify({'user_id': user_id, 'email': email}), 201
        
        except psycopg2.IntegrityError:
            conn.rollback()
            return jsonify({'error': 'Email already exists'}), 409
        
        finally:
            cursor.close()
            conn.close()
    
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Get products (with caching)
@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        # Try cache first
        cached = cache.get('products:all')
        if cached:
            logger.info("Cache hit: products")
            return json.loads(cached), 200
        
        # Query database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description, price, image_url FROM products ORDER BY created_at DESC")
        products = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Cache for 1 hour
        cache.setex('products:all', 3600, json.dumps(products))
        
        logger.info(f"Retrieved {len(products)} products from database")
        return jsonify(products), 200
    
    except Exception as e:
        logger.error(f"Get products error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Create order
@app.route('/api/orders', methods=['POST'])
def create_order():
    try:
        data = request.json
        user_id = data.get('user_id')
        items = data.get('items', [])
        
        if not user_id or not items:
            return jsonify({'error': 'User ID and items required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Calculate total
        total = 0
        for item in items:
            cursor.execute("SELECT price FROM products WHERE id = %s", (item['product_id'],))
            product = cursor.fetchone()
            if product:
                total += product['price'] * item['quantity']
        
        # Create order
        cursor.execute(
            "INSERT INTO orders (user_id, total, status) VALUES (%s, %s, %s) RETURNING id, created_at",
            (user_id, total, 'pending')
        )
        order = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        # Publish event to SNS for payment processing
        sns.publish(
            TopicArn=os.environ['ORDER_TOPIC_ARN'],
            Message=json.dumps({
                'order_id': order['id'],
                'user_id': user_id,
                'total': float(total),
                'created_at': order['created_at'].isoformat()
            })
        )
        
        return jsonify({
            'order_id': order['id'],
            'total': float(total),
            'status': 'pending'
        }), 201
    
    except Exception as e:
        logger.error(f"Create order error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Error handler
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 80)), debug=False)
```

## Lambda: Order Processing

```python
# lambda_function.py
import json
import boto3
import os
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')
table = dynamodb.Table('OrderEvents')

def lambda_handler(event, context):
    """
    Process SNS order events
    """
    try:
        for record in event['Records']:
            # Parse SNS message
            message = json.loads(record['Sns']['Message'])
            order_id = message['order_id']
            user_id = message['user_id']
            total = message['total']
            
            # Store order event
            table.put_item(
                Item={
                    'order_id': order_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'event_type': 'OrderCreated',
                    'user_id': user_id,
                    'total': total
                }
            )
            
            # Send confirmation email
            ses.send_email(
                Source='noreply@ecommerce.example.com',
                Destination={'ToAddresses': [message.get('email', 'customer@example.com')]},
                Message={
                    'Subject': {'Data': f'Order Confirmation #{order_id}'},
                    'Body': {'Html': f'<h1>Your order #{order_id} for ${total} has been received.</h1>'}
                }
            )
            
            print(f"Processed order {order_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps('Orders processed successfully')
        }
    
    except Exception as e:
        print(f"Error: {str(e)}")
        raise
```

These examples provide production-ready starting points for common AWS patterns.
