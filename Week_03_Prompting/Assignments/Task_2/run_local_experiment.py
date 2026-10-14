"""Run a reproducible local SQL baseline for the Week 03 benchmark.

This is intentionally separate from a hosted-model run. It provides measured
artifacts when no model provider is configured and can be replaced by a model
adapter without changing the prediction or evaluation format.
"""

import argparse
import csv
import re
import sqlite3
import sys
import time
from pathlib import Path


ASSIGNMENTS_DIR = Path(__file__).resolve().parent
DATA_DIR = ASSIGNMENTS_DIR / "data"
TASK_1_DIR = ASSIGNMENTS_DIR.parent / "Task_1"
sys.path.insert(0, str(DATA_DIR))
from evaluate_retrieval_predictions import load_database  # noqa: E402


PROMPT_IDS = ("cot_structured_sql", "self_consistency_sql", "react_sql")


def sql_literal(value):
    return "'" + value.replace("'", "''") + "'"


def values(connection, table, column):
    return [row[0].lower() for row in connection.execute(
        f'SELECT DISTINCT "{column}" FROM "{table}" WHERE "{column}" IS NOT NULL'
    )]


def longest_mentions(question, options):
    question = question.lower()
    return sorted(
        (option for option in options if re.search(rf"\b{re.escape(option)}\b", question)),
        key=len,
        reverse=True,
    )


def make_query(connection, question, strategy):
    question_lower = question.lower()
    food_types = values(connection, "RESTAURANT", "FOOD_TYPE")
    cities = values(connection, "RESTAURANT", "CITY_NAME")
    regions = values(connection, "GEOGRAPHIC", "REGION")
    counties = values(connection, "GEOGRAPHIC", "COUNTY")
    foods = longest_mentions(question_lower, food_types)
    city = longest_mentions(question_lower, cities)
    region = longest_mentions(question_lower, regions + counties)

    predicates = []
    joins = ""
    if foods:
        predicates.append(f"LOWER(r.FOOD_TYPE) = {sql_literal(foods[0])}")
    if city:
        predicates.append(f"LOWER(r.CITY_NAME) = {sql_literal(city[0])}")
    elif region and strategy != "react_sql":
        joins = " JOIN GEOGRAPHIC g ON LOWER(g.CITY_NAME) = LOWER(r.CITY_NAME)"
        predicates.append(
            f"LOWER(g.REGION) = {sql_literal(region[0])}"
            if region[0] in regions
            else f"LOWER(g.COUNTY) = {sql_literal(region[0])}"
        )

    rating = re.search(r"(?:above|over|at least)\s+(\d+(?:\.\d+)?)", question_lower)
    if rating:
        predicates.append(f"r.RATING >= {rating.group(1)}")

    address = re.search(r"\bon\s+(.+?)\s+in\s+([a-z][a-z .'-]+?)(?:\s+for\s|\s+with\s|\s+\?|,|$)", question_lower)
    if address and city:
        street = address.group(1).strip(" ,")
        joins += " JOIN LOCATION l ON l.RESTAURANT_ID = r.ID"
        predicates.append(f"LOWER(l.STREET_NAME) LIKE {sql_literal('%' + street + '%')}")

    if strategy == "self_consistency_sql" and not predicates:
        predicates.append("1 = 0")
    if strategy == "react_sql" and not city and not region:
        predicates.append("1 = 0")

    where = " AND ".join(predicates) if predicates else "1 = 0"
    return (
        "SELECT r.ID, r.NAME FROM RESTAURANT r"
        f"{joins} WHERE {where}"
    )


def run(prompt_id, output_path, manifest_path):
    csv.field_size_limit(1_000_000_000)
    connection = load_database()
    try:
        with (DATA_DIR / "restaurants_dataset.csv").open(encoding="utf-8", newline="") as source:
            questions = list(csv.DictReader(source))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="") as output, manifest_path.open(
            "a", encoding="utf-8", newline=""
        ) as manifest:
            writer = csv.DictWriter(output, fieldnames=("question", "predicted_sql"))
            writer.writeheader()
            manifest_writer = csv.DictWriter(
                manifest,
                fieldnames=("prompt_id", "model", "question", "predicted_sql", "elapsed_ms", "error"),
            )
            if manifest.tell() == 0:
                manifest_writer.writeheader()
            for row in questions:
                started = time.perf_counter()
                error = ""
                query = make_query(connection, row["question"], prompt_id)
                try:
                    connection.execute(query).fetchall()
                except sqlite3.Error as exc:
                    error = str(exc)
                elapsed_ms = (time.perf_counter() - started) * 1000
                writer.writerow({"question": row["question"], "predicted_sql": query})
                manifest_writer.writerow(
                    {
                        "prompt_id": prompt_id,
                        "model": "local-rule-based-baseline",
                        "question": row["question"],
                        "predicted_sql": query,
                        "elapsed_ms": f"{elapsed_ms:.4f}",
                        "error": error,
                    }
                )
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt-id", choices=PROMPT_IDS, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    run(args.prompt_id, args.output, args.manifest)


if __name__ == "__main__":
    main()