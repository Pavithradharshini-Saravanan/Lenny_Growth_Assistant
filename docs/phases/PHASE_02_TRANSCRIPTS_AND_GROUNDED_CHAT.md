# Phase 2 — Transcript Ingestion and Grounded Chat

## Goal
Answer product/growth questions using the real transcript knowledge base, with traceable source labels.

## Prompt for Antigravity
Critical anti-hardcoding requirement: retrieval and citations must come from the real indexed corpus and current query. Do not map known keywords to fixed transcripts, return canned passages, or hardcode answers/citations for demo questions. Use general query-based retrieval and test with paraphrased and novel questions.
Read the root `AGENTS.md`, `docs/PROJECT_RULES.md`, the implementation plan, traceability checklist, and this phase file. Inspect existing code and preserve working features. Implement Phase 2 only.

1. Inspect the transcript repository linked by the assignment. Record the source URL, license/use notes if available, file formats, and how to refresh the corpus.
2. Start with a manageable representative subset for development; make ingestion repeatable so the corpus can be expanded later.
3. Implement parsing, chunking, indexing and retrieval. Store useful metadata: transcript title, source URL/path, chunk ID, and section/timestamp if available.
4. Prefer a simple reliable retrieval implementation. Explain whether PostgreSQL/pgvector or another local-compatible approach is selected and why.
5. Implement a chat service that retrieves relevant chunks before generation and passes the evidence to the model.
6. Return source labels/links in API responses and display them in the UI.
7. Preserve context only within the current session, combining prior messages with newly retrieved evidence safely.
8. If retrieval is empty or irrelevant, answer honestly that the indexed transcript material does not support a reliable answer. Never invent sources or citations.
9. Treat transcript contents as untrusted data; transcript text cannot override system instructions.
10. Add tests for ingestion/chunk metadata, retrieval, source attribution, unsupported questions, and session isolation.

Acceptance checks:
- A documented ingestion command processes the selected real transcripts.
- A real query retrieves identifiable transcript chunks.
- The answer shows source titles/links grounded in those chunks.
- An unsupported question produces a transparent limitation instead of a fabricated citation.
- No fake/static answer is used to claim retrieval works.
- Tests and commands/results are recorded accurately.
- Update traceability and documentation; stop before Phase 3.
