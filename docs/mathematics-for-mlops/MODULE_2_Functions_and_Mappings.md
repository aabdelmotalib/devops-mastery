# MODULE 2: Functions and Mappings (Turning Inputs into Outputs)

---

## What This Module Is About

**Plain English:** A function is a machine that takes something in and produces something out. That's it.

In MLOps, you spend your entire career building, monitoring, and fixing functions:
- Your model is a function (raw features → prediction)
- Your data pipeline is a function (raw data → processed data)
- Your feature engineering is a function (raw values → useful features)
- Your loss function is a function (prediction → how wrong are you?)

If you understand functions, you understand:
- What transforms your data
- Where things can break
- Why normalization matters
- Why order matters in pipelines
- What your model is actually doing

Without understanding functions, you'll:
- Apply the wrong transformations
- Scale features incorrectly
- Build pipelines that work on test data but fail in production
- Not understand why your model behaves differently on different data
- Get blindsided by feature engineering mistakes

---

## Where You'll See This in MLOps

### **1. Your Model as a Function**
```
Raw features → [Model] → Prediction

Example:
[house_size: 1500, num_bedrooms: 3, location_score: 85] → [Model] → $250,000
```

The model is a function that transforms input features to a price. If the features change (data drift), the output changes.

### **2. Data Pipelines**
```
Raw CSV → [Parse] → [Clean] → [Normalize] → [Feature Engineer] → ML-ready data

Each step is a function:
- Parse: CSV text → structured data
- Clean: Remove nulls, outliers → cleaned data
- Normalize: Raw numbers → 0-1 scale → normalized data
- Feature Engineer: Original features → new useful features
```

If any function breaks, your whole pipeline breaks.

### **3. Feature Scaling**
```
Age in years: [18, 25, 45, 72] → [Scale using min-max] → [0, 0.23, 0.73, 1.0]
```

Scaling is a function. It transforms age into a different range. **Why does this matter?** Because models train better on scaled features (we'll learn why in later modules).

### **4. Predictions and Thresholds**
```
Raw model output: 0.73 (probability) → [Apply threshold at 0.5] → "Yes" (binary decision)

Or:

Score: 0.73 → [If > 0.8, "high"; if > 0.5, "medium"; else "low"] → "Medium risk"
```

These are functions that turn continuous outputs into business decisions.

### **5. Monitoring Metrics**
```
Raw predictions: [0.8, 0.2, 0.9, 0.3, 0.7]
Actual values: [1, 0, 1, 0, 1]

Apply a loss function:
→ [0.04, 0.04, 0.01, 0.09, 0.04]

Sum them up (another function):
→ 0.22 (total loss)

Average them (another function):
→ 0.044 (average loss per sample)
```

Your monitoring dashboard is built from functions.

---

## Core Concepts (Slow & Detailed)

### **Concept 1: What Is a Function?**

#### Definition
A **function** is a rule that takes an input (or inputs) and produces exactly one output.

The function doesn't change. It's deterministic. Same input, always the same output.

#### Visual Representation
We often write functions like this:
```
f(x) = 2x + 1

"f" is the function's name
"x" is the input
"2x + 1" is the rule

If x = 3, then f(3) = 2(3) + 1 = 7
If x = 10, then f(10) = 2(10) + 1 = 21
```

But this notation is abstract. Let's think operationally.

#### Real Example: Model Prediction
Your fraud detection model:
```
Input: [transaction_amount: 50, location_change: "yes", time_of_day: 2am]
Function: [the model]
Output: 0.92 (92% confident this is fraud)
```

The model is a function. It has:
- **Inputs:** Features (transaction_amount, location_change, time_of_day)
- **Rule:** The internal weights and logic learned during training
- **Output:** A single probability (0.92)

#### Key Property: Consistency
The same input always produces the same output (assuming the function doesn't change).

```
Every time you give the model the exact same transaction:
[amount: 50, location_change: "yes", time: 2am] → 0.92
[amount: 50, location_change: "yes", time: 2am] → 0.92
[amount: 50, location_change: "yes", time: 2am] → 0.92
```

**Why this matters:** In production, you expect consistency. If the same transaction sometimes scores 0.92 and sometimes 0.85, something is broken (your model changed, or your inputs are inconsistent).

---

### **Concept 2: Inputs and Outputs (Domain and Range)**

#### Definition
- **Input** (or **domain**) is what you feed into the function
- **Output** (or **range**) is what the function produces

#### Real Examples

**Example A: Temperature Conversion**
```
Function: Celsius to Fahrenheit
Input: Temperature in Celsius (any number, but practically -50°C to 50°C)
Rule: F = (C × 9/5) + 32
Output: Temperature in Fahrenheit

Input 0°C → Output 32°F
Input 25°C → Output 77°F
```

**Example B: Model Inference**
```
Function: Predict house price
Input: [square_footage, num_bedrooms, location_score, age]
Rule: Trained neural network weights
Output: Price (a positive number, typically $50,000 to $1,000,000)

Input [1500, 3, 85, 20] → Output $250,000
Input [2000, 4, 90, 10] → Output $380,000
```

**Example C: Probability Transformation**
```
Function: Logistic sigmoid
Input: Any real number from -∞ to +∞
Rule: output = 1 / (1 + e^(-input))
Output: Always between 0 and 1

Input -10 → Output ≈0.00005 (almost 0)
Input 0 → Output 0.5 (exactly middle)
Input +10 → Output ≈0.99995 (almost 1)
```

#### Why This Matters
- **Type checking:** Your function expects certain inputs. If you feed it the wrong type, it breaks.
- **Range constraints:** Some outputs don't make sense. A probability should always be 0-1. A count should always be ≥0.
- **Clipping:** Sometimes you force outputs into valid ranges (e.g., "probabilities > 1.0 are impossible, so set to 1.0").

#### Production Trap
You train your model on house prices ranging $50,000 to $500,000. Then a house worth $5,000,000 arrives. Your model might:
- Output a nonsensical value (like $2 billion)
- Crash (overflow error)
- Behave unpredictably (extrapolation beyond training range)

**This is a domain mismatch.** Your model's inputs went outside the range it was trained on.

---

### **Concept 3: Composition (Chaining Functions)**

#### Definition
**Composition** means using the output of one function as the input to another function.

In math notation:
```
f(g(x)) means:
1. Apply g to x, get output
2. Use that output as input to f
3. Get final output
```

But forget the notation. Think operationally.

#### Real Example: Data Pipeline
Your raw data goes through a pipeline:

```
Raw CSV data
    ↓
[Function 1: Parse] → Structured table
    ↓
[Function 2: Clean] → Cleaned table (nulls removed)
    ↓
[Function 3: Normalize] → Normalized table (scales 0-1)
    ↓
[Function 4: Feature Engineer] → New features created
    ↓
[Function 5: Model] → Predictions
    ↓
[Function 6: Threshold] → Binary decision
```

Each function takes the output of the previous function as its input.

**If any function in the chain breaks, everything downstream breaks.**

#### Detailed Walkthrough
Let's follow one data point through a complete pipeline:

**Raw input:** A customer age of "42 years"

**After Function 1 (Parse):**
```
Input: "42 years" (text)
Rule: Extract the number
Output: 42 (a number)
```

**After Function 2 (Clean):**
```
Input: 42
Rule: Check if valid (not null, not negative, not >150)
Output: 42 (still valid)
```

**After Function 3 (Normalize):**
```
Input: 42
Rule: Scale to 0-1 using min=18, max=80
Output: (42 - 18) / (80 - 18) = 24/62 ≈ 0.387
```

**After Function 4 (Feature Engineer):**
```
Input: 0.387 (normalized age)
Rule: Create new feature "age_bin" = "young" if < 0.33, "middle" if 0.33-0.67, "old" if > 0.67
Output: "middle" (categorical)
```

**After Function 5 (Model):**
```
Input: [0.387, ... other features ...]
Rule: Neural network with learned weights
Output: 0.73 (probability of buying)
```

**After Function 6 (Threshold):**
```
Input: 0.73
Rule: If > 0.5, output "yes", else "no"
Output: "yes" (binary decision)
```

**Final output for this customer:** "Yes, likely to buy"

#### Why Composition Matters
- **Order matters.** If you normalize before cleaning, you might normalize bad data (nulls, outliers).
- **Debugging is linear.** If output is wrong, check each step: does input 1 produce right output 1? Does output 1 feed correctly into function 2?
- **Changes cascade.** If you change function 3 (normalization), it affects functions 4, 5, and 6 downstream.

#### Real Production Failure
```
Original pipeline:
Raw → Parse → Clean → Normalize → Model

One day, someone adds feature engineering:
Raw → Parse → Clean → Feature Engineer → Normalize → Model

Problem: Feature engineer expects raw scales, but normalized inputs.
Feature Engineer now gets [0.387, 0.91, 0.22] but expects [42, 950, 18].
It breaks or produces garbage.

This is why composition order is critical.
```

---

### **Concept 4: Linear Functions (The Simplest Useful Function)**

#### Definition
A **linear function** produces output that changes proportionally with input. No curves, no jumps, no surprises.

Formula:
```
f(x) = mx + b

"m" is the slope (how much does output change per unit input?)
"b" is the intercept (what's the output when input is 0?)
```

But forget the formula. Think operationally.

#### Real Examples

**Example A: Billing**
```
Customer makes phone calls.
Cost = $0.05 per minute + $9.99 base fee

f(minutes) = 0.05 × minutes + 9.99

10 minutes → $0.50 + $9.99 = $10.49
100 minutes → $5.00 + $9.99 = $14.99
```

The cost grows *linearly* with minutes. Double the minutes, roughly double the added cost.

**Example B: Server Scaling**
```
Your database processes queries linearly:
Time to answer query = 5ms base + 0.1ms per 1,000 records

f(records) = 5 + 0.0001 × records

1 million records → 5 + 0.1 = 5.1ms
10 million records → 5 + 1.0 = 6ms
```

Wait, this is deceptive. It *looks* linear, but at massive scale, the 0.1ms per 1,000 compounds. The function is linear, but assumptions break (e.g., cache misses, disk seeks become non-linear).

**Example C: Feature Scaling**
```
Min-max normalization:
f(x) = (x - min) / (max - min)

Example:
Age, min=18, max=80
f(25) = (25 - 18) / (80 - 18) = 7/62 ≈ 0.113
f(50) = (50 - 18) / (80 - 18) = 32/62 ≈ 0.516
```

This is a linear transformation. It stretches the input into a new range (0 to 1) proportionally.

#### Why Linear Functions Matter
- **Predictable:** You can reason about them. Double input → roughly double output (plus constant).
- **Simple to invert:** If you know the output, you can calculate the input backward.
- **Debugging:** If the relationship is supposed to be linear but isn't, something is wrong.

#### Common Misconception
**"Linear function means boring function."**

Actually, linear functions are used everywhere in ML:
- Feature scaling (linear)
- Layer outputs before activation (linear)
- Loss function derivatives (often linear in parameters)

Most machine learning is piecewise linear (linear + linear + linear + ...).

---

### **Concept 5: Non-Linear Functions (When Things Get Interesting)**

#### Definition
A **non-linear function** doesn't produce proportional change. The output doesn't grow consistently with input.

#### Real Examples

**Example A: Exponential Growth (Your Costs at Scale)**
```
Your system generates compute costs exponentially:
f(daily_requests) = 0.01 × 2^(requests/1000)

1,000 requests → $0.01 × 2^1 = $0.02
2,000 requests → $0.01 × 2^2 = $0.04
10,000 requests → $0.01 × 2^10 = $10.24
20,000 requests → $0.01 × 2^20 ≈ $10,000

Notice: 2× requests ≠ 2× cost. The cost explodes.
```

**Why?** Maybe your cache miss rate increases, requiring exponentially more compute.

**Example B: Sigmoid Function (Probability Boundaries)**
```
Raw model score → Sigmoid → Probability

f(x) = 1 / (1 + e^(-x))

Score -5 → 0.0067 (almost impossible)
Score 0 → 0.5 (equally likely)
Score +5 → 0.9933 (almost certain)

Notice: Scores far from 0 compress toward 0 or 1.
Changes near 0 matter more than changes at extremes.
```

**Why?** Sigmoid converts unbounded scores into probabilities (0 to 1). It's non-linear because the rate of change varies.

**Example C: Logarithmic (Diminishing Returns)**
```
User engagement plateaus:
f(days_after_launch) = 100 × log(days)

Day 1 → 0
Day 10 → 230
Day 100 → 460
Day 1,000 → 690

Notice: Going from 1 to 10 days adds ~230 users.
Going from 100 to 1,000 days adds ~230 users.
But 100 to 1,000 is 9× the time period.
```

Returns diminish. This is why apps grow fast at first, then plateau.

#### Why Non-Linear Functions Matter
- **Reality is non-linear.** Most real systems don't scale linearly.
- **Modeling:** Some relationships require non-linear functions to capture correctly.
- **Optimization:** Finding the best input is harder because changes don't scale proportionally.
- **Saturation:** Some non-linear functions have hard limits (probabilities max at 1, latencies improve diminishingly).

#### Common Trap: Assuming Linearity
You notice:
```
Model latency at 1,000 req/sec: 50ms
Model latency at 2,000 req/sec: 100ms
```

You assume linearly: "At 5,000 req/sec, latency will be 250ms."

But reality:
```
Model latency at 5,000 req/sec: 1,200ms
```

Why? Queuing effects, cache misses, and resource contention are non-linear. Once you overload a queue or cache, performance degrades exponentially, not linearly.

---

### **Concept 6: Piecewise Functions (Different Rules for Different Inputs)**

#### Definition
A **piecewise function** uses different rules depending on the input value.

```
       ⎧ x + 10,           if x < 0
f(x) = ⎨ x²,               if 0 ≤ x ≤ 10
       ⎩ 100,              if x > 10
```

Forget the notation. Here's the operational version: "If this, do that. Otherwise, do this."

#### Real Examples

**Example A: Pricing Tiers**
```
Cloud storage cost:
- If usage ≤ 1 GB: Free
- If 1 GB < usage ≤ 100 GB: $0.023 per GB
- If 100 GB < usage ≤ 1 TB: $0.022 per GB
- If > 1 TB: $0.021 per GB

Different rules apply depending on usage level.
```

**Example B: Alert Thresholds**
```
       ⎧ "Green" (OK),     if error_rate < 1%
Status = ⎨ "Yellow" (warn),  if 1% ≤ error_rate < 5%
       ⎩ "Red" (critical), if error_rate ≥ 5%
```

Different responses based on different ranges.

**Example C: Neural Network Activation**
```
ReLU (Rectified Linear Unit):
       ⎧ 0,  if x < 0
f(x) = ⎨ x,  if x ≥ 0
```

If input is negative, output 0. If positive, output the input as-is.

This is non-linear, but you can think of it as two linear rules stitched together.

#### Why Piecewise Functions Matter
- **Business logic:** Pricing, discounts, and alert levels are piecewise.
- **Neural networks:** Activation functions are piecewise (ReLU, step functions).
- **Decision boundaries:** Your model might have hard cutoffs (this is fraud, this isn't).
- **Debugging:** If behavior changes at certain thresholds, it's likely piecewise.

#### Production Reality
Most systems are piecewise:
- SLA response times have tiers
- Error budgets reset at specific times
- Rate limiting kicks in at specific thresholds
- Model behavior changes when features cross certain values

Understanding piecewise functions helps you predict where your system will behave unexpectedly.

---

## Worked Examples (Step-by-Step)

### **Worked Example 1: Building a Feature Pipeline**

**Scenario:** You're building a feature for a recommendation model. Raw input is "user session duration" in seconds. You need to:
1. Clean it (remove invalid values)
2. Normalize it to 0-1
3. Create a categorical feature (short/medium/long session)
4. Pass it to the model

Raw session durations from logs:
```
[30, 45, -5, 120, 300, 0, 890, 2400]
```

**Step 1: Define the cleaning function**
```
Rule: Remove if < 0, and cap at 1800 seconds (30 minutes is max for our use case)

Function: clean(x) = x if 0 ≤ x ≤ 1800, else remove
```

**Apply:**
```
30 → 30 ✓ (valid)
45 → 45 ✓
-5 → remove (negative)
120 → 120 ✓
300 → 300 ✓
0 → 0 ✓ (edge case: 0 is valid, user opened and closed immediately)
890 → 890 ✓
2400 → remove (exceeds 1800)

After cleaning: [30, 45, 120, 300, 0, 890]
```

**Step 2: Define the normalization function**
```
Rule: Scale to 0-1 using min=0, max=1800

Function: normalize(x) = (x - 0) / (1800 - 0) = x / 1800
```

**Apply:**
```
30 / 1800 = 0.0167
45 / 1800 = 0.025
120 / 1800 = 0.0667
300 / 1800 = 0.1667
0 / 1800 = 0
890 / 1800 = 0.4944

After normalization: [0.0167, 0.025, 0.0667, 0.1667, 0, 0.4944]
```

**Step 3: Define the categorization function**
```
Rule: Piecewise function
       ⎧ "short",  if x < 0.2
       ⎨ "medium", if 0.2 ≤ x < 0.7
       ⎩ "long",   if x ≥ 0.7

Function: categorize(x) = ...
```

**Apply:**
```
0.0167 → "short" (< 0.2)
0.025 → "short"
0.0667 → "short"
0.1667 → "short"
0 → "short"
0.4944 → "medium" (0.2 ≤ 0.4944 < 0.7)

After categorization: ["short", "short", "short", "short", "short", "medium"]
```

**Step 4: Compose the pipeline**
```
Full pipeline:
raw_value → [clean] → [normalize] → [categorize] → final_feature

Example:
300 → [clean: 300] → [normalize: 0.1667] → [categorize: "medium"] → "medium"
```

**Why this matters:**
- Each step is a function with clear input and output
- If you change one function (e.g., lower the cap from 1800 to 1200), everything downstream changes
- You can test each function independently
- You can invert functions (if needed to explain a prediction)

---

### **Worked Example 2: Understanding Model Behavior as a Function**

**Scenario:** Your fraud detection model is a function:
```
Input: [transaction_amount, days_since_last_purchase, location_change]
Output: Probability of fraud (0 to 1)
```

You notice something strange. Two similar transactions get very different fraud scores:

```
Transaction A:
[amount: $100, days_since_last: 30, location_change: true]
→ Model output: 0.15 (low fraud risk)

Transaction B:
[amount: $105, days_since_last: 30, location_change: true]
→ Model output: 0.75 (high fraud risk)
```

Only the amount changed by $5, but the output changed dramatically. Why?

**Hypothesis 1: Linear behavior** (probably not)
```
If the relationship were linear:
+$5 increase → maybe +0.05 fraud probability
But we got +0.60. That's 12× larger. Probably not linear.
```

**Hypothesis 2: Piecewise/Threshold**
```
Maybe there's a rule: "If amount > $102, fraud probability jumps"?

       ⎧ 0.15, if amount ≤ $102
fraud = ⎨ 0.75, if amount > $102
```

This could explain the sudden jump.

**Hypothesis 3: Non-linear interaction**
```
Maybe the model learned: "Amounts > $100 + location_change = very risky"

When amount = $100, location_change's effect is moderated.
When amount = $105, location_change's effect is amplified.
```

This is called an interaction effect.

**How to investigate:**
1. Test with more transactions in the $95-$110 range
2. Look at the model's learned weights or decision boundaries
3. Check if there's a hard threshold in the code or training logic

**Why this matters:** You need to understand your model's behavior to:
- Catch when something is wrong
- Explain decisions to customers
- Know when the model might be brittle

---

### **Worked Example 3: Debugging a Pipeline Failure**

**Scenario:** Your recommendation system breaks in production.

**Pipeline:**
```
Raw user features → [Scale] → [Feature Engineer] → [Model] → [Threshold] → Recommendation
```

The model predicts recommendations with confidence scores. Yesterday it worked. Today it crashes.

**Symptoms:**
```
Error: "Index out of bounds in feature engineering step"
```

**Debug step 1: Check the input to the failing function**
```
Raw features arriving: [age: -5, income: 50000, account_age: 10]

Age is negative! The scaling function expected age ≥ 0.
```

**Debug step 2: Trace backward**
```
Where did age: -5 come from?
Check raw data ingestion... Found it!

User profile shows: "age: -5 days" (negative age indicating something)
Or: Database migration corrupted a field

This is a change to the input domain. The function's assumptions broke.
```

**Debug step 3: Fix**
```
Option 1: Add validation to the scaling function
  if age < 0:
    handle it (set to 0? log error? interpolate?)

Option 2: Fix the data source
  Why is age negative in the first place?

Option 3: Change the domain assumption
  Document that age can be negative and define what it means
```

**Why this matters:** Functions assume their inputs are valid. When inputs change (data corruption, schema changes, new data source), the function breaks. Understanding what function expects helps you catch and fix it.

---

## Common Confusions & Traps

### **Trap 1: Confusing Function with Output**

**Example:**
```
Person A: "My model's output is 0.73"
Person B: "Is that good?"
Person A: "I don't know, the output is 0.73."

The confusion: 0.73 is the output of the function. The function itself is unknown.
```

**Clearer statement:**
```
"My model's output is 0.73. The model is a logistic regression predicting fraud probability.
For fraud probability, 0.73 means 'very likely fraud' (> 0.5 threshold)."

Now we know: function = logistic regression, output = 0.73, interpretation = "fraud likely"
```

**Why it matters:** The same output (0.73) means different things depending on the function:
- If it's fraud probability: very risky
- If it's customer satisfaction: unhappy
- If it's model confidence: quite confident
- If it's accuracy on a test set: bad (accuracy should be >0.9)

---

### **Trap 2: Not Understanding Pipeline Order**

**Example:**
```
Pipeline A: Raw → [Normalize] → [Feature Engineer] → [Model]
Pipeline B: Raw → [Feature Engineer] → [Normalize] → [Model]

Person thinks: "Same functions, same result."
Reality: Different results, maybe broken.
```

**Why:**
```
Pipeline A:
- Normalize: [age: 42] → [age: 0.35]
- Feature Engineer: "If age > 0.5, set senior=1" → senior=0 (because 0.35 < 0.5)

Pipeline B:
- Feature Engineer: "If age > 40, set senior=1" → senior=1 (because 42 > 40)
- Normalize: [senior: 1] → [senior: 1] (binary, stays the same)

Different results!
```

**Rule:** Order of composition matters. It's not commutative (f(g(x)) ≠ g(f(x)) in general).

---

### **Trap 3: Assuming Linearity When Data Is Non-Linear**

**Example:**
```
You observe:
API response time: 10ms at 100 req/sec
API response time: 20ms at 200 req/sec

You predict: 100ms at 1,000 req/sec

Reality: 5 seconds (500× worse)
```

**Why:** Response time is non-linear due to queuing. You can't extrapolate linearly.

**Rule:** Always plot multiple data points. If you only see two, you can't tell if the relationship is linear or non-linear.

---

### **Trap 4: Changing a Function Without Realizing It**

**Example:**
```
Original feature engineering:
  age_range = "young" if age < 30 else "old"

Someone "optimizes" it:
  age_range = "young" if age < 40 else "old"

They don't retrain the model. The model's weights were learned for the first function.
Now inputs are mapped to the wrong categories.

Result: Model's accuracy drops mysteriously.
```

**Why:** The function changed, but the downstream (the model) didn't know. The function composition is now broken.

**Rule:** If you change a function in your pipeline, retrain everything downstream.

---

### **Trap 5: Domain/Range Mismatches**

**Example:**
```
Your feature scaling function expects age: 0-120 years

Real world:
- User enters: "-5" (typo or data corruption)
- Your function: (−5 − 0) / (120 − 0) = −0.0417 (negative)
- Model expects features in range [0, 1]
- Model breaks or misbehaves
```

**Rule:** Define your function's domain and range explicitly. Add validation.

```
def scale_age(age):
  if age < 0 or age > 120:
    raise ValueError(f"Age {age} out of expected domain [0, 120]")
  return (age - 0) / (120 - 0)
```

---

## Practice Questions

### **Easy Questions**

**Q1: Identifying Functions**
In this pipeline, how many separate functions are there?
```
Raw data → [CSV Parser] → [Null Handler] → [Outlier Remover] → [Normalizer] → ML input
```

<details>
<summary>Click to see answer</summary>

**Answer:** 4 functions (not counting the initial raw data, which is input, not a function)

1. CSV Parser: text → table
2. Null Handler: data with nulls → data without nulls
3. Outlier Remover: data with outliers → data without outliers
4. Normalizer: raw values → 0-1 scaled values

**Why:** Each step transforms its input into a new output via a defined rule.

</details>

---

**Q2: Input and Output**
Your model predicts house prices. What are the input and output domains?

<details>
<summary>Click to see answer</summary>

**Answer:**
- **Input domain:** House features, e.g., [square footage (0-10,000), bedrooms (0-20), location score (0-100), age (0-200 years)]
- **Output domain:** House prices, likely [$0-$2,000,000] based on training data

**Why:** Knowing the domain helps you catch when input is out of range (e.g., a house with -5 bedrooms is invalid).

</details>

---

**Q3: Function Composition**
If function A's output is always 0-1, and function B expects input 0-1, can you safely compose them as B(A(x))?

<details>
<summary>Click to see answer</summary>

**Answer:** Yes, it's safe in terms of domain/range matching. A outputs [0,1], B expects [0,1]. ✓

**But:** This doesn't mean the functions are semantically correct. If A outputs "normalized_age" (0.5 means 50 years old) and B expects "is_adult" (1 means yes), the values match but mean different things. You could feed the wrong feature to the wrong function and get garbage results.

**Rule:** Match both range (0-1 ✓) and meaning (age vs. binary flag ✓).

</details>

---

**Q4: Linear vs. Non-Linear**
A cloud service charges:
- $0.10 per GB stored
- $0.50 per GB downloaded (data egress)

Is the total cost a linear function of storage and download volume?

<details>
<summary>Click to see answer</summary>

**Answer:** Yes, it's linear in both variables.

```
Total cost = 0.10 × storage + 0.50 × download

If storage doubles, cost increases by 0.10 × storage (proportional).
If download triples, cost increases by 0.50 × 3 × download (proportional).
```

**Why:** The total is a sum of linear functions, which is still linear. Each variable contributes proportionally.

**Note:** This assumes no bulk discounts. If there were bulk discounts ("buy 100GB get 10% off"), it would become piecewise non-linear.

</details>

---

### **Medium Questions**

**Q5: Piecewise Functions**
Your alert system uses:
```
       ⎧ Green,  if latency < 100ms
Color = ⎨ Yellow, if 100ms ≤ latency < 500ms
       ⎩ Red,    if latency ≥ 500ms
```

If latency is 99ms, what color? 100ms? 500ms?

<details>
<summary>Click to see answer</summary>

**Answer:**
- 99ms → Green (< 100)
- 100ms → Yellow (100 ≤ 100 < 500) ✓ exactly at boundary
- 500ms → Red (≥ 500) ✓ exactly at boundary

**Why:** Piecewise functions have boundary cases. The ≤ and < matter. A 1ms difference (99 vs. 100) causes different alerts. This is why you test boundary conditions.

</details>

---

**Q6: Function Composition Order**
Which pipeline is correct?

**Pipeline 1:**
```
Raw ages: [5, 30, 75] → [Remove outliers] → [Normalize] → Model
```
Remove outliers: "Remove if age < 10 or age > 100"

**Pipeline 2:**
```
Raw ages: [5, 30, 75] → [Normalize] → [Remove outliers] → Model
```

<details>
<summary>Click to see answer</summary>

**Answer:** Pipeline 1 is more sensible, though the answer depends on what you're optimizing for.

**Pipeline 1:**
- Remove 5 (< 10 outlier) → [30, 75]
- Normalize: 30 → 0.3, 75 → 0.75 (using min=10, max=100 after removing outliers)
- Model gets clean, normalized data ✓

**Pipeline 2:**
- Normalize 5 → 0.05, 30 → 0.3, 75 → 0.75 (before removing outliers)
- Remove outliers on normalized scale: "if < 0.1 or > 0.99" → removes 0.05 but keeps 0.3, 0.75
- Model gets [0.3, 0.75]

**Result:** Same final features, but...
- Pipeline 1 removes outliers on raw scale (intuitive)
- Pipeline 2 removes outliers on normalized scale (changes thresholds)

**Best practice:** Remove outliers *before* normalization. Outliers skew the normalization scale.

</details>

---

**Q7: Understanding Model Behavior**
Your fraud detection model:
- Takes [transaction_amount, days_since_last_purchase, location_change]
- Outputs fraud probability

You test:
```
Test 1: [100, 30, false] → 0.2
Test 2: [100, 30, true] → 0.7
```

Changing only location_change changes output by 0.5. What does this tell you?

<details>
<summary>Click to see answer</summary>

**Answer:** Location change has a significant impact on the model's fraud assessment. Moving from location_change=false to true (at fixed amount and days) increases fraud probability by 50 points.

**What this means:**
- The model learned that location changes are strongly associated with fraud
- This is probably correct (fraud often involves unusual locations)
- But it could be biased (maybe international users move locations legitimately)

**Follow-up investigation:**
- How does the model behave if location_change=true but other factors suggest legitimacy (e.g., amount is small)?
- Is the relationship linear (always +0.5 for location_change) or context-dependent?
- Are there interactions (location_change matters more for large amounts)?

**Why:** Understanding your function's behavior helps you catch biases and unexpected edge cases.

</details>

---

**Q8: Domain and Range Mismatches**
Your model was trained on ages 18-80. In production, you see ages: [22, 45, 82, -10, 105, 200].

Which are safe to pass to the model? Which might break it?

<details>
<summary>Click to see answer</summary>

**Answer:**
- 22 ✓ in range [18, 80]
- 45 ✓ in range
- 82 ✗ slightly out of range (above 80)
- -10 ✗ way out of range (negative)
- 105 ✗ way out of range
- 200 ✗ way out of range

**Safe to pass:** 22, 45. Maybe 82 (slightly extrapolated).

**Might break:** -10, 105, 200.

**Why:** Models make assumptions based on training data. Inputs outside the range are extrapolations. The model might:
- Output garbage (wrong predictions)
- Behave unpredictably
- Clip or error

**Protection:**
```
if age < 18 or age > 80:
  log_warning(f"Age {age} out of training domain [18, 80]")
  age = max(18, min(age, 80))  # Clip to valid range
```

</details>

---

### **Hard Questions**

**Q9: Chaining Transformations**
You have:
- Function A: Input [0, 1] → Output [−1, 1]
- Function B: Input [−1, 1] → Output [0, 1]
- Function C: Input [0, 1] → Output predictions

You build pipeline: Raw [0,100] → [Scale to 0-1] → A(x) → B(x) → C(x)

What's the final domain of outputs?

<details>
<summary>Click to see answer</summary>

**Answer:** Predictions (specific domain depends on function C's definition).

**Trace:**
```
Raw [0, 100]
  ↓ Scale: (x - 0) / (100 - 0) = [0, 1]
  ↓ A(x): [−1, 1]
  ↓ B(x): [0, 1]
  ↓ C(x): Predictions (domain undefined, depends on C)

Example if C outputs probabilities: [0, 1]
Example if C outputs regression: any real number
```

**Why:** Understanding the full chain tells you what to expect. If C outputs [0, 1] probabilities, but you get [3.5], something in the chain is broken.

**Debugging rule:** If output is unexpected, trace backward through each function.

</details>

---

**Q10: Non-Linear Behavior in Production**
Your model's inference latency vs. batch size:
```
Batch 1: 10ms
Batch 10: 50ms
Batch 100: 200ms
Batch 1000: 5,000ms
```

Is this linear? Predict latency for batch 10,000.

<details>
<summary>Click to see answer</summary>

**Analysis:**

**Check linearity:**
```
Batch 1→10: 10× data, 5× latency
Batch 10→100: 10× data, 4× latency
Batch 100→1,000: 10× data, 25× latency
Batch 1,000→10,000: 10× data, ? latency
```

**Not linear!** The relationship is non-linear and accelerating.

**Pattern recognition:**
```
Batch 1: 10ms
Batch 10: 50ms (5×)
Batch 100: 200ms (4×)
Batch 1,000: 5,000ms (25×)
```

This looks like it could be related to memory/caching:
- Small batches fit in cache → linear scaling
- Larger batches exceed cache → exponential scaling (cache misses)

**Prediction for batch 10,000:**
- If the exponential trend continues (25× for 1,000→10,000):
  10,000 batch → ~125,000ms (125 seconds)

This is a rough extrapolation. Real answer could be 50,000−200,000ms depending on the exact non-linear behavior.

**Why:** Non-linear functions are hard to predict beyond the training range. You need to understand the underlying cause (caching, queuing, etc.) to extrapolate safely.

</details>

---

## MLOps Reality Check

### **Failure Mode 1: Changing a Function in the Middle of a Pipeline**
```
Original pipeline worked fine for 2 years.

Then: Someone "optimizes" the feature engineering function.
Instead of: normalize then categorize
Now: categorize then normalize

Model still uses old learned weights. The weights expected normalized features, not categorized.
Result: Accuracy drops 30% overnight. Nobody knows why.

Lesson: Functions are contracts. Changing them breaks the contract.
```

---

### **Failure Mode 2: Domain Creep**
```
Model trained on ages 18-80.
Model trained on incomes $20k-$200k.

Over time, real world changes:
- You expand to ages 10-18 (younger users) and 80+ (seniors)
- New market segment with incomes $500k+

Old functions didn't expect these domains.
Result: Predictions become unreliable at the boundaries.

Lesson: Monitor your input domains. When they drift, retrain.
```

---

### **Failure Mode 3: Pipeline Order Wrong at Startup, Discovered Too Late**
```
Initial team built: Raw → Feature Engineer → Normalize → Model

6 months later, another team discovered: Should be Raw → Normalize → Feature Engineer → Model

Problem: Reordering breaks everything. The model was trained with wrong feature engineering.

If you swap now: accuracy drops. If you keep it: feature quality is suboptimal.

Lesson: Get the pipeline order right from the start. Changing it is expensive.
```

---

### **Failure Mode 4: Non-Linear Behavior Not Accounted For**
```
Your system scales well to 1,000 req/sec (latency: 50ms).
You assume 10,000 req/sec will be 500ms (linear).

Reality: At 10,000 req/sec, latency is 30 seconds (600× worse).

Why? Queuing, garbage collection pauses, database connection pool exhaustion.
These are non-linear.

Lesson: Test at scale. Don't extrapolate linearly from small-scale observations.
```

---

### **Failure Mode 5: Composing Incompatible Functions**
```
Function A outputs: age_group ∈ {"young", "middle", "old"}
Function B expects input: age_group ∈ {0, 1, 2}

Someone feeds A's output directly into B without converting.
B interprets strings as input, crashes or gives garbage.

Lesson: Always verify that output type and range of one function matches input expectations of the next.
```

---

## Summary & Next Steps

**You now understand:**

1. **Functions:** Input → Rule → Output
2. **Composition:** Chaining functions, order matters
3. **Linear functions:** Proportional change
4. **Non-linear functions:** Accelerating/diminishing change
5. **Piecewise functions:** Different rules for different input ranges
6. **Domain and range:** What inputs are valid, what outputs are expected

**In your pipeline, you can now:**
- Understand data transformations as functions
- Debug when outputs are unexpected (trace backward through the pipeline)
- Predict when function composition might break
- Recognize non-linear behavior and plan accordingly
- Test boundary conditions where piecewise functions change behavior

**In the next module** (when ready):
- Derivatives and gradients (how functions change)
- This is how models learn (gradients tell you which direction to move)
- Critical for understanding optimization

**Before moving on:**
1. Draw out your own data pipeline as a series of functions
2. For each function, write:
   - Input domain (what's allowed?)
   - Rule (what does it do?)
   - Output range (what can it produce?)
3. Test boundary cases in your pipeline
4. Look for non-linear behavior in your system (latency, costs, accuracy)

---

**End of Module 2.**

*This is the foundation for understanding how models learn and optimize. Take your time.*
