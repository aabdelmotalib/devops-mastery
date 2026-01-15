# Module 7: Database Performance

## Introduction

**Database performance is the difference between a smooth user experience and a system that times out.**

In this module, you'll learn the techniques that separate fast systems from slow ones:

**What you'll master**:
- **Indexing strategy**: When to add indexes and column order effects
- **Query analysis**: Using EXPLAIN to find bottlenecks
- **Connection pooling**: Reusing connections instead of creating new ones
- **N+1 problem**: Detecting and eliminating the classic performance killer
- **Caching with Redis**: Caching query results for 100-1000x speedup
- **Monitoring**: Finding slow queries in production

**The philosophy**: Measure first, optimize second. Don't optimize for problems you don't have.

---

## Indexing Strategy

### Understanding Indexes

An **index** is a separate data structure (usually B-tree) that lets PostgreSQL find data without scanning every row.

**Visual comparison**:

```
Index: Like a book index
┌─────────────────────┐
│ B-tree (sorted)     │
├─────────────────────┤
│ alice → row 5       │  ← Find 'alice' in O(log n) = 20 steps
│ bob → row 12        │
│ charlie → row 3     │
│ diana → row 8       │
│ ...                 │
└─────────────────────┘

No index: Like reading word-by-word
┌──────────────────────────┐
│ Users table (unsorted)   │
├──────────────────────────┤
│ Row 1: zoe              │
│ Row 2: alice ← FOUND!   │  ← Find 'alice' in O(n) = 1M steps
│ Row 3: charlie          │
│ ...                     │
│ Row 1000000: bob        │
└──────────────────────────┘
```

**What indexes do**:

```sql
-- Without index: Sequential scan (slow)
-- Even with 100 users, FULL TABLE SCAN happens
SELECT * FROM users WHERE email = 'user@example.com';
-- PostgreSQL: "Check every row... nope... nope... found it!"
-- Performance: O(n) - Linear
-- Time: 1M users = 3 seconds

-- With index: Index scan (fast)
CREATE INDEX idx_users_email ON users(email);
SELECT * FROM users WHERE email = 'user@example.com';
-- PostgreSQL: "Check index... found pointer... jump to row"
-- Performance: O(log n) - Logarithmic
-- Time: 1M users = 0.01 seconds (300x faster!)
```

### When to Create Indexes

**Index the following columns immediately**:

1. **Primary keys** - Automatic (SERIAL PRIMARY KEY)
2. **Foreign keys** - Always use in WHERE/JOIN
3. **Columns in WHERE clauses** - Most common
4. **Columns in JOIN conditions** - Speeds up joins
5. **Columns in ORDER BY** - Sorts already-ordered data
6. **Columns in GROUP BY** - Reduces grouping cost

**Example (real backend schema)**:
```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,  -- Indexed automatically
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index email (users search by email)
CREATE INDEX idx_users_email ON users(email);

-- Index created_at (sort by recent users)
CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- Posts table
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,  -- Indexed automatically
    user_id INTEGER NOT NULL REFERENCES users(id),
    published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index foreign key (find posts by user)
CREATE INDEX idx_posts_user_id ON posts(user_id);

-- Index publication status (find published posts)
CREATE INDEX idx_posts_published ON posts(published)
WHERE published = TRUE;  -- Partial index - smaller, faster

-- Composite index for common query
CREATE INDEX idx_posts_published_created ON posts(published, created_at DESC);
-- Helps: WHERE published = TRUE ORDER BY created_at DESC
```

```sql
-- Users table
CREATE INDEX idx_users_email ON users(email);  -- WHERE email = ?
CREATE INDEX idx_users_created_at ON users(created_at);  -- ORDER BY created_at

-- Posts table
CREATE INDEX idx_posts_user_id ON posts(user_id);  -- JOIN, WHERE
CREATE INDEX idx_posts_published_created ON posts(published, created_at);  -- WHERE published = TRUE ORDER BY created_at
```

### Composite Index Column Order

**Rule**: Most selective column first

```sql
-- BAD: created_at first (not selective)
CREATE INDEX idx_posts_created_user ON posts(created_at, user_id);
-- Doesn't help: WHERE user_id = ?

-- GOOD: user_id first (selective)
CREATE INDEX idx_posts_user_created ON posts(user_id, created_at);
-- Helps both:
-- WHERE user_id = ?
-- WHERE user_id = ? AND created_at > ?
-- WHERE user_id = ? ORDER BY created_at
```

### Partial Indexes

```sql
-- Index only published posts
CREATE INDEX idx_posts_published ON posts(created_at)
WHERE published = TRUE;

-- Smaller index, faster queries for published posts
SELECT * FROM posts
WHERE published = TRUE
ORDER BY created_at DESC;
```

### Index Gotchas

**Problem 1**: Function calls prevent index usage
```sql
-- BAD: Index not used
CREATE INDEX idx_users_email ON users(email);
SELECT * FROM users WHERE LOWER(email) = 'user@example.com';

-- GOOD: Functional index
CREATE INDEX idx_users_email_lower ON users(LOWER(email));
SELECT * FROM users WHERE LOWER(email) = 'user@example.com';
```

**Problem 2**: OR conditions prevent index usage
```sql
-- BAD: Index not used efficiently
SELECT * FROM users WHERE email = 'user@example.com' OR username = 'john';

-- GOOD: Use UNION
SELECT * FROM users WHERE email = 'user@example.com'
UNION
SELECT * FROM users WHERE username = 'john';
```

## Query Analysis (EXPLAIN)

### Using EXPLAIN

```sql
-- See query plan
EXPLAIN SELECT * FROM users WHERE email = 'user@example.com';

-- See actual execution stats
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'user@example.com';
```

### Reading EXPLAIN Output

```sql
EXPLAIN ANALYZE
SELECT u.email, COUNT(p.id) as post_count
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
GROUP BY u.id, u.email;

-- Output:
-- HashAggregate  (cost=1000..2000 rows=100 width=32) (actual time=10.5..12.3 rows=100 loops=1)
--   Group Key: u.id
--   ->  Hash Left Join  (cost=100..500 rows=1000 width=16) (actual time=2.1..8.5 rows=1000 loops=1)
--         Hash Cond: (p.user_id = u.id)
--         ->  Seq Scan on posts p  (cost=0..200 rows=1000 width=8) (actual time=0.01..1.5 rows=1000 loops=1)
--         ->  Hash  (cost=50..50 rows=100 width=12) (actual time=0.5..0.5 rows=100 loops=1)
--               ->  Seq Scan on users u  (cost=0..50 rows=100 width=12) (actual time=0.01..0.3 rows=100 loops=1)
-- Planning Time: 0.5 ms
-- Execution Time: 12.8 ms
```

**Key metrics**:
- **Seq Scan**: Full table scan (slow for large tables)
- **Index Scan**: Using index (fast)
- **cost**: Estimated cost (lower is better)
- **actual time**: Real execution time
- **rows**: Number of rows processed

### Identifying Slow Queries

```sql
-- Enable query logging (postgresql.conf)
log_min_duration_statement = 1000  -- Log queries > 1 second

-- Or use pg_stat_statements extension
CREATE EXTENSION pg_stat_statements;

-- Find slowest queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### Optimizing Queries

**Example: Slow query**
```sql
-- Slow: No index on user_id
EXPLAIN ANALYZE
SELECT * FROM posts WHERE user_id = 123;

-- Output: Seq Scan on posts (actual time=50.2..100.5 rows=10)
```

**Fix: Add index**
```sql
CREATE INDEX idx_posts_user_id ON posts(user_id);

EXPLAIN ANALYZE
SELECT * FROM posts WHERE user_id = 123;

-- Output: Index Scan using idx_posts_user_id (actual time=0.1..0.5 rows=10)
```

## Connection Pooling

### Why Connection Pooling Matters

```python
# BAD: New connection per request
@app.route('/users/<int:user_id>')
def get_user(user_id):
    conn = psycopg2.connect("dbname=mydb")  # Slow! (100-200ms)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return jsonify(user)

# GOOD: Connection pool
from sqlalchemy import create_engine

engine = create_engine(
    'postgresql://...',
    pool_size=10,        # Keep 10 connections open
    max_overflow=20,     # Allow 20 additional connections
    pool_recycle=3600,   # Recycle connections after 1 hour
    pool_pre_ping=True   # Test connections before using
)
```

### SQLAlchemy Connection Pool

```python
# backend/app/config.py
class Config:
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,          # Normal pool size
        'max_overflow': 20,       # Extra connections under load
        'pool_timeout': 30,       # Wait 30s for connection
        'pool_recycle': 3600,     # Recycle after 1 hour
        'pool_pre_ping': True     # Verify connections
    }
```

### Monitoring Connection Pool

```python
# Check pool status
from app.db.postgres import db

pool = db.engine.pool
print(f"Pool size: {pool.size()}")
print(f"Checked out: {pool.checkedout()}")
print(f"Overflow: {pool.overflow()}")
print(f"Checked in: {pool.checkedin()}")
```

## N+1 Problem

### The Problem

```python
# BAD: N+1 queries
@app.route('/users')
def get_users():
    users = User.query.all()  # 1 query
    return jsonify([{
        'id': u.id,
        'email': u.email,
        'posts': [p.to_dict() for p in u.posts]  # N queries
    } for u in users])

# With 100 users: 101 queries!
```

### Solution 1: Eager Loading

```python
# GOOD: Eager loading with joinedload
from sqlalchemy.orm import joinedload

@app.route('/users')
def get_users():
    users = User.query.options(joinedload(User.posts)).all()  # 1 query
    return jsonify([{
        'id': u.id,
        'email': u.email,
        'posts': [p.to_dict() for p in u.posts]
    } for u in users])
```

### Solution 2: Subquery Loading

```python
# GOOD: Subquery loading
from sqlalchemy.orm import subqueryload

users = User.query.options(subqueryload(User.posts)).all()  # 2 queries
# Query 1: SELECT * FROM users
# Query 2: SELECT * FROM posts WHERE user_id IN (1, 2, 3, ...)
```

### Solution 3: Select In Loading

```python
# GOOD: Select in loading (best for large datasets)
from sqlalchemy.orm import selectinload

users = User.query.options(selectinload(User.posts)).all()  # 2 queries
```

### Detecting N+1 in Development

```python
# Enable SQL logging
app.config['SQLALCHEMY_ECHO'] = True

# Or use flask-debugtoolbar
from flask_debugtoolbar import DebugToolbarExtension

app.config['DEBUG_TB_ENABLED'] = True
toolbar = DebugToolbarExtension(app)
```

## Caching with Redis

### Query Result Caching

```python
# backend/app/services/user_service.py
from app.db.redis import redis_client
from app.models import User
import json

class UserService:
    CACHE_TTL = 300  # 5 minutes
    
    def get_user(self, user_id):
        # Try cache
        cache_key = f'user:{user_id}'
        cached = redis_client.get(cache_key)
        
        if cached:
            return json.loads(cached)
        
        # Cache miss
        user = User.query.get(user_id)
        if not user:
            return None
        
        user_data = user.to_dict()
        
        # Cache result
        redis_client.set(cache_key, json.dumps(user_data), ex=self.CACHE_TTL)
        
        return user_data
    
    def update_user(self, user_id, **kwargs):
        user = User.query.get(user_id)
        for key, value in kwargs.items():
            setattr(user, key, value)
        db.session.commit()
        
        # Invalidate cache
        redis_client.delete(f'user:{user_id}')
        
        return user.to_dict()
```

### Cache-Aside Pattern

```python
def get_popular_posts(limit=10):
    cache_key = f'popular_posts:{limit}'
    
    # Try cache
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Query database
    posts = Post.query.filter_by(published=True)\
        .order_by(Post.view_count.desc())\
        .limit(limit).all()
    
    posts_data = [p.to_dict() for p in posts]
    
    # Cache for 10 minutes
    redis_client.set(cache_key, json.dumps(posts_data), ex=600)
    
    return posts_data
```

### Cache Invalidation Strategies

**Strategy 1: TTL (Time To Live)**
```python
# Cache expires after fixed time
redis_client.set(key, value, ex=300)  # 5 minutes
```

**Strategy 2: Explicit Invalidation**
```python
def update_post(post_id, **kwargs):
    post = Post.query.get(post_id)
    # Update post
    db.session.commit()
    
    # Invalidate caches
    redis_client.delete(f'post:{post_id}')
    redis_client.delete('popular_posts:10')
```

**Strategy 3: Cache Tags**
```python
def cache_with_tags(key, value, tags, ttl=300):
    # Store value
    redis_client.set(key, value, ex=ttl)
    
    # Store tags
    for tag in tags:
        redis_client.sadd(f'tag:{tag}', key)

def invalidate_tag(tag):
    # Get all keys with this tag
    keys = redis_client.smembers(f'tag:{tag}')
    
    # Delete all keys
    if keys:
        redis_client.delete(*keys)
    
    # Delete tag set
    redis_client.delete(f'tag:{tag}')

# Usage
cache_with_tags('post:1', post_data, tags=['posts', 'user:123'])
invalidate_tag('user:123')  # Invalidate all caches for user 123
```

## Performance Monitoring

### Application-Level Monitoring

```python
# backend/app/middleware/performance.py
import time
from flask import request, g
import logging

logger = logging.getLogger(__name__)

@app.before_request
def before_request():
    g.start_time = time.time()

@app.after_request
def after_request(response):
    if hasattr(g, 'start_time'):
        elapsed = time.time() - g.start_time
        
        # Log slow requests
        if elapsed > 1.0:
            logger.warning(
                f"Slow request: {request.method} {request.path} "
                f"took {elapsed:.2f}s"
            )
    
    return response
```

### Database Query Monitoring

```python
# Log all queries in development
import logging

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### Production Monitoring

```python
# Use APM tools like:
# - New Relic
# - Datadog
# - Sentry

# Example: Sentry integration
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[
        FlaskIntegration(),
        SqlalchemyIntegration()
    ],
    traces_sample_rate=0.1  # Sample 10% of transactions
)
```

---

## Module 7 Exam

### Multiple Choice Questions

1. What is the purpose of a database index?
   a) Store data more efficiently
   b) Speed up data retrieval
   c) Enforce data integrity
   d) Backup data

2. What does EXPLAIN ANALYZE show?
   a) Database schema
   b) Query execution plan and actual performance
   c) Index definitions
   d) Connection pool status

3. What is the N+1 query problem?
   a) A database error
   b) Loading related data in N+1 separate queries instead of one
   c) Having N+1 indexes
   d) N+1 connections in the pool

4. What is the purpose of connection pooling?
   a) Backup connections
   b) Reuse database connections instead of creating new ones
   c) Load balance queries
   d) Cache query results

5. When should you invalidate a cache?
   a) Never - let TTL handle it
   b) When the underlying data changes
   c) Every hour
   d) Only when cache is full

### Practical Design Tasks

**Task 1**: Optimize this slow query:

```sql
SELECT u.email, COUNT(p.id) as post_count
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
WHERE u.created_at > '2024-01-01'
GROUP BY u.id, u.email
ORDER BY post_count DESC
LIMIT 10;
```

The query takes 10 seconds on a table with 1M users and 5M posts. What indexes would you create and why?

**Task 2**: Implement a caching layer for a blog API that:
- Caches individual posts by ID (5 minute TTL)
- Caches list of recent posts (1 minute TTL)
- Invalidates caches when posts are updated
- Handles cache misses gracefully

Provide Python code using Redis.

### Incident Scenario

**Scenario**: Your production API is experiencing timeouts. Investigation reveals:
- Database CPU at 90%
- Slow query log shows the same query repeated thousands of times
- The query has no indexes and does a full table scan
- Connection pool is exhausted (all connections in use)

**Questions**:
1. What are the root causes?
2. What immediate actions would you take?
3. What long-term fixes would you implement?
4. How would you prevent this in the future?
