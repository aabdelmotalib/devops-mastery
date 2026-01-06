# Module 3: Software Architecture Basics

So far, you've learned to think like a programmer and write code. But code by itself isn't enough—**real software** is organized.

Architecture is about asking: "How do I organize code so it's:**
- Easy to understand
- Easy to change
- Easy to test
- Easy to scale

This module is where you move from writing scripts to understanding how real applications are built.

---

## Script vs. Program vs. Application

Understanding the difference helps you know when and how to organize code.

### **Script** - A Simple One-Off Solution
```python
# A script: solves one specific problem, runs once

import csv

# Read file
with open("sales.csv") as f:
    reader = csv.DictReader(f)
    data = list(reader)

# Process
total_sales = sum(float(row["amount"]) for row in data)

# Output
print(f"Total sales: ${total_sales}")
```

**Characteristics:**
- Linear flow (one thing after another)
- Single purpose
- Meant to be run once and forgotten
- No organization needed

### **Program** - Organized Code That Does Something Useful
```python
# A program: solves a problem, organized with functions and logic

import csv
from pathlib import Path

def load_sales_data(filename):
    """Load sales data from CSV"""
    with open(filename) as f:
        return list(csv.DictReader(f))

def calculate_total(data):
    """Calculate total sales"""
    return sum(float(row["amount"]) for row in data)

def format_currency(amount):
    """Format amount as currency"""
    return f"${amount:.2f}"

def main():
    """Main program logic"""
    data = load_sales_data("sales.csv")
    total = calculate_total(data)
    print(f"Total sales: {format_currency(total)}")

if __name__ == "__main__":
    main()
```

**Characteristics:**
- Organized into functions
- Reusable pieces
- Readable and maintainable
- Can be understood by others

### **Application** - Complex Software That Solves Multiple Related Problems
```python
# An application: large system with users, data, persistence, interaction

# Structure:
# app/
#   __init__.py
#   main.py
#   models/
#     __init__.py
#     sales.py
#     user.py
#   services/
#     __init__.py
#     analytics.py
#     reporting.py
#   routes/
#     __init__.py
#     sales_routes.py
#   database/
#     __init__.py
#     connection.py
#     migrations.py

# From app/models/sales.py
class Sale:
    def __init__(self, product, amount, date):
        self.product = product
        self.amount = amount
        self.date = date
    
    def save_to_database(self):
        # Persist to database
        pass

# From app/services/analytics.py
class SalesAnalytics:
    def calculate_total(self, date_range):
        # Query database
        # Aggregate data
        # Return results
        pass

# From app/routes/sales_routes.py
def handle_sales_report(request):
    analytics = SalesAnalytics()
    total = analytics.calculate_total(request.date_range)
    return format_response(total)
```

**Characteristics:**
- Multiple components working together
- Organized into layers (UI, logic, data)
- Persistent data storage
- Used by multiple users
- Meant to evolve and scale

---

## Separation of Concerns

The biggest principle in architecture: **each piece should have ONE job**.

### Example: Without Separation

```python
# Bad: one function does everything
def process_order(order_id):
    # Get from database
    connection = connect_to_database()
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM orders WHERE id = {order_id}")
    order = cursor.fetchone()
    connection.close()
    
    # Calculate total
    subtotal = order["price"] * order["quantity"]
    tax = subtotal * 0.08
    total = subtotal + tax
    
    # Save to database
    connection = connect_to_database()
    cursor = connection.cursor()
    cursor.execute(f"UPDATE orders SET total = {total} WHERE id = {order_id}")
    connection.commit()
    connection.close()
    
    # Send email
    email_service = EmailService()
    email_service.send(order["customer_email"], 
                      f"Order total: ${total}")
    
    # Log transaction
    log_file = open("transactions.log", "a")
    log_file.write(f"Order {order_id}: {total}\n")
    log_file.close()
    
    return total
```

**Problems:**
- Hard to test (needs real database, email service, file system)
- Hard to change (touching one part breaks others)
- Hard to read (too much happening)
- Can't reuse pieces

### Example: With Separation

```python
# Good: separate concerns into different functions

def process_order(order_id):
    """Main logic: coordinate other pieces"""
    order = get_order(order_id)
    total = calculate_order_total(order)
    save_order_total(order_id, total)
    notify_customer(order, total)
    log_transaction(order_id, total)
    return total

def get_order(order_id):
    """Database concern: fetch data"""
    # Only deals with database
    pass

def calculate_order_total(order):
    """Business logic concern: calculate"""
    # Only does math
    subtotal = order["price"] * order["quantity"]
    tax = subtotal * 0.08
    return subtotal + tax

def save_order_total(order_id, total):
    """Database concern: persist data"""
    # Only writes to database
    pass

def notify_customer(order, total):
    """Communication concern: send email"""
    # Only sends email
    pass

def log_transaction(order_id, total):
    """Logging concern: record event"""
    # Only writes to log
    pass
```

**Benefits:**
- Easy to test each piece independently
- Easy to change (modify one concern without affecting others)
- Easy to read (each function is small and focused)
- Easy to reuse (`calculate_order_total` can be used anywhere)

---

## Layers in Architecture

Real applications are organized into **layers**. Think of a sandwich: each layer has a specific job.

### **Three-Layer Architecture**

#### **Presentation Layer (UI)**
- What users interact with
- Displays information
- Captures user input
- Doesn't contain business logic

```python
# Simple example: command-line UI
def show_menu():
    print("=== Sales System ===")
    print("1. Add Sale")
    print("2. View Total Sales")
    print("3. Exit")

def get_user_choice():
    choice = input("Choose option: ")
    return choice
```

#### **Business Logic Layer**
- The rules of your system
- Calculations, decisions, workflows
- Doesn't know about UI or database
- Reusable from anywhere

```python
def calculate_sales_total(sales_list):
    """Business rule: sum all sales"""
    return sum(sale["amount"] for sale in sales_list)

def apply_discount(amount, discount_percent):
    """Business rule: calculate discount"""
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Invalid discount")
    return amount * (1 - discount_percent / 100)
```

#### **Data Layer**
- Reads and writes data
- Talks to database
- Doesn't contain business logic
- Doesn't know about UI

```python
def get_all_sales():
    """Data access: fetch from database"""
    connection = connect_to_database()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM sales")
    data = cursor.fetchall()
    connection.close()
    return data

def save_sale(sale):
    """Data access: write to database"""
    connection = connect_to_database()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO sales VALUES (?)", (sale,))
    connection.commit()
    connection.close()
```

### How Layers Work Together

```
User Input
    ↓
Presentation Layer (UI): "Get user input"
    ↓
Business Logic Layer: "Apply business rules"
    ↓
Data Layer: "Read/write from database"
    ↓
Database
    ↓
Data Layer: "Return data"
    ↓
Business Logic Layer: "Process data"
    ↓
Presentation Layer: "Display to user"
    ↓
User sees output
```

---

## Common Architectural Patterns

### **1. MVC (Model-View-Controller)**

A widely-used pattern that separates presentation, logic, and data.

**Model** = Data and business logic
```python
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
    
    def validate_email(self):
        return "@" in self.email
```

**View** = What the user sees
```python
def display_user(user):
    print(f"Name: {user.name}")
    print(f"Email: {user.email}")
```

**Controller** = Handles user input and coordinates
```python
def create_user_workflow():
    # Get input from user
    name = input("Enter name: ")
    email = input("Enter email: ")
    
    # Create model
    user = User(name, email)
    
    # Validate
    if not user.validate_email():
        print("Invalid email")
        return
    
    # Save
    save_to_database(user)
    
    # Display
    display_user(user)
```

### **2. Client-Server Model**

Two separate pieces: **client** (requests) and **server** (provides).

```
Client (Browser/App)
    ↓
Request: "Get user #5"
    ↓
Server (Web Server)
    ↓
Database: Get user #5
    ↓
Response: User data
    ↓
Client displays data
```

**Why separate:**
- Client can be web, mobile, desktop
- Server can be upgraded without changing clients
- Multiple clients can use same server
- Each can scale independently

### **3. Microservices**

Instead of one big application, split into small, focused services.

```
Monolith (one big application):
┌─────────────────────┐
│ User Service        │
│ Product Service     │
│ Order Service       │
│ Payment Service     │
│ Shared Database     │
└─────────────────────┘

Microservices (small focused apps):
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ User Service │  │ Product Svc  │  │ Order Svc    │  │ Payment Svc  │
│ Own DB       │  │ Own DB       │  │ Own DB       │  │ Own DB       │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
      ↓                   ↓                 ↓                 ↓
    API Calls / Message Queue / Direct Communication
```

---

## APIs: How Pieces Talk

An **API** (Application Programming Interface) is a contract for communication between pieces of code or systems.

### **Internal API** - How your code talks to itself

```python
# API: "Here's how to use the sales system"

def get_total_sales(date_from, date_to):
    """
    Get total sales in date range
    
    Args:
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
    
    Returns:
        Float: total sales amount
    
    Raises:
        ValueError: if dates are invalid
    """
    # Implementation
    pass

# How to use it:
total = get_total_sales("2024-01-01", "2024-01-31")
print(f"Total: ${total}")
```

### **External API** - How other systems talk to yours

```python
# Your application provides a web API
# Other applications can call it over HTTP

# Request: GET /api/sales?from=2024-01-01&to=2024-01-31
# Response: {"total": 15000.00, "count": 42}
```

### API Contract

An API is a **promise**:
- "I'll accept these inputs"
- "I'll return data in this format"
- "If something goes wrong, I'll return this error"

Breaking the contract breaks other code that depends on you.

```python
# Original API
def get_user_by_id(user_id):
    return {"name": "Alice", "email": "alice@example.com"}

# WRONG: Changed what we return
def get_user_by_id(user_id):
    return "Alice"  # Now it's a string, not a dict!

# Code that uses this breaks:
user = get_user_by_id(5)
print(user["email"])  # Error! Can't index a string
```

---

## Software Design Principles

### **DRY (Don't Repeat Yourself)**

Write code once, reuse it everywhere.

```python
# Bad: repeated code
def format_user_name(first, last):
    return f"{first[0].upper()}{first[1:].lower()} {last[0].upper()}{last[1:].lower()}"

def format_product_name(first, last):
    return f"{first[0].upper()}{first[1:].lower()} {last[0].upper()}{last[1:].lower()}"

# Good: one function, reused
def format_name(first, last):
    return f"{first[0].upper()}{first[1:].lower()} {last[0].upper()}{last[1:].lower()}"

user_name = format_name(user_first, user_last)
product_name = format_name(product_first, product_last)
```

### **SOLID Principles** (Advanced, introduced here)

**Single Responsibility** - One class, one reason to change
```python
# Bad: User class does too much
class User:
    def load_from_database(self): pass
    def save_to_database(self): pass
    def send_email(self): pass
    def validate_email(self): pass

# Good: separate classes
class User:
    def __init__(self, name, email): pass

class UserRepository:  # Handles data
    def load(self, user_id): pass
    def save(self, user): pass

class EmailService:  # Handles email
    def send(self, email): pass

class UserValidator:  # Handles validation
    def validate_email(self, email): pass
```

**Open/Closed** - Open for extension, closed for modification
```python
# Create a plugin system: easy to add new features without changing existing code
class PaymentProcessor:
    def process(self, payment):
        pass

class CreditCardProcessor(PaymentProcessor):
    def process(self, payment):
        # Process credit card
        pass

class PayPalProcessor(PaymentProcessor):
    def process(self, payment):
        # Process PayPal
        pass

# Add new payment type? Just create a new class, don't modify existing code
```

---

## Exercises

### Exercise 1: Identify Layers
Look at a simple application you use (like an email client, note app, etc.). Identify:
1. Presentation layer (what you see)
2. Business logic (what happens)
3. Data layer (where information is stored)

### Exercise 2: Refactor Code
Take this script and organize it into layers:
```python
# Current: everything mixed together
import json

data = json.load(open("users.json"))
for user in data:
    if user["age"] >= 18:
        print(f"Email: {user['email']}")
        print(f"Status: Active")
```

Your task:
1. Separate data loading
2. Separate business logic (age check)
3. Separate display

### Exercise 3: Design an API
Design an API for a "student grade tracker":
1. What inputs does it need?
2. What does it return?
3. What errors might occur?

### Exercise 4: Separation of Concerns
Identify concerns in this code and separate them:
```python
def process_student_grades(csv_filename):
    # Read file
    import csv
    with open(csv_filename) as f:
        reader = csv.DictReader(f)
        students = list(reader)
    
    # Calculate averages
    for student in students:
        total = sum(float(g) for g in student["grades"].split(","))
        average = total / len(student["grades"].split(","))
        student["average"] = average
    
    # Save to database
    import sqlite3
    conn = sqlite3.connect("grades.db")
    cursor = conn.cursor()
    for student in students:
        cursor.execute(f"INSERT INTO students VALUES ('{student['name']}', {student['average']})")
    conn.commit()
    conn.close()
    
    # Print report
    print("=== Grade Report ===")
    for student in students:
        print(f"{student['name']}: {student['average']:.2f}")
```

---

## Key Takeaways

✅ **Real software is organized, not just written**

✅ **Scripts are simple; programs are organized; applications are complex systems**

✅ **Separation of concerns makes code manageable**

✅ **Layers separate presentation, logic, and data**

✅ **Patterns like MVC and client-server solve common problems**

✅ **APIs are contracts for communication**

✅ **Good design makes code easy to change**

---

## What's Next?

Now you understand how software is structured. Let's learn **how to think** like an engineer making these decisions.

→ **[Module 4: Thinking Like an Engineer](04-thinking-like-an-engineer.md)**

