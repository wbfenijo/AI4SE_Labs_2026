---
name: architecture-decision-record
description: "Use when analyzing software requirements, proposing multiple architecture options, selecting an architecture, or creating and reviewing an Architecture Decision Record (ADR). Preserve a conversation log, compare at least three alternatives, explain trade-offs and low-level risks, and produce a decision-ready ADR."
argument-hint: "Requirements file or project description to analyze"
user-invocable: true
---

# Architecture Decision Record Workflow

## Purpose

Turn a requirements document into a defensible architecture decision and a
reviewed ADR. Keep the reasoning visible so another engineer can understand
what was considered, why the decision was made, and when it should be
revisited.

## Required outputs

1. A conversation or discussion log. It may be a structured summary rather
   than a verbatim transcript, but it must record:
   - the instruction to keep notes;
   - requirements and architectural drivers;
   - at least three architecture proposals;
   - questions, answers, trade-offs, and painful implementation details;
   - the review and revision of the ADR;
   - the final decision and acceptance.
2. A final ADR containing the sections in the procedure below.

## Procedure

### 1. Establish scope and capture notes

- Read the complete requirements source before proposing an architecture.
- Identify users/roles, core workflows, data ownership, external integrations,
  quality attributes, and implied constraints.
- Start the conversation log before analysis. State that notes will be kept
  throughout the discussion.
- Do not invent requirements. Mark assumptions and unresolved questions.

### 2. Extract decision drivers

Write a concise list of drivers such as consistency, security, availability,
operability, delivery speed, team size, scaling, replaceability of external
providers, and future evolution. Distinguish requirements from preferences.
Call out the highest-risk workflow and its failure modes.

### 3. Propose three materially different architectures

For each proposal, record:

- structure and deployment shape;
- mapping of requirements to components or modules;
- advantages;
- disadvantages and operational costs;
- low-level implementation pain points;
- consistency, failure, security, testing, and scaling implications;
- conditions under which it would be appropriate.

Prefer genuinely different options, for example a layered monolith, a modular
monolith with hexagonal boundaries, and microservices/event-driven services.
Use alternatives appropriate to the requirements rather than selecting a
favorite in advance.

### 4. Compare and select

Use an overview table comparing the alternatives on the decision drivers.
Select one option and explain why it fits the stated scope. Explain why the
rejected options were not selected and identify what evidence could change the
decision.

### 5. Draft and inspect the ADR

Create the ADR with:

1. title and metadata (status, date, owners, scope);
2. context;
3. decision drivers;
4. decision and module/component responsibilities;
5. architecture overview;
6. alternatives considered and comparison table;
7. positive and negative consequences;
8. risks and mitigations;
9. security, consistency, and reliability invariants;
10. validation/testing plan;
11. scope and non-goals;
12. evolution/reconsideration triggers.

Add a technology-neutral diagram when the architecture has meaningful
boundaries. Add a sequence diagram for a workflow whose failure behavior is
central, such as checkout, payment, reservation, or message delivery. Keep
diagrams readable and avoid pretending that a diagram specifies technologies
not chosen.

Inspect the first draft against the requirements. Ask:

- Can a new engineer tell what was chosen and why?
- Are rejected alternatives and their costs explicit?
- Are consistency and failure behaviors visible?
- Is any detail an implementation specification that does not belong in an
  ADR?
- Would a table or diagram make comparison or boundaries clearer?

Revise the ADR at least once based on that inspection, and record the review in
the conversation log.

### 6. Validate and report

- Verify links to the requirements and prior records.
- Check that the selected architecture, diagrams, table, invariants, and
  validation plan are present.
- Run a whitespace or Markdown sanity check when available.
- Report assumptions, artifacts, and validation results.

## Quality rules

- Never treat a browser redirect as proof of payment; require a verified
  provider callback or provider-side lookup.
- For finite inventory, describe an atomic reservation/locking strategy and
  concurrency tests.
- For retries and asynchronous work, describe idempotency, durable messages,
  retry/backoff, and dead-letter/manual recovery behavior.
- Keep authorization server-side and enforce resource ownership.
- Do not put credentials, passwords, reset tokens, or sensitive payment data
  in source files, logs, or emails.
- Prefer explicit invariants and responsibilities over vague claims such as
  "the system will be scalable."

