"""Calculate exact-match accuracy and result-set F1 for Task 2 predictions."""

import argparse
import csv
import json
import sqlite3
from collections import defaultdict, deque
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Task_2" / "data"
LABELS_PATH = DATA_DIR / "restaurants_dataset.csv"


def load_labels():
    csv.field_size_limit(1_000_000_000)
    labels = defaultdict(deque)
    with LABELS_PATH.open(encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            labels[row["question"]].append(json.loads(row["result"]))
    return labels


def result_f1(expected, predicted):
    expected_set = {tuple(item) for item in expected}
    predicted_set = {tuple(item) for item in predicted}
    if not expected_set and not predicted_set:
        return 1.0
    if not expected_set or not predicted_set:
        return 0.0
    overlap = len(expected_set & predicted_set)
    precision = overlap / len(predicted_set)
    recall = overlap / len(expected_set)
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def evaluate(predictions_path, database_loader):
    labels = load_labels()
    connection = database_loader()
    scores = []
    try:
        with predictions_path.open(encoding="utf-8", newline="") as source:
            for row in csv.DictReader(source):
                expected = labels[row["question"]].popleft()
                predicted = [list(result) for result in connection.execute(row["predicted_sql"]).fetchall()]
                scores.append(
                    {
                        "question": row["question"],
                        "exact_match": int({tuple(item) for item in expected} == {tuple(item) for item in predicted}),
                        "result_f1": result_f1(expected, predicted),
                        "expected_count": len(expected),
                        "predicted_count": len(predicted),
                    }
                )
    finally:
        connection.close()
    return scores


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prediction", action="append", required=True, metavar="PROMPT_ID=PATH")
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--per-question", type=Path, required=True)
    args = parser.parse_args()

    from sys import path

    path.insert(0, str(DATA_DIR))
    from evaluate_retrieval_predictions import load_database

    summaries = []
    per_question_rows = []
    for item in args.prediction:
        prompt_id, path_text = item.split("=", 1)
        scores = evaluate(Path(path_text), load_database)
        summaries.append(
            {
                "prompt_id": prompt_id,
                "questions": len(scores),
                "exact_accuracy": f"{sum(row['exact_match'] for row in scores) / len(scores):.6f}",
                "mean_result_f1": f"{sum(row['result_f1'] for row in scores) / len(scores):.6f}",
            }
        )
        per_question_rows.extend({"prompt_id": prompt_id, **row} for row in scores)

    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.per_question.parent.mkdir(parents=True, exist_ok=True)
    with args.summary.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=summaries[0].keys())
        writer.writeheader()
        writer.writerows(summaries)
    with args.per_question.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=per_question_rows[0].keys())
        writer.writeheader()
        writer.writerows(per_question_rows)

    for summary in summaries:
        print(summary)


if __name__ == "__main__":
    main()