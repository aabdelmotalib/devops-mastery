# Quick Reference: Modules 1-3 Summary

## Module 1: Absolute Basics (Numbers You Can Trust)

**Core Concepts:**
- **Sign:** Direction (positive/negative)
- **Magnitude:** Absolute size of a number
- **Ratio:** Comparison via division (new ÷ old)
- **Percentage:** Ratio scaled to 100 (useful for comparisons)
- **Order of magnitude:** Powers of 10 (10×, 100×, etc.)
- **Trend:** Direction over time (increasing/decreasing)

**Key Formulas:**
```
Percentage change = (New - Old) / Old × 100%
Ratio = New ÷ Old
Order of magnitude: 10^n (e.g., 1,000 = 10³, 10,000 = 10⁴)
```

**In MLOps:**
- Read dashboards (latency, error rate, CPU, memory)
- Spot trends before they become crises
- Understand data drift and degradation
- Calculate cost per prediction, error per scale

**Red Flags:**
- Percentage on large numbers (0.5% of 1 billion = 5 million!)
- Ignoring trends (metrics look flat but decreasing)
- Confusing absolute and relative change
- Dashboard scales that mislead

---

## Module 2: Functions and Mappings (Turning Inputs into Outputs)

**Core Concepts:**
- **Function:** Input → Rule → Output (deterministic)
- **Domain:** Valid inputs
- **Range:** Possible outputs
- **Composition:** Chaining functions (output of one = input of next)
- **Linear function:** Proportional change (f(x) = mx + b)
- **Non-linear function:** Non-proportional change (exponential, sigmoid, etc.)
- **Piecewise function:** Different rules for different input ranges

**Key Operations:**
```
Simple composition: raw → [function 1] → [function 2] → output

Order matters: f(g(x)) ≠ g(f(x)) in general

Linear scaling: f(x) = (x - min) / (max - min)
Sigmoid: f(x) = 1 / (1 + e^(-x))
```

**In MLOps:**
- Data pipelines (Parse → Clean → Normalize → Feature Engineer → Model)
- Feature scaling and transformations
- Model inference (prediction → threshold → decision)
- Loss functions and metrics

**Red Flags:**
- Changing function order without retraining downstream
- Domain/range mismatches (input outside training range)
- Non-linear behavior extrapolated linearly
- Assumption of linearity when behavior is piecewise

---

## Module 3: Derivatives and Gradients (How Things Change)

**Core Concepts:**
- **Derivative:** Rate of change at a point (∂f/∂x)
- **Gradient:** Collection of derivatives for multiple inputs (∇f)
- **Gradient descent:** Algorithm to minimize loss (move opposite gradient)
- **Learning rate:** Step size in direction of gradient
- **Convergence:** When gradient approaches zero (reached minimum)
- **Local minimum:** Lowest point nearby (might not be global best)
- **Vanishing gradient:** Gradient gets smaller as you go deeper (early layers don't learn)

**Key Algorithm (Gradient Descent):**
```
repeat until convergence:
  1. Calculate gradient ∇L
  2. Update weights: w_new = w_old - learning_rate × ∇L
  3. Check if loss improved
```

**Key Properties:**
```
Positive gradient: Increasing input increases loss (move opposite)
Negative gradient: Increasing input decreases loss (move in direction)
Large gradient: Steep slope, fast progress
Small gradient: Flat slope, slow progress (approaching minimum)
Zero gradient: At minimum (converged)
```

**In MLOps:**
- Understand training loss curves (should decrease, then flatten)
- Diagnose bad learning rates (oscillating or stalled)
- Monitor gradient behavior (should decrease over time)
- Know when to stop training (when loss plateaus)

**Red Flags:**
- Learning rate too high: Loss bounces around (diverges)
- Learning rate too low: Loss decreases glacially (slow)
- Gradient not decreasing: Model not learning
- Large gap between training and validation loss: Overfitting
- Positive gradient in production: Data drift (loss increasing)

---

## Mental Models Across Modules

### **The Monitoring Dashboard (Module 1 + 3)**
```
Metric over time (e.g., latency):
100ms → 110ms → 125ms → 145ms → 160ms

Module 1 asks: "What's the trend?" (increasing)
Module 1 asks: "By how much?" (60% increase from 100 to 160)
Module 3 asks: "Is the gradient concerning?" (rate of change: ~15ms per day)

Combined: "Latency is increasing at 15ms/day. In 5 days, it'll hit our 200ms threshold."
```

### **The Data Pipeline (Module 2 + 1)**
```
Raw data → [Parse] → [Clean] → [Normalize] → [Feature Engineer] → [Model]

Module 2: "What does each function do?" (transforms input to output)
Module 2: "What's the order?" (order matters!)
Module 1: "What range is expected?" (each step expects certain magnitude/scale)

Combined: "If normalization expects [0, 1] but receives [-5, 100], it breaks."
```

### **Model Training (Module 3 + 2 + 1)**
```
Module 3: "How does the model improve?" (gradient descent, moving downhill)
Module 2: "What's the loss function?" (a mapping from predictions to error magnitude)
Module 1: "Is the improvement real?" (percentages, trends, magnitude of change)

Training curve: loss [5.0 → 3.0 → 1.5 → 1.2 → 1.15 → 1.14]
Module 1: -70% improvement overall, but plateauing
Module 3: Gradient is decreasing (converging)
Decision: Stop training around epoch 5
```

---

## Formulas You'll Use

### **Module 1:**
```
Percentage Change = (New - Old) / Old × 100%
Ratio = New / Old
Percentage of Total = Value / Total × 100%
```

### **Module 2:**
```
Linear scaling: x_scaled = (x - min) / (max - min)
Min-max scaling: x ∈ [old_min, old_max] → x ∈ [0, 1]
```

### **Module 3:**
```
Gradient descent update: w_new = w_old - α × ∇L
where α = learning rate, ∇L = gradient of loss

Numerical gradient (for verification):
∇L ≈ (L(x + ε) - L(x - ε)) / (2ε)
```

---

## Practice: Apply to Your Own Work

### **Right Now, In Your System:**

1. **Find a metric** (latency, error rate, CPU usage, whatever)
2. **Module 1 analysis:**
   - What's the current value?
   - What was it 1 week ago?
   - Percentage change? Order of magnitude?
   - Is there a trend?

3. **Module 2 analysis:**
   - Where does this metric come from?
   - What pipeline of functions produces it?
   - What are the inputs and outputs?

4. **Module 3 analysis:**
   - Is the metric improving (negative gradient) or degrading (positive)?
   - Rate of change per day?
   - If trend continues, when does it hit a threshold?

This is the real work of MLOps. Do this, and you understand the fundamentals.

---

## Common Mistakes to Avoid

| Mistake | Fix |
|---------|-----|
| Ignoring small percentages at scale | Always multiply: percentage × volume |
| Assuming functions commute (order doesn't matter) | Test both orders; usually they don't commute |
| Extrapolating linearly from 2 data points | Plot multiple points; check if trend is linear |
| Thinking large gradient = always better | Large gradient far from optimum; should decrease over time |
| Not checking domain/range compatibility | Validate input ranges before feeding to functions |
| Confusing "gradient is negative" with "bad" | Gradient direction determines weight change direction |
| Training past convergence | Monitor when loss plateaus; stop there |

---

## Next Steps After Modules 1-3

You're ready to understand:
- **Module 4:** How to tune hyperparameters (learning rate, batch size, etc.)
- **Module 5:** How to quantify uncertainty in predictions
- **Module 6:** How to detect when your model degrades in production
- **Module 7:** Different loss functions and when to use them
- **Module 8:** Why feature scaling matters and how to do it correctly

But first: **Take time with Modules 1-3.** They're the foundation. Everything else builds on them.

---

**You now have the mathematical foundations to understand almost every MLOps system. Use this knowledge.**
