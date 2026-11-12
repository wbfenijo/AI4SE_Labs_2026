"""Split the cloned playground into bounded, traceable source-code chunks."""

import argparse
import ast
import json
from pathlib import Path

ASSIGNMENTS = Path(__file__).resolve().parents[1]
REPOSITORY = ASSIGNMENTS / "playground"
OUTPUT = Path(__file__).with_name("chunks.json")
MAX_LINES = 60
OVERLAP = 8


def windows(start, end):
    """Yield inclusive source line ranges with overlap for long definitions."""
    while start <= end:
        stop = min(start + MAX_LINES - 1, end)
        yield start, stop
        if stop == end:
            break
        start = stop - OVERLAP + 1


def chunks_for_file(path, root):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    tree = ast.parse(text, filename=str(path))
    relative = path.relative_to(root).as_posix()
    # Give methods their own chunks; preserve the class name in the embedding text.
    definitions = []
    covered = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if isinstance(node, ast.ClassDef):
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        definitions.append((child.lineno, child.end_lineno, f"{node.name}.{child.name}"))
                # Class-level constants/docstrings and decorators go in the remainder.
                for child in node.body:
                    if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        covered.update(range(child.lineno, child.end_lineno + 1))
                covered.update(range(node.lineno, node.body[0].lineno))
            else:
                definitions.append((node.lineno, node.end_lineno, node.name))
    for start, end, _ in definitions:
        covered.update(range(start, end + 1))

    sections = list(definitions)
    # Keep imports, module docs, class constants, and other top-level context.
    remainder = sorted(set(range(1, len(lines) + 1)) - covered | {
        n for n in covered if not any(s <= n <= e for s, e, _ in definitions)
    })
    if remainder:
        group_start = prev = remainder[0]
        for n in remainder[1:]:
            if n != prev + 1:
                sections.append((group_start, prev, "module/class context"))
                group_start = n
            prev = n
        sections.append((group_start, prev, "module/class context"))

    result = []
    for start, end, symbol in sorted(sections):
        for first, last in windows(start, end):
            content = "\n".join(lines[first - 1:last])
            if content.strip():
                result.append({
                    "id": f"{relative}:{first}-{last}",
                    "path": relative,
                    "symbol": symbol,
                    "start": first,
                    "end": last,
                    "text": content,
                })
    return result


def chunk_repository(root=REPOSITORY):
    """Index source and tests, excluding hidden and generated directories."""
    return [chunk for path in sorted(root.rglob("*.py"))
            if not any(part.startswith(".") or part == "__pycache__"
                       for part in path.relative_to(root).parts)
            for chunk in chunks_for_file(path, root)]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=REPOSITORY)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    chunks = chunk_repository(args.repository.resolve())
    args.output.write_text(json.dumps(chunks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(chunks)} chunks to {args.output}")
