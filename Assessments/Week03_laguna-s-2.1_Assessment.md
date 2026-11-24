# Assessment by laguna-s-2.1

# Week 03 Prompting
- Awarded: 4.5b out of 5b
- Commentary: The student delivers a strong, well-structured pipeline: three distinct prompt frameworks with sources and rationale, a complementary result-set F1 metric with implementation and per-question values, and a thorough Task 4 analysis with tables, a readable bar-chart graph, permutation tests, and a discussion of prompt/model/coding-agent factors. The main weakness is Task 2: the selected Task 1 prompts are not actually run through a language model — a deterministic local rule-based baseline is used instead (transparently disclosed in the report), and no visualization appears in the Task 2 report. Task scores: Task 1 = 1b, Task 2 = 0.5b, Task 3 = 1b, Task 4 = 2b.

## Task 1
- Awarded: 1b   (max 1b)
- Commentary: Three frameworks are selected (Chain-of-Thought with structured output, Self-consistency, ReAct), none of which are ROSES or zero-shot. `prompts.json` contains each template, framework, source URL, and expected behavior, and `report.md` explains the rationale and cites where each was found (promptingguide.ai). The output requirements — a data file of formulated prompts plus a report on why each was chosen and where found — are fully met.

## Task 2
- Awarded: 0.5b   (max 1b)
- Commentary: All required artifacts are present and well-formed: three prediction CSVs, an `experiment_manifest.csv` with prompt_id/model/question/predicted_sql/elapsed_ms/error metadata, the supplied evaluator, a runner script, and measured inference times (155 questions per condition). However, the student did not run the selected Task 1 prompts through a model — the repository has no API credentials, so a deterministic local rule-based baseline was substituted, one that ignores the prompt text and therefore does not produce a genuine prompt comparison. The Task 2 report also omits a visualization (the only chart appears in Task 4). The student is transparent about these limitations throughout. Partial completion.

## Task 3
- Awarded: 1b   (max 1b)
- Commentary: The student proposes macro-averaged result-set F1 as a complementary metric to the supplied exact result-set equality, defends it as more informative for multi-answer questions (partial credit), discusses how it complements rather than replaces exact accuracy, implements it in `evaluate_metrics.py` with no third-party dependencies, and reports both aggregate and per-question values. The output requirements — a metric implementation plus a report comparing values across prompts — are fully met.

## Task 4
- Awarded: 2b   (max 2b)
- Commentary: The student provides `summary.csv` and `pairwise_tests.csv` tables, a readable bar-chart visualization (`metrics.svg`) plus a mermaid chart in the report, a paired sign-permutation test (no comparisons significant at 0.05), and an interpretation that discusses the prompt, model, and coding-agent factors while honestly noting that the experiment isolates pipeline/strategy behavior rather than the causal effect of a hosted model. Reiterates and extends the Task 2/3 comparison with tables, graphs, and statistical analysis. Fully meets the Task 4 output requirements.

<!--
NOTES FOR THE GRADER (deleted in output): Max points: Task 1 = 1b, Task 2 = 1b, Task 3 = 1b, Task 4 = 2b. Total = 5b. Overall awarded 4.5b equals 1 + 0.5 + 1 + 2.
-->
