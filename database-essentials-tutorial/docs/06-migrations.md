# Module 6: Database Migrations

## Why Migrations Exist

### The Problem

```python
# Version 1: Initial schema
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255))

# Version 2: Add username
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255))
    username = db.Column(db.String(50))  # New column

# How do you update production database?
# - Can't drop and recreate (lose data)
# - Can't manually ALTER TABLE (error-prone, not repeatable)
# - Need version control for schema changes
```

### What Migrations Solve

1. **Version control for database schema**
2. **Repeatable schema changes**
3. **Rollback capability**
4. **Team collaboration** (everyone applies same changes)
5. **Production safety** (test migrations before deploying)

## Alembic Fundamentals

### Installation

```bash
pip install alembic
```

### Initialization

```bash
# Initialize Alembic
cd backend
alembic init migrations

# Creates:
# migrations/
# ├── env.py          # Migration environment config
# ├── script.py.mako  # Migration template
# └── versions/       # Migration files
# alembic.ini         # Alembic configuration
```

### Configuration

```python
# alembic.ini
[alembic]
script_location = migrations
sqlalchemy.url = postgresql://user:password@localhost/dbname

# Or use environment variable
# sqlalchemy.url = driver://user:pass@localhost/dbname
```

```python
# migrations/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os

# Import your models
from app.db.postgres import db
from app.models import user, post, tag

# Get database URL from environment
config = context.config
config.set_main_option(
    'sqlalchemy.url',
    os.getenv('DATABASE_URL', 'postgresql://localhost/dbname')
)

# Set target metadata
target_metadata = db.metadata

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
```

### Creating Migrations

**Auto-generate migration**:
```bash
# Alembic compares models to database and generates migration
alembic revision --autogenerate -m "Add username to users"

# Creates: migrations/versions/abc123_add_username_to_users.py
```

**Manual migration**:
```bash
alembic revision -m "Create users table"
```

### Migration File Structure

```python
# migrations/versions/abc123_add_username_to_users.py
"""Add username to users

Revision ID: abc123
Revises: def456
Create Date: 2024-01-01 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision = 'abc123'
down_revision = 'def456'  # Previous migration
branch_labels = None
depends_on = None

def upgrade():
    # Apply changes
    op.add_column('users', sa.Column('username', sa.String(50), nullable=True))
    op.create_index('idx_users_username', 'users', ['username'])

def downgrade():
    # Revert changes
    op.drop_index('idx_users_username', 'users')
    op.drop_column('users', 'username')
```

### Applying Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade abc123

# Apply next migration
alembic upgrade +1

# Rollback one migration
alembic downgrade -1

# Rollback to specific migration
alembic downgrade def456

# Show current version
alembic current

# Show migration history
alembic history
```

## Safe Schema Evolution

### Adding Columns

```python
def upgrade():
    # Add nullable column first
    op.add_column('users', sa.Column('bio', sa.Text, nullable=True))
    
    # If you need NOT NULL:
    # 1. Add as nullable
    # 2. Populate data
    # 3. Make NOT NULL
    
    # Populate default values
    op.execute("UPDATE users SET bio = '' WHERE bio IS NULL")
    
    # Make NOT NULL
    op.alter_column('users', 'bio', nullable=False)
```

### Removing Columns

```python
def upgrade():
    # Safe: Drop column
    op.drop_column('users', 'old_field')

def downgrade():
    # Restore column
    op.add_column('users', sa.Column('old_field', sa.String(255)))
```

**Production warning**: Dropping columns loses data. Consider:
1. Stop using column in code
2. Deploy code
3. Wait (ensure no old code is running)
4. Drop column in migration

### Renaming Columns

```python
def upgrade():
    # PostgreSQL
    op.alter_column('users', 'old_name', new_column_name='new_name')

def downgrade():
    op.alter_column('users', 'new_name', new_column_name='old_name')
```

**Production pattern**: Rename in multiple steps:
1. Add new column
2. Copy data: `UPDATE users SET new_name = old_name`
3. Update code to use new column
4. Deploy
5. Drop old column

### Adding Indexes

```python
def upgrade():
    # Add index
    op.create_index('idx_users_email', 'users', ['email'])
    
    # Add unique index
    op.create_index('idx_users_username', 'users', ['username'], unique=True)
    
    # Add composite index
    op.create_index('idx_posts_user_created', 'posts', ['user_id', 'created_at'])
    
    # Add partial index (PostgreSQL)
    op.create_index(
        'idx_posts_published',
        'posts',
        ['published'],
        postgresql_where=sa.text('published = TRUE')
    )

def downgrade():
    op.drop_index('idx_users_email', 'users')
    op.drop_index('idx_users_username', 'users')
    op.drop_index('idx_posts_user_created', 'posts')
    op.drop_index('idx_posts_published', 'posts')
```

### Adding Foreign Keys

```python
def upgrade():
    # Add foreign key
    op.create_foreign_key(
        'fk_posts_user_id',  # Constraint name
        'posts',              # Source table
        'users',              # Target table
        ['user_id'],          # Source columns
        ['id'],               # Target columns
        ondelete='CASCADE'    # ON DELETE action
    )

def downgrade():
    op.drop_constraint('fk_posts_user_id', 'posts', type_='foreignkey')
```

### Data Migrations

```python
def upgrade():
    # Add column
    op.add_column('users', sa.Column('full_name', sa.String(255)))
    
    # Migrate data
    connection = op.get_bind()
    connection.execute(
        sa.text("UPDATE users SET full_name = first_name || ' ' || last_name")
    )
    
    # Drop old columns
    op.drop_column('users', 'first_name')
    op.drop_column('users', 'last_name')

def downgrade():
    # Add old columns
    op.add_column('users', sa.Column('first_name', sa.String(100)))
    op.add_column('users', sa.Column('last_name', sa.String(100)))
    
    # Migrate data back
    connection = op.get_bind()
    connection.execute(
        sa.text("""
            UPDATE users 
            SET first_name = SPLIT_PART(full_name, ' ', 1),
                last_name = SPLIT_PART(full_name, ' ', 2)
        """)
    )
    
    # Drop new column
    op.drop_column('users', 'full_name')
```

## Rollbacks and Failures

### Testing Migrations

```bash
# Test upgrade
alembic upgrade head

# Test downgrade
alembic downgrade -1

# Test full cycle
alembic upgrade head
alembic downgrade base
alembic upgrade head
```

### Handling Failed Migrations

```python
# If migration fails mid-way, Alembic marks it as failed
# Fix the migration file, then:

# Mark current version manually
alembic stamp head

# Or rollback and retry
alembic downgrade -1
# Fix migration
alembic upgrade +1
```

### Production Migration Strategy

**Step 1: Test locally**
```bash
# Create migration
alembic revision --autogenerate -m "Add feature"

# Test upgrade
alembic upgrade head

# Test downgrade
alembic downgrade -1

# Test upgrade again
alembic upgrade head
```

**Step 2: Test on staging**
```bash
# On staging server
git pull
alembic upgrade head
# Test application
```

**Step 3: Backup production**
```bash
# Backup database before migration
pg_dump dbname > backup_$(date +%Y%m%d_%H%M%S).sql
```

**Step 4: Apply to production**
```bash
# Apply migration
alembic upgrade head

# If it fails:
alembic downgrade -1
# Restore from backup if needed
psql dbname < backup_20240101_120000.sql
```

### Zero-Downtime Migrations

**Pattern: Backward-compatible changes**

```python
# Migration 1: Add new column (nullable)
def upgrade():
    op.add_column('users', sa.Column('new_field', sa.String(255), nullable=True))

# Deploy new code that writes to both old and new fields
# Wait for all old code to stop running

# Migration 2: Backfill data
def upgrade():
    op.execute("UPDATE users SET new_field = old_field WHERE new_field IS NULL")

# Migration 3: Make NOT NULL
def upgrade():
    op.alter_column('users', 'new_field', nullable=False)

# Migration 4: Drop old column
def upgrade():
    op.drop_column('users', 'old_field')
```

## Production Best Practices

### 1. Always Review Auto-Generated Migrations

```python
# Auto-generated migration might miss things
alembic revision --autogenerate -m "Update schema"

# ALWAYS review the generated file
# Check:
# - Are all changes correct?
# - Is downgrade() implemented?
# - Are indexes created?
# - Are foreign keys correct?
```

### 2. Keep Migrations Small

```python
# BAD: One huge migration
def upgrade():
    # 50 schema changes
    pass

# GOOD: Multiple small migrations
# Migration 1: Add users table
# Migration 2: Add posts table
# Migration 3: Add indexes
```

### 3. Never Edit Applied Migrations

```bash
# BAD: Edit migration that's already applied
# This breaks other developers' databases

# GOOD: Create new migration to fix issues
alembic revision -m "Fix previous migration"
```

### 4. Use Transactions

```python
# Alembic uses transactions by default
# If migration fails, changes are rolled back

# For large data migrations, consider batching:
def upgrade():
    connection = op.get_bind()
    
    # Process in batches
    batch_size = 1000
    offset = 0
    
    while True:
        result = connection.execute(
            sa.text(f"SELECT id FROM users LIMIT {batch_size} OFFSET {offset}")
        )
        rows = result.fetchall()
        
        if not rows:
            break
        
        # Process batch
        for row in rows:
            connection.execute(
                sa.text("UPDATE users SET processed = TRUE WHERE id = :id"),
                {'id': row[0]}
            )
        
        offset += batch_size
```

### 5. Document Complex Migrations

```python
"""Add username and migrate from email

This migration:
1. Adds username column
2. Generates usernames from email (part before @)
3. Ensures uniqueness by appending numbers if needed
4. Makes username NOT NULL after population

Revision ID: abc123
Revises: def456
Create Date: 2024-01-01 12:00:00
"""

def upgrade():
    # Implementation
    pass
```

---

## Module 6 Exam

### Multiple Choice Questions

1. What is the primary purpose of database migrations?
   a) Improve query performance
   b) Version control schema changes
   c) Backup data
   d) Optimize indexes

2. What does `alembic upgrade head` do?
   a) Creates a new migration
   b) Applies all pending migrations
   c) Rolls back all migrations
   d) Shows migration history

3. What should you do if a migration fails in production?
   a) Delete the migration file
   b) Edit the applied migration
   c) Rollback and fix the migration
   d) Drop the database

4. How should you add a NOT NULL column to a table with existing data?
   a) Add as NOT NULL directly
   b) Add as nullable, populate data, then make NOT NULL
   c) Drop table and recreate
   d) Use ALTER TABLE only

5. What is the safest way to rename a column in production?
   a) Use ALTER TABLE RENAME
   b) Add new column, copy data, update code, drop old column
   c) Drop and recreate table
   d) Edit the model and auto-generate migration

### Practical Design Tasks

**Task 1**: Write Alembic migrations for:
1. Creating a `users` table with email and password_hash
2. Adding a `username` column (must be unique and NOT NULL)
3. Creating a `posts` table with foreign key to users
4. Adding an index on `posts.created_at`

Include both upgrade() and downgrade() for each.

**Task 2**: You need to split the `full_name` column into `first_name` and `last_name`. Write a migration that:
1. Adds the new columns
2. Migrates existing data
3. Drops the old column
4. Handles edge cases (names with no space, multiple spaces)

### Incident Scenario

**Scenario**: You deployed a migration to production that adds a NOT NULL column without a default value:

```python
def upgrade():
    op.add_column('users', sa.Column('username', sa.String(50), nullable=False))
```

The migration fails because existing rows violate the NOT NULL constraint. The database is now in an inconsistent state.

**Questions**:
1. Why did the migration fail?
2. How do you recover from this?
3. What should the migration have done instead?
4. How do you prevent this in the future?
