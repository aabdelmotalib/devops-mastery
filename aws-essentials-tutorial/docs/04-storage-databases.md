# Module 4: Storage & Databases

Data durability and availability are non-negotiable in production. AWS provides multiple storage and database services optimized for different access patterns. Choose the wrong service and you'll face poor performance, unexpected costs, or data loss.

## 4.1 S3: Object Storage

S3 stores arbitrary objects (files) identified by keys. It's not a file system; it's a key-value store for objects up to 5TB each.

### Buckets and Keys

Bucket: Top-level container (must be globally unique name)
Key: Full path to object including "directories"

```
Bucket: my-app-data
├── Key: documents/resume.pdf
├── Key: images/profile.jpg
├── Key: backups/db-2024-01-15.sql
└── Key: logs/app.log
```

In S3 API:
```bash
# Upload object
aws s3 cp resume.pdf s3://my-app-data/documents/resume.pdf

# Download object
aws s3 cp s3://my-app-data/documents/resume.pdf ./resume.pdf

# List objects
aws s3 ls s3://my-app-data/documents/

# Delete object
aws s3 rm s3://my-app-data/documents/resume.pdf
```

### Storage Classes

S3 offers multiple storage classes for different access patterns and costs:

| Class | Use Case | Cost | Retrieval |
|-------|----------|------|-----------|
| Standard | Frequent access | Highest | Immediate |
| Intelligent-Tiering | Unknown pattern | Medium | Automatic |
| Standard-IA | Infrequent access | Lower | Immediate |
| Glacier Instant | Archive, occasional access | Low | Minutes |
| Glacier Flexible | Archive, rare access | Very low | Hours |
| Deep Archive | Compliance archive | Lowest | 12 hours |

**Selection strategy**:
- **Standard**: Current data, < 30 days old
- **Standard-IA**: Old data, occasional access (backup logs)
- **Glacier**: Archived data, accessed maybe once per year
- **Deep Archive**: Compliance-required retention (7+ years)

### Lifecycle Policies

Automatically transition objects between storage classes to reduce costs:

```bash
# Create lifecycle policy
aws s3api put-bucket-lifecycle-configuration --bucket my-app-data \
  --lifecycle-configuration '{
    "Rules": [{
      "Id": "archive-old-logs",
      "Status": "Enabled",
      "Filter": {"Prefix": "logs/"},
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        },
        {
          "Days": 365,
          "StorageClass": "DEEP_ARCHIVE"
        }
      ],
      "Expiration": {"Days": 2555}
    }]
  }'
```

This policy saves money: Log file uploaded today costs $0.023/GB. After 30 days, it costs $0.0125/GB (standard-IA). After 90 days, $0.004/GB (Glacier). Over 10 years, you save 80%.

### Versioning and MFA Delete

Versioning keeps historical versions of objects. You can restore deleted/overwritten objects.

```bash
# Enable versioning
aws s3api put-bucket-versioning --bucket my-app-data \
  --versioning-configuration Status=Enabled

# Delete creates a delete marker (object is hidden, but versions remain)
aws s3 rm s3://my-app-data/documents/resume.pdf

# Restore by uploading new version with same key
aws s3 cp newresume.pdf s3://my-app-data/documents/resume.pdf

# List all versions
aws s3api list-object-versions --bucket my-app-data
```

MFA delete requires MFA to permanently delete versions:

```bash
# Requires MFA code to delete
aws s3api delete-object --bucket my-app-data --key documents/resume.pdf \
  --mfa "arn:aws:iam::123456789012:mfa/alice 123456"
```

### S3 Encryption

By default, S3 encrypts objects with AWS-managed keys. For sensitive data, use customer-managed KMS keys:

```bash
# Create KMS key
aws kms create-key --description "S3 encryption key"

# Enable encryption on bucket
aws s3api put-bucket-encryption --bucket my-app-data \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "aws:kms",
        "KMSMasterKeyID": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"
      }
    }]
  }'
```

Encryption happens transparently. You upload, S3 encrypts. You download, S3 decrypts. You never see the key.

## 4.2 RDS: Relational Database Service

RDS is a managed relational database. AWS handles patching, backups, replication, automatic failover.

Supported engines: MySQL, PostgreSQL, MariaDB, SQL Server, Oracle, Aurora.

### RDS Setup

```bash
# Create DB instance
aws rds create-db-instance \
  --db-instance-identifier mydb \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username admin \
  --master-user-password MySecurePassword123 \
  --allocated-storage 20 \
  --availability-zone us-east-1a \
  --backup-retention-period 7 \
  --multi-az  # Multi-AZ for high availability

# Get connection details
aws rds describe-db-instances --db-instance-identifier mydb \
  --query 'DBInstances[0].Endpoint'
```

Connect from EC2:
```bash
# Install PostgreSQL client
sudo apt-get install postgresql-client

# Connect (EC2 must be in same VPC and security group must allow port 5432)
psql -h mydb.xxxxx.us-east-1.rds.amazonaws.com -U admin -d mydb
```

### Multi-AZ Deployment

Multi-AZ RDS automatically replicates to a standby instance in another AZ. On primary failure, automatic failover occurs (30-120 seconds of downtime).

Costs 2x, but provides:
- Automatic failover
- Synchronous replication
- No data loss on primary failure

### RDS Read Replicas

Read replicas are asynchronous replicas (can have slight lag). Perfect for read-heavy workloads or reporting.

```bash
# Create read replica
aws rds create-db-instance-read-replica \
  --db-instance-identifier mydb-replica \
  --source-db-instance-identifier mydb \
  --db-instance-class db.t3.micro \
  --availability-zone us-east-1b
```

Architecture:
```
Application writes to Primary (us-east-1a)
    ↓
Synchronously replicates to Standby (us-east-1b, multi-AZ)
    ↓
Asynchronously replicates to Read Replicas (can be cross-region)
```

Example scaling: 1000 requests/second, 80% reads, 20% writes
- Send 200 writes/second to primary
- Send 800 reads/second to replicas
- Each replica handles 200 reads/second (4 replicas needed)

### Backup and Restore

Automated backups:
- Retained for backup retention period (7 days default, up to 35 days)
- Enables point-in-time recovery
- Stored in S3 (transparent)

```bash
# Manual snapshot
aws rds create-db-snapshot --db-instance-identifier mydb \
  --db-snapshot-identifier mydb-backup-2024-01-15

# Restore from snapshot (creates new instance)
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier mydb-restored \
  --db-snapshot-identifier mydb-backup-2024-01-15
```

## 4.3 Aurora

Aurora is AWS's proprietary relational database with MySQL and PostgreSQL compatibility. Significantly faster and more reliable than standard RDS.

Features:
- 5x faster than MySQL, 3x faster than PostgreSQL
- Automatic scaling (up to 128 TB)
- Built-in high availability (3 copies across AZs)
- Read replicas in milliseconds

```bash
# Create Aurora cluster
aws rds create-db-cluster \
  --db-cluster-identifier my-aurora \
  --engine aurora-postgresql \
  --master-username admin \
  --master-user-password MyPassword123

# Add instances to cluster
aws rds create-db-instance \
  --db-instance-identifier my-aurora-1 \
  --db-instance-class db.t3.medium \
  --engine aurora-postgresql \
  --db-cluster-identifier my-aurora
```

**Cost**: Aurora costs more than RDS per instance, but fewer instances are needed.

## 4.4 DynamoDB

DynamoDB is a NoSQL database for key-value and document data. Serverless (auto-scaling), highly available, single-digit millisecond latency.

Use DynamoDB when:
- Key-value access patterns
- Flexible schema (items vary)
- High scale and low latency requirements
- No complex SQL queries

### DynamoDB Table

Table = Collection of items
Item = Individual record (like a JSON object)
Attribute = Property of an item

```bash
# Create table
aws dynamodb create-table \
  --table-name Users \
  --attribute-definitions \
    AttributeName=user_id,AttributeType=S \
  --key-schema \
    AttributeName=user_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Put item
aws dynamodb put-item --table-name Users \
  --item '{"user_id": {"S": "user123"}, "name": {"S": "Alice"}, "email": {"S": "alice@example.com"}}'

# Get item
aws dynamodb get-item --table-name Users \
  --key '{"user_id": {"S": "user123"}}'

# Query items (by partition key)
aws dynamodb query --table-name Users \
  --key-condition-expression "user_id = :uid" \
  --expression-attribute-values '{":uid": {"S": "user123"}}'
```

### Billing Modes

**On-Demand**: Pay per request. Scales automatically.
- Suitable for: Unpredictable workloads
- Cost: $1.25 per million write requests

**Provisioned**: Reserve capacity, auto-scale within limits.
- Suitable: Predictable workloads
- Cost: $0.00013 per write capacity unit per hour
- Cheaper if capacity is stable

## 4.5 ElastiCache

ElastiCache is an in-memory cache (Redis or Memcached). Reduces database load by caching frequently accessed data.

### Redis vs. Memcached

| Feature | Redis | Memcached |
|---------|-------|-----------|
| Data types | Strings, lists, sets, sorted sets, hashes | Strings only |
| Replication | Yes (master-replica) | No (cluster only) |
| Persistence | Yes (RDB snapshots) | No |
| Pub/Sub | Yes | No |
| Sorted sets | Yes | No |

Choose Redis for persistence, replication, complex types. Choose Memcached for simple string caching and distributed cache.

### ElastiCache Setup

```bash
# Create Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id my-cache \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1
```

Use case: Cache product catalog
```python
import redis
import json

cache = redis.Redis(host='my-cache.xxxxx.ng.0001.use1.cache.amazonaws.com', port=6379)

# Try cache first
cached = cache.get('product:123')
if cached:
    product = json.loads(cached)
else:
    # Not in cache, query database
    product = db.query("SELECT * FROM products WHERE id = 123")
    # Cache for 1 hour
    cache.setex('product:123', 3600, json.dumps(product))
```

## 4.6 Backup and Disaster Recovery

### RPO and RTO

- **RPO (Recovery Point Objective)**: Maximum acceptable data loss. How fresh does data need to be?
- **RTO (Recovery Time Objective)**: Maximum acceptable downtime. How quickly must you recover?

Example requirements:
- Financial system: RPO = 1 minute, RTO = 5 minutes
- Blog: RPO = 1 day, RTO = 24 hours

Strategy:
- RPO < 1 minute: Multi-AZ sync replication + backups
- RPO = 1-5 minutes: Multi-AZ async replication
- RPO = 1 hour: Daily snapshots
- RTO < 5 minutes: Multi-region failover (expensive)
- RTO = 30 minutes: Read replicas + monitoring
- RTO = 1+ hour: Manual restore from snapshots

### Backup Strategy

```
Daily automated backups (RDS)
    ↓
Weekly manual snapshots (for long-term retention)
    ↓
Cross-region replica (for disaster recovery)
    ↓
Point-in-time recovery enabled
```

## 4.7 Common Mistakes

**Mistake 1: Storing files in database**
Databases are optimized for structured data. Large files (images, videos) belong in S3. You'll save money and improve performance.

**Mistake 2: Not enabling Multi-AZ for production databases**
Single-AZ RDS has no automatic failover. On failure, you're down. Always use Multi-AZ in production.

**Mistake 3: Insufficient backup retention**
You can't restore data from backups older than the retention period. Set retention based on compliance requirements (usually 30 days minimum).

**Mistake 4: Ignoring database scaling**
Your database will grow. Plan for it. Use read replicas to scale reads. Use vertical scaling (larger instance) for writes.

**Mistake 5: Provisioning excess DynamoDB capacity**
DynamoDB on-demand is more forgiving. If you provision 1000 write capacity units but only need 100, you've wasted money. Use on-demand for unpredictable workloads.

## Assessment

### Practice Questions

**Q1: You need to archive logs older than 90 days to save money. Which storage class?**
A) Standard (no savings)
B) Standard-IA (immediate retrieval)
C) Glacier (hours to retrieve)
D) Deep Archive (12+ hour retrieval)

**Q2: Your RDS primary fails in us-east-1a. How quickly does Multi-AZ failover occur?**
A) Immediate (< 1 second)
B) 30-120 seconds
C) 5-10 minutes
D) No automatic failover

**Q3: You need a database with flexible schema and high scale. Choose:**
A) PostgreSQL (RDS)
B) DynamoDB
C) Aurora
D) ElastiCache

**Q4: What happens when you delete an S3 object with versioning enabled?**
A) Object is permanently deleted
B) Delete marker is created; versions remain
C) Object is moved to Glacier
D) Permission error (versioning prevents deletion)

**Q5: Your application does 10,000 DynamoDB reads/sec, 100 writes/sec. Billing mode?**
A) Provisioned (writes are bottleneck)
B) On-demand (unpredictable ratio)
C) Provisioned for writes, on-demand for reads (not possible)
D) Either; cost is similar

### Hands-On Labs

**Lab 1: S3 Lifecycle and Versioning**

Create bucket, enable versioning, create lifecycle policy, verify transitions.

**Lab 2: RDS Database Setup**

Create RDS instance, configure Multi-AZ, create manual snapshot, restore from snapshot.

### Production Incident Scenario

**Scenario: Data Loss Due to Accidental Deletion**

Developer accidentally runs `DROP TABLE users;` on production RDS. 50 million user records deleted. No backup.

Challenges:
- No point-in-time recovery option
- Backup retention set to 1 day (accidentally disabled)
- Replica would also have been deleted

Recovery options:
1. Restore from backup (if < 1 day old) - Limited data loss
2. Restore from snapshot (if exists) - Days of old data
3. Rebuild from application logs - Slow, incomplete
4. Data loss - Worst case

Prevention:
- Enable automated backups (minimum 7 days)
- Use read replicas in different AZs
- Implement application-level safeguards (soft deletes, audit tables)
- IAM policy: Require MFA to run DROP operations
- Regular backup testing (restore and verify)

---

Next Module: [Module 5: Networking & Content Delivery](05-networking-content-delivery.md)
