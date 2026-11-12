# Task 4 — vector matching

`match.py` embeds the input task with the IDF from Task 3, computes sparse
dot products against every stored unit-length chunk vector (cosine similarity),
and returns the highest `n` scores. Equal scores break ties by chunk ID for
deterministic output. It joins vectors to chunks using stable IDs rather than
relying on row order. An invalid `n` or missing chunk ID is rejected.

A linear scan is simple and sufficient for 826 chunks; time grows with the
index size and nonzero dimensions, while an approximate-nearest-neighbor
index would add unnecessary setup here. Default `n=5` supports Task 5; callers
may choose another positive count.

Try: `python3 Week_06_Implementation/Assignments/Task_4/match.py
'OrderStatus.is_terminal True when a status ends transitions' -n 5`.
