# Module 1: Database Fundamentals

## Introduction

In this module, you'll discover what databases really are and why they're essential for modern backend systems. Rather than viewing databases as simple storage mechanisms, you'll learn how they solve critical problems that file systems cannot address—including concurrent access, data integrity, efficient querying, durability, and structured data access patterns.

By the end of this module, you'll understand:
- **The fundamental problems databases solve** that files cannot
- **The difference between OLTP and OLAP** workloads and when to use each
- **When to choose relational vs non-relational databases** for different scenarios
- **Common mistakes backend engineers make** with database design and usage
- **How to make database selection decisions** for production systems based on real requirements

This foundation is critical because **database decisions are expensive to change later**. Getting these choices right from the start saves months of refactoring and prevents performance problems in production. You're building the backbone of your application—make it strong.

---

## What a Database Really Solves

A database is not just "persistent storage." It solves:

1. **Concurrent access** - Multiple users/processes reading and writing simultaneously
2. **Data integrity** - Ensuring data remains consistent and valid
3. **Query efficiency** - Finding data quickly without scanning everything
4. **Durability** - Not losing data when systems crash
5. **Structured access** - Querying data in flexible ways

### What Files Don't Give You

Let's understand why using files is a critical mistake for backend systems:

```python
# BAD: Using files for backend data
import json
import os

def get_user(user_id):
    with open('users.json', 'r') as f:
        users = json.load(f)  # Loads ENTIRE file into memory
        return users.get(user_id)

def add_user(user_data):
    with open('users.json', 'r') as f:
        users = json.load(f)
    users.append(user_data)
    with open('users.json', 'w') as f:
        json.dump(users, f)  # Complete rewrite

# Problems:
# 1. No concurrent writes (file locks prevent parallel writes)
# 2. No indexing (O(n) linear search through entire file)
# 3. No transactions (partial writes crash loses data)
# 4. No relationships (manual joins and data duplication)
# 5. No data validation (anything goes)
# 6. Memory inefficient (loads 1GB file for single record)
```

**Real-world impact**:
- With 100,000 users, loading one user takes 1GB → 2 seconds
- Two concurrent writes will corrupt the file
- Server crash during write = lost data forever
- No way to enforce user email uniqueness
- Reporting requires loading entire file and manually aggregating

This is why databases exist—they solve all of these problems elegantly.

## OLTP vs OLAP

Understanding the difference between these two workload types is critical because they require completely different optimizations and database choices.

### OLTP (Online Transaction Processing)

**What it is**: Day-to-day operations of your application. Every user action, every business operation.

**Characteristics**:
- **Many small, fast queries** - Typically return a single record or small set
- **INSERT, UPDATE, DELETE heavy** - Database constantly changing
- **Row-oriented** - You access complete rows, not aggregates
- **Normalized data** - Eliminate redundancy, maintain integrity
- **ACID requirements** - Transactions must be reliable
- **Concurrency critical** - Multiple users accessing simultaneously

**Real backend use cases**:
```python
# User registration - OLTP
def register_user(email, password):
    user = User(email=email, password_hash=hash(password))
    db.session.add(user)
    db.session.commit()  # OLTP transaction: atomic, consistent, isolated

# API endpoint handling - OLTP
@app.route('/api/orders', methods=['POST'])
def create_order(user_id, items):
    # Start transaction
    with db.session.begin():
        # Validate user
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Create order
        order = Order(user_id=user_id, total=calculate_total(items))
        db.session.add(order)
        db.session.flush()  # Get order ID before inserting items
        
        # Add order items
        for item in items:
            order_item = OrderItem(order_id=order.id, **item)
            db.session.add(order_item)
        
        db.session.commit()  # All or nothing
    
    return {"order_id": order.id, "status": "created"}

# Real-time notifications - OLTP
def send_friend_request(from_user_id, to_user_id):
    with db.session.begin():
        request = FriendRequest(from_user_id=from_user_id, to_user_id=to_user_id)
        db.session.add(request)
        # Notification sent immediately to to_user
```

**Database choice**: PostgreSQL, MySQL
**Why**: These databases excel at handling many concurrent transactions safely, maintaining data integrity, and supporting complex relationships.

### OLAP (Online Analytical Processing)

**What it is**: Analytics, reporting, business intelligence. Understanding patterns in data.

**Characteristics**:
- **Few large, complex queries** - Might scan millions of rows
- **SELECT heavy with aggregations** - Lots of GROUP BY, SUM, COUNT, AVG
- **Column-oriented** - Access specific columns, not full rows
- **Denormalized data** - Duplicate data for speed, less normalization
- **Batch processing** - Queries run on schedule, not on-demand
- **Historical analysis** - Comparing data over time periods

**Real backend use cases**:
```python
# Monthly revenue report - OLAP
def get_monthly_revenue(year):
    """Scan all orders for the year, group by month, sum totals"""
    return db.session.query(
        func.date_trunc('month', Order.created_at).label('month'),
        func.sum(Order.total).label('revenue'),
        func.count(Order.id).label('order_count')
    ).filter(
        func.extract('year', Order.created_at) == year
    ).group_by(
        func.date_trunc('month', Order.created_at)
    ).order_by('month').all()
    # Scans 1M orders, groups by 12 months: takes 30 seconds

# User analytics - OLAP
def get_user_cohort_analysis():
    """Analyze user behavior by signup month"""
    return db.session.query(
        func.date_trunc('month', User.created_at).label('cohort'),
        func.count(User.id).label('signup_count'),
        func.avg(func.cast(User.total_orders, Numeric)).label('avg_orders')
    ).group_by(
        func.date_trunc('month', User.created_at)
    ).all()

# Dashboard query - OLAP
def get_dashboard_metrics():
    """Multiple aggregations for dashboard"""
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    avg_order_value = db.session.query(func.avg(Order.total)).scalar()
    return {
        "total_users": total_users,
        "active_users": active_users,
        "avg_order_value": avg_order_value
    }
```

**Database choice**: Redshift, BigQuery, ClickHouse, DuckDB
**Why**: These databases are optimized for scanning large datasets efficiently, performing complex aggregations, and returning results quickly.

**Production warning**: **Never run OLAP queries on your OLTP database!**

```python
# BAD: OLAP query on production OLTP database
def get_all_user_stats():
    # This query scans 1M users and their 50M orders
    # Locks tables, blocks real transactions
    users = User.query.all()
    for user in users:
        user.order_count = len(user.orders)
        user.total_spent = sum(o.total for o in user.orders)
    db.session.commit()
    # Meanwhile, real users can't register or place orders!

# GOOD: Use read replica or separate analytics database
# 1. Set up read replica of production database
analytics_engine = create_engine('postgresql://replica-host/dbname')

# 2. Run slow queries on replica
def get_all_user_stats_analytics():
    AnalyticsDB = sessionmaker(bind=analytics_engine)
    analytics_session = AnalyticsDB()
    
    result = analytics_session.query(User, func.count(Order.id).label('order_count')).outerjoin(Order).group_by(User.id).all()
    
    # Production database not affected
```

## Relational vs Non-Relational

Choosing between relational and non-relational databases is one of the most important architectural decisions. Each has fundamentally different trade-offs and best uses.

### Relational (SQL)

**Structure**: Tables with fixed schemas (defined columns and types)

**How it works**:
- Data organized in tables (rows and columns)
- Relationships defined via foreign keys
- Schema must be defined before inserting data
- Rows are normalized (no duplication)
- Supports complex queries with JOINs

**When to use**:
- **Data has clear relationships** - Users, orders, products, comments
- **Need ACID guarantees** - Transactions must be reliable
- **Complex queries with joins** - Need data from multiple tables
- **Financial data** - Payments, invoices, accounting (need transactions)
- **User accounts and auth** - Must enforce constraints
- **Most business applications** - ERP, CRM, accounting systems

**Real use cases**:
```sql
-- E-commerce platform
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Products table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock INTEGER DEFAULT 0
);

-- Orders table (depends on users)
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    order_date TIMESTAMP DEFAULT NOW(),
    total DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending'
);

-- Order items (depends on orders and products)
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price_at_purchase DECIMAL(10, 2) NOT NULL
);

-- Complex query: Orders with items and user info
SELECT 
    u.email,
    o.id as order_id,
    o.total,
    p.name as product_name,
    oi.quantity,
    oi.price_at_purchase
FROM users u
JOIN orders o ON u.id = o.user_id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
WHERE u.id = 123
ORDER BY o.order_date DESC;

-- Transaction: Place order safely
BEGIN;
    INSERT INTO orders (user_id, total) VALUES (123, 299.99);
    INSERT INTO order_items VALUES (currval('orders_id_seq'), 1, 2);  -- Add item
    UPDATE products SET stock = stock - 2 WHERE id = 1;  -- Update inventory
    UPDATE users SET last_order = NOW() WHERE id = 123;  -- Update user
COMMIT;
-- All succeed or all fail - never partial orders
```

**Databases**: PostgreSQL, MySQL, MariaDB, SQL Server
**Why PostgreSQL**: Most advanced open-source relational database, excellent for complex queries and transactions

### Non-Relational (NoSQL)

**Types and characteristics**:

1. **Document Stores** (MongoDB, CouchDB)
   - Store JSON-like documents
   - Flexible schemas
   - Nested data structures
   - Good for: Product catalogs, CMS, flexible content

2. **Key-Value Stores** (Redis, Memcached)
   - Simple key → value mapping
   - In-memory (very fast)
   - No queries, just lookups
   - Good for: Caching, sessions, real-time data

3. **Column-Family Stores** (Cassandra, HBase)
   - Wide column tables
   - Highly scalable
   - Good for: Time-series data, logs, IoT

4. **Graph Databases** (Neo4j)
   - Nodes and relationships
   - Query-optimized for relationships
   - Good for: Social networks, recommendations, knowledge graphs

**When to use NoSQL**:
- **Flexible schema needed** - Structure varies between documents
- **Horizontal scaling required** - Need to shard across servers
- **High write throughput** - Logging, analytics, IoT
- **Non-relational data** - Nested documents, loose relationships
- **Rapid prototyping** - Schema can change during development

**Real use cases**:
```javascript
// Product catalog in MongoDB (flexible schema)
// Products have different attributes based on type

// Electronics product
{
  "_id": ObjectId("..."),
  "sku": "LAPTOP-001",
  "name": "MacBook Pro 16",
  "category": "Electronics",
  "price": 2499.99,
  "attributes": {
    "processor": "M3 Max",
    "ram": "36GB",
    "storage": "512GB SSD",
    "display": "16-inch Retina XDR"
  },
  "specifications": {
    "weight": "2.1kg",
    "battery_life": "18 hours"
  },
  "images": [
    {"url": "img1.jpg", "alt": "Front view"},
    {"url": "img2.jpg", "alt": "Side view"}
  ],
  "reviews": [
    {
      "user_id": ObjectId("..."),
      "rating": 5,
      "text": "Amazing machine!",
      "date": ISODate("2024-01-15")
    }
  ],
  "created_at": ISODate("2024-01-01"),
  "updated_at": ISODate("2024-01-15")
}

// Clothing product - different attributes!
{
  "_id": ObjectId("..."),
  "sku": "SHIRT-001",
  "name": "Cotton T-Shirt",
  "category": "Clothing",
  "price": 29.99,
  "attributes": {
    "color": "blue",
    "size": "M",
    "material": "100% cotton",
    "fit": "relaxed"
  },
  "specifications": {
    "care": "Machine wash cold",
    "weight": "150g"
  },
  "inventory": {
    "S": 50,
    "M": 30,
    "L": 25,
    "XL": 15
  },
  "created_at": ISODate("2024-01-01"),
  "updated_at": ISODate("2024-01-15")
}

// Both stored in same collection - NO schema required!
```

```python
# Redis for real-time features
import redis

redis_client = redis.Redis(host='localhost', port=6379)

# Session storage
def create_session(user_id):
    session_id = 'session:' + token
    redis_client.hset(session_id, mapping={
        'user_id': user_id,
        'created_at': datetime.now(),
        'ip': request.remote_addr
    })
    redis_client.expire(session_id, 86400)  # Expire in 24 hours
    return session_id

# Leaderboard (sorted set)
def update_score(user_id, score):
    redis_client.zadd('leaderboard', {f'user:{user_id}': score})
    
def get_leaderboard(limit=10):
    return redis_client.zrange('leaderboard', 0, limit-1, withscores=True, desc=True)

# Rate limiting (counter)
def check_rate_limit(user_id, limit=100, window=60):
    key = f'rate:{user_id}'
    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, window)
    return current <= limit
```

## Common Backend Mistakes

These mistakes are made constantly in production systems. Understanding why they're wrong will save you from painful debugging sessions.

### Mistake 1: Using NoSQL for Everything

**The myth**: "NoSQL is faster and more scalable"

**Reality**: NoSQL solves specific problems. Using it for everything creates disasters.

```python
# BAD: Using MongoDB for user authentication
# This is a real production bug that happens frequently
def authenticate_user(email, password):
    user = db.users.find_one({"email": email})
    if user and check_password(password, user['password_hash']):
        # Seems fine right? Let's see what goes wrong:
        
        # Problem 1: Race condition on concurrent logins
        # Two requests authenticate simultaneously, both update last_login
        # MongoDB has no transaction guarantees
        user['last_login'] = datetime.now()
        db.users.replace_one({"_id": user['_id']}, user)
        
        # Problem 2: Two users register with same email
        # No unique constraints enforced across documents
        # Your authentication system breaks
        
        # Problem 3: Forgot password - update user and send email
        # Email sending fails, but user already updated
        # No way to rollback both operations atomically
        
        return {"token": generate_token(user['_id'])}

# Result: Users can't authenticate, duplicate accounts, security holes
```

**Fix**: Use PostgreSQL for user accounts
```python
# GOOD: Using PostgreSQL for authentication
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    last_login = db.Column(db.DateTime)

def authenticate_user(email, password):
    user = User.query.filter_by(email=email).first()
    if user and check_password(password, user.password_hash):
        try:
            user.last_login = datetime.utcnow()
            db.session.commit()  # Atomic - all or nothing
            return {"token": generate_token(user.id)}
        except IntegrityError:
            # Duplicate email? Constraint violation caught
            db.session.rollback()
            raise

# PostgreSQL guarantees:
# - Unique constraint prevents duplicate emails
# - Transaction ensures last_login updated reliably
# - Rollback on error keeps database consistent
```

### Mistake 2: Not Using Indexes

**The myth**: "Indexes are optional"

**Reality**: Queries without indexes are catastrophically slow as data grows.

```python
# BAD: Query without index
# With 100 users: takes 10ms (scans all rows)
# With 1M users: takes 3 seconds (still scans all rows)
# With 100M users: takes 5 minutes (completely broken)

sql = "SELECT * FROM users WHERE email = %s"
cursor.execute(sql, ('user@example.com',))  # Linear search O(n)

# The problem: Every request does a full table scan
# 100 concurrent users = 100 full table scans simultaneously
# Database locks up, requests timeout, users leave
```

**Fix**: Add indexes
```sql
-- One-time setup
CREATE INDEX idx_users_email ON users(email);

-- Now the same query is instant
SELECT * FROM users WHERE email = 'user@example.com';
-- Uses B-tree index: O(log n) - finds 1M user in 20 microseconds
```

**When to index**:
- Always: Foreign keys, columns in WHERE clauses, JOIN conditions, ORDER BY
- Frequently: email, username, phone, created_at
- Never: Boolean flags with only 2 values (too few unique values)

### Mistake 3: N+1 Query Problem

**The myth**: "Just loop and fetch, it's fine"

**Reality**: N+1 causes 1000x slowdown as data grows.

```python
# BAD: N+1 queries
users = User.query.all()  # 1 query: SELECT * FROM users (1000 rows)
user_data = []
for user in users:
    posts = user.posts.all()  # N queries: 1000 separate SELECT queries
    user_data.append({
        'email': user.email,
        'post_count': len(posts),
        'posts': posts
    })

# Timeline:
# Query 1: Load 1000 users (5ms)
# Queries 2-1001: Load posts for each user (1000 * 20ms = 20,000ms)
# Total: 20 seconds to load what should be 100ms!
# Server has 20 concurrent requests = system melts down
```

**Fix: Eager load**
```python
# GOOD: Eager loading - 1 query instead of 1001
from sqlalchemy.orm import joinedload

users = User.query.options(joinedload(User.posts)).all()  # 1 clever query
for user in users:
    # Posts already loaded, no new queries
    posts = user.posts  # In-memory access
    print(len(posts))

# Result: 100ms total instead of 20 seconds (200x faster!)
```

### Mistake 4: Storing Everything in Redis

**The myth**: "Redis is faster than PostgreSQL"

**Reality**: Redis is in-memory and limited. PostgreSQL is your actual database.

```python
# BAD: Using Redis as primary database
def create_user(email, password):
    user_id = str(uuid.uuid4())
    redis.hset(f'user:{user_id}', mapping={
        'email': email,
        'password_hash': hash_password(password),
        'created_at': datetime.now().isoformat()
    })
    return user_id

# Problems:
# 1. Memory cost: 16GB Redis for 100M users (costs $$$)
# 2. Data loss risk: Server restarts lose all data
# 3. No queries: Can't find user by email (full scan required)
# 4. No relationships: Can't enforce data integrity
# 5. Can't scale: Redis doesn't shard well

# Result: System loses user data on restart
```

**Fix: Use Redis for caching, PostgreSQL for primary storage**
```python
# GOOD: Proper database architecture
class User(db.Model):  # PostgreSQL
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255))

def get_user(user_id):
    # Try cache first
    cache_key = f'user:{user_id}'
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Cache miss: load from PostgreSQL
    user = User.query.get(user_id)
    if user:
        # Cache for future requests
        redis.setex(cache_key, 3600, json.dumps(user.to_dict()))
    
    return user.to_dict() if user else None

# Benefits:
# - Persistent data in PostgreSQL
# - Fast access via Redis cache
# - If Redis goes down, PostgreSQL still works
# - Data survives restarts
```

### Mistake 5: Not Using Connection Pooling

**The myth**: "Creating new connections is cheap"

**Reality**: Connection setup takes 100-200ms. It's your bottleneck.

```python
# BAD: New connection per request
def get_user(user_id):
    # This happens for EVERY request
    conn = psycopg2.connect(
        "host=localhost dbname=mydb user=postgres password=secret"
    )  # 150ms overhead
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()  # 20ms query
    conn.close()
    return user

# Performance:
# 100 concurrent requests:
# - 100 new connections: 100 * 150ms = 15,000ms
# - 100 queries: 100 * 20ms = 2,000ms
# Total: 17 seconds (users think system is broken)

# With 1000 concurrent requests: system exceeds max connections, crashes
```

**Fix: Connection pooling**
```python
# GOOD: Connection pool
from sqlalchemy import create_engine

engine = create_engine(
    'postgresql://user:password@localhost/dbname',
    pool_size=10,        # Keep 10 connections ready
    max_overflow=20,     # Allow 20 extra under load
    pool_pre_ping=True   # Test connections before use
)

# First request: create 10 connections (1.5s one-time cost)
# All subsequent requests: reuse existing connections (20ms)

# 100 concurrent requests:
# - Reuse from pool: 0ms overhead
# - 100 queries: 100 * 20ms = 2,000ms
# Total: 2 seconds (100x faster!)

# Connection exhaustion handled gracefully
# 1000 concurrent requests:
# - Pool queue up requests
# - As connections free up, requests proceed
# - System stays responsive
```

# BAD: Query without index
# SELECT * FROM users WHERE email = 'user@example.com';
# Scans entire table (slow)

# GOOD: Add index
# CREATE INDEX idx_users_email ON users(email);
# Uses B-tree index (fast)
```

### Mistake 3: N+1 Query Problem

```python
# BAD: N+1 queries
users = User.query.all()  # 1 query
for user in users:
    orders = user.orders.all()  # N queries (one per user)

# GOOD: Eager loading
users = User.query.options(joinedload(User.orders)).all()  # 1 query
```

### Mistake 4: Storing Everything in Redis

```python
# BAD: Using Redis as primary database
redis.set(f'user:{user_id}', json.dumps(user_data))

# Problems:
# - Redis is in-memory (expensive for large data)
# - No complex queries
# - Data loss risk if not configured properly
```

**Fix**: Use Redis for caching, sessions, rate limiting. Use PostgreSQL for primary data.

### Mistake 5: Not Using Connection Pooling

```python
# BAD: New connection per request
def get_user(user_id):
    conn = psycopg2.connect("dbname=mydb")  # Slow!
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    return cursor.fetchone()

# GOOD: Connection pool
from sqlalchemy import create_engine
engine = create_engine('postgresql://...', pool_size=10)
```

## Database Selection Guide

### Use PostgreSQL when:
- Core application data
- Need transactions
- Complex relationships
- ACID guarantees required
- Examples: users, orders, inventory

### Use MongoDB when:
- Flexible schema needed
- Nested documents
- Rapid prototyping
- Examples: logs, product catalogs, CMS

### Use Redis when:
- Caching
- Session storage
- Rate limiting
- Real-time features
- Examples: API cache, user sessions, leaderboards

### Use Multiple Databases

**Production pattern**:
```python
# backend/app/db/postgres.py
from sqlalchemy import create_engine
pg_engine = create_engine('postgresql://...')

# backend/app/db/mongo.py
from pymongo import MongoClient
mongo_client = MongoClient('mongodb://...')

# backend/app/db/redis.py
import redis
redis_client = redis.Redis(host='localhost', port=6379)
```

## Architecture Trade-offs

### Consistency vs Availability (CAP Theorem)

**PostgreSQL**: Chooses consistency
- Transactions guarantee data correctness
- May block during network partitions

**MongoDB**: Chooses availability
- Eventually consistent
- Continues operating during partitions

**Backend decision**:
- User accounts, payments → PostgreSQL (consistency critical)
- Analytics, logs → MongoDB (availability preferred)

### Normalization vs Performance

**Normalized** (PostgreSQL):
```sql
-- Separate tables, no duplication
SELECT u.email, o.total
FROM users u
JOIN orders o ON u.id = o.user_id;
```

**Denormalized** (MongoDB):
```javascript
// Embedded data, faster reads
{
  "email": "user@example.com",
  "orders": [
    {"total": 100.00, "date": "2024-01-01"}
  ]
}
```

**Trade-off**: Normalization saves space but requires joins. Denormalization is faster but duplicates data.

---

## Module 1 Exam

### Multiple Choice Questions

1. What is the primary advantage of using a database over file storage for a backend application?
   a) Databases are always faster
   b) Databases provide concurrent access with integrity guarantees
   c) Databases use less disk space
   d) Databases are easier to set up

2. Which database type is best suited for an e-commerce order processing system?
   a) Redis (key-value)
   b) MongoDB (document)
   c) PostgreSQL (relational)
   d) Neo4j (graph)

3. What is the N+1 query problem?
   a) Running N queries when 1 would suffice
   b) A database error code
   c) A type of SQL injection
   d) A connection pool issue

4. When should you use Redis as your primary database?
   a) For user authentication
   b) For financial transactions
   c) Never - Redis is for caching and sessions
   d) For all NoSQL use cases

5. What does OLTP stand for and what is it used for?
   a) Online Transaction Processing - day-to-day operations
   b) Online Transaction Protocol - network communication
   c) Optimized Long-Term Processing - analytics
   d) Object-Level Transaction Protection - security

### Practical Design Tasks

**Task 1**: Design a database architecture for a social media application that needs to:
- Store user profiles and authentication
- Handle millions of posts with comments
- Provide real-time notifications
- Cache frequently accessed data

Specify which database(s) to use for each component and justify your choices.

**Task 2**: You're building a REST API for a food delivery service. Design the database layer for:
- Restaurants and menus
- User orders (must be ACID-compliant)
- Real-time order tracking
- User session management

Explain your database choices and data flow.

### Incident Scenario

**Scenario**: Your Flask application is experiencing slow response times. Investigation reveals:
- Database connections are being created on every request
- No indexes on frequently queried columns
- Analytics queries running on the production database during peak hours

**Questions**:
1. What are the three main problems?
2. How would you fix each one?
3. What monitoring would you add to prevent this in the future?
