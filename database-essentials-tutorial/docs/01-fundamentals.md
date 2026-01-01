# Module 1: Database Fundamentals

## What a Database Really Solves

A database is not just "persistent storage." It solves:

1. **Concurrent access** - Multiple users/processes reading and writing simultaneously
2. **Data integrity** - Ensuring data remains consistent and valid
3. **Query efficiency** - Finding data quickly without scanning everything
4. **Durability** - Not losing data when systems crash
5. **Structured access** - Querying data in flexible ways

### What Files Don't Give You

```python
# BAD: Using files for backend data
def get_user(user_id):
    with open('users.json', 'r') as f:
        users = json.load(f)  # Loads ENTIRE file
        return users.get(user_id)

# Problems:
# - No concurrent writes (file locks)
# - No indexing (O(n) search)
# - No transactions (partial writes on crash)
# - No relationships (manual joins)
```

## OLTP vs OLAP

### OLTP (Online Transaction Processing)

**What it is**: Day-to-day operations of your application

**Characteristics**:
- Many small, fast queries
- INSERT, UPDATE, DELETE heavy
- Row-oriented
- Normalized data

**Backend use case**:
```python
# User registration
def register_user(email, password):
    user = User(email=email, password_hash=hash(password))
    db.session.add(user)
    db.session.commit()  # OLTP transaction
```

**Database choice**: PostgreSQL, MySQL

### OLAP (Online Analytical Processing)

**What it is**: Analytics, reporting, business intelligence

**Characteristics**:
- Few large, complex queries
- SELECT heavy with aggregations
- Column-oriented
- Denormalized data

**Backend use case**:
```python
# Analytics query
def get_monthly_revenue():
    return db.session.query(
        func.date_trunc('month', Order.created_at),
        func.sum(Order.total)
    ).group_by(func.date_trunc('month', Order.created_at))
```

**Database choice**: Redshift, BigQuery, ClickHouse

**Production note**: Don't run OLAP queries on your OLTP database. Use read replicas or separate analytics databases.

## Relational vs Non-Relational

### Relational (SQL)

**Structure**: Tables with fixed schemas

**When to use**:
- Data has clear relationships
- Need ACID guarantees
- Complex queries with joins
- Financial data, user accounts, orders

**Example**:
```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Orders table (relationship)
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    total DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Non-Relational (NoSQL)

**Types**:
1. **Document** (MongoDB) - JSON-like documents
2. **Key-Value** (Redis) - Simple key-value pairs
3. **Column-family** (Cassandra) - Wide column stores
4. **Graph** (Neo4j) - Nodes and relationships

**When to use**:
- Flexible schema
- Horizontal scaling
- High write throughput
- Caching, sessions, logs

**Example (MongoDB)**:
```python
# Document store - no fixed schema
user_doc = {
    "email": "user@example.com",
    "profile": {
        "name": "John",
        "preferences": {
            "theme": "dark",
            "notifications": True
        }
    },
    "login_history": [
        {"timestamp": "2024-01-01", "ip": "1.2.3.4"}
    ]
}
db.users.insert_one(user_doc)
```

## Common Backend Mistakes

### Mistake 1: Using NoSQL for Everything

```python
# BAD: Using MongoDB for user authentication
user = db.users.find_one({"email": email})
if user and check_password(password, user['password_hash']):
    # What if two processes update user simultaneously?
    # MongoDB doesn't enforce foreign key constraints
    # No transaction guarantees across collections
    pass
```

**Fix**: Use PostgreSQL for core transactional data.

### Mistake 2: Not Using Indexes

```python
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
