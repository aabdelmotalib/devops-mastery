# Module 3: NoSQL Databases

## MongoDB: Document Database

### What MongoDB Actually Is

MongoDB stores data as JSON-like documents (BSON internally):

```javascript
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "email": "user@example.com",
  "profile": {
    "name": "John Doe",
    "age": 30
  },
  "tags": ["python", "backend"],
  "created_at": ISODate("2024-01-01T00:00:00Z")
}
```

**Key characteristics**:
- No fixed schema (flexible structure)
- Nested documents (no joins needed)
- Horizontal scaling (sharding)
- Eventually consistent (by default)

### Installation (Linux)

```bash
# Ubuntu/Debian
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt update
sudo apt install -y mongodb-org

# Start service
sudo systemctl start mongod
sudo systemctl enable mongod

# Access MongoDB
mongosh
```

### Python Setup

```python
# backend/app/db/mongo.py
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import os

class MongoDB:
    def __init__(self):
        self.client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
        self.db = self.client[os.getenv('MONGO_DB', 'backend_db')]
    
    def get_collection(self, name):
        return self.db[name]

mongo = MongoDB()
```

### Basic Operations

```python
# backend/app/repositories/log_repository.py
from app.db.mongo import mongo

class LogRepository:
    def __init__(self):
        self.collection = mongo.get_collection('logs')
        # Create index
        self.collection.create_index('timestamp')
        self.collection.create_index('level')
    
    def insert_log(self, level, message, metadata=None):
        doc = {
            'level': level,
            'message': message,
            'metadata': metadata or {},
            'timestamp': datetime.utcnow()
        }
        result = self.collection.insert_one(doc)
        return str(result.inserted_id)
    
    def get_logs(self, level=None, limit=100):
        query = {'level': level} if level else {}
        return list(self.collection.find(query).sort('timestamp', -1).limit(limit))
    
    def get_error_logs(self, hours=24):
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return list(self.collection.find({
            'level': 'ERROR',
            'timestamp': {'$gte': cutoff}
        }))
```

### When MongoDB is a BAD Idea

**Don't use MongoDB for**:

1. **Transactional data**
```python
# BAD: User registration in MongoDB
def register_user(email, password):
    users = mongo.get_collection('users')
    # No transaction guarantees
    # No foreign key constraints
    # Race conditions possible
    users.insert_one({
        'email': email,
        'password_hash': hash_password(password)
    })
```

2. **Complex relationships**
```python
# BAD: E-commerce orders in MongoDB
{
  "order_id": 1,
  "user": {  # Duplicated user data
    "email": "user@example.com",
    "name": "John"
  },
  "items": [
    {
      "product": {  # Duplicated product data
        "name": "Widget",
        "price": 10.00
      }
    }
  ]
}
# Problem: Update user email → must update ALL orders
```

3. **Financial data**
```python
# BAD: Payment processing in MongoDB
# No ACID guarantees across documents
# Risk of data inconsistency
```

**Use PostgreSQL instead for these cases.**

### When MongoDB is a GOOD Idea

**Use MongoDB for**:

1. **Logging and analytics**
```python
# GOOD: Application logs
{
  "timestamp": ISODate("2024-01-01T12:00:00Z"),
  "level": "ERROR",
  "message": "Database connection failed",
  "metadata": {
    "user_id": 123,
    "endpoint": "/api/users",
    "stack_trace": "..."
  }
}
```

2. **Product catalogs**
```python
# GOOD: E-commerce products (read-heavy, flexible schema)
{
  "sku": "WIDGET-001",
  "name": "Premium Widget",
  "price": 99.99,
  "attributes": {  # Flexible schema
    "color": "blue",
    "size": "large",
    "material": "steel"
  },
  "images": ["url1", "url2"],
  "reviews": [
    {"user": "john", "rating": 5, "comment": "Great!"}
  ]
}
```

3. **Content management**
```python
# GOOD: CMS articles
{
  "title": "How to Use MongoDB",
  "slug": "how-to-use-mongodb",
  "content": "...",
  "author": {
    "name": "John Doe",
    "email": "john@example.com"
  },
  "tags": ["database", "nosql"],
  "published_at": ISODate("2024-01-01T00:00:00Z")
}
```

### Schema Design in Practice

**Pattern 1: Embedding (denormalization)**
```python
# User with embedded addresses
{
  "_id": ObjectId("..."),
  "email": "user@example.com",
  "addresses": [  # Embedded
    {
      "type": "shipping",
      "street": "123 Main St",
      "city": "NYC"
    },
    {
      "type": "billing",
      "street": "456 Oak Ave",
      "city": "LA"
    }
  ]
}

# Good when:
# - Addresses are always accessed with user
# - Limited number of addresses per user
# - Addresses rarely change
```

**Pattern 2: Referencing (normalization)**
```python
# User document
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "email": "user@example.com"
}

# Order documents (reference user)
{
  "_id": ObjectId("..."),
  "user_id": ObjectId("507f1f77bcf86cd799439011"),
  "total": 100.00,
  "items": [...]
}

# Good when:
# - Data is accessed independently
# - Large or unbounded arrays
# - Data changes frequently
```

**Backend example**:
```python
# backend/app/repositories/product_repository.py
from app.db.mongo import mongo
from bson import ObjectId

class ProductRepository:
    def __init__(self):
        self.collection = mongo.get_collection('products')
        # Indexes
        self.collection.create_index('sku', unique=True)
        self.collection.create_index('category')
        self.collection.create_index([('name', 'text')])  # Text search
    
    def create_product(self, sku, name, price, category, attributes=None):
        doc = {
            'sku': sku,
            'name': name,
            'price': price,
            'category': category,
            'attributes': attributes or {},
            'created_at': datetime.utcnow()
        }
        result = self.collection.insert_one(doc)
        return str(result.inserted_id)
    
    def get_product(self, sku):
        return self.collection.find_one({'sku': sku})
    
    def search_products(self, query, category=None):
        filter_doc = {'$text': {'$search': query}}
        if category:
            filter_doc['category'] = category
        return list(self.collection.find(filter_doc).limit(20))
    
    def update_price(self, sku, new_price):
        self.collection.update_one(
            {'sku': sku},
            {'$set': {'price': new_price, 'updated_at': datetime.utcnow()}}
        )
```

---

## Redis: Key-Value Store

### What Redis Actually Is

Redis is an **in-memory** key-value store:

```python
# Simple key-value
redis.set('user:1:name', 'John Doe')
redis.get('user:1:name')  # 'John Doe'

# Expiration
redis.setex('session:abc123', 3600, 'user_data')  # Expires in 1 hour

# Data structures
redis.lpush('queue:emails', 'email1')  # List
redis.sadd('tags:python', 'user1', 'user2')  # Set
redis.hset('user:1', 'name', 'John', 'email', 'john@example.com')  # Hash
```

**Key characteristics**:
- In-memory (very fast, but expensive)
- Data structures (lists, sets, hashes, sorted sets)
- Persistence optional (RDB snapshots, AOF logs)
- Single-threaded (no race conditions)

### Installation (Linux)

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server

# Start service
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test
redis-cli ping  # Should return PONG
```

### Python Setup

```python
# backend/app/db/redis.py
import redis
import os
import json

class RedisClient:
    def __init__(self):
        self.client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_DB', 0)),
            decode_responses=True  # Return strings, not bytes
        )
    
    def get(self, key):
        return self.client.get(key)
    
    def set(self, key, value, ex=None):
        return self.client.set(key, value, ex=ex)
    
    def delete(self, key):
        return self.client.delete(key)
    
    def exists(self, key):
        return self.client.exists(key)

redis_client = RedisClient()
```

### Caching Pattern

```python
# backend/app/services/user_service.py
from app.db.postgres import db
from app.db.redis import redis_client
from app.models import User
import json

class UserService:
    CACHE_TTL = 300  # 5 minutes
    
    def get_user(self, user_id):
        # Try cache first
        cache_key = f'user:{user_id}'
        cached = redis_client.get(cache_key)
        
        if cached:
            return json.loads(cached)
        
        # Cache miss - query database
        user = User.query.get(user_id)
        if not user:
            return None
        
        user_data = user.to_dict()
        
        # Store in cache
        redis_client.set(
            cache_key,
            json.dumps(user_data),
            ex=self.CACHE_TTL
        )
        
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

### Session Storage

```python
# backend/app/services/session_service.py
from app.db.redis import redis_client
import secrets
import json

class SessionService:
    SESSION_TTL = 86400  # 24 hours
    
    def create_session(self, user_id):
        session_id = secrets.token_urlsafe(32)
        session_data = {
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat()
        }
        
        redis_client.set(
            f'session:{session_id}',
            json.dumps(session_data),
            ex=self.SESSION_TTL
        )
        
        return session_id
    
    def get_session(self, session_id):
        data = redis_client.get(f'session:{session_id}')
        return json.loads(data) if data else None
    
    def delete_session(self, session_id):
        redis_client.delete(f'session:{session_id}')
    
    def extend_session(self, session_id):
        key = f'session:{session_id}'
        if redis_client.exists(key):
            redis_client.expire(key, self.SESSION_TTL)
```

### Rate Limiting

```python
# backend/app/middleware/rate_limit.py
from app.db.redis import redis_client
from flask import request, jsonify
from functools import wraps

def rate_limit(max_requests=100, window=60):
    """
    Rate limit decorator
    max_requests: Maximum requests allowed
    window: Time window in seconds
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Use IP address as key
            ip = request.remote_addr
            key = f'rate_limit:{ip}:{f.__name__}'
            
            # Increment counter
            current = redis_client.client.incr(key)
            
            # Set expiration on first request
            if current == 1:
                redis_client.client.expire(key, window)
            
            # Check limit
            if current > max_requests:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': redis_client.client.ttl(key)
                }), 429
            
            return f(*args, **kwargs)
        return wrapped
    return decorator

# Usage
@app.route('/api/expensive-operation')
@rate_limit(max_requests=10, window=60)
def expensive_operation():
    return jsonify({'result': 'success'})
```

### Queue Pattern (Simple)

```python
# backend/app/services/email_queue.py
from app.db.redis import redis_client
import json

class EmailQueue:
    QUEUE_KEY = 'queue:emails'
    
    def enqueue(self, to, subject, body):
        email_data = {
            'to': to,
            'subject': subject,
            'body': body,
            'queued_at': datetime.utcnow().isoformat()
        }
        redis_client.client.lpush(self.QUEUE_KEY, json.dumps(email_data))
    
    def dequeue(self):
        data = redis_client.client.rpop(self.QUEUE_KEY)
        return json.loads(data) if data else None
    
    def queue_size(self):
        return redis_client.client.llen(self.QUEUE_KEY)

# Worker process
def email_worker():
    queue = EmailQueue()
    while True:
        email = queue.dequeue()
        if email:
            send_email(email['to'], email['subject'], email['body'])
        else:
            time.sleep(1)
```

### Production Redis Configuration

```python
# backend/app/config.py
import os

class Config:
    # Redis
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')  # For production
    
    # Cache TTLs
    CACHE_TTL_SHORT = 60  # 1 minute
    CACHE_TTL_MEDIUM = 300  # 5 minutes
    CACHE_TTL_LONG = 3600  # 1 hour
```

**Production notes**:
- Enable persistence (RDB + AOF) for important data
- Set maxmemory policy (e.g., `allkeys-lru`)
- Use Redis Sentinel or Redis Cluster for high availability
- Monitor memory usage
- Use connection pooling

---

## Module 3 Exam

### Multiple Choice Questions

1. When should you use MongoDB instead of PostgreSQL?
   a) For user authentication
   b) For financial transactions
   c) For flexible schema data like logs or product catalogs
   d) Always - MongoDB is faster

2. What is the main advantage of embedding documents in MongoDB?
   a) Saves disk space
   b) Avoids joins - data is retrieved in one query
   c) Enforces data integrity
   d) Provides ACID guarantees

3. What is Redis primarily used for in backend systems?
   a) Primary database for all data
   b) Caching, sessions, and rate limiting
   c) Complex queries and joins
   d) Long-term data storage

4. How does Redis handle concurrent writes?
   a) Uses locks
   b) Single-threaded - no race conditions
   c) Multi-threaded with MVCC
   d) Requires manual synchronization

5. What happens to Redis data by default when the server restarts?
   a) Data is always persisted
   b) Data is lost unless persistence is configured
   c) Data is automatically backed up
   d) Data is moved to disk

### Practical Design Tasks

**Task 1**: Design a logging system using MongoDB that:
- Stores application logs (INFO, WARNING, ERROR)
- Supports querying by level, timestamp, and user_id
- Retains logs for 30 days
- Handles 10,000 log entries per minute

Provide the document schema and necessary indexes.

**Task 2**: Implement a caching layer using Redis for a user profile API that:
- Caches user profiles for 5 minutes
- Invalidates cache on user updates
- Handles cache misses gracefully
- Includes rate limiting (100 requests per minute per IP)

Provide Python code for the service layer.

### Incident Scenario

**Scenario**: Your Flask application uses Redis for caching. After a deployment, users report seeing stale data. Investigation reveals:
- Cache is not being invalidated on updates
- Some cached data is from 2 days ago
- Redis memory usage is at 95%

**Questions**:
1. What are the three main problems?
2. How would you fix the cache invalidation issue?
3. How would you prevent Redis from running out of memory?
4. What monitoring would you add?
