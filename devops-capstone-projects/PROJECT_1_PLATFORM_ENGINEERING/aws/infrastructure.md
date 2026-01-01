# AWS Infrastructure as Code

## EKS Cluster

```bash
# Create EKS cluster
aws eks create-cluster \
  --name production-cluster \
  --version 1.28 \
  --role-arn arn:aws:iam::ACCOUNT:role/eks-service-role \
  --resources-vpc-config subnetIds=subnet-xxx,subnet-yyy,subnet-zzz \
  --logging-config clusterLogging=[{enabled=true,types=[api,audit,authenticator,controllerManager,scheduler]}]

# Add node group
aws eks create-nodegroup \
  --cluster-name production-cluster \
  --nodegroup-name api-nodes \
  --scaling-config minSize=3,maxSize=20,desiredSize=3 \
  --subnets subnet-xxx subnet-yyy subnet-zzz \
  --node-role arn:aws:iam::ACCOUNT:role/eks-node-role \
  --instance-types t3.medium \
  --tags 'team=backend,environment=production'
```

## RDS PostgreSQL

```bash
# Create RDS instance (Multi-AZ)
aws rds create-db-instance \
  --db-instance-identifier saasdb \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 15.4 \
  --allocated-storage 100 \
  --storage-type gp3 \
  --master-username appuser \
  --master-user-password "$(openssl rand -base64 32)" \
  --db-name saasdb \
  --multi-az \
  --storage-encrypted \
  --kms-key-id arn:aws:kms:us-east-1:ACCOUNT:key/KEY_ID \
  --backup-retention-period 30 \
  --db-subnet-group-name saas-db-subnet \
  --vpc-security-group-ids sg-xxx \
  --enable-cloudwatch-logs-exports '["postgresql"]' \
  --deletion-protection

# Create read replica
aws rds create-db-instance-read-replica \
  --db-instance-identifier saasdb-read \
  --source-db-instance-identifier saasdb \
  --db-instance-class db.t3.medium
```

## ElastiCache Redis

```bash
# Create Redis cluster
aws elasticache create-replication-group \
  --replication-group-description "SaaS Cache" \
  --engine redis \
  --engine-version 7.0 \
  --cache-node-type cache.t3.micro \
  --num-cache-clusters 3 \
  --automatic-failover-enabled \
  --multi-az \
  --cache-subnet-group-name saas-cache-subnet \
  --security-group-ids sg-xxx \
  --at-rest-encryption-enabled \
  --transit-encryption-enabled \
  --auth-token "$(openssl rand -base64 32)"
```

## VPC & Networking

```bash
# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16

# Create subnets
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.1.0/24 --availability-zone us-east-1a
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.2.0/24 --availability-zone us-east-1b
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.3.0/24 --availability-zone us-east-1c

# Create NAT Gateway
aws ec2 allocate-address --domain vpc
aws ec2 create-nat-gateway --subnet-id subnet-xxx --allocation-id eipalloc-xxx

# Create Internet Gateway
aws ec2 create-internet-gateway
aws ec2 attach-internet-gateway --vpc-id vpc-xxx --internet-gateway-id igw-xxx
```

## CloudWatch Monitoring

```bash
# Create custom metric namespace
aws cloudwatch put-metric-data \
  --namespace "SaaS/API" \
  --metric-name "RequestLatency" \
  --value 100 \
  --unit Milliseconds

# Create log group
aws logs create-log-group --log-group-name /aws/eks/saas-production

# Create log retention
aws logs put-retention-policy \
  --log-group-name /aws/eks/saas-production \
  --retention-in-days 30
```

## Cost Allocation Tags

```bash
# Tag all resources
aws ec2 create-tags \
  --resources vpc-xxx \
  --tags 'Key=project,Value=saas' 'Key=environment,Value=production' 'Key=team,Value=backend' 'Key=cost-center,Value=engineering'

aws rds add-tags-to-resource \
  --resource-name arn:aws:rds:us-east-1:ACCOUNT:db:saasdb \
  --tags 'Key=project,Value=saas' 'Key=cost-center,Value=database'
```

## Lambda for Cron Jobs

```bash
# Database cleanup (daily)
aws lambda create-function \
  --function-name saas-cleanup \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT:role/lambda-role \
  --handler index.handler \
  --zip-file fileb://lambda-cleanup.zip

# EventBridge rule for daily execution
aws events put-rule \
  --name saas-cleanup-rule \
  --schedule-expression "cron(0 2 * * ? *)"

aws events put-targets \
  --rule saas-cleanup-rule \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:ACCOUNT:function:saas-cleanup"
```

## Backup & Disaster Recovery

```bash
# Enable RDS automated backups
aws rds modify-db-instance \
  --db-instance-identifier saasdb \
  --backup-retention-period 30 \
  --preferred-backup-window "02:00-03:00"

# Enable RDS Enhanced Monitoring
aws rds modify-db-instance \
  --db-instance-identifier saasdb \
  --monitoring-interval 60 \
  --monitoring-role-arn arn:aws:iam::ACCOUNT:role/rds-monitoring-role

# Create snapshot
aws rds create-db-snapshot \
  --db-instance-identifier saasdb \
  --db-snapshot-identifier saasdb-snapshot-20240101
```

## Cost Optimization

```bash
# Use Reserved Instances
aws ec2 describe-reserved-instances-offerings \
  --filters Name=instance-type,Values=t3.medium \
  --query 'ReservedInstancesOfferings[0]'

# Enable RDS Performance Insights
aws rds modify-db-instance \
  --db-instance-identifier saasdb \
  --enable-performance-insights-kms-key-id arn:aws:kms:us-east-1:ACCOUNT:key/KEY_ID

# Use S3 Intelligent-Tiering for logs
aws s3api put-bucket-intelligent-tiering-configuration \
  --bucket saas-logs \
  --id AutoArchive \
  --intelligent-tiering-configuration '{"Id":"AutoArchive","Filter":{"Prefix":"logs/"},"Status":"Enabled","Tierings":[{"Days":90,"AccessTier":"ARCHIVE_ACCESS"}]}'
```
