# Module 0: Prerequisites & Coding Basics

This section covers the foundational concepts you need before diving into Flask. If you're already comfortable with Python and basic web concepts, you can skip to Module 1.

## Part 1: What is Programming?

### The Basics

Programming is giving instructions to a computer. Think of it like cooking:
- **Recipe** = Code (instructions)
- **Ingredients** = Data (information to work with)
- **Chef** = Programming Language (how you write instructions)
- **Cooked Dish** = Output (what the program produces)

### Why Python?

Python is chosen for web development because:

1. **Readable**: Code looks like English
   ```python
   # Easy to understand what this does
   user_age = 25
   if user_age >= 18:
       print("You are an adult")
   ```

2. **Fast to write**: Less boilerplate, more focus on logic
3. **Powerful libraries**: Rich ecosystem for web, data, and automation
4. **Job market**: High demand for Python developers
5. **Beginner-friendly**: Gentle learning curve

---

## Part 2: Python Fundamentals

### 2.1 Variables and Data Types

Variables store information. Think of them as labeled containers.

```python
# Strings (text)
name = "Alice"
greeting = 'Hello'

# Numbers
age = 25              # Integer (whole number)
height = 5.8          # Float (decimal number)
price = 19.99

# Booleans (True/False)
is_student = True
is_developer = False

# Collections
numbers = [1, 2, 3, 4, 5]          # List (ordered, changeable)
unique_items = {1, 2, 3}            # Set (unique items only)
person = {"name": "Bob", "age": 30} # Dictionary (key-value pairs)
```

**Why this matters for Flask:**
- When users send data to your API, it comes in different formats
- You need to handle strings (usernames), numbers (ages), and collections (lists of products)

### 2.2 Basic Operations

```python
# Math
total = 10 + 5        # 15
difference = 10 - 3   # 7
product = 4 * 5       # 20
division = 20 / 4     # 5.0
remainder = 10 % 3    # 1

# String operations
message = "Hello" + " " + "World"  # "Hello World"
repeated = "Ha" * 3                # "HaHaHa"

# Comparisons (return True or False)
5 > 3          # True
10 == 10       # True
age >= 18      # Depends on age value
name != "Bob"  # True if name is not "Bob"
```

### 2.3 Control Flow: Making Decisions

Your program needs to make decisions based on conditions.

```python
# IF statement
score = 85

if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 70:
    grade = "C"
else:
    grade = "F"

print(f"You got a {grade}")
```

**In Flask context:**
```python
# Example: Process user login request
from flask import Flask, request

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    
    # Decision making
    if not username or not password:
        return {"error": "Missing credentials"}, 400
    elif username == "admin" and password == "secret":
        return {"message": "Login successful"}, 200
    else:
        return {"error": "Invalid credentials"}, 401
```

### 2.4 Loops: Repeating Actions

```python
# FOR loop - iterate through a collection
fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    print(fruit)

# FOR loop with range
for i in range(5):  # 0, 1, 2, 3, 4
    print(i)

# WHILE loop - repeat while condition is true
count = 0
while count < 5:
    print(count)
    count += 1

# List comprehension (Python-specific)
squares = [x**2 for x in range(5)]  # [0, 1, 4, 9, 16]
```

**In Flask context:**
```python
# Example: Process a list of orders
from flask import Flask, jsonify

@app.route('/orders')
def get_orders():
    orders = [
        {"id": 1, "status": "completed"},
        {"id": 2, "status": "pending"},
        {"id": 3, "status": "shipped"}
    ]
    
    # Filter pending orders
    pending = [order for order in orders if order["status"] == "pending"]
    
    return jsonify(pending)
```

### 2.5 Functions: Reusable Code

Functions let you write code once and use it many times.

```python
# Define a function
def greet(name, greeting="Hello"):
    """
    Greet someone.
    
    Args:
        name (str): Person's name
        greeting (str): Custom greeting (optional)
    
    Returns:
        str: Greeting message
    """
    return f"{greeting}, {name}!"

# Use the function
print(greet("Alice"))              # "Hello, Alice!"
print(greet("Bob", "Hi"))          # "Hi, Bob!"

# Function that does calculations
def calculate_discount(price, discount_percent):
    discount_amount = price * (discount_percent / 100)
    return price - discount_amount

final_price = calculate_discount(100, 20)  # 80.0
```

**In Flask context:**
```python
# Organize your Flask code with functions
from flask import Flask, request, jsonify

app = Flask(__name__)

def validate_email(email):
    """Check if email looks valid"""
    return "@" in email and "." in email

def hash_password(password):
    """Hash a password for security"""
    # Simplified - use proper libraries in production
    return f"hashed_{password}"

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    
    if not validate_email(data.get('email')):
        return {"error": "Invalid email"}, 400
    
    hashed = hash_password(data.get('password'))
    return {"message": "User created"}, 201
```

### 2.6 Objects and Classes

Objects bundle data and functions together. Like a blueprint for creating things.

```python
# Define a class (blueprint)
class User:
    def __init__(self, name, email, age):
        """Initialize when creating a User object"""
        self.name = name
        self.email = email
        self.age = age
    
    def get_info(self):
        """Method: function inside a class"""
        return f"{self.name} ({self.email})"
    
    def is_adult(self):
        """Check if user is 18+"""
        return self.age >= 18

# Create objects (instances of the class)
user1 = User("Alice", "alice@example.com", 25)
user2 = User("Charlie", "charlie@example.com", 17)

print(user1.get_info())      # "Alice (alice@example.com)"
print(user1.is_adult())       # True
print(user2.is_adult())       # False
```

**In Flask context:**
```python
# You'll create classes to represent your data models
from flask import Flask
from datetime import datetime

class Post:
    def __init__(self, id, title, content, author):
        self.id = id
        self.title = title
        self.content = content
        self.author = author
        self.created_at = datetime.now()
    
    def to_dict(self):
        """Convert to dictionary for JSON response"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "author": self.author,
            "created_at": self.created_at.isoformat()
        }

# Use in Flask
app = Flask(__name__)

@app.route('/posts/<int:post_id>')
def get_post(post_id):
    post = Post(post_id, "My Post", "Great content", "Alice")
    return post.to_dict()
```

### 2.7 Working with Lists and Dictionaries

These are crucial for handling data in web applications.

```python
# Lists - ordered collection
products = ["laptop", "phone", "tablet"]
print(products[0])           # "laptop" (first item)
print(products[-1])          # "tablet" (last item)

products.append("monitor")   # Add to end
products.remove("phone")     # Remove item
print(len(products))         # 3 (count items)

# Dictionaries - key-value pairs
person = {
    "name": "Alice",
    "age": 25,
    "email": "alice@example.com"
}

print(person["name"])        # "Alice"
person["age"] = 26           # Update value
person["city"] = "NYC"       # Add new key
print(person.keys())         # dict_keys(['name', 'age', 'email', 'city'])
print(person.values())       # dict_values(['Alice', 26, 'alice@example.com', 'NYC'])
```

**In Flask context:**
```python
# JSON is basically dictionaries in Flask
from flask import Flask, jsonify, request

app = Flask(__name__)

# Sample data
users = [
    {"id": 1, "name": "Alice", "role": "admin"},
    {"id": 2, "name": "Bob", "role": "user"},
    {"id": 3, "name": "Charlie", "role": "user"}
]

@app.route('/users')
def get_users():
    return jsonify(users)

@app.route('/users', methods=['POST'])
def create_user():
    new_user = request.json
    new_user["id"] = len(users) + 1
    users.append(new_user)
    return jsonify(new_user), 201
```

---

## Part 3: Understanding the Web

### 3.1 HTTP: How the Web Works

The web runs on HTTP (HyperText Transfer Protocol). It's a conversation between a **client** and a **server**.

```
Client                              Server
  |                                  |
  |--- GET /api/users ------>       |
  |                                  |
  |    [Process request]              |
  |                                  |
  |<----- 200 OK + data -------------|
  |                                  |
```

### 3.2 HTTP Methods (Verbs)

These tell the server WHAT you want to do:

```
GET     - Retrieve data (read)
POST    - Create new data (write)
PUT     - Update existing data
DELETE  - Remove data
PATCH   - Partial update
```

### 3.3 HTTP Status Codes

These tell the client WHAT happened:

```
2xx - Success
  200 OK - Request succeeded
  201 Created - New resource created
  204 No Content - Success, no body to return

4xx - Client error
  400 Bad Request - Invalid request
  401 Unauthorized - Need authentication
  403 Forbidden - Not allowed
  404 Not Found - Resource doesn't exist

5xx - Server error
  500 Internal Server Error - Something broke
  503 Service Unavailable - Server is down
```

### 3.4 JSON: Data Format for APIs

JSON (JavaScript Object Notation) is the standard format for web APIs. It looks like Python dictionaries!

```json
{
  "id": 1,
  "name": "Alice",
  "email": "alice@example.com",
  "age": 25,
  "is_active": true,
  "tags": ["python", "web"],
  "profile": {
    "bio": "I love coding",
    "location": "NYC"
  }
}
```

**In Flask:**
```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/user/<int:user_id>')
def get_user(user_id):
    user_data = {
        "id": user_id,
        "name": "Alice",
        "email": "alice@example.com"
    }
    # jsonify() converts Python dict to JSON
    return jsonify(user_data)
```

### 3.5 REST API Concepts

REST (Representational State Transfer) is a style for building APIs.

```
Resource = Thing you're working with (Users, Products, Posts)
Endpoint = URL to access that resource

CRUD Operations:
C - Create  → POST   /api/users
R - Read    → GET    /api/users/1
U - Update  → PUT    /api/users/1
D - Delete  → DELETE /api/users/1

List all: GET    /api/users
List one: GET    /api/users/1
Create:   POST   /api/users
Update:   PUT    /api/users/1
Delete:   DELETE /api/users/1
```

---

## Part 4: Python Project Setup

### 4.1 Virtual Environments

Always use a virtual environment to isolate project dependencies.

```bash
# Create virtual environment
python3 -m venv venv

# Activate it (Linux/Mac)
source venv/bin/activate

# Activate it (Windows)
venv\Scripts\activate

# You'll see: (venv) $ prompt
```

### 4.2 Installing Packages

Python packages are libraries other developers created.

```bash
# Install Flask
pip install flask

# Install multiple packages
pip install flask requests sqlalchemy

# Save dependencies to file
pip freeze > requirements.txt

# Install from requirements file
pip install -r requirements.txt
```

### 4.3 Project Structure

```
my-flask-app/
├── venv/                    # Virtual environment (ignore in git)
├── app.py                   # Main Flask app
├── requirements.txt         # Dependencies
├── README.md                # Documentation
└── config/
    └── settings.py          # Configuration
```

---

## Part 5: Your First Python Program

Let's write a simple program to understand everything:

```python
# my_first_program.py

# 1. DATA - Variables and lists
users = [
    {"id": 1, "name": "Alice", "age": 25},
    {"id": 2, "name": "Bob", "age": 30},
    {"id": 3, "name": "Charlie", "age": 20}
]

# 2. FUNCTION - Reusable code
def find_user_by_name(name):
    """Search for a user by name"""
    for user in users:
        if user["name"].lower() == name.lower():
            return user
    return None

def is_adult(age):
    """Check if someone is 18+"""
    return age >= 18

# 3. DECISION - Control flow
def display_user_info(name):
    """Find and display user information"""
    user = find_user_by_name(name)
    
    if user is None:
        print(f"User '{name}' not found")
        return
    
    print(f"Found: {user['name']} (Age: {user['age']})")
    
    if is_adult(user['age']):
        print("Status: Adult")
    else:
        print("Status: Minor")

# 4. EXECUTION - Run the program
if __name__ == "__main__":
    display_user_info("Alice")     # Found: Alice (Age: 25), Status: Adult
    display_user_info("Charlie")   # Found: Charlie (Age: 20), Status: Adult
    display_user_info("Unknown")   # User 'Unknown' not found
```

Run it:
```bash
python my_first_program.py
```

---

## Part 6: Introduction to Flask

### 6.1 What is Flask?

Flask is a **framework** for building web applications in Python. Instead of manually handling web requests, Flask makes it easy.

Without Flask (manual HTTP):
```python
# You'd need to handle this yourself
import socket
server = socket.socket()
# ... lots of complex code ...
```

With Flask (simple):
```python
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, World!"

# Run with: python -m flask run
```

### 6.2 Flask Basics

```python
from flask import Flask, request, jsonify

# 1. Create the app
app = Flask(__name__)

# 2. Define routes (endpoints)
@app.route('/')  # Route URL
def home():      # Handler function
    return "Welcome to my API"

# 3. Handle different HTTP methods
@app.route('/api/items', methods=['GET'])
def list_items():
    items = [{"id": 1, "name": "Item 1"}]
    return jsonify(items)

@app.route('/api/items', methods=['POST'])
def create_item():
    new_item = request.json
    return jsonify(new_item), 201

@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    return jsonify({"id": item_id, "name": f"Item {item_id}"})

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    return "", 204

# 4. Run the app
if __name__ == '__main__':
    app.run(debug=True)
```

Run it:
```bash
python app.py

# Now visit:
# http://localhost:5000/
# http://localhost:5000/api/items
```

### 6.3 Why Flask is Great for Learning

✅ **Simple** - Small learning curve, easy to understand  
✅ **Flexible** - You build it your way  
✅ **Real-world** - Used in production by companies  
✅ **Practical** - Teaches web fundamentals  
✅ **Community** - Lots of tutorials and help  

---

## Part 7: Git Basics & Version Control

### 7.1 What is Git?

Git is a version control system that tracks changes to your code. Think of it like a time machine for your project:

- **Save snapshots** of your code at different points
- **Track who changed what** and when
- **Revert to previous versions** if something breaks
- **Collaborate** with other developers
- **Work on features** without breaking the main code

### 7.2 Git Workflow

```
Working Directory → Staging Area → Repository
(Your files)      (What's ready) (Saved history)
```

**Simple workflow:**
1. Make changes to files
2. Stage (prepare) changes for saving
3. Commit (save) with a message
4. Push to remote (backup/share)

### 7.3 Essential Git Commands

#### Setup (Do this once)

```bash
# Configure your identity
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Verify configuration
git config --global --list
```

#### Initialize & Clone

```bash
# Create a new repository in current folder
git init

# Clone an existing repository
git clone https://github.com/username/repo.git
git clone https://github.com/username/repo.git my-folder  # Clone to specific folder

# View remote URL
git remote -v
```

#### Check Status & Differences

```bash
# See what changed
git status

# See detailed changes in files
git diff                    # Changes not staged
git diff --staged           # Changes staged for commit
git diff branch1 branch2    # Compare two branches

# View commit history
git log                     # Full history
git log --oneline           # Compact history
git log -n 5                # Last 5 commits
git log --author="Alice"    # By specific author
git log -- filename.py      # For specific file
```

#### Stage & Commit

```bash
# Stage specific files
git add filename.py
git add path/to/file1.py path/to/file2.py

# Stage all changes
git add .

# Unstage a file
git restore --staged filename.py

# Check what will be committed
git diff --staged

# Commit staged changes
git commit -m "Add user login feature"

# Good commit messages:
# - Imperative mood: "Add" not "Added"
# - Be specific: "Fix login bug on mobile" not "Bug fix"
# - Include context: "Add authentication middleware"

# Commit with more detail
git commit -m "Add user login feature" -m "
- Implement POST /login endpoint
- Add password hashing
- Add session management
"

# Amend last commit (before pushing!)
git commit --amend
```

#### Branching

Branches let you work on features without affecting the main code.

```bash
# List branches
git branch              # Local branches
git branch -a          # All branches (local + remote)

# Create a branch
git branch feature-login
git switch feature-login           # Switch to it
git switch -c feature-login        # Create and switch

# Create from specific commit
git switch -c new-branch abc1234

# Delete a branch
git branch -d feature-login        # Safe delete (checks for merges)
git branch -D feature-login        # Force delete

# Rename branch
git branch -m old-name new-name
```

#### Push & Pull

```bash
# Upload local commits to remote
git push origin main                # Push to main branch
git push origin feature-login       # Push feature branch
git push -u origin feature-login    # Push and set upstream
git push origin --all               # Push all branches

# Download remote changes
git pull                # Fetch + merge
git pull origin main    # Pull specific branch

# Fetch only (don't merge)
git fetch
git fetch origin
```

#### Merging

```bash
# Merge a branch into current branch
git merge feature-login

# Resolve merge conflicts (edit conflicted files)
git status                  # See conflicts
# Edit files to resolve
git add .
git commit -m "Resolve merge conflicts"

# Abort merge if needed
git merge --abort
```

#### Undoing Changes

```bash
# Discard changes in working directory
git restore filename.py
git restore .              # All files

# Unstage a file
git restore --staged filename.py

# Undo last commit (keep changes)
git reset HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Revert a specific commit (creates new commit)
git revert abc1234

# View and go to previous state
git checkout abc1234       # Detached HEAD state
git switch -c recover-state abc1234  # Create branch at that point
```

### 7.4 Git Workflow Example

```bash
# 1. Start a new feature
git switch -c feature-user-registration

# 2. Make changes
# (Edit files: app.py, models.py, etc.)

# 3. Stage changes
git add .

# 4. Commit with message
git commit -m "Implement user registration endpoint"

# 5. Push to remote
git push -u origin feature-user-registration

# 6. On GitHub: Create Pull Request (PR)
# (Ask for review, discuss, make improvements)

# 7. After review approved, merge to main
# (Can merge on GitHub via web interface)

# 8. Update local main
git switch main
git pull origin main

# 9. Delete feature branch
git branch -d feature-user-registration
git push origin --delete feature-user-registration
```

### 7.5 Common Scenarios

#### I made changes but want to start over
```bash
git restore .           # Discard all changes
git status             # Should be clean
```

#### I committed to wrong branch
```bash
git log --oneline              # Find the commit
git reset --soft abc1234       # Undo commit, keep changes
git switch correct-branch
git commit -m "Message"
```

#### I want to see what changed in a commit
```bash
git show abc1234              # Full changes
git show abc1234:filename.py  # File content at that commit
```

#### I want to keep my local changes but pull updates
```bash
git stash              # Save your changes temporarily
git pull origin main   # Get latest
git stash pop          # Restore your changes
```

#### Collaborate with others
```bash
# Before starting work
git fetch               # Get latest changes
git pull origin main    # Update your code

# After finishing a feature
git push origin feature-xyz

# Create Pull Request on GitHub for review
```

### 7.6 Best Practices

✅ **Do:**
- Commit frequently with clear messages
- Pull before pushing (stay updated)
- Create feature branches for new work
- Review before merging (code review)
- Use `.gitignore` for secrets and build files
- Keep commits focused on one thing

❌ **Don't:**
- Commit large binary files
- Push secrets or passwords
- Force push to shared branches
- Commit code that doesn't work
- Write vague commit messages ("fix stuff")
- Work directly on main branch

### 7.7 .gitignore for Python Projects

Create a `.gitignore` file in your project root:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/

# Virtual environment
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo

# Flask
instance/
.webassets-cache

# Database
*.db
*.sqlite
*.sqlite3

# Environment variables
.env
.env.local

# OS
.DS_Store
Thumbs.db

# Build
dist/
build/
*.egg-info/
```

### 7.8 Git Cheat Sheet

| Task | Command |
|------|---------|
| **Setup** | `git config --global user.name "Name"` |
| **Start** | `git init` or `git clone <url>` |
| **Status** | `git status` |
| **Changes** | `git diff` |
| **Stage** | `git add <file>` or `git add .` |
| **Commit** | `git commit -m "message"` |
| **Branch** | `git branch` or `git switch -c branch` |
| **Push** | `git push origin <branch>` |
| **Pull** | `git pull origin <branch>` |
| **History** | `git log --oneline` |
| **Merge** | `git merge <branch>` |
| **Undo** | `git restore <file>` |
| **Revert** | `git revert <commit>` |

---

## What's Next?

Now that you understand:
- **Python basics** (variables, functions, classes)
- **Web concepts** (HTTP, REST, JSON)
- **Flask introduction** (routes, requests, responses)

You're ready for **Module 1: Flask Fundamentals**, where we'll dive deeper into how Flask works under the hood.

### Quick Checklist Before Module 1

- [ ] Python 3.11+ installed (`python --version`)
- [ ] Virtual environment created and activated
- [ ] Flask installed (`pip install flask`)
- [ ] You can write a Python script with variables, functions, and loops
- [ ] You understand HTTP methods (GET, POST, PUT, DELETE)
- [ ] You know what JSON is and how to write it

---

## Common Mistakes to Avoid

❌ **Don't** skip understanding Python basics  
✅ **Do** write small test programs to practice

❌ **Don't** memorize syntax  
✅ **Do** write code and look up what you need

❌ **Don't** build without virtual environments  
✅ **Do** isolate your project dependencies

❌ **Don't** ignore error messages  
✅ **Do** read them carefully - they tell you what's wrong

❌ **Don't** write everything in one function  
✅ **Do** break code into small, reusable functions

---

## Helpful Resources

- **Python Official Tutorial**: https://docs.python.org/3/tutorial/
- **REST API Concepts**: https://restfulapi.net/
- **HTTP Status Codes**: https://httpstatuses.com/
- **JSON Intro**: https://www.json.org/

---

**Ready to move forward?** Head to [Module 1: Flask Fundamentals](01-flask-fundamentals.md)
