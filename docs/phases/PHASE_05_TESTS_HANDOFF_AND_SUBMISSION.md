# Phase 5 — Test, Document, Package, and Submit

## Goal
Make it possible for a fresh evaluator to clone the public repository and run the application using only the documented steps.

## Prompt for Antigravity
Before finalizing, perform an anti-hardcoding audit: search for keyword/trigger maps, task-specific `if/elif` workflows, hardcoded domain/app aliases, fixed demo answers, fake retrieval/citations, and prompt-specific branches. Remove or justify any such code. Test at least three distinct inputs including paraphrases, and document results. Do not claim dynamic behavior based only on one happy-path example.
Read `AGENTS.md`, project rules, implementation plan, traceability checklist, and this phase file. Inspect the complete application. Do not claim untested features work. Implement Phase 5 only.

1. Run the complete automated test suite and fix failures without broad rewrites.
2. Ensure meaningful tests cover API validation/errors, transcript retrieval/source attribution, provider routing, session isolation and PostgreSQL persistence.
3. Write a concise manual UI test plan covering new chat, follow-up context, citations, local provider, cloud missing-key behavior, writing skill, Markdown artifact, HTML artifact, and unsafe HTML.
4. Complete `README.md`: purpose, architecture, prerequisites, Windows-friendly setup, environment variables, PostgreSQL setup, transcript ingestion, Ollama/model setup, optional cloud setup, run commands, tests, troubleshooting, known limitations.
5. Ensure `.env.example` has safe placeholders and `.gitignore` excludes `.env`, secrets, virtual environments, databases, generated private data and build output.
6. Review `PRD.md`, `design.md`, `architecture.md`, `implementation-plan.md`, and `docs/REQUIREMENTS_TRACEABILITY.md` for accuracy.
7. Keep coding-agent transcripts/logs in a dedicated folder, including significant failed attempts and corrections; remove secrets and sensitive data.
8. Verify clean Git status, commit sensible changes, publish a public GitHub repository, and test the documented steps from a fresh clone if time permits.
9. Prepare a 2–3 minute camera-on demo plan: explain problem, show a grounded answer with citations, show Ollama local mode, demonstrate writing/artifact behavior, and explain one important trade-off. Upload to YouTube and record the link.
10. Use the submission form in the assignment: https://forms.gle/LgotDHNVxW1mbzNE7

Final report must list:
- Verified features and evidence.
- Commands/tests run and actual results.
- Unverified items (especially live cloud inference if no key).
- Known limitations.
- GitHub and demo links only if they truly exist.
- Submission status.
Do not claim deployment, upload, publication or submission without evidence.
