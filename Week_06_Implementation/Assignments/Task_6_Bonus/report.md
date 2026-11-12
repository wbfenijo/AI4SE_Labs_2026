# Bonus — improved repository-aware code-generation pipeline

1. Parse the repository into symbols (AST/tree-sitter), documentation and
   tests; preserve definitions, signatures, imports, line ranges and ownership.
   Split large functions only on logical blocks with overlap, not arbitrary
   token boundaries; refresh the index after every change.
2. Resolve the target file/class/method **exactly** from the task before any
   similarity search. Follow imports, call sites and referenced fields to
   gather dependencies, related implementations and focused tests.
3. Use hybrid search: lexical/identifier matching (e.g. BM25 or grep) plus
   semantic code embeddings for approximate conceptual matches; rerank by
   symbol relationship and test relevance. A vector alone can rank an
   unrelated similarly worded test above the actual target and can miss exact
   symbol dependencies.
4. Select context to a **token budget**, not a fixed five chunks. Always include
   the target method, owning class, pertinent collaborators and tests; add
   other evidence until marginal relevance falls off. Simple changes may need
   two chunks, cross-file behavior may need many more than five.
5. Ask the model for a minimal structured patch, validate paths and AST,
   run focused then full tests/type checks, and feed failures back into a
   bounded repair loop. Require human review before accepting changes.

Embeddings are useful for discovery, but not the sole or best matching
strategy for a named method in a known repository: exact navigation and
dependency analysis should lead. Small, inspectable edits and tests are more
important than retrieving a predetermined number of passages.
