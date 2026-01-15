# Module 5: SQLAlchemy ORM

## Introduction

SQLAlchemy is the most popular Python ORM (Object-Relational Mapper). It bridges the gap between Python objects and relational databases, letting you work with database records as if they were Python classes.

**What you'll learn**:
- **ORM vs Raw SQL**: When each is appropriate
- **Building models**: Defining tables as Python classes
- **Relationships**: Connecting related data (users ↔ posts)
- **Query optimization**: Avoiding common performance traps
- **Production patterns**: Repository pattern, transaction safety

**The key benefit**: Type-safe, maintainable database code. The key trade-off: Less control over SQL than raw queries.

---

## ORM vs Raw SQL

### What is an ORM?

**ORM (Object-Relational Mapping)** maps database tables to Python classes. Each row becomes an object instance, each column becomes an attribute.

**Example comparison**:

**Raw SQL approach**:
```python
import psycopg2

# Manual connection management
conn = psycopg2.connect(
    host="localhost",
    database="mydb",
    user="postgres",
    password="secret"
)
cursor = conn.cursor()

# Manual SQL (easy to get wrong)
cursor.execute(
    "SELECT id, email, full_name, created_at FROM users WHERE email = %s",
    ('user@example.com',)
)
row = cursor.fetchone()

# Manual unpacking
if row:
    user_id, email, full_name, created_at = row
    user = {'id': user_id, 'email': email, 'full_name': full_name}
else:
    user = None

cursor.close()
conn.close()  # Don't forget!
```

**ORM approach (SQLAlchemy)**:
```python
from sqlalchemy.orm import Session

# Automatic connection pooling, type safety
user = session.query(User).filter_by(email='user@example.com').first()

# Python object (type-safe, autocomplete)
print(user.full_name)  # IDE knows attribute exists
print(user.created_at.year)  # IDE knows it's a datetime
```

### When to Use Each

**Use ORM when**:
- Standard CRUD operations (Create, Read, Update, Delete)
- Need type safety and IDE autocomplete
- Want database-agnostic code (switch databases without code changes)
- Working with relationships (users.posts, post.author)
- Building web frameworks (Flask, FastAPI)

**Use raw SQL when**:
- Complex queries with CTEs, window functions, custom aggregations
- Bulk operations (1M rows insert)
- Database-specific features needed
- Performance-critical queries needing fine control
- Reporting and analytics

**Production pattern**: **Use ORM for 90% of code, raw SQL for 10%**

```python
# ORM: Simple queries
user = User.query.get(user_id)  # PRIMARY KEY lookup

# ORM: Relationships
orders = user.orders.all()  # Foreign key traversal

# Raw SQL: Complex query
from sqlalchemy import text

result = db.session.execute(text("""
    WITH user_stats AS (
        SELECT user_id, COUNT(*) as order_count
        FROM orders
        GROUP BY user_id
    )
    SELECT u.*, s.order_count
    FROM users u
    LEFT JOIN user_stats s ON u.id = s.user_id
    ORDER BY s.order_count DESC
    LIMIT 10
"""))

top_users = result.fetchall()
```

- Want database-agnostic code
- Working with relationships

**Use raw SQL when**:
- Complex queries (CTEs, window functions)
- Bulk operations
- Performance-critical queries
- Database-specific features

**Production pattern**: Use ORM for 80% of queries, raw SQL for complex cases.

## SQLAlchemy Core vs ORM

### SQLAlchemy Core (SQL Expression Language)

```python
from sqlalchemy import Table, Column, Integer, String, MetaData, create_engine

metadata = MetaData()

users = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('email', String(255), unique=True, nullable=False)
)

engine = create_engine('postgresql://...')
metadata.create_all(engine)

# Insert
stmt = users.insert().values(email='user@example.com')
engine.execute(stmt)

# Select
stmt = users.select().where(users.c.email == 'user@example.com')
result = engine.execute(stmt).fetchone()
```

**Use Core when**: You need fine-grained control without ORM overhead.

### SQLAlchemy ORM

```python
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)

# Create tables
Base.metadata.create_all(engine)

# Insert
user = User(email='user@example.com')
session.add(user)
session.commit()

# Select
user = session.query(User).filter_by(email='user@example.com').first()
```

**Use ORM when**: You want object-oriented interface and relationship management.

## Models and Relationships

### Basic Model

```python
# backend/app/models/user.py
from app.db.postgres import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<User {self.email}>'
```

### One-to-Many Relationship

```python
# backend/app/models/post.py
from app.db.postgres import db
from datetime import datetime

class Post(db.Model):
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)
    published = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('posts', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'published': self.published,
            'user': {
                'id': self.user.id,
                'email': self.user.email
            },
            'created_at': self.created_at.isoformat()
        }

# Usage
user = User.query.get(1)
posts = user.posts.all()  # Get all posts by user

post = Post.query.get(1)
author = post.user  # Get post author
```

### Many-to-Many Relationship

```python
# backend/app/models/tag.py
from app.db.postgres import db

# Junction table
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)

class Tag(db.Model):
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug
        }

# Update Post model
class Post(db.Model):
    # ... existing columns ...
    
    tags = db.relationship('Tag', secondary=post_tags, backref='posts')

# Usage
post = Post.query.get(1)
post.tags.append(Tag(name='Python', slug='python'))
db.session.commit()

# Query posts by tag
tag = Tag.query.filter_by(slug='python').first()
posts = tag.posts  # All posts with this tag
```

### Lazy Loading Strategies

```python
# lazy='select' (default) - Load on access (N+1 problem)
user = User.query.get(1)
posts = user.posts.all()  # Separate query

# lazy='joined' - Eager load with JOIN
class User(db.Model):
    posts = db.relationship('Post', backref='user', lazy='joined')

user = User.query.get(1)  # Loads user and posts in one query

# lazy='subquery' - Eager load with subquery
class User(db.Model):
    posts = db.relationship('Post', backref='user', lazy='subquery')

# lazy='dynamic' - Return query object (for filtering)
class User(db.Model):
    posts = db.relationship('Post', backref='user', lazy='dynamic')

user = User.query.get(1)
recent_posts = user.posts.filter(Post.created_at > cutoff).all()
```

## Query Optimization

### N+1 Problem

```python
# BAD: N+1 queries
users = User.query.all()  # 1 query
for user in users:
    print(user.posts.all())  # N queries (one per user)

# GOOD: Eager loading
from sqlalchemy.orm import joinedload

users = User.query.options(joinedload(User.posts)).all()  # 1 query
for user in users:
    print(user.posts)  # No additional queries
```

### Select Specific Columns

```python
# BAD: Load entire object
users = User.query.all()  # Loads all columns

# GOOD: Load only needed columns
from sqlalchemy import select

stmt = select(User.id, User.email)
users = db.session.execute(stmt).all()
```

### Pagination

```python
# backend/app/services/post_service.py
class PostService:
    def get_posts(self, page=1, per_page=20):
        pagination = Post.query.filter_by(published=True)\
            .order_by(Post.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'posts': [p.to_dict() for p in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
```

### Bulk Operations

```python
# BAD: Individual inserts
for data in user_data:
    user = User(**data)
    db.session.add(user)
    db.session.commit()  # Slow!

# GOOD: Bulk insert
db.session.bulk_insert_mappings(User, user_data)
db.session.commit()  # Fast!

# Bulk update
db.session.bulk_update_mappings(User, [
    {'id': 1, 'is_active': False},
    {'id': 2, 'is_active': False}
])
db.session.commit()
```

### Raw SQL When Needed

```python
# Complex query with CTE
from sqlalchemy import text

sql = text("""
    WITH monthly_stats AS (
        SELECT 
            DATE_TRUNC('month', created_at) as month,
            COUNT(*) as post_count
        FROM posts
        WHERE published = TRUE
        GROUP BY DATE_TRUNC('month', created_at)
    )
    SELECT * FROM monthly_stats
    ORDER BY month DESC
    LIMIT 12
""")

result = db.session.execute(sql)
stats = [dict(row) for row in result]
```

## Avoiding ORM Abuse

### Anti-Pattern 1: Loading Entire Table

```python
# BAD: Load everything
all_users = User.query.all()  # Loads 1M users into memory

# GOOD: Use pagination or streaming
for user in User.query.yield_per(1000):
    process_user(user)
```

### Anti-Pattern 2: Ignoring Indexes

```python
# BAD: No index on email
class User(db.Model):
    email = db.Column(db.String(255), unique=True)

# GOOD: Add index
class User(db.Model):
    email = db.Column(db.String(255), unique=True, index=True)
```

### Anti-Pattern 3: Over-Eager Loading

```python
# BAD: Always load everything
class User(db.Model):
    posts = db.relationship('Post', lazy='joined')  # Always loads posts

# GOOD: Load on demand
class User(db.Model):
    posts = db.relationship('Post', lazy='select')

# Eager load when needed
users = User.query.options(joinedload(User.posts)).all()
```

### Anti-Pattern 4: Not Using Transactions

```python
# BAD: No transaction
def transfer_funds(from_user, to_user, amount):
    from_user.balance -= amount
    db.session.commit()  # What if this fails?
    to_user.balance += amount
    db.session.commit()

# GOOD: Use transaction
def transfer_funds(from_user, to_user, amount):
    try:
        from_user.balance -= amount
        to_user.balance += amount
        db.session.commit()  # Atomic
    except:
        db.session.rollback()
        raise
```

## Production Setup

### Database Configuration

```python
# backend/app/config.py
import os

class Config:
    # PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://user:password@localhost/dbname'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set to True for debugging
    
    # Connection pool
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,  # Test connections before using
        'max_overflow': 20
    }
```

### Database Initialization

```python
# backend/app/db/postgres.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    
    with app.app_context():
        # Import all models
        from app.models import user, post, tag
        
        # Create tables
        db.create_all()
```

### Repository Pattern

```python
# backend/app/repositories/user_repository.py
from app.db.postgres import db
from app.models.user import User
from sqlalchemy.exc import IntegrityError

class UserRepository:
    def create(self, email, password, full_name):
        user = User(email=email, full_name=full_name)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            return user
        except IntegrityError:
            db.session.rollback()
            raise ValueError('Email already exists')
    
    def get_by_id(self, user_id):
        return User.query.get(user_id)
    
    def get_by_email(self, email):
        return User.query.filter_by(email=email).first()
    
    def update(self, user_id, **kwargs):
        user = User.query.get(user_id)
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        db.session.commit()
        return user
    
    def delete(self, user_id):
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            return True
        return False
```

---

## Module 5 Exam

### Multiple Choice Questions

1. What is the main advantage of using an ORM?
   a) Always faster than raw SQL
   b) Maps database tables to Python objects
   c) Eliminates need for indexes
   d) Prevents all SQL injection

2. What is the N+1 query problem?
   a) A database error code
   b) Loading related data in separate queries instead of one
   c) Having N+1 tables
   d) A connection pool issue

3. Which lazy loading strategy should you use to avoid N+1 queries?
   a) lazy='select'
   b) lazy='dynamic'
   c) lazy='joined' or joinedload()
   d) lazy='subquery'

4. When should you use raw SQL instead of ORM?
   a) Never - ORM is always better
   b) For complex queries with CTEs or window functions
   c) For all queries - ORM is slow
   d) Only for INSERT statements

5. What is the purpose of `db.session.rollback()`?
   a) Delete all data
   b) Undo uncommitted changes
   c) Create a backup
   d) Close the connection

### Practical Design Tasks

**Task 1**: Design SQLAlchemy models for a library system with:
- Books (title, ISBN, author, published_date)
- Authors (name, bio)
- Users (email, name)
- Borrowing records (user borrows book, due date, returned date)

Include all relationships, constraints, and indexes.

**Task 2**: Write a repository class for the Book model that:
- Creates a new book
- Finds books by author
- Finds available books (not currently borrowed)
- Updates book information
- Handles errors gracefully

### Incident Scenario

**Scenario**: Your Flask API endpoint is slow:

```python
@app.route('/users')
def get_users():
    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'email': u.email,
        'post_count': len(u.posts.all())
    } for u in users])
```

With 10,000 users, this endpoint takes 30 seconds.

**Questions**:
1. What is the performance problem?
2. How many database queries are executed?
3. How would you fix it?
4. What would the optimized code look like?
