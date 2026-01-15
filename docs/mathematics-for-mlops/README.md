# Mathematics for MLOps: A Ground-Up, No-Nonsense Tutorial

This is a mathematics curriculum **for people who dislike math** and need to understand the concepts that actually matter in machine learning operations.

## Core Philosophy

- **No assumed background.** We start from zero.
- **Why first.** Every topic explains where it appears in real systems and what breaks if misunderstood.
- **Concrete, operational examples.** No abstract proofs. Real dashboards, real monitoring, real failures.
- **One idea at a time.** No conceptual dependencies you haven't already learned.
- **Slow explanations.** Every symbol, every operation, every step is explained.

## How to Use This

1. **Read Module 1 first. Stop there.** Don't jump ahead.
2. **Work through the examples step-by-step.** Don't skip steps.
3. **Do the practice questions.** Start with the easy ones. They build confidence.
4. **Look at your own systems.** Read real dashboards. See where these numbers show up.
5. **Only then move to the next module.**

Each module includes:
- What it's about and why it matters
- Where you'll see it in MLOps
- Detailed explanations of core concepts
- Worked examples (every step shown)
- Common confusions and traps
- Practice questions (with answers)
- Reality checks (what breaks in production)

## Curriculum Roadmap

**[✅ Complete] Module 1: Absolute Basics (Numbers You Can Trust)**
- Numbers, signs, and magnitude
- Ratios and percentages
- Orders of magnitude
- Reading charts and dashboards
- Why monitoring depends on this

**[✅ Complete] Module 2: Functions and Mappings**
- What a function is (not the abstract definition)
- Inputs, outputs, and transformations
- Why data pipelines are functions
- Feature scaling and normalization
- Composition and pipeline order

**[✅ Complete] Module 3: Derivatives and Gradients**
- What "rate of change" means in real terms
- How gradient descent works
- Why it matters for model training
- Learning rate and convergence
- Common failures and fixes

**[Coming] Module 4: Optimization Intuition**
- What we're actually optimizing
- Why loss functions matter
- Convergence and stopping criteria
- When to retrain vs. tune
- Hyperparameter tuning basics

**[Coming] Module 5: Probability for ML**
- Randomness and uncertainty
- Why your model's predictions vary
- Confidence and risk
- Testing and validation

**[Coming] Module 6: Statistics for Monitoring and Drift**
- What to measure in production
- Detecting when things change
- Data drift, model drift, concept drift
- Setting alerts that don't cry wolf

**[Coming] Module 7: Loss Functions and Convergence**
- Understanding different loss functions
- Why they matter for different problems
- Convergence and when to stop training
- Overfitting and the generalization gap

**[Coming] Module 8: Scaling, Normalization, and Stability**
- Why numbers blow up or vanish
- Normalization (multiple types)
- Keeping numbers stable in computation
- Numerical stability and edge cases

## What You'll Be Able to Do

By the end of all modules, you will:

- Understand monitoring dashboards and spot real problems vs. noise
- Know what "loss is decreasing" means and why it matters
- Set reasonable alerts (no false alarms)
- Explain why features need scaling
- Understand what's happening inside model training
- Catch data drift before it breaks your model
- Make informed decisions about retraining, tuning, and deployment
- Explain these concepts to non-technical stakeholders

## For Instructors or Self-Learners

This curriculum enforces **zero topic dependencies**. You can't understand Module 3 without Module 1 and 2. But within a module, every concept is explained before use.

If you're stuck on something, that's normal. The confusion usually means:
1. You skipped a concept (go back and re-read)
2. The explanation wasn't clear (good feedback—let me know)
3. You're thinking too abstractly (try working with actual numbers)

**Difficulty is normal. Confusion is feedback, not failure.**

---

**Start with [MODULE_1_Absolute_Basics.md](MODULE_1_Absolute_Basics.md) and take your time.**
