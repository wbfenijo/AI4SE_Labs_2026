# Task 5 — RAG code generation and tests

`solve.py` accepts a textual task via `solve_text(text, file, class_name,
method_name)` (or `--text '...' --file ... --class ... --method ...`), plus
`--task N`/`--all` for `missing_code.json`. For each
of its ten entries it embeds the description, retrieves **five** chunks,
prompts the permitted `openai/gpt-6-luna` model through `opencode run`, parses
the JSON text response, and replaces **only the stub body** in the target
source file. It includes the original method and target class for reliable
field names. It checks the target path, class/method, AST shape of the answer,
that the existing method is a stub, and that the resulting file compiles.
The command refuses to overwrite an implemented method. `--dry-run` lists
matches without calling the model; run it on the original stubs. For a new
unmodified clone with matching paths and an authenticated OpenCode CLI:

```sh
python3 Week_06_Implementation/Assignments/Task_2/chunk.py
python3 Week_06_Implementation/Assignments/Task_3/embed.py
python3 Week_06_Implementation/Assignments/Task_5/solve.py --all --model gpt-6-luna
```

All ten methods were initially generated with this pipeline. A test run then
exposed incorrect generated field names and an exception type; these were
reviewed and corrected in the cloned source. The prompt was improved to
include the authoritative target class for future runs. Chunks and embeddings
were regenerated after final edits to keep the stored index current.

Testing with the available standard-library runner (`pytest` is not installed):

```sh
cd Week_06_Implementation/Assignments/playground/playground
python3 -m unittest discover -s tests -q
```

**Result: 481 tests, 1 failure, 0 errors (480 pass).** The remaining test,
`test_contains_present_even_if_zero_on_hand_after_commit` in
`playground/tests/test_inventory.py`, expects `sku in ledger` to be true when
on-hand stock has reached **zero**. That contradicts the explicit Task 5
specification in `missing_code.json` for `InventoryLedger.__contains__`:
"positive on-hand stock". The implementation follows the specification,
returning `False` for zero stock. Neither the test nor its requirement was
silently changed. Before implementation the same suite had 35 failures and
17 errors. Separately, all five pipeline checks pass:

```sh
python3 -m unittest discover -s Week_06_Implementation/Assignments/Task_5 -p 'test_*.py' -q
```
