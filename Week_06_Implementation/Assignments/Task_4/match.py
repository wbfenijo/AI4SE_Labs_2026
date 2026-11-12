"""Rank indexed repository chunks by cosine similarity to a textual task."""

import argparse
import json
from pathlib import Path
import sys

ASSIGNMENTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ASSIGNMENTS / "Task_3"))
from embed import embed  # noqa: E402

CHUNKS = ASSIGNMENTS / "Task_2" / "chunks.json"
INDEX = ASSIGNMENTS / "Task_3" / "embeddings.json"


def match(task, n=5, chunks_path=CHUNKS, index_path=INDEX):
    """Return n (chunk, cosine score) pairs, highest score first."""
    if n < 1:
        raise ValueError("n must be positive")
    chunks = json.loads(Path(chunks_path).read_text(encoding="utf-8"))
    index = json.loads(Path(index_path).read_text(encoding="utf-8"))
    by_id = {chunk["id"]: chunk for chunk in chunks}
    query = embed(task, index["idf"])
    scored = []
    for entry in index["entries"]:
        if entry["id"] not in by_id:
            raise ValueError(f"index and chunks disagree: {entry['id']}")
        score = sum(value * entry["vector"].get(key, 0) for key, value in query.items())
        scored.append((by_id[entry["id"]], score))
    return sorted(scored, key=lambda pair: (-pair[1], pair[0]["id"]))[:n]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", help="Textual coding task")
    parser.add_argument("-n", type=int, default=5)
    args = parser.parse_args()
    for chunk, score in match(args.task, args.n):
        print(f"{score:.4f}  {chunk['id']}  {chunk['symbol']}")
