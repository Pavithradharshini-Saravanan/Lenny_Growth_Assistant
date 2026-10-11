# Agent Log — Phase 1: Minimal Runnable Foundation

**Date:** 2026-10-10  
**Phase:** Phase 1 — Minimal Runnable Foundation  
**Status:** COMPLETED  

## 1. Accomplishments
- Implemented FastAPI backend application in `backend/app/main.py`.
- Implemented database models in `backend/app/db/models.py` for PostgreSQL / SQLite persistence (`sessions`, `messages`, `transcripts`, `transcript_chunks`, `artifacts`).
- Implemented session management CRUD services in `backend/app/services/session_service.py`.
- Established shared tool domain layer in `backend/app/tools/base.py` (`search_transcripts`, `run_ship30_skill`, `create_artifact`).
- Implemented `ClaudeAgentSDKAdapter` (`claude-agent-sdk`) for Cloud mode and `OllamaAgentAdapter` (`qwen2.5:3b`) for Local mode.
- Enforced strict key verification: selecting Cloud mode without `ANTHROPIC_API_KEY` returns `HTTP 400 Bad Request` with an explicit diagnostic message (zero silent fallback to Ollama).
- Created frontend SPA in `frontend/` (`index.html`, `styles.css`, `app.js`) featuring deep space slate theme, provider selector, session sidebar, chat panel, and sandboxed iframe artifact viewer (`sandbox="allow-scripts"`).
- Created `.env.example`, `.gitignore`, `docker-compose.yml`, and `run.py`.

## 2. Automated Test Execution Results
Executed command: `python -m pytest tests/ -v`

```text
tests/test_agent.py::test_agent_dispatcher_instantiation PASSED          [ 14%]
tests/test_agent.py::test_missing_cloud_key_raises_error PASSED          [ 28%]
tests/test_agent.py::test_chat_endpoint_missing_cloud_key_returns_400 PASSED [ 42%]
tests/test_api.py::test_health_endpoint PASSED                           [ 57%]
tests/test_api.py::test_config_endpoint PASSED                           [ 71%]
tests/test_api.py::test_session_lifecycle PASSED                         [ 85%]
tests/test_api.py::test_session_isolation PASSED                         [100%]

7 passed in 8.69s
```

## 3. Evidence
- Session Isolation: `test_session_isolation` verified that messages in Session A do not leak into Session B.
- Provider Enforcement: `test_chat_endpoint_missing_cloud_key_returns_400` verified that requesting Cloud mode without an API key raises `HTTP 400` without silently switching to Ollama.
