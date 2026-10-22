"""Agentic requirements-refinement network.

The input is deliberately a directory rather than a list of named files:

    python requirements_network.py --input-dir data/corpus --output output.json

Put OPENAI_API_KEY in the adjacent .env file before running. The three model
names are configurable so the same network can be used with the models
supplied for the laboratory.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from dotenv import load_dotenv
from pydantic import BaseModel, Field


class Candidate(BaseModel):
    name: str
    explanation: str
    priority: Literal["Must", "Should", "Could"]
    source_documents: list[str] = Field(min_length=1)


class DiscardedRequirement(BaseModel):
    candidate: str
    reason: str
    source_documents: list[str] = Field(min_length=1)


class CandidateBatch(BaseModel):
    requirements: list[Candidate]
    discarded_requirements: list[DiscardedRequirement] = Field(default_factory=list)


class Review(BaseModel):
    approved: bool
    issues: list[str] = Field(default_factory=list)
    missing_topics: list[str] = Field(default_factory=list)


class FinalDocument(BaseModel):
    requirements: list[Candidate]
    discarded: list[dict[str, Any]]


class NetworkState(TypedDict, total=False):
    documents: list[dict[str, str]]
    candidates: list[Candidate]
    reviewed: list[Candidate]
    review: Review
    discarded: list[dict[str, Any]]
    output: dict[str, Any]
    iteration: int


def load_documents(input_dir: Path) -> list[dict[str, str]]:
    if not input_dir.is_dir():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    paths = sorted(path for path in input_dir.rglob("*") if path.is_file())
    if not paths:
        raise ValueError(f"Input directory contains no files: {input_dir}")
    return [{"source": path.relative_to(input_dir).as_posix(), "text": path.read_text(encoding="utf-8", errors="replace")}
            for path in paths]


def corpus_text(documents: list[dict[str, str]]) -> str:
    return "\n\n".join(f"--- SOURCE: {doc['source']} ---\n{doc['text']}" for doc in documents)


def make_model(name: str, temperature: float) -> ChatOpenAI:
    load_dotenv(Path(__file__).with_name(".env"), override=False)
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set; add your key to the .env file next to "
            "requirements_network.py"
        )
    model_options: dict[str, Any] = {}
    if name == "gpt-5.6-luna":
        model_options["reasoning_effort"] = "none"
    return ChatOpenAI(model=name, temperature=temperature, **model_options)


def build_graph(models: tuple[str, str, str]):
    extractor = make_model(models[0], 0.1).with_structured_output(
        CandidateBatch, method="function_calling"
    )
    synthesizer = make_model(models[1], 0.2).with_structured_output(
        CandidateBatch, method="function_calling"
    )
    reviewer = make_model(models[2], 0.0).with_structured_output(
        Review, method="function_calling"
    )

    def extract(state: NetworkState) -> NetworkState:
        prompt = """Extract every distinct, testable software requirement from the corpus.
Do not invent requirements. Preserve source filenames exactly. Ignore historical
background unless it states a requested capability. Use Must for essential
operation/compliance, Should for important value, and Could for optional value.
Return concise names and paragraph-length explanations.

CORPUS:
""" + corpus_text(state["documents"]) + "\n\nEXACT SOURCE FILENAMES:\n" + json.dumps(
            [document["source"] for document in state["documents"]], indent=2
        )
        result = extractor.invoke([SystemMessage(content="You are a requirements analyst."),
                                   HumanMessage(content=prompt)])
        return {
            "candidates": result.requirements,
            "discarded": [
                discarded.model_dump()
                for discarded in result.discarded_requirements
            ],
        }

    def synthesize(state: NetworkState) -> NetworkState:
        prompt = """Merge the candidate requirements into one complete, coherent set.
Remove semantic duplicates, resolve terminology, and preserve the union of all
source_documents. Do not discard a real requirement merely because it is similar.
Return only requirements with stable descriptive names and paragraph explanations.
Every source_documents value must be copied exactly from the source catalog below;
never use an author's name, email address, subject, or any other text from a file
as a source identifier.

Candidates:
""" + json.dumps([candidate.model_dump() for candidate in state["candidates"]], indent=2)
        prompt += (
            "\n\nCandidates already identified as discarded. Preserve them in the "
            "blacklist when they remain unsupported, conflicting, or unsafe:\n"
            + json.dumps(state.get("discarded", []), indent=2)
            + "\n\nEXACT SOURCE FILENAMES:\n"
            + json.dumps(
                [document["source"] for document in state["documents"]], indent=2
            )
        )
        result = synthesizer.invoke([SystemMessage(content="You are a senior SRS editor."),
                                     HumanMessage(content=prompt)])
        return {
            "reviewed": result.requirements,
            "discarded": [
                *state.get("discarded", []),
                *[
                    discarded.model_dump()
                    for discarded in result.discarded_requirements
                ],
            ],
        }

    def review(state: NetworkState) -> NetworkState:
        prompt = """Audit the proposed requirements against the original corpus.
Reject if requirements are duplicated, contradictory, unsupported, missing a
major topic, missing traceability, or not testable. If rejected, list concrete
issues and missing topics for the next synthesis pass.
Traceability is valid only when each source identifier is one of the exact
filenames listed below.

CORPUS:
""" + corpus_text(state["documents"]) + "\n\nEXACT SOURCE FILENAMES:\n" + json.dumps(
            [document["source"] for document in state["documents"]], indent=2
        ) + "\n\nPROPOSED:\n" + json.dumps(
            [candidate.model_dump() for candidate in state["reviewed"]], indent=2)
        result = reviewer.invoke([SystemMessage(content="You are a strict requirements auditor."),
                                  HumanMessage(content=prompt)])
        return {"review": result}

    def revise(state: NetworkState) -> NetworkState:
        prompt = ("""Revise the proposed requirements using the audit feedback.
Keep valid requirements, fix contradictions and duplicates, add missing topics
only when supported by the corpus, and retain exact source filenames.
Each source_documents value must be copied exactly from the source catalog;
never use a sender name or email address.

AUDIT:
""" + json.dumps(state["review"].model_dump(), indent=2) + "\n\nPROPOSED:\n" + json.dumps(
            [candidate.model_dump() for candidate in state["reviewed"]], indent=2)
        + "\n\nEXACT SOURCE FILENAMES:\n"
        + json.dumps(
            [document["source"] for document in state["documents"]], indent=2
        )
        )
        result = synthesizer.invoke([SystemMessage(content="You are a meticulous SRS reviser."),
                                     HumanMessage(content=prompt)])
        return {
            "reviewed": result.requirements,
            "discarded": [
                *state.get("discarded", []),
                *[
                    discarded.model_dump()
                    for discarded in result.discarded_requirements
                ],
            ],
            "iteration": state.get("iteration", 0) + 1,
        }

    def finalize(state: NetworkState) -> NetworkState:
        if not state.get("reviewed"):
            raise ValueError("The network produced no requirements")

        requirements = [
            {"id": f"REQ-{index:03d}", **candidate.model_dump()}
            for index, candidate in enumerate(state["reviewed"], start=1)
        ]
        source_names = {document["source"] for document in state["documents"]}
        for requirement in requirements:
            invalid_sources = set(requirement["source_documents"]) - source_names
            if invalid_sources:
                raise ValueError(
                    f"Requirement {requirement['name']!r} cites unknown sources: "
                    f"{sorted(invalid_sources)}"
                )
        output = {
            "title": "PINES Integrated Library System Reporting Requirements",
            "priority_scale": {
                "Must": "Required for a usable or compliant release.",
                "Should": "Important; may be scheduled after Must requirements.",
                "Could": "Desirable enhancement if time and budget permit.",
            },
            "requirements": requirements,
            "discarded_requirements": state.get("discarded", []),
            "review_iterations": state.get("iteration", 0),
        }
        return {"output": output}

    def route_after_review(state: NetworkState) -> str:
        if state["review"].approved or state.get("iteration", 0) >= 2:
            return "finalize"
        return "revise"

    graph = StateGraph(NetworkState)
    graph.add_node("extract", extract)
    graph.add_node("synthesize", synthesize)
    graph.add_node("review", review)
    graph.add_node("revise", revise)
    graph.add_node("finalize", finalize)
    graph.add_edge(START, "extract")
    graph.add_edge("extract", "synthesize")
    graph.add_edge("synthesize", "review")
    graph.add_conditional_edges("review", route_after_review, {"revise": "revise", "finalize": "finalize"})
    graph.add_edge("revise", "review")
    graph.add_edge("finalize", END)
    return graph.compile()


def run(input_dir: Path, output_path: Path, models: tuple[str, str, str]) -> None:
    graph = build_graph(models)
    result = graph.invoke({"documents": load_documents(input_dir), "iteration": 0})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result["output"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--extractor-model", default="gpt-5.4-nano")
    parser.add_argument("--synthesizer-model", default="gpt-5.6-luna")
    parser.add_argument("--reviewer-model", default="gpt-4o-mini")
    args = parser.parse_args()
    run(args.input_dir, args.output, (args.extractor_model, args.synthesizer_model, args.reviewer_model))


if __name__ == "__main__":
    main()
