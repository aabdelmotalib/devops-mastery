# Quick Reference Guide

A quick lookup for syntax and concepts from the tutorial.

---

## Variables and Data Types

```python
# Integer
age = 25

# Float
height = 5.8

# String
name = "Alice"
message = f"Hello, {name}"  # f-strings for formatting

# Boolean
is_active = True
is_admin = False

# Converting types
age_string = str(25)        # "25"
age_int = int("25")         # 25
price_float = float("19.99") # 19.99
```

---

## Collections

### Lists
```python
# Create
fruits = ["apple", "banana", "cherry"]
numbers = [1, 2, 3]
mixed = [1, "hello", 3.14]

# Access
first = fruits[0]           # "apple"
last = fruits[-1]           # "cherry"

# Modify
fruits[0] = "blueberry"     # Change
fruits.append("date")       # Add to end
fruits.remove("apple")      # Remove by value
fruits.pop(0)               # Remove by index

# Information
length = len(fruits)        # 3
is_present = "apple" in fruits  # True/False

# Slice
first_two = fruits[0:2]     # ["blueberry", "banana"]
all_but_first = fruits[1:]  # ["banana", "cherry", ...]
```

### Dictionaries
```python
# Create
user = {
    "name": "Alice",
    "age": 25,
    "email": "alice@example.com"
}

# Access
name = user["name"]         # "Alice"
email = user.get("email")   # Safe access

# Modify
user["age"] = 26
user["city"] = "NYC"        # Add new key

# Remove
del user["city"]

# Information
keys = user.keys()          # All keys
values = user.values()      # All values
has_key = "name" in user    # True/False
```

### Tuples
```python
# Create (immutable)
coordinates = (10, 20)
color = (255, 128, 0)

# Access
x = coordinates[0]          # 10

# Unpack
x, y = coordinates
r, g, b = color
```

---

## Conditionals

```python
# If-Else
if age >= 18:
    print("Adult")
else:
    print("Minor")

# Multiple conditions
if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 70:
    grade = "C"
else:
    grade = "F"

# Logical operators
if age >= 18 and has_license:
    print("Can drive")

if age < 13 or age > 65:
    print("Special category")

if not is_admin:
    print("Not admin")
```

---

## Loops

### For Loop
```python
# Through list
for fruit in fruits:
    print(fruit)

# Specific number of times
for i in range(5):          # 0, 1, 2, 3, 4
    print(i)

# With index
for index, fruit in enumerate(fruits):
    print(f"{index}: {fruit}")

# Through dictionary
for key, value in user.items():
    print(f"{key}: {value}")

# List comprehension
doubled = [x * 2 for x in numbers]
even = [x for x in numbers if x % 2 == 0]
```

### While Loop
```python
# Repeat while condition is true
count = 0
while count < 5:
    print(count)
    count = count + 1

# Infinite loop (be careful!)
while True:
    user_input = input("Enter something: ")
    if user_input == "quit":
        break  # Exit loop
```

---

## Functions

```python
# Basic function
def greet(name):
    """Greeting function"""
    return f"Hello, {name}!"

result = greet("Alice")

# Multiple parameters
def add(a, b):
    return a + b

result = add(5, 3)

# Default values
def greet(name, greeting="Hello"):
    return f"{greeting}, {name}!"

greet("Alice")                          # "Hello, Alice!"
greet("Alice", greeting="Hi")           # "Hi, Alice!"

# Multiple return values
def get_min_max(numbers):
    return min(numbers), max(numbers)

min_val, max_val = get_min_max([1, 5, 3])

# Optional parameter
def describe(name, age=None):
    if age:
        return f"{name} is {age}"
    return f"I don't know {name}'s age"
```

---

## Strings

```python
# Creating
name = "Alice"
greeting = 'Hello'
multi_line = """This is
multiple lines"""

# Formatting
age = 25
message = f"I am {age} years old"

# Methods
upper = name.upper()                # "ALICE"
lower = name.lower()                # "alice"
length = len(name)                  # 5
has_a = "a" in name.lower()         # True

# Splitting and joining
words = "hello world test".split()   # ["hello", "world", "test"]
sentence = " ".join(words)          # "hello world test"

# Stripping whitespace
text = "  hello  "
clean = text.strip()                # "hello"

# Replacing
replaced = name.replace("a", "e")   # "elice"

# Checking
starts = name.startswith("A")       # True
ends = name.endswith("e")           # True
```

---

## Error Handling

```python
# Try-Except
try:
    age = int(input("Age: "))
except ValueError:
    print("Invalid number")

# Multiple exceptions
try:
    result = 10 / 0
except ValueError:
    print("Wrong type")
except ZeroDivisionError:
    print("Can't divide by zero")

# Catching everything (use carefully)
try:
    # Code
    pass
except Exception as e:
    print(f"Error: {e}")

# Finally (always runs)
try:
    file = open("data.txt")
except FileNotFoundError:
    print("File not found")
finally:
    file.close()  # Always runs

# Raising errors
if age < 0:
    raise ValueError("Age cannot be negative")
```

---

## File Operations

```python
# Reading
with open("file.txt") as f:
    content = f.read()          # Read entire file
    lines = f.readlines()       # Read as lines

# Writing
with open("file.txt", "w") as f:
    f.write("Hello")
    f.writelines(["Line 1\n", "Line 2\n"])

# Appending
with open("file.txt", "a") as f:
    f.write("New line\n")

# JSON
import json
data = {"name": "Alice", "age": 25}
json_string = json.dumps(data)  # To string
loaded = json.loads(json_string) # From string

with open("data.json", "w") as f:
    json.dump(data, f)
with open("data.json") as f:
    data = json.load(f)
```

---

## Classes

```python
# Define a class
class Dog:
    """A dog class"""
    
    def __init__(self, name, breed):
        """Constructor"""
        self.name = name
        self.breed = breed
    
    def bark(self):
        """Make noise"""
        return f"{self.name} barks!"
    
    def __str__(self):
        """String representation"""
        return f"{self.name} ({self.breed})"

# Create instance
dog = Dog("Buddy", "Golden Retriever")

# Use
print(dog.bark())       # "Buddy barks!"
print(dog.name)         # "Buddy"
print(dog)              # "Buddy (Golden Retriever)"
```

---

## Common Patterns

### Initializing Variables
```python
total = 0
items = []
user_data = {}
```

### Counting
```python
count = 0
for item in items:
    if condition(item):
        count += 1
```

### Filtering
```python
valid = [item for item in items if is_valid(item)]
```

### Transforming
```python
squared = [x ** 2 for x in numbers]
names = [user["name"] for user in users]
```

### Finding
```python
# First match
first = next((item for item in items if condition(item)), None)

# All matches
matches = [item for item in items if condition(item)]
```

### Aggregating
```python
total = sum(values)
average = sum(values) / len(values)
maximum = max(values)
minimum = min(values)
```

---

## Debugging Tips

```python
# Print values
print(f"Variable x = {x}")

# Check type
print(type(x))

# Check length
print(len(items))

# Check membership
print("key" in my_dict)

# Check conditions
assert condition, "Assertion failed"

# Trace execution
import traceback
traceback.print_exc()
```

---

## Style Guide

```python
# Names are lowercase with underscores
user_name = "Alice"
student_grades = [85, 92, 78]

# Constants are uppercase
MAX_ATTEMPTS = 5
DEFAULT_PORT = 8000

# Booleans start with is_, has_, or should_
is_active = True
has_admin_rights = False
should_notify = True

# Functions and methods describe what they do
def calculate_total()
def validate_email()
def get_user_by_id()

# Spaces around operators
x = 5 + 3
if age > 18:
    pass

# Spaces after commas
my_list = [1, 2, 3]
my_func(a, b, c)

# Line length: keep under 80-100 characters
```

---

## Cheat Sheet: Common Tasks

```python
# Check if file exists
from pathlib import Path
exists = Path("file.txt").exists()

# Get current time
from datetime import datetime
now = datetime.now()
formatted = now.strftime("%Y-%m-%d %H:%M:%S")

# Round number
rounded = round(3.7)        # 4
rounded = round(3.14159, 2) # 3.14

# Absolute value
abs_value = abs(-5)         # 5

# Min/Max
minimum = min(1, 5, 3)      # 1
maximum = max(1, 5, 3)      # 5

# Sorted
sorted_list = sorted([3, 1, 4, 1, 5])  # [1, 1, 3, 4, 5]

# Reversed
reversed_list = list(reversed([1, 2, 3]))  # [3, 2, 1]

# Unique items
unique = list(set([1, 1, 2, 2, 3]))  # [1, 2, 3]

# Combine lists
combined = list1 + list2

# Range
range(5)        # 0, 1, 2, 3, 4
range(1, 5)     # 1, 2, 3, 4
range(0, 10, 2) # 0, 2, 4, 6, 8
```

---

## Computational Thinking Reminders

### Decomposition
- Break problem into smaller pieces
- Each piece should do one thing
- Pieces should be independent

### Abstraction
- Hide unnecessary details
- Focus on what matters
- Use functions and classes to simplify

### Pattern Recognition
- Look for similarities
- Reuse solutions
- Avoid repeating code

### Algorithms
- Think step-by-step
- Consider different approaches
- Test with examples

---

## Architecture Reminders

### Separation of Concerns
- Data layer (storage, database)
- Business logic layer (calculations, decisions)
- Presentation layer (UI, output)

### Design Principles
- **DRY** - Don't Repeat Yourself
- **KISS** - Keep It Simple, Stupid
- **YAGNI** - You Aren't Gonna Need It
- **SOLID** - Single responsibility, Open/closed, Liskov, Interface, Dependency

### Questions to Ask
- What could go wrong?
- What are the edge cases?
- Is this code readable?
- Can I test this?
- Is there duplication?

---

## Common Mistakes to Avoid

❌ Using variable names like `x`, `temp`, `data`
✅ Use descriptive names: `user_age`, `temp_results`

❌ Functions that do multiple things
✅ Functions that do one thing well

❌ Ignoring errors and edge cases
✅ Anticipate problems and handle them

❌ Writing code without understanding it
✅ Trace through code before running it

❌ Not testing your code
✅ Test with normal, edge, and invalid inputs

❌ Over-engineering simple problems
✅ Start simple, add complexity when needed

---

## Getting Help

1. **Read the error message** - It tells you what's wrong
2. **Check the documentation** - Official docs have examples
3. **Google the error** - Someone's had this problem before
4. **Ask others** - Show your code and what you tried
5. **Use debugging** - Add print statements, trace execution
6. **Ask AI** - Be specific about what's wrong

---

**Last Updated:** January 2026

