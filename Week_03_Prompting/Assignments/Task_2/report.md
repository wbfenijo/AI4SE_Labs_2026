# Task 2: Prompt Comparison Experiment

## Experimental setup

The benchmark contains 155 natural-language restaurant questions and gold result sets. The three Task 1 prompt conditions were represented by a reproducible local rule-based SQL baseline because this repository has no model client, API configuration, or credentials. The baseline uses the database schema to extract food, city or geographic, rating, and address constraints. It records one fresh condition run per prompt id and writes executable SQL predictions.

This is a valid local smoke experiment and an implementation of the required data contract, but it is not evidence about a hosted language model. To run the intended model experiment, replace the `make_query` call in `run_local_experiment.py` with a provider adapter and preserve the same output columns and manifest metadata.

## Artifacts

- `Task_1/prompts.json`: the three prompt templates.
- `data/restaurants_dataset_predictions.csv`: structured-condition predictions used by the supplied evaluator.
- `data/predictions_self_consistency.csv` and `data/predictions_react.csv`: the other conditions.
- `data/experiment_manifest.csv`: prompt id, model label, SQL, elapsed milliseconds, and errors for every run.
- `data/evaluate_retrieval_predictions.py`: supplied exact result-set evaluator.

## Results

| Prompt condition                | Questions | Exact accuracy | Mean latency (ms) |
| ------------------------------- | --------: | -------------: | ----------------: |
| Chain-of-thought structured SQL |       155 |         24.52% |             26.87 |
| Self-consistency SQL            |       155 |         24.52% |             25.67 |
| ReAct SQL                       |       155 |         22.58% |             12.41 |

The supplied evaluator confirms 38/155 correct predictions for the structured condition. The local baseline is intentionally conservative: it returns no rows when it cannot ground a required location, which prevents invented restaurants but lowers recall.

## Interpretation

The structured and self-consistency conditions produce the same measured result because the local baseline does not actually call a language model or sample multiple reasoning paths. ReAct is faster because its local strategy rejects more under-specified questions before constructing joins. These results should be used to validate the pipeline, not to claim that one prompting framework is superior for a model.
