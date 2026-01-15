# MODULE 5: Probability for ML (Understanding Uncertainty)

---

## What This Module Is About

**Plain English:** Probability is how we measure uncertainty. In MLOps, nothing is certain. Your model's predictions vary. Data is random. Errors happen.

Probability lets you quantify and work with that uncertainty.

Without understanding probability:
- You'll treat predictions as certain when they're not
- You won't know your model's confidence
- You can't set meaningful thresholds
- You'll be surprised when rare events happen
- You can't understand error margins

With understanding probability:
- You'll know your model's confidence in each prediction
- You can make risk-aware decisions
- You'll understand error rates and false positives
- You can set smart thresholds
- You can plan for edge cases

---

## Where You'll See This in MLOps

### **1. Classification Confidence**
```
Model predicts: "This is fraud" with 0.92 probability
Interpretation: 92% confident, 8% uncertain

Threshold: If probability > 0.5, flag as fraud
Result: Flag if > 50% confident (might catch false positives)

Decision: Set threshold to 0.8? (flag only if > 80% confident)
```

### **2. Error Rates and Expectations**
```
Model accuracy: 95% (on test data)
Meaning: In production, expect ~5% errors

If you process 10,000 predictions:
  Expected correct: 9,500
  Expected errors: 500

Planning: Allocate resources for 500 error reviews
```

### **3. False Positives vs. False Negatives**
```
Fraud detection:
  False positive: Flag legitimate as fraud (customer upset)
  False negative: Miss actual fraud (company loses money)

Cost: False negative costs $1000, false positive costs $10

Decision: Adjust threshold to reduce false negatives (higher cost)
```

### **4. Rare Events**
```
Your system has 99.9% uptime (0.1% downtime).
0.1% of 365 days = 0.365 days ≈ 9 hours per year

This "rare" event (9 hours downtime) is predictable and expected.
Planning: Schedule maintenance before expected downtime occurs
```

### **5. Sampling and Aggregation**
```
Test your model on 1,000 samples.
Accuracy: 94%

Question: Is the true accuracy 94% or somewhere else?
Answer: True accuracy is probably between 93-95% (confidence interval)
Not certain, but constrained.
```

---

## Core Concepts (Slow & Detailed)

### **Concept 1: Probability (Basic Definition)**

#### Definition
**Probability** is a number between 0 and 1 that represents how likely something is.

- 0 = impossible
- 1 = certain
- 0.5 = equally likely or unlikely

#### Operational Interpretation
```
Probability 0.9 = "In 10 similar situations, expect ~9 successes"
Probability 0.2 = "In 5 similar situations, expect ~1 success"
Probability 0.05 = "In 100 similar situations, expect ~5 occurrences"
```

#### Real Example: Weather
```
"50% chance of rain tomorrow"
Meaning: If we looked at 100 days with similar conditions, it rained on ~50 of them

"20% chance of snow"
Meaning: If we looked at 100 similar days, it snowed on ~20 of them
```

#### Real ML Example: Model Prediction
```
Model predicts: "Customer will churn" with probability 0.7
Meaning: Similar customers with this profile, ~70% actually churn

If you have 100 such customers:
  Expected churners: 70
  Expected retained: 30
```

---

### **Concept 2: The Distribution (How Probabilities Spread)**

#### Definition
A **distribution** describes how probabilities are spread across possible outcomes.

#### Visual Example: Normal Distribution
```
        |
        |  *
        | * *
        |*   *
        |*   *
    ____|_____*__→
   -3  -2  -1  0  1  2  3

This is the "bell curve". 
Most values near the center (mean).
Fewer values at the extremes.
```

#### Real ML Example: Model Confidence Scores
```
Your model outputs probabilities:
  5% chance: 0.05
  10% chance: 0.1
  15% chance: 0.15
  20% chance: 0.2
  18% chance: 0.25
  15% chance: 0.3
  10% chance: 0.35
  5% chance: 0.4
  2% chance: 0.5

Most predictions cluster around 0.2-0.3
Fewer predictions at extreme confidence (0.95, 0.05)

This is the distribution of your model's confidence.
```

---

### **Concept 3: Accuracy, Precision, Recall (Different Perspectives on Error)**

#### Definition
When your model makes predictions on classes (yes/no, fraud/legitimate):

- **Accuracy:** What % of all predictions are correct?
- **Precision:** Of the positives we predicted, what % are actually positive?
- **Recall:** Of the actual positives, what % did we predict?

#### Visual with a Confusion Matrix
```
                Predicted Positive    Predicted Negative
Actually Pos    TP (True Positive)    FN (False Negative)
Actually Neg    FP (False Positive)   TN (True Negative)

Accuracy = (TP + TN) / Total
Precision = TP / (TP + FP)   ← "Of what I predicted positive, how many were right?"
Recall = TP / (TP + FN)      ← "Of actual positives, how many did I find?"
```

#### Real Example: Fraud Detection
```
You predict 1,000 transactions:
                Predicted Fraud    Predicted Legit
Actually Fraud  95 (TP)            5 (FN)
Actually Legit  50 (FP)            850 (TN)

Accuracy = (95 + 850) / 1000 = 94.5%
Precision = 95 / (95 + 50) = 65.5%  ("Of 145 I flagged, only 65% were actual fraud")
Recall = 95 / (95 + 5) = 95%        ("Of 100 actual frauds, I caught 95")
```

#### When to Use Which
```
Precision matters when: False positives are expensive
  (e.g., rejecting legitimate customers)

Recall matters when: False negatives are expensive
  (e.g., missing fraud)

Accuracy: General purpose, but misleading if classes are imbalanced
  (If 99% are legit, a model that predicts "all legit" is 99% accurate but useless)
```

---

### **Concept 4: False Positive Rate (FPR) and True Positive Rate (TPR)**

#### Definition
- **FPR:** Of actual negatives, what % did we incorrectly predict as positive?
- **TPR:** Of actual positives, what % did we correctly predict? (same as Recall)

```
FPR = FP / (FP + TN)  ← "Of legitimate cases, how many did we incorrectly flag?"
TPR = TP / (TP + FN)  ← "Of fraud cases, how many did we catch?"
```

#### Why It Matters
You can move the threshold to trade off FPR and TPR:

```
Strict threshold (only predict fraud if model is >95% confident):
  High precision, high TPR, low FPR
  Catch most fraud, few false alarms

Loose threshold (predict fraud if model is >10% confident):
  Low precision, high TPR, high FPR
  Catch almost all fraud, many false alarms

You choose based on cost of each type of error.
```

---

### **Concept 5: The ROC Curve (Seeing All Tradeoffs)**

#### Definition
A **ROC curve** plots all possible TPR/FPR combinations as you vary the threshold.

#### Visual Example
```
TPR (Recall)
  |       *
  |      * *
  |     *   *
  |    *     *
  |   *       *
  |  *         *
  | *___________*
  |________________→ FPR
  0               1

Point at (0, 1): Perfect classifier
  (0 FPR: no false alarms, 1 TPR: catch everything)

Diagonal line: Random classifier
  (equally likely to be right or wrong)

Area Under Curve (AUC): How good is the model?
  AUC = 1.0: Perfect
  AUC = 0.5: Random (no better than flipping a coin)
  AUC = 0.8: Good
```

#### Real MLOps Usage
```
You train 3 models:
  Model A: AUC = 0.92
  Model B: AUC = 0.88
  Model C: AUC = 0.75

Model A is significantly better.
Model B is acceptable.
Model C is poor (barely better than random).

Decision: Use Model A.
```

---

### **Concept 6: Confidence Intervals (What the True Value Might Be)**

#### Definition
A **confidence interval** is a range of values where the true value probably lies.

#### Example
```
You test your model on 1,000 samples.
Accuracy: 94%

Question: Is the true accuracy 94%?
Answer: No, but it's probably close.

95% confidence interval: 92.5% to 95.5%
Meaning: In 95 out of 100 experiments, the true accuracy falls in this range.
```

#### Why It Matters
```
Test accuracy: 94%
95% CI: 92.5% to 95.5%

Two models:
  Model A: Accuracy 94%, CI: 92.5% to 95.5%
  Model B: Accuracy 93%, CI: 91.0% to 95.0%

Are they different?
  Not necessarily! The confidence intervals overlap.
  Statistically, they might be equivalent.
```

#### Real Scenario
```
You deploy Model A.
One week later, accuracy on new data: 91%

Is this normal variation or is the model degrading?

If 95% CI from training is 92.5% to 95.5%:
  91% is outside the confidence interval
  This suggests real degradation (not just random variation)
  
Action: Investigate and possibly retrain.
```

---

## Worked Examples (Step-by-Step)

### **Worked Example 1: Choosing a Fraud Detection Threshold**

**Scenario:** Your fraud model outputs probabilities. You need to choose a threshold.

Data from 10,000 test transactions:
```
Threshold 0.5: TP=450, FN=50, FP=200, TN=9300
Threshold 0.7: TP=400, FN=100, FP=80, TN=9420
Threshold 0.9: TP=300, FN=200, FP=10, TN=9490
```

Business costs:
- False positive (block legitimate): $10 cost + customer frustration
- False negative (miss fraud): $1,000 loss

**Question:** What threshold should you use?

**Step 1: Calculate metrics for each**
```
Threshold 0.5:
  Precision = 450 / (450 + 200) = 69%
  Recall = 450 / (450 + 50) = 90%
  FPR = 200 / (200 + 9300) = 2.1%
  
  False positive cost: 200 × $10 = $2,000
  False negative cost: 50 × $1,000 = $50,000
  Total cost: $52,000

Threshold 0.7:
  Precision = 400 / (400 + 80) = 83%
  Recall = 400 / (400 + 100) = 80%
  
  False positive cost: 80 × $10 = $800
  False negative cost: 100 × $1,000 = $100,000
  Total cost: $100,800

Threshold 0.9:
  Precision = 300 / (300 + 10) = 97%
  Recall = 300 / (300 + 200) = 60%
  
  False positive cost: 10 × $10 = $100
  False negative cost: 200 × $1,000 = $200,000
  Total cost: $200,100
```

**Step 2: Compare**
```
Threshold 0.5: $52,000 total cost (lowest)
Threshold 0.7: $100,800 total cost
Threshold 0.9: $200,100 total cost
```

**Step 3: Decision**
```
Choose threshold 0.5.

Cost-benefit: Catch more fraud (cost $50,000) vs. false alarms (cost $2,000).
It's worth having some false positives to avoid high fraud losses.

Alternative: If customer frustration is a big issue, threshold 0.7 is a compromise.
```

---

### **Worked Example 2: Interpreting Test Results**

**Scenario:** Your model trained and tested on 500 samples.

Test accuracy: 87%
Test precision: 82%
Test recall: 79%

**Question:** Is this good? Should you deploy?

**Step 1: Check sample size**
```
500 samples is moderate (good for initial evaluation, but not huge).

Typical rule: Need at least 30 samples of minority class for reliable estimates.
If your minority class is fraud (10% of data = 50 samples), that's borderline.
```

**Step 2: Calculate confidence intervals** (rough approximation)
```
Accuracy 87% on 500 samples:
  Standard error ≈ sqrt(0.87 × 0.13 / 500) ≈ 1.5%
  95% CI: 87% ± 3% = 84% to 90%
  
Interpretation: True accuracy is likely between 84-90%.
If your requirement is 90%, this doesn't quite meet it (confidence interval includes below 90%).

Recall 79% on 500 samples:
  Standard error ≈ sqrt(0.79 × 0.21 / 50) ≈ 5.7%  (using minority class count)
  95% CI: 79% ± 11% = 68% to 90%
  
Interpretation: True recall is uncertain, could be as low as 68%.
```

**Step 3: Decision**
```
Metrics look reasonable, but confidence intervals are wide.
Recommendation:
  1. Deploy to production with monitoring
  2. Track actual metrics in production
  3. Retrain when you have more data
  4. Expect production accuracy to be ~84-90% (based on confidence intervals)
```

---

### **Worked Example 3: Expected Number of Errors in Production**

**Scenario:** You deploy a model with 95% accuracy. It processes 1 million predictions per day.

**Question:** How many errors should you expect per day?

**Step 1: Calculate expected errors**
```
Accuracy: 95%
Error rate: 5% (100% - 95%)

Predictions: 1,000,000
Expected errors: 0.05 × 1,000,000 = 50,000 errors per day
```

**Step 2: Break down by type** (assuming binary classification)
```
If 50% positive, 50% negative class:

False positives (errors on negative class):
  Assuming precision 92%: 0.08 × (0.5 × 1M) = 40,000 false positives

False negatives (errors on positive class):
  Assuming recall 98%: 0.02 × (0.5 × 1M) = 10,000 false negatives

Total: 50,000 (matches)
```

**Step 3: Plan for the scale**
```
50,000 errors per day.
That's:
  - 2,083 per hour
  - 35 per minute
  
This is very high! 

Action:
  - Set up automated error handling/logging
  - Sample errors for manual review (can't review all 50k)
  - Monitor error rate in real-time
  - Alert if error rate spikes above 5%
```

---

## Common Confusions & Traps

### **Trap 1: Confusing Accuracy with What You Actually Care About**

```
Two models:
  Model A: 99% accuracy
  Model B: 90% accuracy

Which is better?

If data is 99% class A, 1% class B:
  Model A might just predict "always A" (useless, but 99% accurate)
  Model B might correctly identify 90% of class B (useful)

Accuracy misleads when classes are imbalanced.
Use precision/recall or F1 score instead.
```

---

### **Trap 2: Thinking High Recall Means No Problems**

```
Recall = 95%: "We catch 95% of fraud"

Missing cases: 5% of fraud goes undetected.

If your fraud detection needs to catch 99.9% to be acceptable, 95% is bad.
```

---

### **Trap 3: Small Sample Size False Confidence**

```
You test on 10 samples.
Accuracy: 100% (10/10 correct)

Confidence: "Perfect model!"

Reality: 100% on 10 samples is expected noise, not skill.
95% CI for true accuracy: ~71% to 100%

Wait for 100+ samples before claiming success.
```

---

### **Trap 4: Ignoring Class Imbalance**

```
Your test set: 995 legitimate, 5 frauds

Your model: Always predicts "legitimate"
Accuracy: 99.5% !!

But: Catches 0 frauds (useless for actual fraud detection)

Lesson: Don't use accuracy on imbalanced data.
Use precision, recall, F1, or confusion matrix.
```

---

## Practice Questions

### **Easy Questions**

**Q1: Probability Interpretation**
A weather forecast says "70% chance of rain."

What does this mean?

<details>
<summary>Click to see answer</summary>

**Answer:** In similar weather conditions, it rains about 70% of the time.

Or: If we looked at 100 days with similar conditions, it rained on ~70 of them.

Not: "Rain will cover 70% of the area" (that's a different kind of probability).

</details>

---

**Q2: Identifying Accuracy Mislead**
Dataset: 10,000 samples (9,900 negative, 100 positive)
Model: Always predicts negative
Accuracy: 99%

Is this a good model?

<details>
<summary>Click to see answer</summary>

**Answer:** No, it's useless.

**Why:** Accuracy is 99%, but the model never detects the positive class (recall = 0%).
On imbalanced data, accuracy is misleading.

**Better metric:** Precision/recall or F1 score.

</details>

---

**Q3: ROC/AUC Understanding**
Model A: AUC = 0.9
Model B: AUC = 0.55

Which is better?

<details>
<summary>Click to see answer</summary>

**Answer:** Model A is significantly better.

**Why:** 
- AUC = 0.9: Good, can separate positive/negative well
- AUC = 0.55: Barely better than random (0.5)

Choose Model A.

</details>

---

### **Medium Questions**

**Q4: Precision vs. Recall Decision**
You're building a fraud detection system.

False positive: Block legitimate customer, they leave
False negative: Miss fraud, company loses $10,000

Which should you prioritize: precision or recall?

<details>
<summary>Click to see answer</summary>

**Answer:** Recall (catching fraud) is more important.

**Why:** False negatives cost $10,000 each (company loss). False positives cost customer frustration (eventually replaceable, but expensive). 

High recall means: Catch as much fraud as possible.
Accept some false positives.

Trade-off: Reduce threshold to flag more as fraud (increase recall).

</details>

---

**Q5: Confidence Interval Interpretation**
Test accuracy: 89%
95% confidence interval: 87% to 91%

Your requirement: accuracy > 90%

Does this model meet the requirement?

<details>
<summary>Click to see answer</summary>

**Answer:** Not confidently.

**Why:** The CI is 87% to 91%. The true accuracy could be as low as 87%, which is below 90%.

**Action:** Collect more test data to narrow the confidence interval. Or accept the risk that true accuracy might be 87%.

</details>

---

**Q6: Scaling Errors**
Test accuracy: 98% on 1,000 samples
Production volume: 10 million predictions/day

How many errors per day?

<details>
<summary>Click to see answer</summary>

**Answer:** 200,000 errors per day.

**Calculation:**
- Error rate: 2% (100% - 98%)
- Errors: 0.02 × 10M = 200,000

**Impact:** That's 200k errors daily! Need automated handling, logging, monitoring.

</details>

---

### **Hard Questions**

**Q7: ROC Threshold Selection**
Your model's ROC curve shows:
- Threshold 0.5: TPR = 85%, FPR = 10%
- Threshold 0.6: TPR = 80%, FPR = 5%
- Threshold 0.7: TPR = 70%, FPR = 2%

Cost: Each false negative costs $500, each false positive costs $20.

Which threshold should you choose?

<details>
<summary>Click to see answer</summary>

**Answer:** Threshold 0.5.

**Calculation:**
(Using 10,000 test samples)

Threshold 0.5:
- FN = 15% × 5000 = 750, cost = $375,000
- FP = 10% × 5000 = 500, cost = $10,000
- Total: $385,000

Threshold 0.6:
- FN = 20% × 5000 = 1000, cost = $500,000
- FP = 5% × 5000 = 250, cost = $5,000
- Total: $505,000

Threshold 0.7:
- FN = 30% × 5000 = 1500, cost = $750,000
- FP = 2% × 5000 = 100, cost = $2,000
- Total: $752,000

Threshold 0.5 has lowest total cost.

</details>

---

**Q8: Sample Size Impact**
You test your model on 50 samples with 94% accuracy.

Is this a strong result?

<details>
<summary>Click to see answer</summary>

**Answer:** Weak. The sample size is too small.

**Why:** 94% on 50 samples = ~3 errors. The standard error is high.

95% CI: ~94% ± 7% = 87% to 101% (wide!)

**Rule of thumb:** Use at least 100-300 samples for reliable accuracy estimates.

**What to do:** Test on more samples or use cross-validation.

</details>

---

## MLOps Reality Check

### **Failure Mode 1: Deploying with Misleading Accuracy**
```
Model trained on balanced data: 92% accuracy
Deployed to production (9:1 class imbalance): 85% accuracy

Why the drop?
  Accuracy metric isn't appropriate for imbalanced data.
  On imbalanced data, accuracy is naturally lower even for good models.

Fix: Monitor precision/recall in production, not just accuracy.
```

---

### **Failure Mode 2: Not Planning for Scale**
```
Model accuracy: 99% on 1,000 test samples
Deploy to 1 billion predictions/month

Errors: 0.01 × 1B = 10 million per month

Expected? Not planned for.
Cost: Can't manually review 10M errors, systems overload, outages.

Fix: Plan error handling and monitoring for the scale.
```

---

### **Failure Mode 3: Threshold Never Tuned**
```
Default threshold: 0.5 (for any binary classification)

Cost analysis shows:
  Optimal threshold: 0.7 (based on business costs)

Using 0.5 wastes resources.

Fix: Analyze costs, compute optimal threshold, implement it.
```

---

## Summary & Next Steps

**You now understand:**

1. **Probability:** How to measure uncertainty
2. **Classification metrics:** Accuracy, precision, recall, F1
3. **Error types:** False positives, false negatives, costs
4. **Threshold tuning:** Balancing tradeoffs
5. **Confidence intervals:** Uncertainty in estimates
6. **ROC/AUC:** Comprehensive model evaluation

**In your pipeline, you can now:**
- Understand model confidence in predictions
- Set smart thresholds based on costs
- Evaluate models appropriately
- Plan for error scale
- Monitor production performance

**In the next module** (Module 6):
- Statistics for monitoring and drift detection

---

**End of Module 5.**
