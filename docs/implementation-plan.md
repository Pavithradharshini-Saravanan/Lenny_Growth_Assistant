# Implementation Plan and Phase Status

**Current Status:** Phase 2 — Transcript Ingestion and Grounded Chat (COMPLETED, awaiting approval for Phase 3)  
**Deadline:** 12 October 2026, end of day  
**Working rule:** Complete one end-to-end local path before polishing optional details.

---

## Phase Roadmap & Status

### Phase 0 — Understand and Plan (COMPLETED)
- **Status:** Completed & Approved. Architecture revised to use `ClaudeAgentSDKAdapter` (`claude-agent-sdk`) for Cloud mode and `OllamaAgentAdapter` for Local mode.

---

### Phase 1 — Minimal Runnable Foundation (COMPLETED)
- **Status:** Completed & Approved. FastAPI backend, PostgreSQL schema, independent session CRUD, provider toggle, and UI shell built and verified (7/7 tests passed).

---

### Phase 2 — Transcript Ingestion and Grounded Chat (COMPLETED)
- **Goal:** Answer product/growth questions using the real transcript knowledge base, with traceable source labels.
- **Completed Tasks:**
  1. Inspected transcript source repository (`https://github.com/ChatPRD/lennys-podcast-transcripts`) and documented file structure (269 episode transcripts in Markdown with YAML frontmatter).
  2. Built repeatable ingestion pipeline in `backend/app/ingestion/ingest.py` parsing YAML metadata (`guest`, `title`, `youtube_url`, `publish_date`), chunking text semantically by speaker/paragraph boundaries, and persisting to `TranscriptModel` and `TranscriptChunkModel`.
  3. Created RAG retrieval engine in `backend/app/services/retrieval_service.py` performing hybrid search and relevance scoring over indexed chunks.
  4. Wired `search_transcripts_domain` in `backend/app/tools/base.py` to `RetrievalService` for grounded evidence retrieval.
  5. Created `/api/ingest` endpoint (`backend/app/api/ingest.py`) to trigger sample or batch transcript ingestion on demand.
  6. Added comprehensive automated tests in `tests/test_ingestion.py` and `tests/test_retrieval.py` verifying parsing, chunking, database persistence, grounded retrieval, source attribution metadata, empty retrieval, and novel/paraphrased queries.
- **Evidence / Verification:** All 14 automated tests passed in `pytest tests/ -v` (`14 passed in 19.35s`).

---

### Phase 3 — Writing Skill & Sandboxed Artifact Viewer (COMPLETED)
- **Goal:** Dedicated Ship 30 for 30 writing skill (~1,250 words) and Markdown/HTML artifact generation with sandboxed in-app viewer.
- **Completed Tasks:**
  1. Built reusable `Ship30WritingSkill` in `backend/app/skills/ship30.py` implementing hook, 5-pillar progression, skimmability, practical takeaway, transcript evidence grounding, and ~1,250 words targeting (1,100–1,400 word tolerance).
  2. Linked `run_ship30_skill_domain` in `backend/app/tools/base.py` to `Ship30WritingSkill`.
  3. Built `create_artifact_domain` with robust `bleach` HTML sanitization neutralizing sandbox escape vectors (`window.parent`, `top.location`, `document.cookie`, `localStorage`), `javascript:` URIs, and dangerous attributes.
  4. Enhanced in-app Artifact Viewer beside chat in `frontend/index.html` and `frontend/app.js` with preview/code tab switching, formatted Markdown rendering, code copy button, and strict iframe sandboxing (`sandbox="allow-scripts"` with opaque `null` origin).
  5. Implemented automated regression and unit tests in `tests/test_skills.py` and `tests/test_artifacts.py`.
- **Evidence / Verification:** 46/46 automated tests passed (`python -m pytest tests/ -v`).

---

### Phase 4 — Final Hardening, Documentation & Handoff (COMPLETED)
- **Goal:** Final test suite verification, comprehensive `README.md` handoff documentation, manual UI test plan, container files, and submission preparation.
- **Completed Tasks:**
  1. Fixed missing `re` import in `backend/app/agent/ollama_agent.py` and added regression tests.
  2. Created `requirements.txt` and `Dockerfile` for reproducible container startup.
  3. Created concise `docs/manual-ui-test-plan.md` covering all 9 manual verification workflows.
  4. Wrote complete, production-grade `README.md` with architecture, quickstart, ingestion guide, provider details, security model, and troubleshooting.
  5. Ran complete test suite: all 48 tests passing (`48 passed in 4.88s`).
  6. Verified live end-to-end Ollama chat and UI citation rendering via browser subagent.
- **Evidence / Verification:** 48/48 automated tests passed (`python -m pytest tests/ -v`).

---

## Status Log
- **2026-10-10 (Phase 2):** Transcript ingestion pipeline, RAG retrieval engine, and `/api/ingest` endpoint implemented.
- **2026-10-11 (Phase 3):** Reusable Ship 30 writing skill (~1,250 words), HTML/Markdown artifact creation, `bleach` sanitization, and sandboxed Artifact Viewer implemented. All 46 pytest tests passed (`46 passed in 4.60s`).
- **2026-10-11 (Phase 4):** Regression tests added (48 passed), `README.md`, `Dockerfile`, `requirements.txt`, and `docs/manual-ui-test-plan.md` created. Live browser UI verified. Ready for video recording and repo submission.

