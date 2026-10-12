# Coding Agent Transcripts & Execution Logs

This directory contains the complete record of coding-agent sessions, implementation phases, automated test runs, failed attempts, and technical corrections performed during the development of **The Lenny Growth Assistant**.

---

## 1. Secrets Sanitization Guarantee
In accordance with the assignment guidelines:
- **Zero Secrets Committed:** All API keys (`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`), database passwords, and personal credentials have been stripped or replaced with sanitized placeholders (`***` or environment variable references).
- **Zero Committed `.env`:** The actual local environment configuration is excluded via `.gitignore`. Evaluators use `.env.example` as the canonical template.

---

## 2. Directory Index & Log Files

| File | Phase / Topic | Summary & Key Decisions |
|---|---|---|
| [`phase_00_verification.md`](phase_00_verification.md) | **Phase 0:** Architecture & SDK Verification | Verified runtime constraints for `claude-agent-sdk`, defined dual-adapter pattern (Ollama vs. Claude), audited system environment. |
| [`phase_01_execution.md`](phase_01_execution.md) | **Phase 1:** Foundation & Persistence | Built FastAPI skeleton, SQLAlchemy database persistence for sessions/messages, provider selector, and verified with 7 automated tests. |
| [`phase_02_execution.md`](phase_02_execution.md) | **Phase 2:** Ingestion & Grounded RAG | Built repeatable ingestion for Lenny transcripts, semantic chunking, BM25 TF-IDF retrieval, grounded Q&A, and citation generation. |
| [`phase_03_execution.md`](phase_03_execution.md) | **Phase 3:** Ship 30 Skill & Sandboxed Artifacts | Created Ship 30 for 30 writing skill (~1,250 words), Bleach HTML sanitizer, side-by-side Artifact Viewer with `null` origin iframe. |
| [`phase_04_execution.md`](phase_04_execution.md) | **Phase 4:** Hardening, Container & UI Polish | Added Dockerfile, docker-compose, requirements.txt, manual UI test plan, resolved Ollama timeout edge case. |
| [`phase_05_complete_ingestion_and_gemini.md`](phase_05_complete_ingestion_and_gemini.md) | **Phase 5:** Full Library & Gemini Provider | Ingested full 303-episode upstream library with async background ingestion manager, added Google Gemini cloud adapter, dynamic progress card. |
| [`lifecycle_reliability_fix.md`](lifecycle_reliability_fix.md) | **Reliability Fix:** Background Task Lifecycle | Corrected FastAPI lifespan startup blocking issue by decoupling ingestion into a non-blocking background task. |
| [`test_regression_fix_20261012.md`](test_regression_fix_20261012.md) | **Regression Fix:** Test Isolation & Typing | Fixed test runner state isolation across database fixtures, resolved keyword argument signatures for tools, and ensured all 65 tests pass. |

---

## 3. Notable Failed Attempts & How They Were Corrected

### Incident 1: FastAPI Lifespan Startup Deadlock during Upstream Ingestion
- **Failure:** Ingesting 303 podcast transcripts synchronously during FastAPI's `@asynccontextmanager` startup caused server launch to hang for 30+ seconds before accepting HTTP traffic. Health check endpoints timed out.
- **Root Cause:** Awaiting the full HTTP ingestion loop inside the application lifespan blocked the Uvicorn worker event loop from binding to the listening socket.
- **Correction:** Refactored ingestion into `IngestionManager` using `asyncio.create_task()`. The lifespan immediately yields, serving `/health` and UI within 50ms, while ingestion progresses in the background with real-time UI progress updates (`/api/ingest/status`).
- **Log Reference:** [`lifecycle_reliability_fix.md`](lifecycle_reliability_fix.md)

### Incident 2: Incomplete Function-Calling on Smaller Local LLMs (Gemma / Phi)
- **Failure:** While `qwen2.5:3b` handles Ollama function calling cleanly, smaller models like `gemma3:4b` or `phi3:mini` do not support native Ollama tool-calling capabilities and output raw JSON strings or skipped tool invocations.
- **Root Cause:** Ollama API rejects `tools` array for models without tool-call capability tags in `/api/show`.
- **Correction:** Implemented capability detection (`_supports_native_tools()`) in `OllamaAgentAdapter`. For non-tool models, the adapter prompts the model with explicit JSON formatting, parses tool calls with fallback regex, and provides a robust transcript search fallback if the model answers directly.
- **Log Reference:** [`phase_05_complete_ingestion_and_gemini.md`](phase_05_complete_ingestion_and_gemini.md)

### Incident 3: Missing Module Import (`re`) in Ollama Agent Regex Handling
- **Failure:** A unit test mocking raw JSON tool extraction failed with `NameError: name 're' is not defined`.
- **Root Cause:** Missing top-level `import re` statement in `ollama_agent.py`.
- **Correction:** Added `import re` and added regression tests in `test_agent.py` ensuring both native and parsed tool calls execute without error.
- **Log Reference:** [`test_regression_fix_20261012.md`](test_regression_fix_20261012.md)

### Incident 4: Database Fixture State Leaks in Pytest
- **Failure:** Running `pytest` across all suites concurrently caused sporadic `404 Session Not Found` failures when tests shared an in-memory database connection.
- **Root Cause:** Database session fixture teardown was closing the SQLite session before subsequent async assertions completed.
- **Correction:** Configured separate scoped SQLite test databases per test module with transaction rollbacks on fixture teardown.
- **Log Reference:** [`test_regression_fix_20261012.md`](test_regression_fix_20261012.md)
