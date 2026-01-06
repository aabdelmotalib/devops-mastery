# Module 2: Core Programming Concepts

Now that you understand *how to think* about problems, let's learn the basic building blocks that every program uses.

These concepts appear in **every programming language**. Once you understand them, switching languages is just learning new syntax.

---

## What Are Core Concepts?

Core programming concepts are the fundamental ideas that appear in every program:
- **Data storage** (variables)
- **Data types** (numbers, text, collections)
- **Decision-making** (conditions)
- **Repetition** (loops)
- **Reusable code** (functions)
- **Organizing data** (data structures)

Think of them like the skeleton of a program. Different programs build different shapes on top, but the skeleton is always there.

---

## 1. Variables: Storing and Naming Data

### What's a Variable?

A **variable** is a named container that holds a value.

```python
age = 25
name = "Alice"
is_student = True
```

Here:
- `age` is the variable name
- `=` means "store the value on the right into the container on the left"
- `25` is the value being stored

### Why Variables?

Without variables, you'd need to repeat values:
```python
# Without variables (bad)
print(25)
print(25 + 1)
print(25 * 2)

# With variables (good)
age = 25
print(age)
print(age + 1)
print(age * 2)
```

Variables let you:
- Store data for later use
- Name data so code is readable
- Change a value in one place instead of many

### Naming Variables

**Bad variable names:**
```python
a = 5           # What is 'a'?
x = "hello"     # What is this?
data = [1,2,3]  # What kind of data?
temp = 42       # Temporary? Temporary why?
```

**Good variable names:**
```python
user_age = 25           # Clear: a user's age
greeting_message = "hello"  # Clear: a greeting message
scores = [85, 92, 78]   # Clear: a collection of scores
celsius_temperature = 42  # Clear: temperature in celsius
```

**Rules:**
- Start with letter or underscore: ✅ `name`, `_private`, ❌ `2name`
- Use lowercase with underscores: ✅ `first_name`, ❌ `firstName`, ❌ `FIRSTNAME`
- Be descriptive: ✅ `user_email`, ❌ `ue`
- Avoid keywords: ❌ `class`, `def`, `return` (Python reserves these)

### Variable Exercise

```python
# Rename these poorly-named variables to improve clarity
x = 30000
y = "Software Engineer"
z = True

# Your answer:
annual_salary = 30000
job_title = "Software Engineer"
is_employed = True
```

---

## 2. Data Types: What Kind of Data?

Every value has a **type**. The type tells you what kind of data it is and what you can do with it.

### Basic Data Types

#### **Integer (int)** - Whole numbers
```python
age = 25
count = 0
temperature = -5

# Operations
result = age + 10       # 35
result = age * 2        # 50
result = age // 3       # 8 (integer division)
result = age % 3        # 1 (remainder)
```

#### **Float (float)** - Decimal numbers
```python
pi = 3.14159
height = 5.8
temperature = 98.6

# Operations
result = pi * 2         # 6.28318
result = height / 2     # 2.9
```

#### **String (str)** - Text
```python
name = "Alice"
message = "Hello, world!"
empty = ""

# Operations
full_name = "Alice" + " " + "Smith"  # Concatenation: "Alice Smith"
repeated = "ha" * 3                   # "hahaha"
upper = name.upper()                  # "ALICE"
lower = name.lower()                  # "alice"
length = len(message)                 # 13
```

#### **Boolean (bool)** - True or False
```python
is_student = True
is_raining = False

# Used in conditions
if is_student:
    print("Enroll in course")
```

### Type Conversion

You can convert between types:
```python
# String to Integer
age_string = "25"
age_number = int(age_string)  # 25

# Integer to String
count = 42
count_string = str(count)     # "42"

# String to Float
price_string = "19.99"
price_float = float(price_string)  # 19.99

# To Boolean
bool(0)          # False
bool(1)          # True
bool("")         # False
bool("hello")    # True
bool([])         # False
bool([1, 2, 3])  # True
```

### Checking Types

```python
age = 25
print(type(age))      # <class 'int'>

name = "Alice"
print(type(name))     # <class 'str'>

price = 19.99
print(type(price))    # <class 'float'>

result = isinstance(age, int)  # True (is age an integer?)
```

---

## 3. Collections: Storing Multiple Items

### Lists - Ordered, Changeable

A **list** holds multiple values in order.

```python
# Create a list
fruits = ["apple", "banana", "cherry"]
scores = [85, 92, 78, 95]
mixed = [1, "hello", 3.14, True]

# Access items by index (0-based)
first_fruit = fruits[0]    # "apple"
second_fruit = fruits[1]   # "banana"
last_fruit = fruits[-1]    # "cherry" (negative index counts backward)

# Modify items
fruits[1] = "blueberry"    # Change "banana" to "blueberry"

# Add items
fruits.append("date")      # Add to end

# Remove items
fruits.remove("apple")     # Remove by value
fruits.pop(0)              # Remove by index

# Check length
length = len(fruits)       # 3

# Check membership
is_present = "apple" in fruits  # True or False?

# Slice a list
subset = fruits[0:2]       # First two items
subset = fruits[1:]        # All except first
```

### Dictionaries - Key-Value Pairs

A **dictionary** stores key-value pairs. Like a phone book: name (key) → phone number (value).

```python
# Create a dictionary
user = {
    "name": "Alice",
    "age": 25,
    "email": "alice@example.com"
}

# Access by key
name = user["name"]        # "Alice"
age = user["age"]          # 25

# Modify
user["age"] = 26

# Add new key-value pair
user["city"] = "New York"

# Remove
del user["city"]

# Check if key exists
has_email = "email" in user  # True

# Get keys and values
keys = user.keys()         # dict_keys(['name', 'age', 'email'])
values = user.values()     # dict_values(['Alice', 25, 'alice@example.com'])
```

### Tuples - Immutable Lists

A **tuple** is like a list, but you can't change it after creation.

```python
# Create a tuple
coordinates = (10, 20)
color = ("red", 128, 255)

# Access
x = coordinates[0]         # 10

# Can't modify (this will error)
# coordinates[0] = 15  # TypeError!

# Use when: you have fixed data that shouldn't change
def get_user_info():
    return ("Alice", 25, "alice@example.com")

name, age, email = get_user_info()
```

---

## 4. Control Flow: Making Decisions

### Conditionals - If/Else

Run different code based on conditions.

```python
age = 18

if age >= 18:
    print("You're an adult")
else:
    print("You're a minor")
```

**Multiple conditions:**
```python
score = 85

if score >= 90:
    print("A: Excellent!")
elif score >= 80:
    print("B: Good!")
elif score >= 70:
    print("C: Passing")
else:
    print("F: Failing")
```

**Logical operators:**
```python
age = 25
has_license = True

if age >= 18 and has_license:
    print("You can drive")

if age < 18 or age > 65:
    print("Special category")

if not has_license:
    print("Get a license first")
```

### Loops - Repetition

#### **For Loop** - When you know how many times

```python
# Loop through a list
fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    print(fruit)

# Loop a specific number of times
for i in range(5):  # 0, 1, 2, 3, 4
    print(i)

# Loop with index
for index, fruit in enumerate(fruits):
    print(f"{index}: {fruit}")
    # Output:
    # 0: apple
    # 1: banana
    # 2: cherry
```

#### **While Loop** - When you don't know how many times

```python
# Repeat until condition is false
count = 0
while count < 5:
    print(count)
    count = count + 1

# Common pattern: process user input
while True:
    user_input = input("Enter a number (or 'quit'): ")
    if user_input == "quit":
        break  # Exit the loop
    print(f"You entered: {user_input}")
```

---

## 5. Functions: Reusable Code

A **function** is a reusable piece of code that does one job.

### Basic Function

```python
def greet(name):
    """Greet someone by name"""
    message = f"Hello, {name}!"
    return message

result = greet("Alice")
print(result)  # "Hello, Alice!"
```

**Parts:**
- `def` - keyword to define a function
- `greet` - function name
- `(name)` - parameter (input)
- `"""..."""` - docstring (documentation)
- `return` - what to send back

### Functions with Multiple Parameters

```python
def add(a, b):
    """Add two numbers"""
    return a + b

result = add(5, 3)  # 8
```

### Functions with Default Values

```python
def greet(name, greeting="Hello"):
    """Greet with custom greeting"""
    return f"{greeting}, {name}!"

print(greet("Alice"))                    # "Hello, Alice!"
print(greet("Bob", greeting="Hi"))       # "Hi, Bob!"
```

### Functions That Don't Return Anything

```python
def print_box(text):
    """Print text in a box"""
    print("*" * (len(text) + 4))
    print(f"* {text} *")
    print("*" * (len(text) + 4))

print_box("Hello")
# Output:
# *******
# * Hello *
# *******
```

### Functions Are Abstractions

Functions hide complexity:

```python
# Without function: you need to understand all the details
name = "alice smith"
words = name.split()
capitalized = [word.capitalize() for word in words]
result = " ".join(capitalized)
print(result)  # "Alice Smith"

# With function: simple to use
def format_name(name):
    """Convert name to title case"""
    return " ".join(word.capitalize() for word in name.split())

print(format_name("alice smith"))  # "Alice Smith"
```

---

## 6. State and Data Flow

### Understanding State

**State** is the current condition of your program (what values it's holding).

```python
# A simple counter
count = 0           # Initial state: count is 0

count = count + 1   # Change state: count is now 1
count = count + 1   # Change state: count is now 2
count = count + 1   # Change state: count is now 3

print(count)        # Final state: count is 3
```

### Data Flow

Data flows through your program:
1. **Input** - Get data (from user, file, network)
2. **Process** - Transform/analyze data
3. **Output** - Send data (print, save, send)

```python
# Example: Temperature converter

# INPUT
celsius = float(input("Enter temperature in Celsius: "))

# PROCESS
fahrenheit = (celsius * 9/5) + 32

# OUTPUT
print(f"{celsius}°C = {fahrenheit}°F")
```

### Tracing Data Flow

When debugging, trace how data moves through your program:

```python
def calculate_discount(price, discount_percent):
    discount_amount = price * (discount_percent / 100)
    final_price = price - discount_amount
    return final_price

# Trace:
# Input: price = 100, discount_percent = 20
# Process:
#   discount_amount = 100 * (20 / 100) = 20
#   final_price = 100 - 20 = 80
# Output: 80

print(calculate_discount(100, 20))  # 80
```

---

## 7. Errors and Debugging

### Common Error Types

#### **SyntaxError** - You wrote invalid code
```python
# Missing colon
if age > 18
    print("Adult")

# Python error: SyntaxError: expected ':'
```

#### **NameError** - Variable doesn't exist
```python
print(age)  # But we never defined 'age'

# Python error: NameError: name 'age' is not defined
```

#### **TypeError** - Wrong data type
```python
age = "25"
result = age + 5  # Can't add string and integer

# Python error: TypeError: can only concatenate str (not "int") to str
```

#### **IndexError** - Index doesn't exist
```python
fruits = ["apple", "banana"]
print(fruits[5])  # There is no 5th item

# Python error: IndexError: list index out of range
```

### Debugging Strategy

When you get an error:

1. **Read the error message carefully**
   - What line is the error on?
   - What type of error is it?
   - What does it say went wrong?

2. **Look at that line of code**
   - Does it match the description?
   - What should it do?

3. **Add debug output**
   ```python
   fruits = ["apple", "banana"]
   print(f"fruits list: {fruits}")
   print(f"length: {len(fruits)}")
   print(f"trying to access index 5")
   print(fruits[5])  # Now the error makes sense!
   ```

4. **Fix and test**
   ```python
   fruits = ["apple", "banana"]
   if len(fruits) > 5:
       print(fruits[5])
   else:
       print("Index out of range")
   ```

---

## Exercises

### Exercise 1: Variables and Types
Create variables with appropriate names and types:
1. A person's full name (string)
2. Their age (integer)
3. Their height in meters (float)
4. Whether they're currently employed (boolean)
5. A list of their hobbies (list)

### Exercise 2: Conditionals
Write code that:
1. Takes an age as input
2. Prints "Child" if under 13
3. Prints "Teen" if 13-19
4. Prints "Adult" if 20 or older

### Exercise 3: Loops
Write a program that:
1. Creates a list of 5 numbers
2. Uses a loop to print each number multiplied by 2

### Exercise 4: Functions
Write a function that:
1. Takes a person's first and last name
2. Returns their email in format: `firstname.lastname@example.com`
3. Test it with at least 2 names

### Exercise 5: Data Flow and Debugging
Here's broken code. Trace the data flow and fix it:
```python
def calculate_total(prices):
    total = 0
    for price in prices:
        total = total + price
    return total

items = [10, 20, "thirty", 40]
result = calculate_total(items)
print(result)
```

**Hint:** What happens when you try to add a string to a number?

---

## Key Takeaways

✅ **Variables store data with meaningful names**

✅ **Data types determine what you can do with data**

✅ **Collections let you store multiple items**

✅ **Conditions and loops control program flow**

✅ **Functions are reusable, organized code**

✅ **State is the current condition of your program**

✅ **Errors are information; debugging is a skill**

---

## What's Next?

Now you know the building blocks. Let's learn how to **organize** these blocks into real software structures.

→ **[Module 3: Software Architecture Basics](03-software-architecture-basics.md)**

