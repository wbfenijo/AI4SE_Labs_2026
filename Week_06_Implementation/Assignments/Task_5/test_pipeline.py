"""Offline checks for the chunk, embedding, retrieval, and patch guardrails."""

import ast
import json
from pathlib import Path
import sys
import unittest

ASSIGNMENTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ASSIGNMENTS / "Task_2"))
sys.path.insert(0, str(ASSIGNMENTS / "Task_3"))
from chunk import MAX_LINES, chunk_repository  # noqa: E402
from embed import DIMENSIONS, embed  # noqa: E402
from solve import extract_body, find_method, match  # noqa: E402


class PipelineTests(unittest.TestCase):
    def test_chunks_cover_all_python_files_and_are_bounded(self):
        chunks = chunk_repository()
        paths = {chunk["path"] for chunk in chunks}
        files = {p.relative_to(ASSIGNMENTS / "playground").as_posix()
                 for p in (ASSIGNMENTS / "playground").rglob("*.py")
                 if p.read_text(encoding="utf-8").strip()}
        self.assertEqual(paths, files)
        self.assertTrue(all(c["end"] - c["start"] < MAX_LINES for c in chunks))

    def test_stored_vectors_and_query_have_same_dimension(self):
        index = json.loads((ASSIGNMENTS / "Task_3" / "embeddings.json").read_text())
        self.assertEqual(index["dimensions"], DIMENSIONS)
        self.assertEqual(len(index["entries"]), len(chunk_repository()))
        self.assertTrue(all(0 <= int(k) < DIMENSIONS for entry in index["entries"]
                            for k in entry["vector"]))
        self.assertTrue(embed("OrderStatus is_terminal", index["idf"]))

    def test_top_five_include_target(self):
        results = match("playground/playground/enums.py OrderStatus.is_terminal "
                        "True when the status ends further transitions", n=5)
        self.assertEqual(len(results), 5)
        self.assertTrue(any(c["symbol"] == "OrderStatus.is_terminal" for c, _ in results))
        self.assertEqual([score for _, score in results],
                         sorted((score for _, score in results), reverse=True))

    def test_extract_accepts_one_method_only(self):
        body = extract_body("def f(self):\n    return 42", "f")
        self.assertIsInstance(body[0], ast.Return)
        with self.assertRaises(ValueError):
            extract_body("def f(self):\n    pass\ndef unrelated():\n    pass", "f")

    def test_find_method_targets_correct_class(self):
        tree = ast.parse("class A:\n    def f(self):\n        pass\n")
        self.assertEqual(find_method(tree, "A", "f").name, "f")
        with self.assertRaises(ValueError):
            find_method(tree, "B", "f")


if __name__ == "__main__":
    unittest.main()
