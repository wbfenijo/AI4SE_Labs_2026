# Task 1: Prompt Framework Selection

## Objective

The Task 2 problem is natural-language-to-SQL retrieval over the restaurant database. The prompts therefore require the model to produce one executable SQLite `SELECT` statement and to respect the supplied schema.

## Selected Frameworks

### Chain-of-Thought with structured output

Source: [Prompting Guide: Chain-of-Thought](https://www.promptingguide.ai/techniques/cot)

This framework was selected because the questions combine several constraints: food type, geography, rating threshold, and sometimes an address. The template asks the model to reason through those constraints internally but constrains the visible answer to SQL. That separation makes the output easier to execute and score.

Expected behavior: fewer missed predicates and fewer malformed queries than an unstructured request.

### Self-consistency

Source: [Prompting Guide: Self-Consistency](https://www.promptingguide.ai/techniques/consistency)

This framework was selected because the benchmark contains distractor text and ambiguous wording. Independent query plans allow the model to compare interpretations before selecting one. It is expected to be more robust on noisy questions, at the cost of additional inference time and tokens.

Expected behavior: better semantic accuracy on ambiguous questions, with higher latency than the other prompts.

### ReAct

Source: [Prompting Guide: ReAct](https://www.promptingguide.ai/techniques/react)

This framework was selected because schema inspection is central to the task. The internal Thought/Action/Observation loop encourages the model to verify table names, joins, and predicates before returning SQL. The final-only SQL instruction keeps the artifact executable.

Expected behavior: fewer unknown-column and invalid-join errors, with moderate latency overhead.

## Experimental Controls

- Use the same model, temperature, question order, schema text, and system instructions for all prompt conditions.
- Start a fresh model session for each prompt condition as required by Task 2.
- Record `prompt_id`, framework, model identifier, temperature, question, predicted SQL, elapsed time, and error status.
- Evaluate every prediction with the supplied SQLite evaluator before comparing conditions.
