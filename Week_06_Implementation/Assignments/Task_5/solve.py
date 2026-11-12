"""Solve missing playground methods with five retrieved chunks and an LLM.

Run `python3 solve.py --all` from any directory; requires the `opencode` CLI and
access to one of the assignment's permitted models. `--dry-run` does not call
the model or change files. Only a method whose body is `pass` may be replaced.
"""

import argparse
import ast
import json
from pathlib import Path
import subprocess
import sys
import textwrap

ASSIGNMENTS = Path(__file__).resolve().parents[1]
REPOSITORY = ASSIGNMENTS / "playground"
TASKS = ASSIGNMENTS / "missing_code.json"
sys.path.insert(0, str(ASSIGNMENTS / "Task_4"))
from match import match  # noqa: E402

ALLOWED_MODELS = {
    "gpt-6-luna", "gpt-5.6-luna", "gpt-5.4-nano", "gpt-5-nano",
    "gpt-5-mini", "gpt-4.1-nano", "gpt-4o-mini",
}


def find_method(tree, class_name, method_name):
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name]
    if len(classes) != 1:
        raise ValueError(f"Expected exactly one class {class_name}")
    methods = [n for n in classes[0].body
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == method_name]
    if len(methods) != 1:
        raise ValueError(f"Expected exactly one {class_name}.{method_name}")
    return methods[0]


def generate(prompt, model):
    """Ask OpenCode for text (not autonomous tool edits); parse its JSON event stream."""
    if model not in ALLOWED_MODELS:
        raise ValueError(f"Model not allowed by assignment: {model}")
    completed = subprocess.run(
        ["opencode", "run", "--archived", "--format", "json", "--model",
         f"openai/{model}", prompt], cwd=REPOSITORY, text=True,
        capture_output=True, check=True, timeout=180,
    )
    events = [json.loads(line) for line in completed.stdout.splitlines() if line.strip().startswith("{")]
    if any(event.get("type") == "tool_use" or event.get("part", {}).get("type") == "tool"
           for event in events):
        raise ValueError("Model called a tool instead of returning only source code")
    result = "".join(e["part"]["text"] for e in events if e.get("type") == "text")
    if not result.strip():
        raise ValueError(f"Model returned no text: {completed.stderr[-500:]}")
    return result.strip()


def extract_body(answer, name):
    """Accept one function (optional decorator/fence), never arbitrary file edits."""
    if answer.startswith("```"):
        answer = "\n".join(answer.splitlines()[1:-1])
    tree = ast.parse(textwrap.dedent(answer))
    if len(tree.body) != 1 or not isinstance(tree.body[0], (ast.FunctionDef, ast.AsyncFunctionDef)):
        raise ValueError("Expected only a function definition")
    method = tree.body[0]
    if method.name != name or not method.body or isinstance(method.body[-1], ast.Pass):
        raise ValueError(f"Expected implemented function {name}")
    return method.body


def solve(task, model="gpt-6-luna", dry_run=False):
    """Retrieve 5 chunks, request implementation, and replace only target body."""
    path = (REPOSITORY / task["file"]).resolve()
    if not path.is_relative_to(REPOSITORY.resolve()) or not path.is_file():
        raise ValueError(f"Unsafe or missing target path: {task['file']}")
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    method = find_method(tree, task["class"], task["method"])
    target_class = next(n for n in tree.body
                        if isinstance(n, ast.ClassDef) and n.name == task["class"])
    if len(method.body) != 1 or not isinstance(method.body[0], ast.Pass):
        raise ValueError(f"Refusing to overwrite a non-stub: {task['class']}.{task['method']}")
    description = ast.literal_eval(task["docstring"].strip())
    query = f"{task['file']} {task['class']}.{task['method']}: {description}"
    retrieved = match(query, n=5)
    if dry_run:
        print(query)
        for chunk, score in retrieved:
            print(f"  {score:.4f} {chunk['id']}")
        return
    context = "\n\n".join(
        f"File {chunk['path']} lines {chunk['start']}-{chunk['end']} "
        f"({chunk['symbol']}):\n{chunk['text']}"
        for chunk, _ in retrieved
    )
    original = "\n".join(source.splitlines()[method.lineno - 1:method.end_lineno])
    class_context = "\n".join(source.splitlines()[target_class.lineno - 1:target_class.end_lineno])
    prompt = (
        "Implement exactly the Python method below, using the repository context. "
        "Return ONLY one complete Python function definition with the same name and "
        "signature, no class, explanation, imports or other code. Do not use tools. "
        "The returned body must implement the documented behavior and should validate "
        "inputs consistent with the surrounding code. Use only attributes shown in "
        "the target class; do not guess attribute names.\n\n"
        f"Task: {query}\nCurrent method:\n{original}\n\n"
        f"Five retrieved repository chunks:\n{context}\n\n"
        f"Target class (authoritative for available fields):\n{class_context}"
    )
    body = extract_body(generate(prompt, model), task["method"])
    # Insert statements only: signatures, decorators, neighboring methods, and
    # comments outside the stub remain byte-for-byte unchanged.
    lines = source.splitlines(keepends=True)
    indentation = " " * (method.col_offset + 4)
    replacement = "".join(textwrap.indent(ast.unparse(stmt), indentation) + "\n" for stmt in body)
    updated = "".join(lines[:method.body[0].lineno - 1]) + replacement + "".join(lines[method.body[0].end_lineno:])
    compile(updated, str(path), "exec")
    path.write_text(updated, encoding="utf-8")
    print(f"Implemented {task['class']}.{task['method']} in {task['file']}")


def solve_text(text, file, class_name, method_name, model="gpt-6-luna", dry_run=False):
    """Solve an arbitrary textual coding task for a named repository method."""
    solve({"file": file, "class": class_name, "method": method_name,
           "docstring": repr(text)}, model=model, dry_run=dry_run)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="Solve every task in missing_code.json")
    parser.add_argument("--task", type=int, help="One-based position in missing_code.json")
    parser.add_argument("--text", help="Free-form textual task (requires --file, --class, --method)")
    parser.add_argument("--file", help="Path relative to the cloned repository")
    parser.add_argument("--class", dest="class_name", help="Target class name")
    parser.add_argument("--method", help="Target method name")
    parser.add_argument("--model", default="gpt-6-luna", choices=sorted(ALLOWED_MODELS))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if sum((args.all, args.task is not None, args.text is not None)) != 1:
        parser.error("choose exactly one of --all, --task and --text")
    if args.text is not None:
        if not all((args.file, args.class_name, args.method)):
            parser.error("--text needs --file, --class and --method")
        solve_text(args.text, args.file, args.class_name, args.method,
                   model=args.model, dry_run=args.dry_run)
        sys.exit(0)
    tasks = json.loads(TASKS.read_text(encoding="utf-8"))
    if args.task is not None and not 1 <= args.task <= len(tasks):
        parser.error(f"--task must be between 1 and {len(tasks)}")
    selected = tasks if args.all else [tasks[args.task - 1]]
    for task in selected:
        solve(task, model=args.model, dry_run=args.dry_run)
