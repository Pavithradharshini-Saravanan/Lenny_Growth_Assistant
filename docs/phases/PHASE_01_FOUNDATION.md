# Phase 1 — Runnable Foundation and Persistence

## Goal
Create the smallest complete application skeleton that starts reliably and persists separate chat sessions.

## Prompt for Antigravity
Apply the anti-hardcoding rules in `docs/PROJECT_RULES.md`. Do not add keyword-based request routing, task-specific branches, canned assistant responses, or fake data presented as real. Keep configuration data-driven.
Read `AGENTS.md`, `docs/PROJECT_RULES.md`, `docs/implementation-plan.md`, `docs/REQUIREMENTS_TRACEABILITY.md`, and this phase file. Inspect the existing repository before editing. Implement Phase 1 only.

Build:
- A FastAPI backend with health/readiness endpoints, typed request/response schemas, validation and structured errors.
- A simple frontend shell with a chat layout and a visible selected-provider indicator, even if model calls arrive in a later phase.
- PostgreSQL schema/migrations for sessions and messages, including IDs, timestamps and appropriate user/session metadata.
- Create/list/open chat sessions; ensure each session has separate message history.
- Configuration loaded from environment variables and `.env.example` with placeholders only.
- A reproducible local startup path. Prefer Docker Compose only if it makes setup simpler and does not hide Ollama's host connection details.
- Basic API and persistence tests.

Constraints:
- Do not implement fake AI answers to simulate a completed feature.
- Do not build retrieval, the writing skill or artifact generation yet unless a minimal UI placeholder is necessary.
- Keep modules separated but avoid unnecessary abstractions.
- Never commit secrets or local databases.

Acceptance checks:
1. Backend starts with documented command.
2. Health endpoint returns healthy status.
3. Database migrations/schema setup work from documented steps.
4. A session and messages can be saved and retrieved.
5. Two sessions do not share messages.
6. Tests run and their real output is reported.
7. README/setup notes are updated.
8. Traceability statuses change only where verified.

At the end, report changed files, commands run, test results, remaining blockers, and ask before starting Phase 2.
