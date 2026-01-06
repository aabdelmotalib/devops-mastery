# Module 4: Thinking Like an Engineer

Writing code that works is just the starting point. **Engineers** write code that:
- Other people understand
- Can be changed safely
- Runs efficiently
- Scales when needed

This is where craft meets engineering. This is where you move from "making it work" to "making it right."

---

## Code Is Communication

Your code will be read **far more than it will be written**.

You might spend:
- 15 minutes writing a function
- 6 months reading and modifying it

**Most of your code's audience is humans, not machines.**

### Why Code Readability Matters

```python
# Hard to read (clever, but confusing)
result = [x*2 for x in numbers if x%2==0]

# Easy to read (clear intent)
even_numbers = [x for x in numbers if x % 2 == 0]
result = [x * 2 for x in even_numbers]

# Even better (explicit steps)
even_numbers = [num for num in numbers if num % 2 == 0]
doubled = [num * 2 for num in even_numbers]
```

The second and third versions are longer, but a human can understand them in 3 seconds. The first version requires thinking.

---

## Naming: The Most Important Skill

Good naming is **the most powerful tool** for clear code. Bad names make code impossible to understand, even if it's correct.

### Variable Names

**Bad names:**
```python
d = 5                    # What is d?
temp_x = user.get()      # Temporary? Why?
data = [1, 2, 3]         # What kind of data?
a = 25                   # a what?
foo_bar = True           # Meaningless
```

**Good names:**
```python
days_in_month = 5
current_user = user.get()
test_scores = [85, 92, 78]
user_age = 25
is_authenticated = True
```

**Rules:**
- Name should explain **what** it contains
- Longer names are fine if they're clearer
- Use nouns for variables (contains data)
- Avoid `temp`, `data`, `foo`, `x` (unless you're in a short loop)
- Use full words: ✅ `current_user`, ❌ `curr_usr`

### Function Names

**Bad names:**
```python
def do_stuff(x, y):
    pass

def process(data):
    pass

def calculate(a, b):
    pass
```

**Good names:**
```python
def calculate_total_price(items, tax_rate):
    pass

def fetch_user_by_email(email):
    pass

def validate_credit_card(card_number):
    pass
```

**Rules:**
- Name should say **what the function does**
- Use verbs: `calculate`, `validate`, `fetch`, `process`
- Be specific: ✅ `get_user_by_id()`, ❌ `get_user()`
- Shorter function names are better (but not at cost of clarity)

### Class Names

**Bad names:**
```python
class Thing:
    pass

class Handler:
    pass

class Manager:
    pass
```

**Good names:**
```python
class BankAccount:
    pass

class EmailNotificationService:
    pass

class UserAuthenticator:
    pass
```

**Rules:**
- Use nouns (classes represent things)
- Specific, not generic: ✅ `BankAccount`, ❌ `Account`
- One word preferred: ✅ `User`, ❌ `UserObject`

### Boolean Variables

**Bad names:**
```python
flag = True
done = False
x = True
```

**Good names:**
```python
is_authenticated = True
has_admin_rights = False
should_send_email = True
```

**Pattern:** Use `is_`, `has_`, `should_` prefix for booleans.

---

## Code Structure and Readability

### Short Functions

Functions should do **one thing**, clearly.

**Bad: Long function doing multiple things**
```python
def process_order(order):
    # Calculate totals
    subtotal = sum(item["price"] for item in order["items"])
    tax = subtotal * 0.08
    total = subtotal + tax
    
    # Check inventory
    for item in order["items"]:
        if item["quantity"] > get_stock(item["id"]):
            return {"error": "Out of stock"}
    
    # Update inventory
    for item in order["items"]:
        reduce_stock(item["id"], item["quantity"])
    
    # Create shipment
    shipment = {
        "order_id": order["id"],
        "items": order["items"]
    }
    send_to_warehouse(shipment)
    
    # Send email
    send_confirmation_email(order["customer_email"], total)
    
    return {"success": True, "total": total}
```

**Good: Small functions, each doing one thing**
```python
def process_order(order):
    total = calculate_order_total(order)
    check_inventory(order)
    update_inventory(order)
    create_shipment(order)
    send_confirmation(order, total)
    return {"success": True, "total": total}

def calculate_order_total(order):
    subtotal = sum(item["price"] for item in order["items"])
    tax = subtotal * 0.08
    return subtotal + tax

def check_inventory(order):
    for item in order["items"]:
        if item["quantity"] > get_stock(item["id"]):
            raise OutOfStockError(f"Item {item['id']} out of stock")

# ... other functions
```

**Benefits:**
- Easy to understand what happens
- Easy to test each step
- Easy to change one part without affecting others
- Easy to reuse functions

### Consistent Code Style

**Bad: Inconsistent**
```python
def calc_total( price,tax ):
    return price+tax

def calculate_discount(orig_price, percent):
    return orig_price * (1 - percent / 100)

result=calc_total(100,8)
```

**Good: Consistent**
```python
def calculate_total(price, tax):
    return price + tax

def calculate_discount(original_price, discount_percent):
    return original_price * (1 - discount_percent / 100)

result = calculate_total(100, 8)
```

**Style rules (use these consistently):**
- Spaces around operators: `a = b + c` (not `a=b+c`)
- Spaces after commas: `func(a, b)` (not `func(a,b)`)
- Indentation: 4 spaces per level (most common)
- Line length: keep lines under 80-100 characters

### Comments: When and How

**Bad comments:**
```python
# Add 1 to x
x = x + 1

# Check if age is greater than 18
if age > 18:
    pass

# Loop through list
for item in items:
    pass
```

These comments say *what* the code does. The code already says that.

**Good comments:**
```python
# Use the smaller of the two estimates for conservative calculation
x = min(estimate1, estimate2)

# Users must be 18 to enter (legal requirement)
if age > 18:
    allow_access()

# Skip test entries (start with underscore by convention)
for item in items:
    if item.startswith("_"):
        continue
```

These comments say *why* the code does it.

**When to comment:**
- Explain non-obvious decisions
- Explain *why*, not *what*
- Document assumptions
- Mark temporary hacks (so they get fixed)

**When NOT to comment:**
- To explain obvious code
- To restate what variable names already say
- To comment out old code (use version control instead)

---

## Errors and Exceptions

Errors aren't bad—they're information. Good code **anticipates** errors and handles them.

### Anticipate Problems

```python
# Bad: assumes input is valid
def parse_age(user_input):
    return int(user_input)

# Test:
parse_age("25")      # Works
parse_age("hello")   # Crashes! ValueError
parse_age("")        # Crashes! ValueError

# Good: handles errors
def parse_age(user_input):
    try:
        age = int(user_input)
        if age < 0 or age > 150:
            raise ValueError("Age must be between 0 and 150")
        return age
    except ValueError as e:
        print(f"Invalid age: {e}")
        return None

# Test:
parse_age("25")      # Returns 25
parse_age("hello")   # Prints error, returns None
parse_age("-5")      # Prints error, returns None
```

### Document Assumptions

```python
def calculate_discount(price, discount_percent):
    """
    Calculate discounted price.
    
    Args:
        price: Product price (must be positive)
        discount_percent: Discount percentage (0-100)
    
    Returns:
        Discounted price
    
    Raises:
        ValueError: If inputs are invalid
    """
    if price < 0:
        raise ValueError("Price must be positive")
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Discount must be 0-100")
    
    return price * (1 - discount_percent / 100)
```

---

## Trade-Offs: Speed vs. Clarity vs. Scalability

Every software decision involves trade-offs. Good engineers make conscious choices.

### Speed (Development Speed) vs. Clarity

```python
# Fast to write, hard to understand
users = [u for u in filter(lambda u: u['age']>18, 
    map(lambda u: {**u, 'active': True}, 
        fetch_users()))]

# Takes longer to write, easy to understand
all_users = fetch_users()
adult_users = [u for u in all_users if u['age'] > 18]
active_adult_users = [
    {**u, 'active': True} for u in adult_users
]
users = active_adult_users
```

**Decision:** Usually choose **clarity**. Development is 10% writing, 90% reading and understanding. Invest in clarity.

### Clarity vs. Performance (Runtime Speed)

```python
# Clear and simple
def find_user(users, target_id):
    for user in users:
        if user['id'] == target_id:
            return user
    return None

# Faster (for large lists)
users_by_id = {u['id']: u for u in users}  # Build index once
def find_user(users_by_id, target_id):
    return users_by_id.get(target_id)
```

**Decision:** Usually choose **clarity first**. Optimize only when you have evidence it's slow. (Premature optimization is a common mistake.)

### Simplicity vs. Flexibility

```python
# Simple: works for one currency
def calculate_tax(price):
    return price * 0.08  # US tax rate

# Flexible: works for any currency
tax_rates = {
    'US': 0.08,
    'CA': 0.05,
    'EU': 0.19
}

def calculate_tax(price, country):
    rate = tax_rates.get(country)
    if rate is None:
        raise ValueError(f"Unknown country: {country}")
    return price * rate
```

**Decision:** Choose simplicity first. Add flexibility only when needed. (Over-engineering is a common mistake.)

---

## Refactoring: Making Code Better

**Refactoring** means improving code without changing what it does.

### Why Refactor?

Code gets messy. Refactoring keeps it clean.

### How to Refactor

1. **Test first** - Make sure it works before you change it
2. **Make small changes** - Change one thing at a time
3. **Test after each change** - Ensure it still works

### Common Refactoring Patterns

#### **Extract Function**

```python
# Before: long function
def process_user(user):
    # Validate
    if not user.get('email') or '@' not in user['email']:
        return False
    if not user.get('age') or user['age'] < 18:
        return False
    
    # Process
    user['email'] = user['email'].lower()
    user['is_active'] = True
    
    return True

# After: extracted validation
def is_valid_user(user):
    has_email = user.get('email') and '@' in user['email']
    is_adult = user.get('age') and user['age'] >= 18
    return has_email and is_adult

def process_user(user):
    if not is_valid_user(user):
        return False
    
    user['email'] = user['email'].lower()
    user['is_active'] = True
    return True
```

#### **Replace Magic Numbers with Constants**

```python
# Before: what does 12 mean?
if user_age < 12:
    discount = 0.2

# After: clear intention
CHILD_DISCOUNT_THRESHOLD = 12
CHILD_DISCOUNT_RATE = 0.2

if user_age < CHILD_DISCOUNT_THRESHOLD:
    discount = CHILD_DISCOUNT_RATE
```

#### **Simplify Complex Logic**

```python
# Before: nested ifs
if email_is_valid:
    if user_is_active:
        if not is_already_subscribed:
            subscribe_user()

# After: early return
if not email_is_valid:
    return
if not user_is_active:
    return
if is_already_subscribed:
    return

subscribe_user()
```

---

## Testing Your Code

Before you send code anywhere, **test it yourself**.

### Manual Testing

```python
def calculate_age(birth_year):
    current_year = 2024
    return current_year - birth_year

# Test various cases
print(calculate_age(2000))  # 24 (expected)
print(calculate_age(2024))  # 0 (just born)
print(calculate_age(1950))  # 74 (elderly)
print(calculate_age(2025))  # -1 (not born yet—bug!)
```

### Systematic Testing

```python
def test_calculate_age():
    assert calculate_age(2000) == 24
    assert calculate_age(2024) == 0
    assert calculate_age(1950) == 74
    # Now I see the bug with future years

test_calculate_age()
```

### Test Edge Cases

```python
def divide(a, b):
    return a / b

# Edge cases:
divide(10, 2)      # Normal: 5
divide(10, 1)      # Divide by 1
divide(0, 5)       # Divide zero
divide(10, 0)      # Divide by zero—ERROR!

# Fix it:
def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
```

---

## Exercises

### Exercise 1: Naming
Rename these poorly-named variables and functions:
```python
x = 5
temp_data = [1, 2, 3]
process(a, b)
class Handler:
    pass
```

### Exercise 2: Code Clarity
Rewrite this code for clarity:
```python
def f(n):
    if n<=1:
        return n
    return f(n-1)+f(n-2)
```

### Exercise 3: Comments
Add meaningful comments to this code (say WHY, not WHAT):
```python
def calculate_price(base_price, quantity):
    if quantity > 100:
        discount = 0.1
    else:
        discount = 0.05
    return base_price * quantity * (1 - discount)
```

### Exercise 4: Error Handling
Add error handling to this function:
```python
def parse_date(date_string):
    parts = date_string.split("-")
    year = int(parts[0])
    month = int(parts[1])
    day = int(parts[2])
    return (year, month, day)
```

### Exercise 5: Refactoring
Refactor this code to be clearer:
```python
def process_data(data):
    result = []
    for i in range(len(data)):
        if data[i] % 2 == 0 and data[i] > 10:
            result.append(data[i] * 2)
    return result
```

---

## Key Takeaways

✅ **Code is for humans to read; computers only need to run it**

✅ **Good naming is the most powerful clarity tool**

✅ **Short functions do one thing well**

✅ **Comments explain WHY, not WHAT**

✅ **Every design choice involves trade-offs**

✅ **Refactor constantly; keep code clean**

✅ **Test your code before trusting it**

---

## What's Next?

You now understand how to write good code. But you're going to make mistakes. Let's learn how to **use AI as a tool** to help you, without becoming dependent on it.

→ **[Module 5: Programming With AI Assistance](05-programming-with-ai.md)**

