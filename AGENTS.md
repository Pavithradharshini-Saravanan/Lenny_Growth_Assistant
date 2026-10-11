# Persistent Instructions for Coding Agent — The Lenny Growth Assistant

Before every implementation task:
1. Read this file.
2. Read `docs/PROJECT_RULES.md`.
3. Read `docs/implementation-plan.md` and the currently active phase file in `docs/phases/`.
4. Read `docs/REQUIREMENTS_TRACEABILITY.md` before deciding a requirement is complete.
5. Inspect the existing code and tests before editing.
6. State the active phase, intended files to change, and acceptance criteria in a short plan.
7. Make only the changes needed for the active task. Do not start later phases without permission.

## Source of truth
The original assignment in `docs/reference/Forward_Deployed_Engineer_Take_Home_Assignment_12_Oct_2026.docx` is the primary source of requirements. If it is missing, stop and ask for it; do not invent missing requirements. These project documents translate the assignment into an implementation plan; they do not override it.

## Critical anti-hardcoding rule
The application must handle novel and paraphrased requests dynamically. Do not create fixed keyword/trigger lists, hardcoded domain/app aliases, phrase-to-action dictionaries, task-specific intent branches, canned answers, fixed citations, or fake retrieval results. Use the model/agent to interpret each request and choose among reusable, typed, validated tools. Tool implementations may be deterministic, but must provide general capabilities rather than hardcoded workflows for specific prompts. Only use fixed rules for security, validation, protocol constraints, or other documented invariants. Test with unseen paraphrases and inspect code for task-specific branches before declaring a feature complete. See `docs/PROJECT_RULES.md`, section 5.

## Workflow
- Work one phase at a time.
- At the end of a phase, run relevant tests and report exact commands and results.
- Update the traceability checklist and implementation plan only when there is evidence.
- Keep `docs/agent-logs/` or `agent-logs/` records of significant attempts, failures, and corrections, with secrets removed.
- If blocked, explain the blocker and offer the smallest compliant alternative.
- Ask before major architecture changes, deleting data, changing database schema in a breaking way, or adding a new service.

## No false completion
Never say a feature is complete merely because code was written. Verify it with a test, a reproducible manual check, or explicitly label it unverified.
