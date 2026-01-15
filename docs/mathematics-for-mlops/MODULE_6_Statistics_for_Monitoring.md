# MODULE 6: Statistics for Monitoring and Drift Detection

---

## What This Module Is About

**Plain English:** Your model works great on test data, then fails in production. Why? The data changed.

Statistics gives you tools to:
- Detect when data changes (data drift)
- Detect when performance degrades (model drift)
- Know what's normal vs. abnormal
- Alert before things break

Without statistics, you have blind faith. With statistics, you measure.

---

## Where You'll See This in MLOps

### **1. Data Drift Detection**
```
Training data: Customer ages 18-65, avg income $50k
Production data: Suddenly lots of age 70+, avg income $120k

System: "Is this drift, or normal variation?"
Solution: Statistical test. If change is >2 standard deviations from normal, alert.
```

### **2. Model Performance Degradation**
```
Model accuracy: 92% historically
Last week: 87% accuracy
Question: Did the model actually degrade, or is this random variation?

Statistical answer: If 87% is >2 standard deviations below 92%, model degraded.
Action: Investigate and retrain.
```

### **3. Baseline Behavior (Normal Range)**
```
Error rate normally: 2-3%
This week: 5% error rate

Is 5% a problem? 
Statistical answer: If historical distribution shows 2-3%, then 5% is abnormal.
Alert: Yes, something changed.
```

### **4. Comparing Models in Production**
```
Model A: 91% accuracy ± 1.5%
Model B: 92% accuracy ± 1.4%

Is Model B better?
Statistical answer: Confidence intervals overlap slightly. 
Not clearly different. Maybe not worth switching.
```

### **5. Decision Thresholds (When to Act)**
```
Accuracy alerts:
  Normal range: 90-93%
  Warning: Below 90% or above 93%
  Critical: Below 88% or above 95%

Based on statistics, you set threshold bands.
```

---

## Core Concepts (Slow & Detailed)

### **Concept 1: Mean and Standard Deviation (Center and Spread)**

#### Definition
- **Mean:** The average
- **Standard Deviation (σ):** How much values spread around the average

#### Formulas (Don't Memorize, Just Understand)
```
Mean = sum of all values / count

Standard Deviation = sqrt(average of squared differences from mean)

Example:
Values: 10, 20, 30
Mean = (10+20+30)/3 = 20

Differences from mean: -10, 0, +10
Squared: 100, 0, 100
Average squared: 200/3 ≈ 67
SD = sqrt(67) ≈ 8.2
```

#### Why It Matters
```
If mean accuracy is 90% with SD = 1%:
  Normal range: 88% to 92% (within 2 SDs)
  Anomaly: 87% or 93% (outside 2 SDs)

If mean accuracy is 90% with SD = 5%:
  Normal range: 80% to 100% (wider, more variation)
  Anomaly: Much harder to detect (needs to be <75% or >105%)

Lower SD = more consistent, easier to spot problems.
Higher SD = more noise, harder to spot problems.
```

#### Real MLOps Example
```
Model latency:
  Mean: 150ms
  SD: 10ms
  Normal range: 130-170ms

If latency spikes to 200ms:
  Outside normal range (>2 SDs), alert!
```

---

### **Concept 2: Distribution Shape (Normal, Skewed, Heavy-tailed)**

#### Definition
How values are spread matters. Different shapes have different properties.

#### Normal Distribution (Bell Curve)
```
        |
        |  *
        | * *
        |*   *
    ____|_____*__
   -3  -2  -1  0  1  2  3

Properties:
- 68% of values within 1 SD of mean
- 95% of values within 2 SDs
- 99.7% of values within 3 SDs
```

#### Skewed Distribution (Tail on One Side)
```
      |
      |
    * | *
  *   |   *
 *    |    * *
*_____|_______ *

Mean is pulled toward the tail.
Contains rare extreme values.
```

#### Heavy-tailed Distribution (Lots of Extremes)
```
     |
     |
   * | *
 *   |   *
*    |    * * *
*____|_______* * * *

Many more extreme values than normal distribution.
Standard deviation less meaningful.
```

#### MLOps Implication
```
Latency distribution:
  Normally: Bell curve, mean 150ms ± 10ms
  After load spike: Heavy-tailed, outliers at 5000ms+
  
Statistical alert: Distribution changed (not just mean).
This tells you load handling broke, not just a random spike.
```

---

### **Concept 3: Statistical Significance (Difference is Real, Not Luck)**

#### Definition
A change is **statistically significant** if it's unlikely to be random chance.

#### Example
```
Coin flipped 10 times: Heads 6 times, Tails 4 times
Is the coin biased?

No. Even a fair coin produces this sometimes.
6/10 is normal variation.
```

---

```
Coin flipped 1000 times: Heads 700 times, Tails 300 times
Is the coin biased?

Yes! Impossible for a fair coin.
700/1000 is statistically significant.

Probability of this happening by chance: <0.0001%
Conclusion: The coin (or flip process) is biased.
```

#### Decision Rule
```
Is a change significant?

Calculate: "How likely is this difference by pure chance?"

If probability < 5% (or 1%, depends on field):
  Significant! Change is real.

If probability > 5%:
  Not significant. Could be random luck.
```

#### MLOps Example
```
Model accuracy drop:
  Historical: 92% ± 0.5%
  Last week: 90%

Question: Is this real degradation or random luck?

Statistical test:
  Probability of seeing 90% when true accuracy is 92%: 2%
  2% < 5% threshold
  Conclusion: Significant! Real degradation detected.

Action: Investigate root cause, retrain model.
```

---

### **Concept 4: P-Value (Probability of Being Wrong)**

#### Definition
**P-value:** Probability of seeing this result if nothing actually changed.

#### How to Interpret
```
P-value = 0.05 (5%)
Meaning: If nothing changed, we'd see this result 5% of the time.

P-value = 0.001 (0.1%)
Meaning: If nothing changed, we'd see this result 0.1% of the time.
Conclusion: Almost certainly something changed.

P-value = 0.50 (50%)
Meaning: If nothing changed, we'd see this result 50% of the time.
Conclusion: Normal random variation, nothing changed.
```

#### Decision Threshold
```
Industry standard: P-value < 0.05 means significant change

If p-value < 0.05:
  Reject "nothing changed"
  Accept "something actually changed"
  
If p-value > 0.05:
  Can't reject "nothing changed"
  Might just be random luck
```

#### Real Example
```
Your model accuracy:
  Week 1-4: 92%
  Week 5: 89%

Test: Is this degradation real or luck?

P-value calculation: 0.02

Result: P-value = 0.02 < 0.05 threshold
Conclusion: Significant degradation detected!
This is not just random luck.

Action: Investigate and retrain.
```

---

### **Concept 5: Control Limits and Anomaly Detection**

#### Definition
**Control limits** define the normal operating range. Outside = alert.

#### How to Set Them
```
Calculate from historical data:
  Historical accuracy: 92%
  Standard deviation: 1%

Control limits:
  Upper: 92% + (3 × 1%) = 95%
  Lower: 92% - (3 × 1%) = 89%

Normal: 89-95%
Alert if: <89% or >95%
```

#### Why 3 Standard Deviations?
```
In normal distribution:
- 1 SD: 68% of values (some outliers expected)
- 2 SD: 95% of values (fewer outliers)
- 3 SD: 99.7% of values (very rare outliers)

Using 3 SD means <0.3% false alarms from random variation.
This keeps you from over-alerting.
```

#### Real Dashboard Example
```
Model Accuracy Monitor

Current: 91%
Normal range: 89% - 95%
Status: NORMAL

Warning: Accuracy falls between 88% - 89% or 95% - 96%
Alert: Accuracy below 88% or above 96%

(Red zone = something is definitely wrong)
```

---

### **Concept 6: Drift Detection (Comparing Distributions)**

#### Definition
**Drift** is when the distribution of data changes significantly.

Types of drift:
- **Covariate drift:** Input features change (e.g., customer profile changes)
- **Label drift:** Target variable distribution changes (e.g., fraud rate increases)
- **Concept drift:** Relationship between input and output changes

#### How to Detect
```
Method 1: Compare means
  Old data mean: $50k income
  New data mean: $65k income
  
  Statistical test: Is this difference significant?
  If yes: Drift detected (customer profile changed)

Method 2: Compare distributions
  Old data: Bell curve centered at 50k
  New data: Bell curve centered at 65k, but wider
  
  Statistical test: Are these distributions different?
  If yes: Drift detected (different shape = different behavior)

Method 3: Kolmogorov-Smirnov Test
  Compares entire distributions, detects any difference
  Simple rule: If KS test p-value < 0.05, distributions differ
```

#### Real Example
```
Training data (6 months ago):
  Customer age: Mean 42, SD 8
  Income: Mean $52k, SD $15k

Current production data (last week):
  Customer age: Mean 48, SD 10
  Income: Mean $68k, SD $18k

Analysis:
  Age difference: +6 years (real drift, older customers)
  Income difference: +$16k (real drift, wealthier customers)
  
Result: Covariate drift detected
Action: Retrain model on recent data to match current customer profile
```

---

## Worked Examples (Step-by-Step)

### **Worked Example 1: Setting Up Model Monitoring**

**Scenario:** You're deploying a model and need to set up alerts. You have 1 month of historical performance data.

Historical performance:
```
Accuracy: 92.1% (day 1), 91.8% (day 2), 92.3% (day 3), ..., 91.9% (day 30)
Mean: 92.0%
SD: 0.8%
```

**Question:** What control limits should you set?

**Step 1: Calculate control limits**
```
Using 3 standard deviation rule:
  Upper control limit: 92.0% + 3(0.8%) = 94.4%
  Lower control limit: 92.0% - 3(0.8%) = 89.6%
  
Warning limits (2 SD):
  Upper: 92.0% + 2(0.8%) = 93.6%
  Lower: 92.0% - 2(0.8%) = 90.4%
```

**Step 2: Set alerting rules**
```
GREEN (Normal): 90.4% to 93.6%
YELLOW (Warning): 89.6% to 90.4% or 93.6% to 94.4%
RED (Alert): Below 89.6% or above 94.4%
```

**Step 3: Implement dashboard**
```
Daily monitoring:
- If day's accuracy in GREEN: All good, no action
- If day's accuracy in YELLOW: Check logs, investigate slightly
- If day's accuracy in RED: Page on-call, something's wrong
```

**Step 4: Reasoning**
```
Why these limits?
- 3 SD rule: False alarm rate ~0.3% (only triggers if really abnormal)
- 2 SD rule: Alert once/month on random variation alone
- Balanced: Catch real problems without noise

If you set limits too wide (like 5% above/below):
  Miss real degradation

If you set limits too narrow (like 0.5%):
  Constant false alarms (alert fatigue)

3 SD is the practical sweet spot.
```

---

### **Worked Example 2: Detecting Drift**

**Scenario:** Your fraud model trained 6 months ago. You need to detect if data has drifted.

Training data (6 months ago):
```
Transaction amount: Mean $125, SD $45
Age of customer: Mean 38, SD 12
Time of day: 70% daytime, 30% evening
```

Current data (last week):
```
Transaction amount: Mean $110, SD $50
Age of customer: Mean 35, SD 13
Time of day: 50% daytime, 50% evening
```

**Question:** Has drift occurred?

**Step 1: Test each feature**
```
Transaction amount:
  Old: mean=125, SD=45
  New: mean=110, SD=50
  Difference: -15
  
  Is -15 statistically significant?
  Standard error: sqrt(45²/n_old + 50²/n_new)
  (Assuming n>100)
  
  Difference is ~0.3 SDs (within normal noise)
  P-value: ~0.76 (high)
  Conclusion: NOT significant
  
  Transaction amounts haven't really changed.

Age of customer:
  Old: mean=38
  New: mean=35
  Difference: -3
  
  SD of difference: ~1.2
  Difference is ~2.5 SDs
  P-value: ~0.01 (low)
  Conclusion: SIGNIFICANT
  
  Customer base is getting younger.

Time of day:
  Old: 70% daytime vs. 30% evening
  New: 50% daytime vs. 50% evening
  
  Difference: -20 percentage points
  P-value: <0.001 (very low)
  Conclusion: HIGHLY SIGNIFICANT
  
  Usage patterns completely changed (more evening transactions).
```

**Step 2: Overall verdict**
```
Customer age: Drifted (getting younger)
Time of day: Drifted significantly (more evening transactions)
Transaction amount: Stable

Result: Covariate drift detected
```

**Step 3: Action**
```
Implications:
- Model was trained on older customers (avg 38)
- Now serving younger customers (avg 35)
- Behavior is different between age groups

Actions:
1. Retrain model on recent data (younger customer profile)
2. Monitor age distribution continuously
3. Set alert if mean age changes >5 years
```

---

### **Worked Example 3: Determining Significance of Performance Change**

**Scenario:** Your model had been stable at 91% accuracy. Last week it dropped to 87%.

Historical baseline:
```
Accuracy: 90.5% - 92.5% (last 90 days)
Mean: 91.2%
SD: 0.9%
```

Last week:
```
Monday: 90.8%
Tuesday: 88.2%
Wednesday: 87.1%
Thursday: 86.9%
Friday: 87.3%
Average last week: 88.1%
```

**Question:** Is this degradation real or random noise?

**Step 1: Calculate difference**
```
Historical mean: 91.2%
Last week mean: 88.1%
Difference: -3.1 percentage points
```

**Step 2: Test for significance**
```
How many standard deviations is -3.1%?
-3.1 / 0.9 ≈ 3.4 SDs below normal

In normal distribution:
  >3.4 SDs = extremely rare (p-value < 0.0005)
```

**Step 3: Conclusion**
```
Result: Highly significant degradation

P-value: < 0.0005 (less than 0.05% chance of random luck)
Interpretation: This is almost certainly a real problem, not noise.

Confidence: 99.95% confident degradation is real
```

**Step 4: Action**
```
Immediate:
1. Check recent data for drift (customer profile changed?)
2. Check for data quality issues
3. Check for environment changes (inference hardware, serving code)

Within 24 hours:
1. Investigate root cause
2. If drift detected, retrain model
3. If quality issue, fix data pipeline
4. Deploy fix and monitor

Within 1 week:
1. Post-mortem (what failed, how prevent next time)
2. Add monitoring for early drift detection
3. Consider weekly retraining to stay current
```

---

## Common Confusions & Traps

### **Trap 1: Confusing Statistical Significance with Practical Significance**

```
Model accuracy:
  Before: 91.00%
  After: 91.02%
  
P-value: 0.03 (statistically significant)

Interpretation: The difference is real, not luck.

But: 0.02% improvement is negligible.
Worth the effort to deploy? Probably not.

Lesson: Significant ≠ Important. Look at actual difference magnitude.
```

---

### **Trap 2: Over-Alerting Due to Tight Limits**

```
You set control limits to 1 SD:
  Normal range: 91% ± 0.5% (91.5% to 90.5%)

Result: Alert every 3-4 days on random variation

Problem: Alert fatigue. People ignore alerts.

Fix: Use 3 SD (false alarm rate ~0.3% per day, better).
```

---

### **Trap 3: Not Accounting for Seasonality**

```
Your fraud model:
  Summer: 5% fraud rate
  Winter: 7% fraud rate
  
You set alert threshold at 6%.

Winter comes: Alert triggers constantly.

Problem: You ignored seasonal pattern.

Fix: Set different thresholds for different seasons.
Or: Retrain model monthly to account for seasonality.
```

---

### **Trap 4: Small Sample Size False Positives**

```
You test for drift on yesterday's data (100 transactions).

Test shows drift (p-value = 0.04).

Alert! Something changed!

Problem: Sample size is tiny. p-value could be noise.

Fix: Wait for more data (1000+ transactions) before alerting.
Or: Use higher threshold (p < 0.01 instead of 0.05).
```

---

## Practice Questions

### **Easy Questions**

**Q1: Mean vs. Standard Deviation**
Dataset: Latency values 100ms, 150ms, 140ms, 160ms, 130ms

What is approximately:
A) Mean (average)
B) Rough range (±1 SD)

<details>
<summary>Click to see answer</summary>

**Answer:**
A) Mean = (100+150+140+160+130)/5 = 140ms

B) Range approximation:
   Differences from mean: -40, +10, 0, +20, -10
   Rough SD ≈ 20ms
   Normal range: 120-160ms (140 ± 20)

(Exact SD calculation would give ~24ms, but that's OK)

</details>

---

**Q2: Normal vs. Abnormal**
Your model accuracy:
- Normal: 89-93%
- Yesterday: 88.5%

Is this abnormal?

<details>
<summary>Click to see answer</summary>

**Answer:** Borderline. At edge of normal range.

88.5% is just outside the 89-93% band.

Action: Monitor trend. If next day is also 88%, alert. If bounces back to 90%, OK.

</details>

---

**Q3: P-Value Interpretation**
Statistical test result: p-value = 0.08

Is the change significant?

<details>
<summary>Click to see answer</summary>

**Answer:** No, not at standard 0.05 threshold.

0.08 > 0.05, so the change is not statistically significant.
Could be random luck.

(In some fields, 0.10 threshold is used, but 0.05 is standard for ML.)

</details>

---

### **Medium Questions**

**Q4: Control Limit Calculation**
Historical accuracy: mean 91%, SD 0.6%

Using 2 SD rule, what's the warning range?

<details>
<summary>Click to see answer</summary>

**Answer:**
Upper: 91% + 2(0.6%) = 92.2%
Lower: 91% - 2(0.6%) = 89.8%

Warning range: 89.8% to 92.2%

Outside this range = warning alert (check logs).

</details>

---

**Q5: Drift Detection**
Training data (3 months ago): Customer age mean 45, SD 10
Current data: Customer age mean 38, SD 11

Has customer age drifted?

<details>
<summary>Click to see answer</summary>

**Answer:** Likely yes.

Difference: 45 - 38 = 7 years

Standard error of difference: ~1.4 years (rough)
Difference is ~5 SDs (7/1.4)

This is highly significant (p < 0.001).

Conclusion: Customer base got younger.
Action: Retrain model on current age distribution.

</details>

---

**Q6: Alert Sensitivity**
You set alert threshold at 1 SD from mean.

Expected false alarm rate (on stable system)?

<details>
<summary>Click to see answer</summary>

**Answer:** ~32% per day (high!).

Reason:
- Normal distribution: 68% within 1 SD
- So 32% outside 1 SD
- If you check daily, you'll alert once every 3 days just on random variation

This is too sensitive.

Better: Use 3 SD (false alarm rate 0.3% per day).

</details>

---

### **Hard Questions**

**Q7: Multiple Testing Problem**
You monitor 100 metrics for drift.
Each test uses p-value < 0.05.

Expected false positives per week (on stable system)?

<details>
<summary>Click to see answer</summary>

**Answer:** ~35 false positives per week.

Why:
- 100 metrics × 0.05 false positive rate = 5 per day
- 5 × 7 days = 35 per week

This is alert fatigue!

Fix: Bonferroni correction
- Adjust threshold: 0.05 / 100 = 0.0005 per test
- Or: Use higher threshold like 0.01 per test
- Or: Combine related metrics into composite alerts

(This is called the "multiple testing problem")

</details>

---

**Q8: Seasonality and Thresholds**
Model accuracy:
- Q1 (winter): 88-92% (mean 90%)
- Q2 (spring): 90-94% (mean 92%)
- Q3 (summer): 92-96% (mean 94%)
- Q4 (fall): 89-93% (mean 91%)

Should you use the same alert threshold for all seasons?

<details>
<summary>Click to see answer</summary>

**Answer:** No, adjust for seasonality.

If you use single threshold (e.g., 88-96%):
- Summer accuracy naturally high, might miss degradation
- Winter accuracy naturally low, might false alert

Better approach:
- Q1 alerts: <86% or >94% (2% below/above seasonal mean)
- Q2 alerts: <88% or >96%
- Q3 alerts: <90% or >98%
- Q4 alerts: <87% or >95%

This matches expected seasonal variation.

Or: Retrain monthly to stay aligned with current season.

</details>

---

## MLOps Reality Check

### **Failure Mode 1: No Monitoring = Blind Deployment**
```
Model deployed with 92% test accuracy.
In production: Accuracy slowly degrades to 87% over 2 months.

Nobody noticed.

Damage:
- 2 months of poor predictions served to users
- Lost customer trust
- Competitors caught up

Fix: Implement control limits and daily monitoring.
Alert when accuracy drops below 90%.
```

---

### **Failure Mode 2: False Alerts = Alert Fatigue**
```
Alert threshold set too tight (90% accuracy).
Results:
- Alerts every 1-2 days
- Engineers start ignoring alerts
- Real problem occurs, gets ignored as "just another alert"

Fix: Use 3 SD rule for realistic alert rates.
Expected: ~1 false alarm per year, not per week.
```

---

### **Failure Mode 3: Undetected Drift**
```
Model accuracy stable at 92%, but:
- Customer age distribution shifted younger
- Usage patterns changed (more mobile vs. web)
- Data quality degraded

Accuracy still 92%, but for wrong reasons (fitting noise).

Result: Model works until something breaks suddenly.

Fix: Monitor individual features for drift, not just accuracy.
Detect changes early before they break the model.
```

---

### **Failure Mode 4: Single Threshold Across Contexts**
```
Model deployed in US and Europe.

US: Normal accuracy 90%
Europe: Normal accuracy 87% (different user behavior)

You set alert at 88%.

Result:
- Europe constantly below alert (false positives)
- US degradation to 89% not detected (false negative)

Fix: Use separate baselines and thresholds per region/segment.
```

---

## Summary & Next Steps

**You now understand:**

1. **Mean and SD:** How to describe data with 2 numbers
2. **Normal distribution:** Most values cluster around mean
3. **Control limits:** Define normal operating range (±3 SD)
4. **Statistical significance:** Change is real, not luck
5. **P-values:** Probability of seeing result if nothing changed
6. **Drift detection:** Methods to detect when data changes
7. **Practical vs. statistical significance:** Significant ≠ Important

**In your pipeline, you can now:**
- Set up monitoring dashboards with control limits
- Detect when models degrade
- Distinguish signal from noise
- Detect data drift before it breaks models
- Alert appropriately (not too sensitive, not too loose)

**In the next module** (Module 7):
- Loss functions and convergence behavior

---

**End of Module 6.**
