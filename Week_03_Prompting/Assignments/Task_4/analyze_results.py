"""Analyze paired prompt-condition results without third-party dependencies."""

import argparse
import csv
import random
import statistics
from collections import defaultdict
from pathlib import Path


def load_rows(path):
    csv.field_size_limit(1_000_000_000)
    with path.open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def permutation_p_value(differences, repetitions=10000):
    nonzero = [difference for difference in differences if difference]
    if not nonzero:
        return 1.0
    observed = abs(statistics.mean(nonzero))
    randomizer = random.Random(20261014)
    at_least_as_extreme = 0
    for _ in range(repetitions):
        simulated = statistics.mean(
            value if randomizer.randrange(2) else -value for value in nonzero
        )
        if abs(simulated) >= observed:
            at_least_as_extreme += 1
    return (at_least_as_extreme + 1) / (repetitions + 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-question", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--tests", type=Path, required=True)
    args = parser.parse_args()

    rows = load_rows(args.per_question)
    by_prompt = defaultdict(dict)
    for row in rows:
        by_prompt[row["prompt_id"]][row["question"]] = row
    manifest = load_rows(args.manifest)
    by_manifest = defaultdict(list)
    for row in manifest:
        by_manifest[row["prompt_id"]].append(float(row["elapsed_ms"]))

    summaries = []
    for prompt_id, prompt_rows in by_prompt.items():
        f1 = [float(row["result_f1"]) for row in prompt_rows.values()]
        exact = [int(row["exact_match"]) for row in prompt_rows.values()]
        times = by_manifest[prompt_id]
        summaries.append(
            {
                "prompt_id": prompt_id,
                "questions": len(f1),
                "exact_accuracy": f"{statistics.mean(exact):.6f}",
                "mean_result_f1": f"{statistics.mean(f1):.6f}",
                "median_result_f1": f"{statistics.median(f1):.6f}",
                "mean_latency_ms": f"{statistics.mean(times):.6f}",
                "median_latency_ms": f"{statistics.median(times):.6f}",
            }
        )

    prompt_ids = sorted(by_prompt)
    tests = []
    for index, left in enumerate(prompt_ids):
        for right in prompt_ids[index + 1 :]:
            questions = sorted(set(by_prompt[left]) & set(by_prompt[right]))
            differences = [
                float(by_prompt[left][question]["result_f1"])
                - float(by_prompt[right][question]["result_f1"])
                for question in questions
            ]
            tests.append(
                {
                    "left_prompt": left,
                    "right_prompt": right,
                    "paired_questions": len(differences),
                    "mean_f1_difference": f"{statistics.mean(differences):.6f}",
                    "permutation_p_value": f"{permutation_p_value(differences):.6f}",
                    "significant_at_0.05": str(permutation_p_value(differences) < 0.05),
                }
            )

    args.summary.parent.mkdir(parents=True, exist_ok=True)
    with args.summary.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=summaries[0].keys())
        writer.writeheader()
        writer.writerows(summaries)
    with args.tests.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=tests[0].keys())
        writer.writeheader()
        writer.writerows(tests)
    print("Wrote", args.summary)
    print("Wrote", args.tests)


if __name__ == "__main__":
    main()