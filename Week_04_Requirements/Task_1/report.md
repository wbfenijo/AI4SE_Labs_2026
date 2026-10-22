# Week 04 Task 1 — Agentic requirements refinement

## Design

`requirements_network.py` implements a LangGraph state graph. It accepts any
directory of text-like files recursively, so corpus filenames and subfolders
are not embedded in the logic. The graph has:

1. **Extract** — an OpenAI model extracts traceable candidate requirements.
2. **Synthesize** — a second model merges semantic duplicates and standardizes
   terminology.
3. **Review** — a third model checks completeness, contradictions, support, and
   traceability.
4. **Revise** — rejected drafts return to synthesis, with at most two review
   iterations to prevent an accidental infinite loop.
5. **Finalize** — a deterministic node assigns IDs and writes one JSON document.

This meets ANS1 (three LLM nodes), ANS2 (deterministic loading/finalization),
ANS3 (review/revise feedback loop), ANS4 (three configurable model names), and
ANS5 (LangGraph).

## Output contract

The final JSON contains one structured document with a priority-scale
definition, IDs in the `REQ-###` form, a paragraph explanation, source
filenames, and a `discarded_requirements` section. The prompts explicitly
require semantic deduplication, terminology consistency, completeness, and
conflict detection. The reviewer is allowed to reject a draft and identify
missing topics; the revision node uses that feedback rather than silently
accepting it.

## Running

```powershell
python -m pip install -r requirements.txt
# Paste the key supplied for the lab into .env before running.
python requirements_network.py `
  --input-dir data/corpus `
  --output output/requirements.json
```

The key is loaded from the adjacent `.env` file with `python-dotenv`; it is
not stored in source, arguments, or generated artifacts. The checked-in
`output/requirements.json` is an example result for the supplied corpus and
allows the deliverable to be reviewed without making an API call.
