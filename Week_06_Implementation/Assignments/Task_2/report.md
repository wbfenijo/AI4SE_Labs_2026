# Task 2 — chunking design

`chunk.py` creates `chunks.json` from the cloned repository's Python source
**and tests** (currently 826 nonempty chunks). Each record has a stable
`path:start-end` ID, relative path, symbol name, inclusive line range and
verbatim source text. An AST identifies classes/functions and keeps individual
methods together; module imports, class headers and constants are retained as
context chunks. Definitions longer than 60 lines are divided into 60-line
windows with eight lines of overlap. Empty files do not need chunks.

Most methods fit into one chunk; this avoids losing a method's signature or
intent at a fixed character boundary. Sixty lines is a practical upper bound
for the small repository: chunks remain inexpensive to include in the prompt,
while overlapping windows retain boundary context for long definitions.
Including tests makes expected behaviors searchable. The method-level split
occasionally leaves small class-context fragments; that is a tradeoff for
precise symbol retrieval, and the solver also supplies the target class.

Rebuild: `python3 Week_06_Implementation/Assignments/Task_2/chunk.py`.
