# Phase 0 — Understand, Plan, and Verify (Do not code yet)

## Goal
Turn the assignment into an approved, feasible plan. Avoid building the wrong architecture.

## Prompt for Antigravity
Critical: this must be a dynamic agentic application. In the plan, identify likely hardcoding failure modes and explain how general-purpose tools, model-based request interpretation, runtime retrieval, configuration and validation will avoid them. Do not design fixed keyword-to-action routing, hardcoded source/citation maps, or example-specific workflows.
Read `AGENTS.md`, `docs/PROJECT_RULES.md`, this phase file, and the original assignment at `docs/reference/Forward_Deployed_Engineer_Take_Home_Assignment_12_Oct_2026.docx`. The assignment is the source of truth.

Do not implement application code yet. Do not install dependencies yet.

1. Extract all mandatory requirements, deliverables, deadline and evaluation criteria into `docs/REQUIREMENTS_TRACEABILITY.md`. Preserve the original meaning.
2. Find and inspect the transcript repository and the Ship 30 for 30 guide linked in the assignment. Record their actual URLs and the relevant principles you found. If a link cannot be accessed, say so and ask me; do not invent the guide's contents or URL.
3. Inspect my local environment relevant to Windows, Python, Node, PostgreSQL/Docker, Ollama and installed models. Do not expose private machine data.
4. Verify the proposed agent integration (Anthropic Claude Agent SDK or Pi Coding Agent) can fit the required FastAPI architecture and the local Ollama demo. Verify how it can support the cloud adapter. Report actual limitations before selecting it.
5. Propose a minimal local-first architecture: frontend, FastAPI backend, PostgreSQL, transcript ingestion/retrieval, provider adapters, writing skill, artifact viewer and tests.
6. Explain provider switching. Local Ollama must work without a cloud key; cloud must be implemented but optional to run; no silent fallback.
7. Define database entities, API contracts, error handling, retrieval/citation behavior, artifact isolation and startup approach.
8. Create or update `docs/PRD.md`, `docs/architecture.md`, `docs/design.md`, and `docs/implementation-plan.md`. Include discovery brief, user/problem, success metrics, assumptions, scope, user flows, acceptance criteria, risks, and trade-offs.
9. Create a list of acceptance checks and mark all items not yet implemented.
10. Give me a simple-English summary: what we are building, why each major component exists, what is hardest, and what must be finished first.

Stop and ask for my approval before writing application code. Do not mark any requirement as completed unless verified.
