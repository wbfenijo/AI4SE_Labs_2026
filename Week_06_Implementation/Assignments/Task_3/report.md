# Task 3 — embeddings and storage

`embed.py` reads Task 2's chunks and writes `embeddings.json` (currently 826
chunk/vector pairs). A deterministic 384-dimensional hashed TF-IDF embedding
tokenizes code identifiers, camelCase and snake_case, lowercases words, and
embeds `path + symbol + text` so both the code and its location can be found.
It computes document frequencies across the chunks, stores the IDF weights,
and L2-normalizes each vector. Queries are embedded with the **same** hash,
dimension and stored IDF weights; only nonzero vector coordinates are saved.

This uses only the Python standard library, works offline, and is repeatable
across machines. A small JSON index is adequate for this repository and needs
no database or external embedding service. Limitations: hash collisions and
lexical rather than semantic matching (synonyms may be missed). If scaling to
large codebases, use a semantic code embedding model and a vector index.

Rebuild after chunking:
`python3 Week_06_Implementation/Assignments/Task_3/embed.py`.
