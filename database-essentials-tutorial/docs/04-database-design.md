# Module 4: Database Design

## Normalization vs Denormalization

### Normalization (Relational Databases)

**Goal**: Eliminate data redundancy

**Normal Forms** (what actually matters):

**1NF (First Normal Form)**: No repeating groups
```sql
-- BAD: Violates 1NF
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255),
    phone_numbers VARCHAR(255)  -- "555-1234, 555-5678" (multiple values)
);

-- GOOD: 1NF compliant
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255)
);

CREATE TABLE user_phones (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    phone_number VARCHAR(20)
);
```

**2NF (Second Normal Form)**: No partial dependencies
```sql
-- BAD: Violates 2NF
CREATE TABLE order_items (
    order_id INTEGER,
    product_id INTEGER,
    product_name VARCHAR(255),  -- Depends only on product_id
    quantity INTEGER,
    PRIMARY KEY (order_id, product_id)
);

-- GOOD: 2NF compliant
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255)
);

CREATE TABLE order_items (
    order_id INTEGER,
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER,
    PRIMARY KEY (order_id, product_id)
);
```

**3NF (Third Normal Form)**: No transitive dependencies
```sql
-- BAD: Violates 3NF
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    user_email VARCHAR(255),  -- Depends on user_id, not order id
    total DECIMAL(10, 2)
);

-- GOOD: 3NF compliant
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255)
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    total DECIMAL(10, 2)
);
```

**Production rule**: Aim for 3NF, denormalize only when performance requires it.

### Denormalization (Performance Optimization)

**When to denormalize**:
- Read-heavy workloads
- Expensive joins
- Caching not sufficient

**Example: E-commerce orders**

**Normalized (slow)**:
```sql
-- Query requires 3 joins
SELECT 
    o.id,
    u.email,
    u.full_name,
    p.name as product_name,
    oi.quantity,
    oi.price
FROM orders o
JOIN users u ON o.user_id = u.id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
WHERE o.id = 123;
```

**Denormalized (fast)**:
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    user_email VARCHAR(255),  -- Denormalized
    user_name VARCHAR(255),   -- Denormalized
    total DECIMAL(10, 2),
    created_at TIMESTAMP
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    product_name VARCHAR(255),  -- Denormalized
    quantity INTEGER,
    price DECIMAL(10, 2)  -- Snapshot of price at purchase time
);

-- Single query, no joins
SELECT * FROM orders WHERE id = 123;
SELECT * FROM order_items WHERE order_id = 123;
```

**Trade-off**: Faster reads, but must update denormalized data when source changes.

## Relationships

### One-to-Many

**Example**: User has many posts

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content TEXT
);

-- Query: Get user with posts
SELECT u.*, p.id as post_id, p.title
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
WHERE u.id = 1;
```

**SQLAlchemy**:
```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    posts = db.relationship('Post', backref='user', lazy='dynamic')

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text)
```

### Many-to-Many

**Example**: Posts have many tags, tags have many posts

```sql
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL
);

CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- Junction table
CREATE TABLE post_tags (
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, tag_id)
);

-- Query: Get posts with tag "python"
SELECT p.*
FROM posts p
JOIN post_tags pt ON p.id = pt.post_id
JOIN tags t ON pt.tag_id = t.id
WHERE t.name = 'python';
```

**SQLAlchemy**:
```python
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    tags = db.relationship('Tag', secondary=post_tags, backref='posts')

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
```

### One-to-One

**Example**: User has one profile

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE user_profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    bio TEXT,
    avatar_url VARCHAR(500),
    website VARCHAR(255)
);
```

**SQLAlchemy**:
```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    profile = db.relationship('UserProfile', backref='user', uselist=False)

class UserProfile(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(500))
```

## Designing for Reads vs Writes

### Read-Heavy Systems

**Characteristics**:
- Social media feeds
- News sites
- Product catalogs

**Optimization strategies**:

1. **Denormalize data**
```sql
-- Store computed values
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500),
    comment_count INTEGER DEFAULT 0,  -- Denormalized
    like_count INTEGER DEFAULT 0,     -- Denormalized
    created_at TIMESTAMP
);

-- Update counts with triggers
CREATE OR REPLACE FUNCTION update_comment_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE posts SET comment_count = comment_count + 1
    WHERE id = NEW.post_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER increment_comment_count
AFTER INSERT ON comments
FOR EACH ROW EXECUTE FUNCTION update_comment_count();
```

2. **Add indexes aggressively**
```sql
CREATE INDEX idx_posts_created_at ON posts(created_at);
CREATE INDEX idx_posts_user_id ON posts(user_id);
CREATE INDEX idx_posts_published ON posts(published) WHERE published = TRUE;
```

3. **Use caching**
```python
@cache.memoize(timeout=300)
def get_popular_posts():
    return Post.query.filter_by(published=True)\
        .order_by(Post.like_count.desc())\
        .limit(10).all()
```

### Write-Heavy Systems

**Characteristics**:
- Logging systems
- Analytics ingestion
- IoT data collection

**Optimization strategies**:

1. **Minimize indexes**
```sql
-- Only essential indexes
CREATE TABLE logs (
    id BIGSERIAL PRIMARY KEY,
    level VARCHAR(20),
    message TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Only index timestamp for time-range queries
CREATE INDEX idx_logs_timestamp ON logs(timestamp);
```

2. **Use batch inserts**
```python
# BAD: Individual inserts
for log in logs:
    db.session.add(Log(**log))
    db.session.commit()  # Slow!

# GOOD: Batch insert
db.session.bulk_insert_mappings(Log, logs)
db.session.commit()  # Fast!
```

3. **Consider append-only design**
```sql
-- Never UPDATE or DELETE, only INSERT
CREATE TABLE events (
    id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(50),
    user_id INTEGER,
    data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Common Anti-Patterns

### Anti-Pattern 1: God Table

```sql
-- BAD: Everything in one table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255),
    password_hash VARCHAR(255),
    -- Profile fields
    bio TEXT,
    avatar_url VARCHAR(500),
    -- Settings
    theme VARCHAR(20),
    notifications_enabled BOOLEAN,
    -- Metadata
    last_login TIMESTAMP,
    login_count INTEGER,
    -- ... 50 more columns
);
```

**Fix**: Separate concerns
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255),
    password_hash VARCHAR(255)
);

CREATE TABLE user_profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    bio TEXT,
    avatar_url VARCHAR(500)
);

CREATE TABLE user_settings (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    theme VARCHAR(20),
    notifications_enabled BOOLEAN
);
```

### Anti-Pattern 2: EAV (Entity-Attribute-Value)

```sql
-- BAD: Generic attribute table
CREATE TABLE entity_attributes (
    entity_id INTEGER,
    attribute_name VARCHAR(100),
    attribute_value TEXT
);

-- Nightmare to query
SELECT * FROM entity_attributes
WHERE entity_id = 1 AND attribute_name = 'email';
```

**Fix**: Use proper columns or JSONB
```sql
-- Option 1: Proper columns
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255),
    full_name VARCHAR(255)
);

-- Option 2: JSONB for flexible data
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255),
    metadata JSONB
);
```

### Anti-Pattern 3: Polymorphic Associations

```sql
-- BAD: Generic foreign key
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    commentable_type VARCHAR(50),  -- 'Post' or 'Photo'
    commentable_id INTEGER,        -- ID of post or photo
    content TEXT
);

-- Can't enforce foreign key constraint
-- Can't join efficiently
```

**Fix**: Separate tables or use inheritance
```sql
-- Option 1: Separate tables
CREATE TABLE post_comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id),
    content TEXT
);

CREATE TABLE photo_comments (
    id SERIAL PRIMARY KEY,
    photo_id INTEGER REFERENCES photos(id),
    content TEXT
);

-- Option 2: Nullable foreign keys
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id),
    photo_id INTEGER REFERENCES photos(id),
    content TEXT,
    CHECK (
        (post_id IS NOT NULL AND photo_id IS NULL) OR
        (post_id IS NULL AND photo_id IS NOT NULL)
    )
);
```

### Anti-Pattern 4: Premature Optimization

```python
# BAD: Over-engineering before measuring
class UserRepository:
    def get_user(self, user_id):
        # Complex caching logic
        # Multiple cache layers
        # Unnecessary complexity
        pass
```

**Fix**: Start simple, optimize when needed
```python
# GOOD: Simple first
class UserRepository:
    def get_user(self, user_id):
        return User.query.get(user_id)

# Add caching only when profiling shows it's needed
```

## Real-World Example: Blog Platform

```sql
-- Users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Posts
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    title VARCHAR(500) NOT NULL,
    slug VARCHAR(500) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    published BOOLEAN DEFAULT FALSE,
    published_at TIMESTAMP,
    view_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,  -- Denormalized for performance
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Comments
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tags
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL
);

-- Post-Tag junction
CREATE TABLE post_tags (
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, tag_id)
);

-- Indexes
CREATE INDEX idx_posts_user_id ON posts(user_id);
CREATE INDEX idx_posts_published_at ON posts(published_at) WHERE published = TRUE;
CREATE INDEX idx_posts_slug ON posts(slug);
CREATE INDEX idx_comments_post_id ON comments(post_id);
CREATE INDEX idx_comments_user_id ON comments(user_id);
```

---

## Module 4 Exam

### Multiple Choice Questions

1. What is the main goal of database normalization?
   a) Improve query performance
   b) Eliminate data redundancy
   c) Reduce disk space
   d) Simplify queries

2. When should you denormalize a database?
   a) Always - it's faster
   b) Never - it violates best practices
   c) When read performance is critical and joins are expensive
   d) Only for NoSQL databases

3. How do you implement a many-to-many relationship in SQL?
   a) Add an array column
   b) Use a junction table
   c) Use JSONB
   d) Use multiple foreign keys

4. What is the EAV anti-pattern?
   a) Storing everything in one table
   b) Using generic attribute-value pairs instead of proper columns
   c) Not using foreign keys
   d) Over-indexing tables

5. What is the best approach for a write-heavy logging system?
   a) Normalize to 3NF with many indexes
   b) Minimize indexes and use batch inserts
   c) Use many-to-many relationships
   d) Denormalize everything

### Practical Design Tasks

**Task 1**: Design a database schema for a task management application with:
- Users and teams
- Projects (belong to teams)
- Tasks (belong to projects)
- Task assignments (users assigned to tasks)
- Task comments

Include all tables, relationships, constraints, and indexes. Justify your design choices.

**Task 2**: You have a social media application where users can follow each other. Design the database schema for:
- User profiles
- Follow relationships (user A follows user B)
- Posts
- Likes on posts

Optimize for:
- Fast feed generation (get posts from followed users)
- Fast follower/following counts

### Incident Scenario

**Scenario**: Your e-commerce application is slow when loading order history. The schema is:

```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER
);
```

The query joins orders → order_items → products for each order. With 1M orders and 5M order_items, it takes 10 seconds.

**Questions**:
1. What is the performance bottleneck?
2. Should you normalize or denormalize? Why?
3. What specific changes would you make?
4. What are the trade-offs of your solution?
