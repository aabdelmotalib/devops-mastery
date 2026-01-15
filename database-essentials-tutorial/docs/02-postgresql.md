# Module 2: SQL Databases (PostgreSQL)

## Introduction

PostgreSQL is the most advanced open-source relational database available. In this module, you'll learn how to design and work with PostgreSQL for production backend systems.

**What you'll master**:
- PostgreSQL architecture and how it guarantees data reliability
- Creating robust schema with proper types, constraints, and relationships
- Designing efficient indexes for query performance
- Writing production-ready SQL queries with proper error handling
- Understanding transaction semantics and isolation levels
- Best practices for backend data models

By the end of this module, you'll be able to design complete production database schemas and understand why each decision matters for reliability and performance.

---

## PostgreSQL Architecture (Practical View)

### What PostgreSQL Actually Does

PostgreSQL is a **process-based** relational database that:

1. **Manages concurrent connections via separate processes** - Each client connection gets its own backend process. This provides true isolation but uses more memory than threaded approaches.

2. **Uses WAL (Write-Ahead Logging) for crash recovery** - Before any data is modified on disk, the change is written to a log. If the server crashes, it replays this log to recover. **This is why your data survives crashes**.

3. **Implements MVCC (Multi-Version Concurrency Control) for transactions** - Multiple transactions see different versions of the same data simultaneously. Readers never block writers, and writers don't block readers. **This is why concurrent access is fast**.

4. **Stores data in 8KB pages on disk** - Data is organized in fixed-size pages. This affects how indexes work and query planning.

**What matters for your application**:
- PostgreSQL handles concurrency extremely well (thousands of simultaneous users)
- It's fully ACID-compliant (your data is safe)
- It scales vertically (better hardware = better performance)
- It's not designed for massive horizontal scaling (but works fine for most applications)

### Installation (Linux)

The installation process varies slightly by distribution. Here's the most common approach:

```bash
# Ubuntu/Debian/Linux Mint
sudo apt update
sudo apt install -y postgresql postgresql-contrib postgresql-client

# Verify installation
sudo -u postgres psql --version

# Start PostgreSQL service
sudo systemctl start postgresql

# Enable auto-start on boot
sudo systemctl enable postgresql

# Verify it's running
sudo systemctl status postgresql
```

**On a development machine**, PostgreSQL starts automatically after installation.

**On a server**, you might need to configure:
```bash
# Allow remote connections (CAUTION: requires authentication)
sudo nano /etc/postgresql/15/main/postgresql.conf
# Find and change: listen_addresses = 'localhost' to listen_addresses = '*'

# Allow remote authentication
sudo nano /etc/postgresql/15/main/pg_hba.conf
# Add: host    all             all             0.0.0.0/0            md5
```

### Creating a Database

The `postgres` user is the superuser created during installation. You'll use it to create your application user and database.

```sql
-- Connect as superuser
sudo -u postgres psql

-- Create database for application
CREATE DATABASE backend_db ENCODING 'UTF8';

-- Create user with password (for application to use)
CREATE USER backend_user WITH PASSWORD 'strong_password_here';

-- Grant privileges on database
GRANT CONNECT ON DATABASE backend_db TO backend_user;
GRANT USAGE ON SCHEMA public TO backend_user;
GRANT CREATE ON SCHEMA public TO backend_user;

-- Grant all privileges on all tables (current and future)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO backend_user;

-- If you created tables as postgres, transfer ownership
-- ALTER TABLE table_name OWNER TO backend_user;

-- Verify user was created
\du

-- Connect to new database as new user
\c backend_db backend_user

-- Exit
\q
```

**Connection string for application**:
```python
# Flask/SQLAlchemy
DATABASE_URL = "postgresql://backend_user:password@localhost/backend_db"

# Or with environment variable (recommended)
import os
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://backend_user:password@localhost/backend_db')
```


## Tables, Rows, Columns

### Creating Tables

A table is the fundamental structure in PostgreSQL. Each table represents an entity (users, posts, orders), and each row is an instance of that entity.

```sql
-- Users table - core entity
CREATE TABLE users (
    id SERIAL PRIMARY KEY,                              -- Auto-incrementing ID
    email VARCHAR(255) UNIQUE NOT NULL,                 -- Email must be unique
    password_hash VARCHAR(255) NOT NULL,                -- Password hash (never store plaintext)
    full_name VARCHAR(255),                             -- Optional full name
    is_active BOOLEAN DEFAULT TRUE,                     -- Active status, defaults to TRUE
    created_at TIMESTAMP DEFAULT NOW(),                 -- Timestamp when created
    updated_at TIMESTAMP DEFAULT NOW(),                 -- Timestamp of last update
    
    -- Optional: explicitly name primary key
    -- CONSTRAINT pk_users PRIMARY KEY (id)
);

-- Posts table - depends on users
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,                           -- Foreign key to users
    title VARCHAR(500) NOT NULL,
    content TEXT,                                       -- Unlimited length
    published BOOLEAN DEFAULT FALSE,
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Relationship: each post belongs to one user
    CONSTRAINT fk_posts_user_id FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE
        -- ON DELETE CASCADE: Delete posts when user is deleted
);

-- Comments table - multiple relationships
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Relationships
    CONSTRAINT fk_comments_post_id FOREIGN KEY (post_id)
        REFERENCES posts(id) ON DELETE CASCADE,
    
    CONSTRAINT fk_comments_user_id FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE SET NULL
        -- ON DELETE SET NULL: Keep comment but remove user reference
);
```

**Common table creation mistakes to avoid**:

```sql
-- BAD: Missing NOT NULL constraints
CREATE TABLE users (
    email VARCHAR(255),  -- Can be NULL (useless)
    password_hash VARCHAR(255)  -- Can be NULL (security issue!)
);

-- GOOD: Enforce required fields
CREATE TABLE users (
    email VARCHAR(255) NOT NULL,  -- Must be provided
    password_hash VARCHAR(255) NOT NULL
);

-- BAD: No defaults for timestamps
CREATE TABLE posts (
    created_at TIMESTAMP,  -- Have to set manually (error-prone)
);

-- GOOD: Automatic timestamps
CREATE TABLE posts (
    created_at TIMESTAMP DEFAULT NOW(),  -- Automatically set
    updated_at TIMESTAMP DEFAULT NOW()
);

-- BAD: VARCHAR with no size limit
CREATE TABLE users (
    name VARCHAR  -- PostgreSQL allows unlimited, but wasteful
);

-- GOOD: Reasonable limit
CREATE TABLE users (
    name VARCHAR(255)  -- Enough for real names
);
```

### Data Types (What Actually Matters)

PostgreSQL has many data types. Focus on these 10 that cover 95% of real applications:

### Data Types (What Actually Matters)

PostgreSQL has many data types. Focus on these 10 that cover 95% of real applications:

**Text Types**:
- **`VARCHAR(n)`** - Variable length string, max n characters
  - Use for: emails, usernames, names, phone numbers, URLs
  - Example: `VARCHAR(255)` for email (RFC 5321 limit is 254)
  - Don't use: VARCHAR without size (allows unlimited, causes bloat)

  ```sql
  CREATE TABLE users (
      email VARCHAR(255) NOT NULL,  -- Good: reasonable limit
      username VARCHAR(50) NOT NULL  -- Good: short usernames
  );
  ```

- **`TEXT`** - Unlimited length string
  - Use for: descriptions, content, bio, comments
  - Example: Blog post content, user bio, product description
  - Benefits: No need to guess max length
  - Costs: Slightly slower than VARCHAR for very short strings (usually negligible)

  ```sql
  CREATE TABLE posts (
      title VARCHAR(500) NOT NULL,  -- Short, bounded
      content TEXT NOT NULL          -- Long, unbounded
  );
  ```

**Numeric Types**:
- **`INTEGER`** - 32-bit signed integer: -2,147,483,648 to 2,147,483,647
  - Use for: counts, ages, quantities, status codes
  - Sufficient for: Most applications (2B users? probably don't need it yet)
  - Size: 4 bytes

  ```sql
  CREATE TABLE products (
      stock INTEGER DEFAULT 0,       -- Number in stock
      reorder_point INTEGER,          -- Reorder threshold
      views INTEGER DEFAULT 0
  );
  ```

- **`BIGINT`** - 64-bit signed integer: -9.2 quintillion to 9.2 quintillion
  - Use for: When you'll definitely exceed 2B values
  - Example: Total hits counter for viral sites, high-frequency trading
  - Size: 8 bytes (twice as much disk/memory)
  - When to use: 1M+ events per day × 10 years = probably need BIGINT

  ```sql
  CREATE TABLE events (
      id BIGSERIAL PRIMARY KEY,      -- Use BIGSERIAL for auto-increment
      event_count BIGINT DEFAULT 0
  );
  ```

- **`SERIAL` / `BIGSERIAL`** - Auto-incrementing integer (use for primary keys)
  - Use for: Primary key IDs
  - SERIAL: Starts at 1, increments by 1, max 2B values
  - BIGSERIAL: Same but up to 9.2 quintillion
  - Creates a sequence automatically (don't worry about details)

  ```sql
  CREATE TABLE users (
      id SERIAL PRIMARY KEY,          -- Auto-increment from 1
      email VARCHAR(255) UNIQUE
  );
  
  -- Or explicit with BIGSERIAL
  CREATE TABLE events (
      id BIGSERIAL PRIMARY KEY        -- For very high volume
  );
  ```

- **`DECIMAL(p, s)`** - Exact decimal number
  - Use for: Money, prices, precise calculations
  - **NEVER** use FLOAT for money (rounding errors!)
  - `p` = total digits, `s` = digits after decimal
  - Size: Depends on precision (up to 38 digits)

  ```sql
  CREATE TABLE orders (
      total DECIMAL(10, 2) NOT NULL,     -- Max 10 digits: $99,999,999.99
      tax DECIMAL(10, 2),                -- Always 2 decimals for cents
      discount_percent DECIMAL(5, 2)    -- Up to 999.99%
  );
  
  -- BAD: Don't use float for money!
  price FLOAT  -- Results in 19.99 becoming 19.989999... or 20.000001...
  
  -- GOOD: Always DECIMAL
  price DECIMAL(10, 2)  -- Exactly 19.99
  ```

**Boolean Type**:
- **`BOOLEAN`** - TRUE or FALSE (not NULL-safe)
  - Use for: Flags, boolean states, yes/no values
  - In SQL: `TRUE`, `FALSE`, `'t'`, `'f'`, `1`, `0`
  - In Python: True, False, None
  - Size: 1 byte

  ```sql
  CREATE TABLE users (
      is_active BOOLEAN DEFAULT TRUE,      -- Active by default
      is_verified BOOLEAN DEFAULT FALSE,   -- Not verified by default
      is_admin BOOLEAN NOT NULL            -- Required field
  );
  
  -- Usage
  UPDATE users SET is_active = FALSE WHERE id = 123;
  SELECT * FROM users WHERE is_verified = TRUE;
  ```

**Date/Time Types**:
- **`TIMESTAMP`** - Date and time with timezone awareness
  - Use for: Timestamps when things happened (created_at, updated_at, logged_in_at)
  - Includes: Year, month, day, hour, minute, second, millisecond
  - Size: 8 bytes
  - Best practice: Always use `DEFAULT NOW()` to auto-set

  ```sql
  CREATE TABLE users (
      created_at TIMESTAMP DEFAULT NOW(),           -- When record created
      updated_at TIMESTAMP DEFAULT NOW(),           -- When last updated
      last_login TIMESTAMP                          -- Can be NULL (never logged in)
  );
  
  -- Query time ranges
  SELECT * FROM users WHERE created_at > NOW() - INTERVAL '30 days';
  SELECT * FROM users WHERE last_login < NOW() - INTERVAL '6 months';
  ```

- **`DATE`** - Date only, no time component
  - Use for: Birthdays, deadlines, dates when time doesn't matter
  - Example: User birthdate (9:45am birthday is same as 11:20pm)
  - Size: 4 bytes (saves space if time not needed)

  ```sql
  CREATE TABLE users (
      birthdate DATE,                 -- Just the date
      account_expiry_date DATE
  );
  ```

**JSON Type**:
- **`JSONB`** - Binary JSON (optimized for queries)
  - Use for: Flexible data, metadata, nested structures
  - Better than TEXT JSON (JSONB is indexed and queryable)
  - Supports: Objects, arrays, primitives

  ```sql
  CREATE TABLE users (
      metadata JSONB DEFAULT '{}'::jsonb    -- Flexible schema
  );
  
  -- Insert
  INSERT INTO users (email, metadata) VALUES (
      'user@example.com',
      '{"preferences": {"theme": "dark", "language": "en"}, "tags": ["vip", "beta"]}'::jsonb
  );
  
  -- Query JSONB
  SELECT * FROM users WHERE metadata -> 'preferences' ->> 'theme' = 'dark';
  SELECT * FROM users WHERE metadata @> '{"tags": ["vip"]}'::jsonb;
  ```

**Type Selection Summary**:

| Need | Type | Example |
|------|------|---------|
| Small integer | INTEGER | age, stock count |
| Huge count | BIGINT | total events, impressions |
| Auto ID | SERIAL/BIGSERIAL | Primary key |
| Money | DECIMAL(10,2) | Price, salary |
| Flag/Status | BOOLEAN | is_active, published |
| Timestamp | TIMESTAMP | created_at, updated_at |
| Date only | DATE | birthdate, deadline |
| Short text | VARCHAR(n) | email, name, username |
| Long text | TEXT | description, content, bio |
| Flexible | JSONB | metadata, preferences |

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
