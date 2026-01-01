# Module 2: SQL Databases (PostgreSQL)

## PostgreSQL Architecture (Practical View)

### What PostgreSQL Actually Does

PostgreSQL is a **process-based** relational database that:
1. Manages concurrent connections via separate processes
2. Uses WAL (Write-Ahead Logging) for crash recovery
3. Implements MVCC (Multi-Version Concurrency Control) for transactions
4. Stores data in 8KB pages on disk

**You don't need to memorize this**. What matters:
- PostgreSQL handles concurrency well
- It's ACID-compliant (reliable for transactions)
- It scales vertically (better hardware = better performance)

### Installation (Linux)

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Access PostgreSQL
sudo -u postgres psql
```

### Creating a Database

```sql
-- As postgres user
CREATE DATABASE backend_db;
CREATE USER backend_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE backend_db TO backend_user;

-- Connect to database
\c backend_db
```

## Tables, Rows, Columns

### Creating Tables

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Posts table
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Data Types (What Actually Matters)

**Text**:
- `VARCHAR(n)` - Variable length, max n characters (use for emails, names)
- `TEXT` - Unlimited length (use for content, descriptions)

**Numbers**:
- `INTEGER` - Whole numbers (-2B to 2B)
- `BIGINT` - Large whole numbers (use for IDs if you expect > 2B rows)
- `SERIAL` - Auto-incrementing integer (use for primary keys)
- `DECIMAL(p, s)` - Exact decimals (use for money: `DECIMAL(10, 2)`)

**Boolean**:
- `BOOLEAN` - TRUE/FALSE (use for flags: is_active, is_verified)

**Date/Time**:
- `TIMESTAMP` - Date and time (use for created_at, updated_at)
- `DATE` - Date only (use for birthdays, deadlines)

**JSON**:
- `JSONB` - Binary JSON (use for flexible data, metadata)

### Backend Example: User Model

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    metadata JSONB,  -- Flexible data
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Insert user
INSERT INTO users (email, password_hash, full_name, metadata)
VALUES (
    'user@example.com',
    '$2b$12$...',  -- bcrypt hash
    'John Doe',
    '{"preferences": {"theme": "dark"}}'::jsonb
);

-- Query user
SELECT * FROM users WHERE email = 'user@example.com';
```

## Primary Keys and Foreign Keys

### Primary Keys

**Purpose**: Uniquely identify each row

```sql
-- Auto-incrementing ID (most common)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

-- UUID (for distributed systems)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL,
    token VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL
);

-- Composite primary key (rare)
CREATE TABLE user_roles (
    user_id INTEGER,
    role_id INTEGER,
    PRIMARY KEY (user_id, role_id)
);
```

**When to use UUID vs SERIAL**:
- SERIAL: Single database, simpler, faster
- UUID: Distributed systems, merge databases, public-facing IDs

### Foreign Keys

**Purpose**: Enforce relationships between tables

```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    total DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- What this does:
-- 1. Prevents inserting order with non-existent user_id
-- 2. Prevents deleting user who has orders (by default)
```

### Foreign Key Actions

```sql
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    content TEXT NOT NULL
);

-- ON DELETE CASCADE: Delete comments when post is deleted
-- ON DELETE SET NULL: Set user_id to NULL when user is deleted
-- ON DELETE RESTRICT: Prevent deletion if comments exist (default)
```

**Production pattern**:
```sql
-- Good: Explicit foreign key with name
ALTER TABLE orders
ADD CONSTRAINT fk_orders_user
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT;

-- Bad: No foreign key (data integrity issues)
CREATE TABLE orders (
    user_id INTEGER  -- Nothing prevents invalid user_id
);
```

## Indexes (What Actually Matters)

### Why Indexes Exist

Without index:
```sql
SELECT * FROM users WHERE email = 'user@example.com';
-- Scans ALL rows (slow for large tables)
```

With index:
```sql
CREATE INDEX idx_users_email ON users(email);
SELECT * FROM users WHERE email = 'user@example.com';
-- Uses B-tree index (fast, O(log n))
```

### When to Create Indexes

**Always index**:
- Primary keys (automatic)
- Foreign keys
- Columns in WHERE clauses
- Columns in JOIN conditions
- Columns in ORDER BY

**Example**:
```sql
-- Users table
CREATE INDEX idx_users_email ON users(email);  -- WHERE email = ?
CREATE INDEX idx_users_created_at ON users(created_at);  -- ORDER BY created_at

-- Orders table
CREATE INDEX idx_orders_user_id ON orders(user_id);  -- Foreign key
CREATE INDEX idx_orders_created_at ON orders(created_at);  -- Date range queries
```

### Index Types

**B-tree (default)**: Use for most cases
```sql
CREATE INDEX idx_users_email ON users(email);
```

**Unique index**: Enforce uniqueness
```sql
CREATE UNIQUE INDEX idx_users_email_unique ON users(email);
-- Same as: ALTER TABLE users ADD CONSTRAINT users_email_unique UNIQUE (email);
```

**Partial index**: Index subset of rows
```sql
-- Only index active users
CREATE INDEX idx_active_users_email ON users(email) WHERE is_active = TRUE;
```

**Composite index**: Multiple columns
```sql
-- For queries like: WHERE user_id = ? AND created_at > ?
CREATE INDEX idx_posts_user_created ON posts(user_id, created_at);
```

**GIN index**: For JSONB and arrays
```sql
CREATE INDEX idx_users_metadata ON users USING GIN (metadata);

-- Query JSONB
SELECT * FROM users WHERE metadata @> '{"preferences": {"theme": "dark"}}';
```

### Index Gotchas

**Problem 1**: Too many indexes slow down writes
```sql
-- Bad: Index everything
CREATE INDEX idx1 ON users(email);
CREATE INDEX idx2 ON users(full_name);
CREATE INDEX idx3 ON users(created_at);
CREATE INDEX idx4 ON users(updated_at);
CREATE INDEX idx5 ON users(is_active);
-- Every INSERT/UPDATE must update 5 indexes
```

**Problem 2**: Wrong column order in composite index
```sql
-- Bad: created_at first
CREATE INDEX idx_posts_created_user ON posts(created_at, user_id);
-- Doesn't help: WHERE user_id = ?

-- Good: user_id first
CREATE INDEX idx_posts_user_created ON posts(user_id, created_at);
-- Helps both: WHERE user_id = ? AND WHERE user_id = ? AND created_at > ?
```

**Rule**: Most selective column first (column that narrows down results most)

## Constraints and Data Integrity

### NOT NULL

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,  -- Must have a name
    description TEXT  -- Optional
);

-- Prevents:
INSERT INTO products (description) VALUES ('...');  -- Error: name is NULL
```

### UNIQUE

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,  -- No duplicate emails
    username VARCHAR(50) UNIQUE NOT NULL  -- No duplicate usernames
);

-- Prevents:
INSERT INTO users (email, username) VALUES ('user@example.com', 'john');
INSERT INTO users (email, username) VALUES ('user@example.com', 'jane');  -- Error
```

### CHECK

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) CHECK (price >= 0),  -- Price can't be negative
    stock INTEGER CHECK (stock >= 0)
);

-- Prevents:
INSERT INTO products (name, price, stock) VALUES ('Widget', -10.00, 5);  -- Error
```

### DEFAULT

```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    status VARCHAR(50) DEFAULT 'pending',  -- Default status
    created_at TIMESTAMP DEFAULT NOW()  -- Auto-set timestamp
);

-- No need to specify status or created_at
INSERT INTO orders DEFAULT VALUES;
```

### Backend Example: Complete Table

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    age INTEGER CHECK (age >= 18),  -- Must be 18+
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    published BOOLEAN DEFAULT FALSE,
    view_count INTEGER DEFAULT 0 CHECK (view_count >= 0),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_posts_user_id ON posts(user_id);
CREATE INDEX idx_posts_published_created ON posts(published, created_at);
```

## Common SQL Queries for Backend

### CRUD Operations

```sql
-- CREATE
INSERT INTO users (email, password_hash, full_name)
VALUES ('user@example.com', '$2b$12$...', 'John Doe')
RETURNING id, email, created_at;  -- Return inserted data

-- READ
SELECT id, email, full_name, created_at
FROM users
WHERE email = 'user@example.com';

-- UPDATE
UPDATE users
SET full_name = 'Jane Doe', updated_at = NOW()
WHERE id = 1
RETURNING *;

-- DELETE
DELETE FROM users WHERE id = 1;
```

### Joins

```sql
-- Get user with their posts
SELECT u.email, p.title, p.created_at
FROM users u
INNER JOIN posts p ON u.id = p.user_id
WHERE u.id = 1
ORDER BY p.created_at DESC;

-- Get users who have never posted
SELECT u.id, u.email
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
WHERE p.id IS NULL;
```

### Aggregations

```sql
-- Count posts per user
SELECT u.email, COUNT(p.id) as post_count
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
GROUP BY u.id, u.email
HAVING COUNT(p.id) > 5
ORDER BY post_count DESC;

-- Total revenue per day
SELECT DATE(created_at) as date, SUM(total) as revenue
FROM orders
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date;
```

### Pagination

```sql
-- Page 1 (0-19)
SELECT * FROM posts
ORDER BY created_at DESC
LIMIT 20 OFFSET 0;

-- Page 2 (20-39)
SELECT * FROM posts
ORDER BY created_at DESC
LIMIT 20 OFFSET 20;
```

---

## Module 2 Exam

### Multiple Choice Questions

1. What is the purpose of a foreign key constraint?
   a) To make queries faster
   b) To enforce referential integrity between tables
   c) To create indexes automatically
   d) To prevent NULL values

2. Which index type should you use for JSONB columns?
   a) B-tree
   b) Hash
   c) GIN
   d) GIST

3. What does `ON DELETE CASCADE` do?
   a) Deletes all rows in the table
   b) Prevents deletion of referenced rows
   c) Automatically deletes dependent rows
   d) Creates a backup before deletion

4. When should you use `SERIAL` vs `UUID` for primary keys?
   a) Always use UUID for better performance
   b) Use SERIAL for single database, UUID for distributed systems
   c) Use UUID for better security
   d) They are interchangeable

5. What is the correct column order for a composite index on `(user_id, created_at)`?
   a) Always alphabetical
   b) Most selective column first
   c) Least selective column first
   d) Order doesn't matter

### Practical Design Tasks

**Task 1**: Design a PostgreSQL schema for a blog platform with:
- Users (email, password, profile)
- Posts (title, content, published status)
- Comments (on posts)
- Tags (many-to-many with posts)

Include all tables, constraints, foreign keys, and indexes.

**Task 2**: Write SQL queries for:
1. Get all published posts by a specific user
2. Get the 10 most commented posts
3. Get all posts with a specific tag
4. Get users who have never commented

### Incident Scenario

**Scenario**: Your Flask API is timing out on a query that fetches user orders:

```python
@app.route('/users/<int:user_id>/orders')
def get_user_orders(user_id):
    orders = db.session.query(Order).filter_by(user_id=user_id).all()
    return jsonify([o.to_dict() for o in orders])
```

The `orders` table has 10 million rows. The query takes 30 seconds.

**Questions**:
1. What is the likely cause?
2. How would you diagnose it using PostgreSQL tools?
3. What is the fix?
4. How would you prevent this in the future?
