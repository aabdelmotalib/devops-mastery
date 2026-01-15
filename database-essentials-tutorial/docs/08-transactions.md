# Module 8: Transactions and ACID

## Introduction

**Transactions are how databases keep data correct when things go wrong.** They're the foundation of reliability in production systems.

**What you'll master**:
- **ACID properties**: Atomicity, Consistency, Isolation, Durability
- **Isolation levels**: When transactions see each other's data
- **Locks and deadlocks**: What happens when transactions conflict
- **Transaction patterns**: Optimistic locking, pessimistic locking, idempotency
- **Production patterns**: Handling failures and retries

**Real-world stakes**:
- Without transactions: Database corruptions, lost money, data inconsistencies
- With transactions: Reliable systems that handle failures gracefully

---

## What ACID Actually Means in Practice

ACID is not just an acronym—it's a guarantee that your data stays correct even when systems fail.

### Atomicity

**Definition**: A transaction is all-or-nothing. Either all operations succeed, or all fail (rollback).

**Why it matters**:

```python
# BAD: Not atomic - LOSE MONEY
def transfer_funds(from_account, to_account, amount):
    print(f"Transferring ${amount}")
    
    # Step 1: Debit from_account
    from_account.balance -= amount
    db.session.commit()
    print(f"Debit done: {from_account.balance}")
    
    # What if server crashes HERE?
    # from_account is debited but to_account is not credited
    # $500 vanishes!
    
    # Step 2: Credit to_account
    to_account.balance += amount
    db.session.commit()
    print(f"Credit done: {to_account.balance}")

# SCENARIO: Server crashes between steps
# Before: Account A = $1000, Account B = $1000
# After crash: Account A = $500, Account B = $1000
# Result: $500 lost forever (audit nightmare!)

# GOOD: Atomic transaction
def transfer_funds(from_account, to_account, amount):
    try:
        from_account.balance -= amount
        to_account.balance += amount
        
        # Both changes committed together
        db.session.commit()
        print(f"Transfer complete: A=${from_account.balance}, B=${to_account.balance}")
        
    except Exception as e:
        # If anything fails: ROLLBACK everything
        db.session.rollback()
        print(f"Transfer failed, rolled back: {e}")
        raise

# SCENARIO: Server crashes during commit
# PostgreSQL handles the recovery using WAL (Write-Ahead Log)
# After restart: Either both changes exist, or neither
# No partial state possible!
```

**Key guarantee**: If `db.session.commit()` succeeds, all changes are saved. If it fails or crashes, none are.

### Consistency

**Definition**: Database moves from one valid state to another. Constraints are never violated.

**How it works**:

```python
# Database enforces constraints
class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    balance = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Constraint: Balance can't be negative
    __table_args__ = (
        db.CheckConstraint('balance >= 0', name='positive_balance'),
    )

# Trying to violate consistency
account = Account.query.get(1)
account.balance = -100  # INVALID!

try:
    db.session.commit()
except IntegrityError as e:
    # PostgreSQL PREVENTS the invalid state
    db.session.rollback()
    print(f"Consistency violation prevented: {e}")
    # Database still valid, never entered invalid state

# Real scenario: Overdraft protection
# User tries to withdraw more than balance
def withdraw(account_id, amount):
    account = Account.query.with_for_update().get(account_id)  # Lock the row
    
    if account.balance < amount:
        raise ValueError("Insufficient funds")
    
    account.balance -= amount
    db.session.commit()
    # PostgreSQL guarantees: balance never goes negative
```

### Isolation

**Definition**: Concurrent transactions don't see each other's partial changes.

**Real-world problem**:

```python
# Scenario: Two users try to book the last seat simultaneously

# User A's request (in transaction)
def book_seat(user_id, seat_id):
    seat = Seat.query.get(seat_id)
    if seat.available:
        print(f"User {user_id}: Seat is available")
        seat.available = False
        db.session.commit()
        return "Booked!"
    return "Not available"

# At time T=1ms: Both User A and B query the seat
# User A: seat.available = True
# User B: seat.available = True (B doesn't see A's pending change yet)

# At time T=2ms: User A commits
# User B doesn't see this yet (isolation!)

# At time T=3ms: User B commits
# Result: Both users booked the same seat! (DISASTER!)
```

**Fix: Row-level locks**
```python
def book_seat_safe(user_id, seat_id):
    # Lock the row BEFORE checking (prevents other transactions from reading)
    seat = Seat.query.filter_by(id=seat_id).with_for_update().first()
    
    if seat.available:
        seat.available = False
        db.session.commit()
        return "Booked!"
    return "Not available"

# Timeline with locks:
# T=1ms: User A locks seat (User B waits)
# T=2ms: User A checks available=True
# T=3ms: User A books and commits (lock released)
# T=4ms: User B gets lock, checks available=False
# T=5ms: User B returns "Not available"
# Result: Only one user books the seat (CORRECT!)
```

### Durability

**Definition**: Once committed, data persists even if system crashes.

**How PostgreSQL ensures it**:

1. **Write-Ahead Logging (WAL)**: Before modifying a page on disk, write intent to log
2. **Fsync to disk**: Sync log to physical disk before returning to application
3. **Crash recovery**: On restart, replay WAL log to recover state

**You don't need to do anything**—PostgreSQL handles this automatically. Your data is safe.

```python
# Safe transaction
account = Account.query.get(1)
account.balance += 100
db.session.commit()  # Returns immediately (data safely persisted)

# Even if:
# - Server crashes 1ms later
# - Power loss
# - Disk fails
# - Meteorite hits the datacenter
#
# That $100 deposit is saved (in the log files)
# Recovery process will replay it
```


**Definition**: Database moves from one valid state to another

**Example: Constraints enforced**
```python
# Database ensures constraints
class Account(db.Model):
    balance = db.Column(db.Decimal(10, 2), nullable=False)
    
    __table_args__ = (
        db.CheckConstraint('balance >= 0', name='positive_balance'),
    )

# Transaction fails if constraint violated
account.balance = -100  # Violates constraint
db.session.commit()  # Raises IntegrityError
```

### Isolation

**Definition**: Concurrent transactions don't interfere with each other

**Example: Race condition**
```python
# Two users try to book the last seat simultaneously

# User A:
seat = Seat.query.get(1)  # available = True
seat.available = False
db.session.commit()

# User B (at same time):
seat = Seat.query.get(1)  # available = True (before A commits)
seat.available = False
db.session.commit()

# Both think they booked the seat!
```

**Fix: Use isolation**
```python
# Use SELECT FOR UPDATE (row-level lock)
seat = Seat.query.filter_by(id=1).with_for_update().first()
if seat.available:
    seat.available = False
    db.session.commit()
else:
    raise ValueError("Seat already booked")
```

### Durability

**Definition**: Committed data persists even after crashes

**How PostgreSQL ensures durability**:
1. Write-Ahead Logging (WAL)
2. Fsync to disk before commit
3. Crash recovery from WAL

**You don't need to do anything** - PostgreSQL handles this.

## Isolation Levels

### Read Uncommitted

**Behavior**: Can read uncommitted changes from other transactions

**Problem**: Dirty reads

**PostgreSQL**: Not supported (treated as Read Committed)

### Read Committed (Default)

**Behavior**: Only see committed changes

**Example**:
```python
# Transaction A
user = User.query.get(1)
user.balance = 100
# Not committed yet

# Transaction B (different connection)
user = User.query.get(1)
print(user.balance)  # Still old value (not 100)

# Transaction A
db.session.commit()

# Transaction B
user = User.query.get(1)
print(user.balance)  # Now 100
```

**Problem**: Non-repeatable reads
```python
# Transaction A
user = User.query.get(1)
print(user.balance)  # 100

# Transaction B commits change
# user.balance = 200

# Transaction A (same transaction)
user = User.query.get(1)
print(user.balance)  # 200 (changed!)
```

### Repeatable Read

**Behavior**: See snapshot of database at transaction start

**Example**:
```python
# Set isolation level
from sqlalchemy import create_engine

engine = create_engine(
    'postgresql://...',
    isolation_level='REPEATABLE READ'
)

# Transaction A
user = User.query.get(1)
print(user.balance)  # 100

# Transaction B commits change
# user.balance = 200

# Transaction A (same transaction)
user = User.query.get(1)
print(user.balance)  # Still 100 (snapshot)
```

**Problem**: Phantom reads (new rows)
```python
# Transaction A
count = User.query.count()  # 100

# Transaction B inserts new user
# db.session.add(User(...))
# db.session.commit()

# Transaction A
count = User.query.count()  # 101 (phantom row)
```

### Serializable

**Behavior**: Transactions execute as if serial (one after another)

**Example**:
```python
# Set isolation level
engine = create_engine(
    'postgresql://...',
    isolation_level='SERIALIZABLE'
)

# Prevents all anomalies but may cause serialization errors
try:
    # Transaction logic
    db.session.commit()
except SerializationError:
    db.session.rollback()
    # Retry transaction
```

**Trade-off**: Safest but slowest, may require retries

### Choosing Isolation Level

**Read Committed** (default): Use for most cases
- Good performance
- Prevents dirty reads
- Acceptable for most applications

**Repeatable Read**: Use when you need consistent snapshot
- Analytics queries
- Reports
- Batch processing

**Serializable**: Use for critical operations
- Financial transactions
- Inventory management
- Anything requiring strict consistency

## Locks and Deadlocks

### Row-Level Locks

```python
# SELECT FOR UPDATE: Exclusive lock
seat = Seat.query.filter_by(id=1).with_for_update().first()
# Other transactions wait until this transaction commits

# SELECT FOR SHARE: Shared lock
seat = Seat.query.filter_by(id=1).with_for_update(read=True).first()
# Other transactions can read but not update
```

### Lock Timeout

```python
# Set lock timeout
db.session.execute("SET LOCAL lock_timeout = '5s'")

try:
    seat = Seat.query.filter_by(id=1).with_for_update().first()
except OperationalError:
    # Lock timeout exceeded
    db.session.rollback()
    raise ValueError("Resource is locked")
```

### Deadlocks

**What is a deadlock?**

```python
# Transaction A:
account1 = Account.query.filter_by(id=1).with_for_update().first()
account2 = Account.query.filter_by(id=2).with_for_update().first()

# Transaction B (at same time):
account2 = Account.query.filter_by(id=2).with_for_update().first()  # Locks account 2
account1 = Account.query.filter_by(id=1).with_for_update().first()  # Waits for account 1

# Deadlock! A waits for B, B waits for A
```

**PostgreSQL detects and aborts one transaction**:
```
ERROR: deadlock detected
DETAIL: Process 1234 waits for ShareLock on transaction 5678
```

**Preventing deadlocks**:

1. **Always acquire locks in same order**
```python
# GOOD: Always lock lower ID first
def transfer(from_id, to_id, amount):
    ids = sorted([from_id, to_id])
    account1 = Account.query.filter_by(id=ids[0]).with_for_update().first()
    account2 = Account.query.filter_by(id=ids[1]).with_for_update().first()
    # Process transfer
```

2. **Keep transactions short**
```python
# BAD: Long transaction
with db.session.begin():
    user = User.query.with_for_update().first()
    time.sleep(10)  # Holds lock for 10 seconds
    user.balance += 100

# GOOD: Short transaction
user_id = get_user_id()
# Do slow work here
with db.session.begin():
    user = User.query.filter_by(id=user_id).with_for_update().first()
    user.balance += 100
```

3. **Retry on deadlock**
```python
from sqlalchemy.exc import OperationalError

def transfer_with_retry(from_id, to_id, amount, max_retries=3):
    for attempt in range(max_retries):
        try:
            transfer(from_id, to_id, amount)
            return
        except OperationalError as e:
            if 'deadlock detected' in str(e):
                db.session.rollback()
                if attempt == max_retries - 1:
                    raise
                time.sleep(0.1 * (2 ** attempt))  # Exponential backoff
            else:
                raise
```

## When Transactions Hurt Performance

### Problem 1: Long Transactions

```python
# BAD: Long transaction blocks other queries
with db.session.begin():
    users = User.query.all()
    for user in users:
        # Expensive operation
        process_user(user)
        time.sleep(1)
    # Transaction held for minutes

# GOOD: Short transactions
users = User.query.all()
for user in users:
    process_user(user)
    # Commit each user separately
    with db.session.begin():
        db.session.add(user)
```

### Problem 2: Unnecessary Transactions

```python
# BAD: Transaction for read-only query
with db.session.begin():
    users = User.query.all()  # Read-only, no need for transaction

# GOOD: No transaction
users = User.query.all()
```

### Problem 3: Too Many Small Transactions

```python
# BAD: 1000 separate transactions
for data in user_data:
    user = User(**data)
    db.session.add(user)
    db.session.commit()  # Slow!

# GOOD: Batch in single transaction
for data in user_data:
    user = User(**data)
    db.session.add(user)
db.session.commit()  # Fast!
```

## Transaction Patterns

### Pattern 1: Optimistic Locking

```python
class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Decimal(10, 2))
    version = db.Column(db.Integer, default=0)  # Version number

def withdraw(account_id, amount):
    account = Account.query.get(account_id)
    old_version = account.version
    
    # Check balance
    if account.balance < amount:
        raise ValueError("Insufficient funds")
    
    # Update
    account.balance -= amount
    account.version += 1
    
    # Commit with version check
    rows_updated = db.session.query(Account)\
        .filter_by(id=account_id, version=old_version)\
        .update({'balance': account.balance, 'version': account.version})
    
    if rows_updated == 0:
        db.session.rollback()
        raise ValueError("Account was modified by another transaction")
    
    db.session.commit()
```

### Pattern 2: Pessimistic Locking

```python
def withdraw(account_id, amount):
    # Lock row immediately
    account = Account.query.filter_by(id=account_id).with_for_update().first()
    
    if account.balance < amount:
        raise ValueError("Insufficient funds")
    
    account.balance -= amount
    db.session.commit()
```

### Pattern 3: Idempotent Operations

```python
# Ensure operation can be retried safely
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    idempotency_key = db.Column(db.String(255), unique=True)
    amount = db.Column(db.Decimal(10, 2))
    status = db.Column(db.String(20))

def process_payment(idempotency_key, amount):
    # Check if already processed
    existing = Payment.query.filter_by(idempotency_key=idempotency_key).first()
    if existing:
        return existing  # Already processed
    
    # Process payment
    payment = Payment(
        idempotency_key=idempotency_key,
        amount=amount,
        status='completed'
    )
    db.session.add(payment)
    db.session.commit()
    
    return payment
```

### Pattern 4: Two-Phase Commit (Distributed Transactions)

```python
# For transactions across multiple databases
from sqlalchemy import create_engine

pg_engine = create_engine('postgresql://...')
mongo_client = MongoClient('mongodb://...')

def distributed_transaction():
    # Phase 1: Prepare
    pg_conn = pg_engine.connect()
    pg_trans = pg_conn.begin()
    
    try:
        # PostgreSQL operations
        pg_conn.execute("UPDATE accounts SET balance = balance - 100 WHERE id = 1")
        
        # MongoDB operations
        mongo_client.db.logs.insert_one({'action': 'transfer', 'amount': 100})
        
        # Phase 2: Commit
        pg_trans.commit()
        
    except Exception as e:
        # Rollback both
        pg_trans.rollback()
        # MongoDB doesn't support transactions across collections in older versions
        # Use compensating transactions or saga pattern
        raise
```

## Production Best Practices

### 1. Keep Transactions Short

```python
# BAD
with db.session.begin():
    # Query
    users = User.query.all()
    # Expensive processing
    results = [expensive_operation(u) for u in users]
    # Update
    for user, result in zip(users, results):
        user.processed = result

# GOOD
users = User.query.all()
results = [expensive_operation(u) for u in users]

with db.session.begin():
    for user, result in zip(users, results):
        user.processed = result
```

### 2. Handle Errors Properly

```python
def safe_transaction():
    try:
        # Transaction logic
        user = User.query.get(1)
        user.balance += 100
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ValueError("Constraint violation")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Transaction failed: {e}")
        raise
```

### 3. Use Appropriate Isolation Level

```python
# Default (Read Committed) for most operations
user = User.query.get(1)

# Repeatable Read for reports
db.session.connection(execution_options={'isolation_level': 'REPEATABLE READ'})
report_data = generate_report()

# Serializable for critical operations
db.session.connection(execution_options={'isolation_level': 'SERIALIZABLE'})
process_payment()
```

### 4. Monitor Transaction Duration

```python
import time

@app.before_request
def before_request():
    g.transaction_start = time.time()

@app.after_request
def after_request(response):
    if hasattr(g, 'transaction_start'):
        duration = time.time() - g.transaction_start
        if duration > 1.0:
            logger.warning(f"Long transaction: {duration:.2f}s")
    return response
```

---

## Module 8 Exam

### Multiple Choice Questions

1. What does the "A" in ACID stand for and what does it mean?
   a) Atomicity - all operations succeed or all fail
   b) Availability - database is always accessible
   c) Authentication - users are verified
   d) Accuracy - data is correct

2. What is the default isolation level in PostgreSQL?
   a) Read Uncommitted
   b) Read Committed
   c) Repeatable Read
   d) Serializable

3. What is a deadlock?
   a) A database crash
   b) Two transactions waiting for each other's locks
   c) A slow query
   d) A connection timeout

4. When should you use SELECT FOR UPDATE?
   a) For all SELECT queries
   b) When you need to lock rows for update
   c) Only for DELETE operations
   d) Never - it's deprecated

5. What is optimistic locking?
   a) Assuming transactions will succeed
   b) Using version numbers to detect conflicts
   c) Not using locks at all
   d) Locking entire tables

### Practical Design Tasks

**Task 1**: Implement a seat booking system that:
- Prevents double-booking (two users booking same seat)
- Handles concurrent requests
- Uses appropriate locking strategy
- Handles errors gracefully

Provide Python code with SQLAlchemy.

**Task 2**: Design a transaction-safe inventory system for an e-commerce site that:
- Decrements stock when order is placed
- Prevents overselling (stock going negative)
- Handles concurrent orders
- Supports rollback if payment fails

Include database schema and Python code.

### Incident Scenario

**Scenario**: Your production database is experiencing frequent deadlocks. Investigation reveals:
- Deadlocks occur during order processing
- Multiple orders are processed simultaneously
- Each order updates inventory for multiple products
- Products are locked in random order based on cart contents

**Questions**:
1. Why are deadlocks occurring?
2. How would you prevent them?
3. What code changes are needed?
4. How would you handle deadlocks that still occur?
