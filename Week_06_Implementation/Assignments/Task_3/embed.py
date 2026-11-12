"""Build a reproducible 384-dimensional hashed TF-IDF chunk index."""

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re

ASSIGNMENTS = Path(__file__).resolve().parents[1]
CHUNKS = ASSIGNMENTS / "Task_2" / "chunks.json"
INDEX = Path(__file__).with_name("embeddings.json")
DIMENSIONS = 384


def tokens(text):
    """Split snake_case, camelCase and punctuation in code and task descriptions."""
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9]*|[0-9]+", text.lower())
    return words


def bucket(word):
    return int.from_bytes(hashlib.blake2b(word.encode(), digest_size=8).digest(), "big") % DIMENSIONS


def embed(text, idf):
    """Return a sparse, unit-length vector; indices are string keys for JSON."""
    counts = Counter(tokens(text))
    vector = Counter()
    for word, count in counts.items():
        index = bucket(word)
        vector[str(index)] += (1 + math.log(count)) * idf[index]
    norm = math.sqrt(sum(value * value for value in vector.values()))
    return {key: round(value / norm, 8) for key, value in sorted(vector.items())} if norm else {}


def build_index(chunks):
    documents = [f"{c['path']} {c['symbol']} {c['text']}" for c in chunks]
    frequency = Counter()
    for document in documents:
        frequency.update({bucket(word) for word in tokens(document)})
    idf = [math.log((len(documents) + 1) / (frequency[i] + 1)) + 1
           for i in range(DIMENSIONS)]
    return {
        "dimensions": DIMENSIONS,
        "idf": idf,
        "entries": [{"id": chunk["id"], "vector": embed(document, idf)}
                    for chunk, document in zip(chunks, documents)],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunks", type=Path, default=CHUNKS)
    parser.add_argument("--output", type=Path, default=INDEX)
    args = parser.parse_args()
    chunks = json.loads(args.chunks.read_text(encoding="utf-8"))
    index = build_index(chunks)
    args.output.write_text(json.dumps(index, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Wrote {len(index['entries'])} embeddings to {args.output}")
