# Module 1: Programming Thinking (Foundations)

## What Is Programming, Really?

Here's the truth: **programming is not about typing code. Programming is about solving problems.**

Your job as a programmer is to:
1. Understand a problem
2. Break it into logical steps
3. Translate those steps into instructions a computer can follow
4. Test that your solution actually works

The computer part? That's the easy part. The hard part is *thinking clearly*.

---

## The Programming Mindset

### A Simple Example: Making a Sandwich

Let's say someone asks you to "make a sandwich." Simple, right?

But what does the computer need to know?

```
1. Where is the bread? Do we have it?
2. Where is the filling? Do we have it?
3. Do we need to prepare the filling first (cook it, slice it)?
4. Where are the tools (knife, plate)?
5. What's the order of operations?
   - Get two slices
   - Spread filling on first slice
   - Place second slice on top
   - Cut diagonally or straight?
6. What about edge cases?
   - What if we run out of bread?
   - What if the filling spills?
   - What if someone is allergic?
```

A human can fill in these gaps. A computer **cannot**. The computer needs *explicit* instructions.

**This is the programming mindset:** think like the computer. Be precise. Leave nothing to assumption.

---

## Computational Thinking: The Four Pillars

Computational thinking is a way of breaking down problems so a computer can solve them. There are four key concepts:

### **1. Decomposition**
Breaking a big problem into smaller, manageable pieces.

**Example:** Building a house
- Don't think "build a house" (too big)
- Think:
  - Design the blueprint
  - Build the foundation
  - Frame the walls
  - Install the roof
  - Install electrical and plumbing
  - Finish walls
  - Paint
  - Move in furniture

Each step is simpler than "build a house."

**In programming:**
```python
# Bad: one big function
def make_dinner():
    # 200 lines of complicated code
    pass

# Good: decomposed into steps
def plan_meals(week):
    # 10 lines
    pass

def buy_ingredients(meals):
    # 15 lines
    pass

def prepare_ingredients(ingredients):
    # 20 lines
    pass

def cook(prepared_ingredients):
    # 30 lines
    pass
```

### **2. Pattern Recognition**
Spotting similarities and reusing solutions.

**Example:** Grocery shopping patterns
- Every week, you shop for similar items (produce, dairy, meat)
- Instead of planning fresh each week, you recognize the pattern and repeat it
- You optimize it (same store, same route) based on what worked

**In programming:**
```python
# Pattern 1: Processing a list of numbers
numbers = [1, 2, 3, 4, 5]
doubled = []
for num in numbers:
    doubled.append(num * 2)

# Pattern 2: Processing a list of names
names = ["Alice", "Bob", "Carol"]
capitalized = []
for name in names:
    capitalized.append(name.upper())

# Recognition: "Process each item and transform it"
# Solution: Use a function that applies a transformation to any list
def transform_list(items, transformation):
    result = []
    for item in items:
        result.append(transformation(item))
    return result

doubled = transform_list([1, 2, 3, 4, 5], lambda x: x * 2)
capitalized = transform_list(["Alice", "Bob"], lambda x: x.upper())
```

### **3. Abstraction**
Hiding unnecessary detail and focusing on what matters.

**Example:** Using a car
- You don't need to understand the entire engine to drive
- You abstract the complexity: pedals, steering wheel, gear shift
- You ignore: fuel injection timing, transmission fluid viscosity, etc.

**In programming:**
```python
# Without abstraction: you need to know all the details
connection = sqlite3.connect('database.db')
cursor = connection.cursor()
cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
result = cursor.fetchone()
connection.close()

# With abstraction: you use a simpler interface
user = database.get_user(user_id)  # Don't care HOW it gets the user
```

Abstraction lets you:
- Use complex things without understanding every detail
- Change the implementation without changing how you use it
- Reduce mental load (only think about what matters)

### **4. Algorithms**
Step-by-step procedures for solving a problem.

**Example:** Finding someone in a phonebook
- *Bad algorithm:* Flip to random page, check if name is there, repeat (inefficient)
- *Good algorithm:* Start in the middle, if name is alphabetically before current page, go to left half; if after, go to right half; repeat (binary search)

**In programming:**
```python
# Algorithm: Find the largest number in a list
def find_max(numbers):
    if not numbers:  # Handle empty list
        return None
    
    max_value = numbers[0]  # Start with first number
    
    for num in numbers:  # Check each number
        if num > max_value:  # If bigger than current max
            max_value = num  # Update max
    
    return max_value
```

---

## From Problem to Code: A Concrete Example

Let's apply computational thinking to a real problem.

### **Problem:** Count how many times the word "the" appears in a text

#### **Step 1: Decompose**
Break it into pieces:
- Get the text
- Break text into words
- Count occurrences of "the"
- Return the count

#### **Step 2: Recognize Patterns**
We're doing:
- Text processing (finding patterns in data)
- Counting (a fundamental operation)

#### **Step 3: Abstract**
We don't need to worry about:
- How the text is stored (file, database, memory)
- Case sensitivity (should "The" count as "the"?)
- What counts as a word boundary (punctuation?)

We *do* need to define these, but they're separate from the core logic.

#### **Step 4: Write the Algorithm**

```python
def count_word(text, word):
    """
    Count how many times 'word' appears in 'text'.
    
    Steps:
    1. Convert text to lowercase for fair comparison
    2. Split text into individual words
    3. Go through each word
    4. If it matches our target word, increment counter
    5. Return the counter
    """
    text = text.lower()           # Step 1: Handle case
    words = text.split()          # Step 2: Split into words
    count = 0                      # Step 3: Start counter
    
    for word_in_text in words:    # Step 4: Check each word
        if word_in_text == word:
            count += 1
    
    return count                   # Step 5: Return result

# Test it
text = "The quick brown fox jumps over the lazy dog. The end."
result = count_word(text, "the")
print(result)  # Output: 3
```

---

## Common Beginner Thinking Mistakes

### **Mistake 1: "I'll Start Coding Right Away"**
**Problem:** You sit down and immediately start typing code.

**Why it fails:** You haven't thought through the problem. You end up:
- Writing code that solves the wrong problem
- Going in circles and rewriting
- Getting lost in details

**The fix:**
- Spend 5-10 minutes understanding the problem
- Write down what you need to do (pseudocode, not code)
- Then translate to code

### **Mistake 2: "This Code Is Too Complicated to Debug"**
**Problem:** Your code has an error, but you're intimidated to look for it.

**Why it fails:** You avoid the problem, restart, or ask someone else to fix it without understanding why it was broken.

**The fix:**
- Add `print()` statements to see what's happening
- Trace through your code step-by-step
- Ask yourself: "What did I expect? What actually happened?"

**Example:**
```python
# Buggy code: supposed to sum numbers 1 to 5
total = 0
for i in range(5):
    total = total + i
print(total)  # Output: 10, but should be 15

# Debug: add print statements
total = 0
for i in range(5):
    print(f"Before: total={total}, i={i}")
    total = total + i
    print(f"After: total={total}")
print(total)

# Output:
# Before: total=0, i=0
# After: total=0
# Before: total=0, i=1
# After: total=1
# Before: total=1, i=2
# After: total=3
# Before: total=3, i=3
# After: total=6
# Before: total=6, i=4
# After: total=10

# Aha! range(5) gives 0,1,2,3,4 (not 1,2,3,4,5)
# Fix: range(1, 6) or use different logic
```

### **Mistake 3: "I Don't Know Where to Start"**
**Problem:** The problem feels too big and undefined.

**Why it fails:** Paralysis. You can't see a first step, so you don't start.

**The fix:**
- Ask specific questions
- Start with the simplest possible version
- Build up from there

**Example:**
- ❌ "I want to build a weather app"
- ✅ "I want to read a temperature value, display it, and convert C to F"

### **Mistake 4: "The Computer Does What I Mean"**
**Problem:** You write code that *sounds* like what you want, but it doesn't.

**Why it fails:** Computers are very literal. They do *exactly* what you tell them, not what you intended.

**The fix:**
- Always test your code
- Think through edge cases
- Ask: "What if the input is empty? Negative? Huge?"

**Example:**
```python
# You write:
age = int(input("How old are you? "))
if age = 18:  # ERROR! = is assignment, not comparison
    print("You're an adult")

# The fix:
if age == 18:  # == is comparison
    print("You're exactly 18")

if age >= 18:  # What you probably meant
    print("You're an adult")
```

### **Mistake 5: "I Should Know All the Syntax"**
**Problem:** You waste time trying to memorize syntax instead of learning concepts.

**Why it fails:** You forget syntax the minute you stop using it. That's normal.

**The fix:**
- Look up syntax when you need it
- Focus on understanding *what* the code does
- Build mental models, not syntax memorization

---

## The Debugging Mindset

Errors are gifts. They tell you exactly where your thinking went wrong.

### **Three-Step Debugging Process**

#### **Step 1: Understand the Error**
```python
# When you see:
# TypeError: 'int' object is not subscriptable

# Ask yourself:
# - What does "subscriptable" mean? (indexing, like list[0])
# - Where in my code do I try to index something?
# - What type am I actually trying to index?
```

#### **Step 2: Find Where It Happens**
```python
# Add print statements before the error
x = 5
print(f"x is type {type(x)}")  # Check what x is
print(f"About to do x[0]")     # Mark the spot
result = x[0]                  # Error happens here
print(result)                  # Never reached
```

#### **Step 3: Fix the Root Cause**
```python
# Once you know x is an int, not a list:
x = 5
# Either: use the value directly
print(x)

# Or: make it a list
x = [5]
print(x[0])
```

---

## Exercises

### **Exercise 1: Decomposition**
Take one of these problems and decompose it into steps. Don't write code—just list the steps.

1. Make a cup of coffee
2. Brush your teeth
3. Find a specific contact in your phone

**Example solution for "Make coffee":**
```
1. Check if coffee machine is available
2. Check if we have coffee beans
3. Get a mug
4. Measure water
5. Add water to machine
6. Measure ground coffee
7. Add to machine
8. Turn on machine
9. Wait for brewing
10. Check if done
11. Pour into mug
12. Add milk/sugar if desired
```

### **Exercise 2: Pattern Recognition**
Look at these three code snippets. What pattern do they all follow?

```python
# Snippet 1
fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    print(fruit.upper())

# Snippet 2
numbers = [1, 2, 3, 4, 5]
for number in numbers:
    print(number * 2)

# Snippet 3
colors = ["red", "blue", "green"]
for color in colors:
    print(f"Color: {color}")
```

**Pattern:** All process each item in a list and do something with it.

### **Exercise 3: Debugging**
Here's broken code. Find the error using the three-step debugging process.

```python
def get_initials(name):
    """Return first letter of first and last names"""
    parts = name.split()
    first_initial = parts[0]
    last_initial = parts[1]
    return f"{first_initial}.{last_initial}."

print(get_initials("John Smith"))      # Should work
print(get_initials("Cher"))             # What happens here?
```

**Hints:**
1. Add print statements to see what `parts` contains
2. Ask: what happens when there's only one name?
3. Fix: handle the case where there's no second name

---

## Key Takeaways

✅ **Programming is problem-solving, not code typing**

✅ **Computational thinking has four pillars: decomposition, pattern recognition, abstraction, and algorithms**

✅ **Spend time thinking before coding**

✅ **Errors are information, not failure**

✅ **Debugging is a skill you can learn**

✅ **Syntax is secondary; thinking is primary**

---

## What's Next?

Now that you understand *how* to think about problems, let's learn the **building blocks** you use to express those thoughts in code.

→ **[Module 2: Core Programming Concepts](02-core-programming-concepts.md)**

