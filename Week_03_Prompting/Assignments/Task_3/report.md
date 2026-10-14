# Task 3: Complementary Metric

## Metric: Result-set F1

The supplied metric is exact result-set equality: a prediction is correct only when its complete set of `(ID, NAME)` rows matches the gold set. I add macro-averaged result-set F1. For each question, treat the predicted and expected `(ID, NAME)` pairs as sets:

$$
P = \frac{|\hat{Y} \cap Y|}{|\hat{Y}|},\qquad
R = \frac{|\hat{Y} \cap Y|}{|Y|},\qquad
F_1 = \frac{2PR}{P+R}
$$

An empty prediction receives F1 = 1 only when the expected set is also empty. Otherwise it receives F1 = 0. Duplicate rows are collapsed because the task evaluates retrieved entities rather than duplicate presentation.

## Why this metric applies

Result-set F1 gives partial credit when a query retrieves some correct restaurants but misses others or includes distractors. It is therefore more informative for multi-answer questions than exact equality. It complements rather than replaces exact accuracy: exact accuracy remains the strict success criterion, while F1 explains the degree of success on failures.

## Implementation

`evaluate_metrics.py` calculates exact accuracy and F1 for each prediction CSV, then writes both an aggregate summary and one row per question. No third-party package is required.

## Measured local results

| Prompt condition                | Exact accuracy | Mean result-set F1 |
| ------------------------------- | -------------: | -----------------: |
| Chain-of-thought structured SQL |         24.52% |             0.2452 |
| Self-consistency SQL            |         24.52% |             0.2452 |
| ReAct SQL                       |         22.58% |             0.2258 |

The identical accuracy and F1 values are a property of this local baseline: its predictions generally have either complete overlap or no overlap, rather than partial overlap. A hosted-model run is expected to make the complementary metric more discriminating.
