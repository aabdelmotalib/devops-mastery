# MODULE 8: Scaling, Normalization, and Numerical Stability

---

## What This Module Is About

**Plain English:** Your numbers matter. Big numbers vs. small numbers affect how the model trains. Scaling is about putting all numbers on a fair playing field.

Without understanding scaling:
- Your model trains slowly or fails
- Some features dominate others unfairly
- You get numerical errors (overflow, underflow)
- You can't compare models across datasets

With understanding scaling:
- Model trains faster and more reliably
- All features contribute equally
- You avoid numerical disasters
- You understand why preprocessing matters

---

## Where You'll See This in MLOps

### **1. Feature Scaling Before Training**
```
Feature A: House size (1000-5000 square feet)
Feature B: House color (coded as 1-4 for colors)

Without scaling:
  Size dominates (numbers 1000x larger)
  Color is ignored (gradient too small)

With scaling:
  Size: [0-1]
  Color: [0-1]
  Both contribute equally
```

### **2. Numerical Stability**
```
Computing probability: exp(x)

If x = 1000: exp(1000) = infinity (overflow!)
If x = -1000: exp(-1000) = 0 (underflow)

Solution: Subtract max before exp (log-sum-exp trick)
Result: Numerically stable, no overflow
```

### **3. Model Comparison**
```
Model A trained on raw values (1-10000)
Model B trained on scaled values (0-1)

Model A's loss: 500,000
Model B's loss: 0.05

Which is better? Can't compare! Different scales.

With normalization: Both on same scale, comparison is fair.
```

### **4. Deploy to Edge Devices**
```
Training: Float32 (full precision)
Edge device: Int8 (low precision)

Numbers must be carefully scaled to fit in Int8 without losing too much info.
Requires understanding of range and precision.
```

### **5. Handling Outliers**
```
Feature: House price
Range: $100k - $10M
Outlier: $500M mansion

Without handling:
  Mean shifts to $8M
  Normal homes (1-3M) look cheap by comparison
  
With scaling/outlier handling:
  Use median instead of mean (robust to outliers)
  Or cap extreme values
```

---

## Core Concepts (Slow & Detailed)

### **Concept 1: Why Scaling Matters (Fairness and Speed)**

#### Definition
**Scaling** is converting features to a standard range (typically 0-1 or -1 to 1).

#### Why It Matters
```
Feature A: 0 to 10,000 (size in sqft)
Feature B: 0 to 1 (is_basement: no/yes)

Gradient descent step:
  Adjustment to feature A: Δweight_A = -learning_rate × gradient_A
  Adjustment to feature B: Δweight_B = -learning_rate × gradient_B
  
  gradient_A is huge (due to large numbers)
  gradient_B is tiny (due to small numbers)
  
Result:
  Weight A changes quickly
  Weight B changes slowly or not at all
  Model effectively ignores feature B
  
Solution: Scale all features to [0,1]
  Now both contribute equally
```

#### Fairness Perspective
```
Unscaled model:
  "I care 1000x more about size than basement"
  
Scaled model:
  "I'll let the data tell me what matters"
  
Scaling ensures features compete on merit, not magnitude.
```

---

### **Concept 2: Min-Max Scaling (0 to 1 Range)**

#### Definition
**Min-Max scaling** transforms values to [0, 1] range.

#### Formula
```
scaled_value = (value - min) / (max - min)

Example:
  House price: $200,000
  Min: $100,000
  Max: $500,000
  
  scaled = (200,000 - 100,000) / (500,000 - 100,000)
  scaled = 100,000 / 400,000
  scaled = 0.25
```

#### Intuition
```
min = 0.0 (the minimum value maps to 0)
max = 1.0 (the maximum value maps to 1)
middle = ~0.5 (median maps to 0.5)
```

#### Practical Example
```
Age data:
  Values: 18, 25, 35, 42, 60, 75
  Min: 18
  Max: 75
  Range: 57
  
  18 → (18-18)/(75-18) = 0/57 = 0.0
  25 → (25-18)/(75-18) = 7/57 = 0.12
  35 → (35-18)/(75-18) = 17/57 = 0.30
  75 → (75-18)/(75-18) = 57/57 = 1.0
```

#### Problem
```
What if new data has values outside [min, max]?

Example: Age 85 (older than training max of 75)
  scaled = (85-18)/(75-18) = 67/57 = 1.18 (outside [0,1]!)
  
Solution: Clamp to [0,1] or use standardization instead.
```

---

### **Concept 3: Standardization (Z-Score Normalization)**

#### Definition
**Standardization** transforms data to mean=0, SD=1.

#### Formula
```
z = (value - mean) / standard_deviation

Example:
  Age: 35
  Mean age: 40
  SD: 8
  
  z = (35 - 40) / 8 = -5/8 = -0.625
```

#### Intuition
```
Mean = 0.0 (center of distribution)
SD away = ±1.0
2 SDs away = ±2.0

Values typically fall in [-3, +3] range
Outliers can be > 3
```

#### Practical Example
```
Income data:
  Values: $40k, $50k, $60k, $70k, $80k
  Mean: $60k
  SD: $14.14k
  
  $40k → (40-60)/14.14 = -20/14.14 = -1.41 (1.4 SDs below mean)
  $60k → (60-60)/14.14 = 0/14.14 = 0.0 (at the mean)
  $80k → (80-60)/14.14 = 20/14.14 = 1.41 (1.4 SDs above mean)
```

#### Advantage Over Min-Max
```
New data can be outside original range:

Age 85 (training max 75):
  Standardized: (85-40)/8 = 5.625 (still meaningful, "5.6 SDs above mean")
  Min-max: 1.18 (outside [0,1], breaks assumptions)

Standardization handles extrapolation naturally.
```

---

### **Concept 4: Log Scaling (For Skewed Data)**

#### Definition
**Log scaling** applies logarithm to compress large ranges.

#### Formula
```
log_value = log(value)

Example:
  Income: $20k, $100k, $1M, $10M
  Regular: Range is 500x (huge)
  
  Log:
    log(20k) ≈ 4.3
    log(100k) ≈ 4.6 (ratio 20x, but only difference 0.3)
    log(1M) ≈ 6.0 (difference 1.4)
    log(10M) ≈ 6.3 (difference 0.3)
  
  Range becomes [4.3, 6.3] = 2.0 (manageable)
```

#### When to Use
```
Data with:
- Very large ranges (100x to 1000000x)
- Exponential growth (prices, populations, network traffic)
- Right-skewed distribution (tail on high end)

Examples:
  Income: Log scale
  Network latency: Log scale (microseconds to seconds)
  Server capacity: Log scale (megabytes to petabytes)
```

#### Example
```
Network latency (microseconds):
  Values: 100μs, 1000μs, 10000μs, 100000μs (100x range)
  
  Log scale:
    log(100) = 2.0
    log(1000) = 3.0
    log(10000) = 4.0
    log(100000) = 5.0
  
  Now range is [2, 5] (manageable for model)
  Ratios preserved (10x difference becomes 1.0 on log scale)
```

---

### **Concept 5: Batch Normalization (Normalizing During Training)**

#### Definition
**Batch normalization** normalizes data within each training batch to stabilize training.

#### Why It Matters
```
Without batch norm:
  Epoch 1: First layer sees raw features (large numbers)
  After first layer: Weights scale those features
  Second layer sees scaled features
  Problem: Scales can change unpredictably, training is unstable
  
With batch norm:
  After each layer: Normalize outputs to mean=0, SD=1
  Next layer always sees normalized inputs
  Result: Stable, predictable training
```

#### Practical Impact
```
Without batch norm: Learning rate 0.001 (very small, needs tuning)
With batch norm: Learning rate 0.01-0.1 (10-100x larger, less sensitive)
Result: Faster convergence, easier to tune
```

---

### **Concept 6: Numerical Stability (Avoiding Overflow/Underflow)**

#### Definition
**Numerical stability** is ensuring computations don't produce infinity, NaN, or zero.

#### Common Problem: Softmax Overflow
```
Softmax formula: exp(x) / sum(exp(x))

If x = 1000:
  exp(1000) = infinity (overflow!)

Solution: Subtract max before exp
  shift = max(x_1, x_2, ..., x_n)
  exp(x_i - shift) (will be [0, 1])
  
Example:
  x = [100, 101, 102]
  shift = 102
  exp(100-102) = exp(-2) ≈ 0.135
  exp(101-102) = exp(-1) ≈ 0.368
  exp(102-102) = exp(0) = 1.0
  
  sum = 1.503
  softmax = [0.09, 0.24, 0.67]
  
Result: No overflow, numerically stable.
```

#### Common Problem: Log Underflow
```
log(0) = undefined (negative infinity)

If probability = 0 (from softmax underflow):
  log(0) breaks your loss calculation

Solution: Clamp to minimum value
  prob = max(prob, 1e-7)
  log(max(prob, 1e-7))
  
Or use log-softmax directly (numerically stable version)
```

---

## Worked Examples (Step-by-Step)

### **Worked Example 1: Scaling Features for Fair Training**

**Scenario:** You have two features for house valuation:

Feature A: Square footage (500-5000)
Feature B: Number of bathrooms (1-10)

Without scaling, what happens?

**Step 1: Calculate ranges**
```
Feature A range: 5000 - 500 = 4500
Feature B range: 10 - 1 = 9

Ratio: 4500 / 9 = 500

Feature A is 500x larger in magnitude.
```

**Step 2: See the problem**
```
Initialize weights randomly:
  w_A = 0.001
  w_B = 0.001

Compute prediction:
  prediction = w_A × sqft + w_B × bathrooms
  
On a typical house (2000 sqft, 3 bathrooms):
  prediction = 0.001 × 2000 + 0.001 × 3 = 2.0 + 0.003 = 2.003
  
Gradient:
  ∂loss/∂w_A depends on sqft values (large)
  ∂loss/∂w_B depends on bathroom values (small)
  
  gradient_A ≈ 2000 × error (large)
  gradient_B ≈ 3 × error (small)
  
  Weight A updates much faster than weight B!
```

**Step 3: Apply min-max scaling**
```
Feature A (sqft):
  min = 500, max = 5000
  scaled = (sqft - 500) / 4500
  
  500 → 0.0
  2500 → 0.44
  5000 → 1.0

Feature B (bathrooms):
  min = 1, max = 10
  scaled = (bathrooms - 1) / 9
  
  1 → 0.0
  3 → 0.22
  10 → 1.0
```

**Step 4: Result**
```
Both features now [0, 1]
Gradients are comparable in magnitude
Weights update fairly
Both features contribute proportionally to accuracy
```

---

### **Worked Example 2: Detecting and Handling Outliers**

**Scenario:** You're training a model on customer spending.

Data:
```
Customer spending: $100, $200, $150, $300, $250, $400, $180, $1,000,000
```

**Question:** How does the outlier affect scaling?

**Step 1: Analyze without outlier handling**
```
Without outlier:
  min = $100
  max = $400
  mean = $225
  
  Scaling: $150 → (150-100)/(400-100) = 0.17

With outlier:
  min = $100
  max = $1,000,000
  mean = $132,000 (!!)
  
  Scaling: $150 → (150-100)/(1M-100) ≈ 0.00005 (almost zero!)
  
The outlier compresses normal values to near-zero range.
```

**Step 2: Impact on training**
```
Normal customers ($100-$400):
  Unscaled (no outlier): [0, 1] range (good)
  Unscaled (with outlier): [0.0001, 0.0004] (gradient too small)
  
Model can't learn from compressed normal range.
```

**Step 3: Outlier handling options**
```
Option 1: Remove outlier
  Good if outlier is data error
  Bad if outlier is real (e.g., VIP customer)

Option 2: Cap at 99th percentile
  99th percentile = $400
  Cap $1M to $400
  
  Reasoning: VIP is valuable but shouldn't break model
  New max = $400, all data fits [100, 400]

Option 3: Use robust scaling (median, IQR)
  median = $225
  IQR (25th to 75th percentile) = $200
  
  Robust scaling = (value - median) / IQR
  (150 - 225) / 200 = -0.375 (not compressed!)
  (1M - 225) / 200 = 5000 (outlier is far, but normal values preserved)
```

**Step 4: Decision**
```
For this problem: Option 2 (cap at 99th percentile)
  Reasoning:
  - Outlier is real (VIP customer), don't remove
  - Don't need exact outlier value (just "high spender" matters)
  - Capping preserves normal value range for good learning
  
Result: All data in [100, 400], model trains well
```

---

### **Worked Example 3: Numerical Stability in Softmax**

**Scenario:** Computing softmax for 3-class classification.

Raw scores: [100, 101, 102]

**Step 1: Compute naively (overflow)**
```
Softmax = exp(x) / sum(exp(x))

exp(100) = 3.7 × 10^43 (huge!)
exp(101) = 2.7 × 10^44 (huge!)
exp(102) = 3.7 × 10^44 (huge!)

All overflowed, result = NaN or infinity
```

**Step 2: Apply the fix (subtract max)**
```
max_score = 102
shifted_scores = [100-102, 101-102, 102-102] = [-2, -1, 0]

exp(-2) = 0.135
exp(-1) = 0.368
exp(0) = 1.0

sum = 1.503
softmax = [0.135/1.503, 0.368/1.503, 1.0/1.503]
softmax = [0.090, 0.245, 0.665]
```

**Step 3: Verify**
```
Result is valid probabilities:
  - All between 0 and 1 ✓
  - Sum to 1 ✓
  - No overflow ✓
  - No NaN ✓

Numerically stable and correct.
```

**Step 4: Why it works**
```
Mathematically:
  softmax(x) = exp(x) / sum(exp(x))
           = exp(x - c) / sum(exp(x - c))  (same result, c = max)
           
Subtracting max:
  - Doesn't change the result (ratios preserved)
  - Prevents overflow (all exponents now < 0)
  - Prevents underflow (all exponents now > a negative number)
```

---

## Common Confusions & Traps

### **Trap 1: Scaling Training But Forgetting Test/Production**

```
Training:
  Data: 100-500
  Scaled: (x - 100) / 400
  
Test data:
  Apply same scaling using training min/max ✓
  
Production data:
  Forget to scale! ✗
  Model gets raw data (100-500) instead of scaled (0-1)
  Predictions are garbage
  
Fix: Always save the scaler (min, max, or mean, std)
     Apply exact same transformation to all data
     
Code:
  train_scaler = MinMaxScaler()
  train_scaler.fit(train_data)
  
  train_scaled = train_scaler.transform(train_data)
  test_scaled = train_scaler.transform(test_data)  ← use same scaler
  prod_scaled = train_scaler.transform(prod_data)  ← use same scaler
```

---

### **Trap 2: Fitting Scaler on Both Train and Test**

```
Wrong:
  scaler_train = MinMaxScaler()
  scaler_train.fit(train_data)
  train_scaled = scaler_train.transform(train_data)
  
  scaler_test = MinMaxScaler()  ← Different scaler!
  scaler_test.fit(test_data)    ← fit on test data!
  test_scaled = scaler_test.transform(test_data)
  
Problem: Scaler is different for test
         Model gets different scale than training
         Fair evaluation impossible

Right:
  scaler = MinMaxScaler()
  scaler.fit(train_data)  ← fit only on training
  
  train_scaled = scaler.transform(train_data)
  test_scaled = scaler.transform(test_data)  ← same scaler
```

---

### **Trap 3: Scaling Categorical Variables**

```
Feature: Color (red=1, blue=2, green=3)

Wrong:
  Assume blue (2) is "between" red (1) and green (3)
  Scale to [0, 1]
  
Problem: No such order exists
         Color is categorical, not ordinal

Right:
  One-hot encode: red=[1,0,0], blue=[0,1,0], green=[0,0,1]
  Don't scale (already [0, 1])
  
Or: Leave as-is, let model learn the meaning
```

---

### **Trap 4: Log Scaling Zero Values**

```
Data: 0, 1, 10, 100, 1000

Apply log:
  log(0) = -infinity (undefined!)
  log(1) = 0
  log(10) = 1.0
  log(100) = 2.0
  log(1000) = 3.0

Problem: log(0) breaks

Solution:
  log(max(x, 1e-7))  ← clamp to small value
  or
  log(x + 1)  ← add 1 before log
  
Result: log(1) = 0, log(2) ≈ 0.69, log(11) ≈ 2.4 (all valid)
```

---

## Practice Questions

### **Easy Questions**

**Q1: Why Scale?**
Feature A ranges [0, 10000]
Feature B ranges [0, 1]

Without scaling, what happens?

<details>
<summary>Click to see answer</summary>

**Answer:** Feature A dominates.

Why: Gradient with respect to A is 10,000x larger.
Weight A updates much faster than weight B.
Model effectively ignores B.

Solution: Scale both to [0, 1], then both contribute fairly.

</details>

---

**Q2: Min-Max Scaling**
Value: 30
Min in data: 10
Max in data: 50

What's the scaled value?

<details>
<summary>Click to see answer</summary>

**Answer:**
scaled = (30 - 10) / (50 - 10) = 20 / 40 = 0.5

Interpretation: Value 30 is halfway between min and max.

</details>

---

**Q3: Standardization vs. Min-Max**
Which handles values outside the original range better?

<details>
<summary>Click to see answer</summary>

**Answer:** Standardization (z-score).

Why:
- Min-Max: New value outside [original_min, original_max] breaks
- Standardization: New value can be any z-score, still meaningful

Example:
  Training max age: 80
  Test age: 85 (outside)
  
  Min-max: (85-min)/range → outside [0,1]
  Standardization: (85-mean)/sd → valid z-score

Standardization is more robust.

</details>

---

### **Medium Questions**

**Q4: Outlier Detection**
Income data: $20k, $25k, $30k, $35k, $1M

What's a reasonable handling strategy?

<details>
<summary>Click to see answer</summary>

**Answer:** Cap at 99th percentile or use robust scaling.

Option 1: Cap
  99th percentile ≈ $35k
  Cap $1M to $35k
  Result: All values in [$20k, $35k]

Option 2: Robust scaling (median, IQR)
  Median: $30k
  IQR: ~$10k
  Preserves normal range, handles outlier naturally

Choose capping if outlier is error or unnecessary precision.
Choose robust scaling if outlier is real but should be dampened.

</details>

---

**Q5: Log Scaling**
Data: 1, 10, 100, 1000, 10000

Range is 10,000x. After log scaling, what's the range?

<details>
<summary>Click to see answer</summary>

**Answer:**
log(1) = 0
log(10) = 1.0
log(100) = 2.0
log(1000) = 3.0
log(10000) = 4.0

Range: [0, 4] = 4 (much more manageable than 10,000x)

Log scaling compresses exponential ranges.

</details>

---

**Q6: Scaler Fit/Transform**
You have train and test data.

Should you:
A) Fit scaler on train, apply to both train and test
B) Fit scaler on train, fit separate scaler on test
C) Fit scaler on combined train+test

<details>
<summary>Click to see answer</summary>

**Answer:** Option A (fit on train, apply to both).

Why:
- A: Fair evaluation (test scaled by training statistics)
- B: Wrong (test scaler is different, unfair comparison)
- C: Wrong (test data leaks into training scaler)

Always: Fit on training only, apply to all other data.

</details>

---

### **Hard Questions**

**Q7: Batch Normalization Advantage**
Why does batch norm allow larger learning rates?

<details>
<summary>Click to see answer</summary>

**Answer:** Batch norm stabilizes internal activations.

Without batch norm:
  Large learning rate → weights change a lot
  → activations change unpredictably
  → training becomes unstable, diverges

With batch norm:
  Batch norm normalizes outputs after each layer
  → next layer always sees mean=0, sd=1 input
  → stable, predictable training
  → can use larger learning rate without diverging

Benefit: Faster convergence, less learning rate tuning needed.

</details>

---

**Q8: Numerical Stability in Practice**
You compute: loss = -log(softmax(scores))

Scores are [100, 101, 102]. What happens?

<details>
<summary>Click to see answer</summary>

**Answer:** Overflow and NaN loss.

Step by step:
  softmax = exp(scores) / sum(exp(scores))
  exp(100) = 3.7e43 (overflow!)
  Result: NaN or infinity
  
  log(NaN) or log(infinity) = NaN
  loss = NaN (training breaks)

Fix: Use log-softmax directly
  log_softmax(scores) = (scores - max(scores)) - log(sum(exp(scores - max(scores))))
  
  = (scores - 102) - log(sum(exp(scores - 102)))
  = [-2, -1, 0] - log(exp(-2) + exp(-1) + exp(0))
  = [-2, -1, 0] - log(0.135 + 0.368 + 1.0)
  = [-2, -1, 0] - 0.405
  = [-2.405, -1.405, -0.405]
  
Result: All valid (no overflow, numerically stable)

</details>

---

## MLOps Reality Check

### **Failure Mode 1: Unscaled Features in Production**
```
Training:
  Features scaled to [0, 1]
  Model trained on scaled data
  Accuracy: 95%

Production:
  Forgot to scale features
  Model gets raw data
  Accuracy: 25% (garbage!)

Why: Model was trained on [0, 1] data, expects that scale
     Gets 100-10000 instead, completely outside training distribution

Fix: Serialize scaler with model
     Apply scaler before prediction
     Code review to ensure scaler used consistently
```

---

### **Failure Mode 2: Numerical Overflow in Softmax**
```
Model training goes well, then suddenly:
  loss = NaN
  model stops learning
  
Investigation:
  Some scores reached 1000+ (overflow in softmax)
  exp(1000) = infinity
  softmax = NaN
  
Root cause:
  Learning rate too high, weights grew too large

Fix:
  1. Reduce learning rate
  2. Add weight regularization
  3. Use log-softmax (numerically stable)
```

---

### **Failure Mode 3: Wrong Scaler in Deployment**
```
Dev environment:
  Train data scaled: mean=100, std=20
  Scaler saved to pickle file
  Model works: 91% accuracy
  
Production:
  Different scaler used: mean=102, std=19
  (from production data statistics)
  
Result:
  Model performance drops: 87% accuracy
  Different scale than training
  
Fix:
  Use training data scaler, not production data scaler
  Apply exact same transformation to all data
  Code: train_data.scaler → production_data (never refit scaler)
```

---

### **Failure Mode 4: Outliers Cause Extreme Scaling**
```
Training data: Income $30k-$100k
Outlier: $10B (typo or fraud)

Min-max scaling:
  min = $30k
  max = $10B
  
  Normal customer $50k: (50k-30k)/(10B-30k) ≈ 0 (compressed!)
  Normal range is squeezed to near-zero

Model can't learn from compressed range.

Fix:
  Detect outliers: IQR method or isolation forest
  Remove or cap outliers before scaling
  Result: Normal range preserved, model trains well
```

---

## Summary & Next Steps

**You now understand:**

1. **Why scaling:** Fair feature comparison, faster training
2. **Min-Max scaling:** Map to [0, 1] range
3. **Standardization:** Z-score normalization, handles extrapolation
4. **Log scaling:** Compress exponential ranges
5. **Batch normalization:** Stabilize training, allow larger learning rates
6. **Numerical stability:** Avoid overflow, underflow, NaN
7. **Common mistakes:** Scaling inconsistently, forgetting outliers, fitting on test data

**In your pipeline, you can now:**
- Scale features appropriately for your problem
- Handle outliers without breaking your model
- Avoid numerical errors in production
- Understand why preprocessing matters
- Deploy models with consistent scaling

---

## Completion: Full Mathematics for MLOps Curriculum

**You have completed all 8 modules:**

1. ✅ Absolute Basics (numbers, trends, percentages)
2. ✅ Functions and Mappings (data pipelines, transformations)
3. ✅ Derivatives and Gradients (model training, optimization)
4. ✅ Optimization Intuition (hyperparameters, overfitting)
5. ✅ Probability for ML (uncertainty, thresholds, risk)
6. ✅ Statistics for Monitoring (drift, control limits, significance)
7. ✅ Loss Functions (convergence, overfitting detection)
8. ✅ Scaling & Normalization (fairness, stability)

**What you can now do:**

- Understand the mathematics behind your models
- Debug training issues and interpret curves
- Make informed decisions about hyperparameters
- Monitor models in production for degradation
- Handle edge cases and numerical problems
- Explain ML concepts without the elitism

**Next steps in your MLOps journey:**

1. Apply these concepts to your actual models
2. Build monitoring dashboards based on statistical concepts
3. Experiment with different loss functions and metrics
4. Implement proper scaling and preprocessing pipelines
5. Set up early stopping and convergence detection

---

**End of Module 8. End of Curriculum.**
