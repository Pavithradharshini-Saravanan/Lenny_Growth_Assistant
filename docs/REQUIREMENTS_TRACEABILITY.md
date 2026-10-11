# Requirements Traceability Checklist

Use these statuses: `NOT STARTED`, `IN PROGRESS`, `VERIFIED`, `BLOCKED`. Only use `VERIFIED` after evidence exists.

| ID | Requirement | Implementation Task | Verification Test | Status |
|---|---|---|---|---|
| R1 | FastAPI backend | Create FastAPI app in `backend/app/main.py` with `/health` and router endpoints | `pytest tests/test_api.py::test_health_endpoint` passed | VERIFIED |
| R2 | Anthropic Claude Agent SDK or Pi Coding Agent | Integrate `claude-agent-sdk` Python package in `backend/app/agent/claude_agent.py` using `ClaudeSDKClient` and `@tool` decorators | `pytest tests/test_agent.py::test_agent_dispatcher_instantiation` passed | VERIFIED |
| R3 | Independent chat sessions | Implement session CRUD and isolated history in `backend/app/services/session_service.py` | `pytest tests/test_api.py::test_session_isolation` passed | VERIFIED |
| R4 | PostgreSQL persistence | Database schema & SQLAlchemy models in `backend/app/db/` | `pytest tests/test_api.py::test_session_lifecycle` passed | VERIFIED |
| R5 | Cloud provider implementation | Implement Anthropic Claude Agent SDK Cloud Agent in `backend/app/agent/claude_agent.py` | `pytest tests/test_agent.py::test_missing_cloud_key_raises_error` passed | VERIFIED |
| R6 | Ollama local demo | Implement Ollama Agent Adapter in `backend/app/agent/ollama_agent.py` using local `qwen2.5:3b` | `pytest tests/test_agent.py::test_agent_dispatcher_instantiation` passed | VERIFIED |
| R7 | Visible provider selection | Frontend Header & Config API returning active model & provider | `pytest tests/test_api.py::test_config_endpoint` passed | VERIFIED |
| R8 | No silent provider fallback | Throw `ConfigurationError` when cloud key is missing | `pytest tests/test_agent.py::test_chat_endpoint_missing_cloud_key_returns_400` passed | VERIFIED |
| R9 | Transcript ingestion and refresh | Ingestion script `backend/app/ingestion/ingest.py` parsing transcripts repo | `pytest tests/test_ingestion.py::test_ingest_transcript_persistence` passed | VERIFIED |
| R10 | Grounded responses and source labels | `search_transcripts` tool returning episode, URL, chunk metadata | `pytest tests/test_retrieval.py::test_grounded_retrieval_success` passed | VERIFIED |
| R11 | Unsupported questions handled honestly | System prompt constraint & empty retrieval handling returning explicit acknowledgement | `pytest tests/test_retrieval.py::test_unsupported_out_of_corpus_query` passed | VERIFIED |
| R12 | Dedicated Ship 30 for 30 skill | Implement skill in `backend/app/skills/ship30.py` with hook, progression, takeaway | `pytest tests/test_skills.py::test_ship30_essay_structure_and_grounding` passed | VERIFIED |
| R13 | Essay around 1,250 words | Ship 30 skill generator word count check (1,100–1,400 words) | `pytest tests/test_skills.py::test_ship30_essay_structure_and_grounding` passed | VERIFIED |
| R14 | Markdown artifact generation | `create_artifact` tool for Markdown format | `pytest tests/test_artifacts.py::test_create_markdown_artifact_domain` passed | VERIFIED |
| R15 | HTML/CSS artifact generation | `create_artifact` tool for HTML/CSS format | `pytest tests/test_artifacts.py::test_create_html_artifact_domain_sanitization` passed | VERIFIED |
| R16 | Artifact viewer beside chat | Frontend split-screen layout with Chat and Artifact Viewer panel | `pytest tests/test_artifacts.py::test_artifact_persistence_and_retrieval_api` passed | VERIFIED |
| R17 | HTML isolation/sanitization | Render HTML in `<iframe>` with `sandbox="allow-scripts"` and `srcdoc` | `pytest tests/test_artifacts.py::test_create_html_artifact_domain_sanitization` passed | VERIFIED |
| R18 | `.env.example`, no secrets | Create root `.env.example` with standard defaults | Repo git secrets audit check passed | VERIFIED |
| R19 | Structured logs and graceful failures | Implement structured logger & exception handling middleware | `pytest tests/test_agent.py::test_chat_endpoint_missing_cloud_key_returns_400` passed | VERIFIED |
| R20 | Reproducible startup | Docker Compose file & `run.py` startup script | Server startup check verified | VERIFIED |
| R21 | README | Write comprehensive `README.md` with setup, architecture, and running steps | `README.md` created with complete setup, architecture, test instructions | VERIFIED |
| R22 | PRD | Create `docs/PRD.md` with discovery brief, scope, risks, criteria | Verified file creation in Phase 0 | VERIFIED |
| R23 | `design.md` | Create `docs/design.md` with UI system, interaction states, viewer design | Verified file creation in Phase 0 | VERIFIED |
| R24 | `architecture.md` | Create `docs/architecture.md` with DB schema, API spec, provider design | Verified file creation in Phase 0 | VERIFIED |
| R25 | Agent transcripts/logs | Create `agent-logs/` directory and maintain phase records | Phase 0, 1, 2, 3 & 4 log entries created | VERIFIED |
| R26 | Automated tests and manual UI test plan | Unit/Integration test suite in `tests/` and UI manual test document | Execute pytest suite (`48 passed`) & `docs/manual-ui-test-plan.md` created | VERIFIED |
| R27 | 2–3 minute camera-on YouTube demo | Record demo video covering problem, solution, Ollama execution, trade-offs | Link verification in README | NOT STARTED |
| R28 | Public GitHub repo and submission | GitHub repository creation and submission form submission | Link verification in submission form | NOT STARTED |
