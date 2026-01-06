# Module 5: Programming With AI Assistance

AI is powerful. It's also seductive. It can do things for you instantly, which is awesome—and dangerous.

This module teaches you **how to use AI responsibly** as a programming tool. You'll learn what it's great at, what it's terrible at, and most importantly, how to verify that AI-generated code is actually correct.

---

## The AI Reality Check

### What AI Is Good At

**Explaining concepts**
```
You: "Can you explain what a decorator is in Python?"
AI: [Clear, multi-example explanation]
```

**Generating boilerplate**
```
You: "Generate a class for a BankAccount with deposit and withdraw methods"
AI: [Standard, correct implementation]
```

**Helping debug errors**
```
You: "I'm getting TypeError: 'int' object is not subscriptable when I run [code]"
AI: "This error means you're trying to index something that isn't indexable. In your code, 
    [explanation]. Try [fix]."
```

**Code review**
```
You: [Share code]
AI: "This is good, but here are potential improvements: [suggestions]"
```

**Writing tests and documentation**
```
You: "Write docstring and tests for this function"
AI: [Professional docstring and test cases]
```

### What AI Is Bad At

**Architecture decisions**
- AI can't understand your full requirements
- AI doesn't know your constraints
- AI won't make trade-off decisions

❌ "Design my entire application"
✅ "Here's my architecture. Does it make sense? What am I missing?"

**Correct implementation (without verification)**
- AI generates code that *looks* right but doesn't work
- AI makes subtle bugs that compile but fail in edge cases
- AI sometimes hallucinates (makes up things)

❌ Copy AI code directly into production
✅ Copy AI code, test it thoroughly, understand it, then use it

**Making judgment calls**
- Should this be a database query or in-memory calculation?
- Should we refactor now or later?
- Is this code clear enough?

❌ "Tell me what to do"
✅ "Here are the options. Help me think through trade-offs"

**Learning**
- Using AI to do your work means you don't learn
- You end up dependent on AI
- You can't debug or improve code you don't understand

❌ "Write this entire feature for me"
✅ "I'm stuck on this specific part. Help me understand [concept]"

---

## The AI-Assisted Workflow

Here's a process for using AI responsibly:

### **Step 1: Understand the Problem**

Before asking AI anything, *you* must understand what you're trying to do.

```
Bad:
"I need to build an e-commerce site"

Good:
"I need a Python function that:
- Takes a list of product dictionaries with 'name', 'price', 'quantity'
- Calculates total cost including 8% tax
- Validates that price and quantity are positive
- Returns total or raises error if invalid"
```

### **Step 2: Try It Yourself First**

Don't ask AI for help immediately. Try for 10-15 minutes.

Why? You learn by struggling. You understand the problem better. You know what you don't know.

### **Step 3: Ask Specific Questions**

Specific questions → useful answers.

```
Bad questions:
- "How do I use databases?"
- "Help me debug this code"
- "Write a function"

Good questions:
- "I need to connect Python to PostgreSQL. What library should I use and how?"
- "My code crashes with 'TypeError: 'NoneType' object is not subscriptable' at line 42. 
   Here's the code. What's happening?"
- "Write a function that takes a list and returns the sum of even numbers"
```

### **Step 4: Verify AI's Answer**

**This is critical.** Don't trust AI just because it sounds authoritative.

```python
# AI gives you this code
def calculate_discount(price, percent):
    return price - (price * percent)

# Test it:
print(calculate_discount(100, 0.1))  # What should it return?
# Result: 90

# Is that right? 100 - (100 * 0.1) = 100 - 10 = 90
# Looks good!

# But what about edge cases?
print(calculate_discount(100, 2))  # What should it return?
# Result: -100

# That's wrong! A 200% discount should be rejected, not result in negative price.
# AI didn't handle edge cases.
```

### **Step 5: Understand the Code**

Read AI-generated code as if you wrote it. Trace through it.

```python
# AI generated this
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

# Trace it:
# What does it do? (Sorts array)
# How does it work? (Compares adjacent elements, swaps if needed)
# What's the performance? (O(n²), slow)
# Is it right? (Yes, for this use case)
# Should I use it? (Depends on array size)
```

### **Step 6: Modify as Needed**

AI gives you a starting point. You finish it.

```python
# AI gives you basic function
def get_user(user_id):
    return database.query(f"SELECT * FROM users WHERE id = {user_id}")

# You add:
def get_user(user_id):
    """Get user by ID, with validation"""
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("user_id must be a positive integer")
    
    user = database.query(f"SELECT * FROM users WHERE id = {user_id}")
    
    if not user:
        raise UserNotFoundError(f"User {user_id} not found")
    
    return user
```

---

## Common AI Pitfalls and How to Avoid Them

### **Pitfall 1: Blind Copy-Paste**

```python
# You ask: "How do I download a file?"
# AI gives 20 lines of code
# You copy and paste it without understanding

# Later: something breaks, you have no idea why
```

**Fix:** Type it yourself. Understand each line.

### **Pitfall 2: Trusting Without Testing**

```python
# AI gives you a function to parse dates
def parse_date(date_string):
    # Implementation
    pass

# You use it immediately without testing

# Later: it fails on some date format and crashes in production
```

**Fix:** Write tests before using code.

### **Pitfall 3: Asking AI to Design**

```python
# Bad: "Design my user authentication system"
# AI gives you something, but it might not fit your needs

# Good: "I need user authentication. Here's my tech stack and requirements. 
#        Should I use JWT or sessions? Here are the trade-offs I see..."
```

**Fix:** Make architectural decisions yourself. Use AI for implementation.

### **Pitfall 4: Not Reading Error Messages**

```python
# AI generates code
# You run it and get an error
# You ask AI: "Fix this error"

# Instead, read the error! It tells you what's wrong.
```

**Fix:** Read error messages carefully. Ask AI to explain them, not fix them.

### **Pitfall 5: Code You Don't Understand**

```python
# AI generates something clever but complex
# You don't understand it, so you don't modify it
# You can't debug it when it breaks

# This is worse than writing simple code yourself
```

**Fix:** If you don't understand it, ask AI to explain it. If it's still complex, ask for a simpler version.

---

## How to Ask AI Good Questions

### Framework: Be Specific

```
CONTEXT: What are you building? What problem are you solving?
ATTEMPT: What did you try? What happened?
DESIRED: What should happen?
CODE: Show the relevant code
```

### Example: Good Question

```
CONTEXT: I'm building a program to track student grades. I'm 
using Python and storing data in a dictionary.

ATTEMPT: I wrote a function to calculate average grade, but 
it crashes when the list is empty.

DESIRED: The function should return None for empty lists 
instead of crashing.

CODE:
def calculate_average(grades):
    total = sum(grades)
    return total / len(grades)

grades = []
result = calculate_average(grades)  # ZeroDivisionError
```

**AI can now help effectively.**

### Framework: Start Broad, Get Specific

```
First: "How do I handle errors in Python?"
Then: "How do I use try-except for this specific error?"
Then: "Here's my code. Does this handle errors right?"
```

### Framework: Ask About Concepts, Not Just Code

```
❌ "Write code that does X"
✅ "Explain how X works. Show me an example. Here's code I 
   wrote based on that. Does it use the concept correctly?"
```

---

## Verification Checklist

When AI gives you code, ask yourself:

### **Does It Do What I Asked?**
```python
# You asked: "Calculate total including tax"
# AI gave you: [code]
# Does it actually calculate total including tax?
# Test with specific numbers
```

### **Does It Handle Edge Cases?**
```python
# What if input is empty?
# What if input is None?
# What if input is negative?
# What if input is extremely large?

# Test all of these
```

### **Is It Secure?**
```python
# Does it validate input?
# Could a user break it?
# Does it access sensitive data safely?
```

### **Is It Efficient?**
```python
# Will it be slow with large input?
# Does it use a reasonable algorithm?
# Are there obviously wasteful operations?
```

### **Is It Readable?**
```python
# Can you understand what it does?
# Are variable names clear?
# Could someone else read this?

# If not, ask AI to make it clearer, or rewrite it yourself
```

### **Does It Match Your Style?**
```python
# Does it match your project's conventions?
# Does it match other code you've written?
# If not, refactor it to match
```

---

## AI for Different Tasks

### **For Explaining Concepts**

```
Good use:
You: "I don't understand how closures work"
AI: [Explanation with examples]

Bad use:
You: "Explain everything about Python"
AI: [Too much, overwhelming]

Best practice: Ask about one concept at a time
```

### **For Debugging**

```
Good use:
You: "My code returns [X] but I expect [Y]. Here's the code. Why?"
AI: [Explains what's happening]

Bad use:
You: "My code is broken"
AI: [Guesses, might be wrong]

Best practice: Share the error message and code
```

### **For Generating Tests**

```
Good use:
You: "Write unit tests for this function"
AI: [Good test cases]
You: [Review and modify if needed]

Bad use:
You: [Trust tests without reviewing]

Best practice: Review generated tests, add more if needed
```

### **For Refactoring**

```
Good use:
You: "Here's my code. How could I make it clearer?"
AI: [Suggestions]
You: [Implement suggestions you agree with]

Bad use:
You: [Use all suggestions blindly]

Best practice: Consider suggestions, use what makes sense
```

---

## When NOT to Use AI

### **Don't use AI when:**

1. **You're learning fundamentals**
   - Writing functions, loops, conditionals should be muscle memory
   - Do it 100 times yourself before asking AI for help

2. **You need to make decisions**
   - Architecture, technology choices, trade-offs
   - These are your responsibility

3. **You don't understand what it gives you**
   - If you can't explain it, don't use it
   - Ask AI to explain better, or write it yourself

4. **It would be faster to write it yourself**
   - For very simple code, typing it is faster than prompting
   - This happens more often than you'd think

5. **You're trying to look competent**
   - Pretending to understand AI code makes you incompetent
   - Admitting confusion and fixing it makes you competent

---

## AI as a Learning Partner

The **best** way to use AI is as a teacher:

```
Workflow:
1. You try something
2. You get stuck
3. You ask AI to explain (not fix)
4. You understand the concept
5. You write the code yourself

This is learning.
```

### Example: Learning to Use Databases

```
Bad: "Write code to query a database"
→ You get code you don't understand

Good: 
"I'm trying to use SQLite. Explain the basic steps:
1. How do I connect?
2. How do I execute a query?
3. How do I get results?
4. How do I close the connection?

Here's my first attempt: [code]
Does this do it right?"
→ You understand, you write it, you learn
```

---

## Exercises

### Exercise 1: Asking Good Questions
Rewrite these AI requests to be more specific:

1. "Help me code"
2. "How do I use lists?"
3. "Debug my program"

### Exercise 2: Verification
AI gives you this code. Test it and identify any problems:

```python
def find_max(numbers):
    max_value = numbers[0]
    for num in numbers:
        if num > max_value:
            max_value = num
    return max_value
```

Test cases:
- Normal list: [1, 5, 3, 9, 2]
- Empty list: []
- Negative numbers: [-5, -1, -10]
- Single item: [42]

### Exercise 3: Code Review
AI generated this. Review it for clarity, correctness, and efficiency:

```python
def calculate_average(nums):
    if not nums:
        return 0
    return sum(nums) / len(nums)
```

Questions:
- Is it correct?
- Should it return 0 for empty list, or None, or raise error?
- How would you improve it?

### Exercise 4: Learning Approach
You need to understand decorators. Write out a learning approach:
1. What would you ask AI?
2. How would you test your understanding?
3. How would you practice?

### Exercise 5: When to Use AI
For each scenario, decide: use AI, or do it yourself? Why?

1. You're stuck on a syntax error
2. You need to decide between database systems
3. You need to write 5 unit tests
4. You need to understand a concept
5. You need to generate a lot of boilerplate code

---

## Key Takeaways

✅ **AI is a tool, not a replacement for thinking**

✅ **Understand the problem before asking AI**

✅ **Verify every piece of AI-generated code**

✅ **Ask specific questions**

✅ **Use AI to explain, not to replace learning**

✅ **Edge cases are your responsibility to think about**

✅ **Code you don't understand is code you shouldn't use**

---

## What's Next?

Now you know how to code and how to use AI responsibly. Let's apply it all to **real projects**.

→ **[Module 6: Practical Examples & Projects](06-practical-examples.md)**

