# Agent Log — Chat Request Lifecycle Diagnosis & Reliability Fix

**Date:** 2026-10-10  
**Phase:** Request Lifecycle & Grounded Retrieval Reliability Fix  
**Status:** COMPLETED & VERIFIED  

## 1. Proven Root Cause Summary
1. **Network Error (HTTP 500) Root Cause:**
   - In `backend/app/api/chat.py`, `SessionService.update_session(db, request.session_id, SessionUpdate(title=new_title))` was invoked when session titles were default ("New Chat").
   - `SessionUpdate` was missing from schema imports in `chat.py`, causing Python to raise `NameError: name 'SessionUpdate' is not defined`.
   - The unhandled `NameError` triggered an HTTP 500 Internal Server Error, rendered in the UI as "Network error or server unavailable."

2. **Duplicate Messages & Refresh Behavior Root Cause:**
   - `chat.py` committed the user's message to the database *before* executing the agent adapter and updating session title.
   - When the 500 error occurred, the user message remained saved in PostgreSQL/SQLite without an assistant response.
   - On page refresh, history loaded the orphan user message. Resubmitting or retrying created a second identical user message entry in the database.
   - The frontend did not lock submission during in-flight requests or disable input controls, allowing accidental double-clicks to issue concurrent `POST /api/chat` requests.

4. **Existing Session History Degradation & Degenerative Repetition Loop:**
   - In existing sessions with multiple turns, passing unbounded conversation history to a local 3B model (`qwen2.5:3b`) caused context explosion and severe CPU evaluation latency (exceeding browser timeouts and triggering network errors).
   - Furthermore, when a prior turn in history contained negative assistant boilerplate ("The available transcripts do not contain information..."), the 3B model learned the few-shot completion pattern from its own history, bypassing tool calls (`tool_calls = []`) and repeating the negative text token sequence directly.
   - Also, a previous filter that checked `if "do not contain information" in content.lower(): sources = []` erroneously wiped legitimate sources if the assistant wrote nuanced sentences like *"While the transcripts do not contain information on X, Brian Chesky stated that..."*.

## 2. Key Code Changes
- **[ollama_agent.py](../backend/app/agent/ollama_agent.py):**
  - Implemented history normalization with a sliding window of recent messages (`history[-6:]`) and deduplication of consecutive identical message turns.
  - Implemented robust tool fallback: if the 3B model skips tool invocation on a factual prompt due to prior history bias, the adapter checks whether grounded transcript chunks exist for the prompt and feeds the evidence to Turn 2 synthesis.
  - Removed substring wipeout of sources; citations are accurately preserved whenever retrieved.
- **[chat.py](../backend/app/api/chat.py):**
  - Added missing `SessionUpdate` import.
  - Added structured Python logging (`logger.info`, `logger.error`, `logger.exception`).
  - Added transaction rollback (`db.delete(user_msg); db.commit()`) in exception handlers to delete orphan user messages if agent execution or response persistence fails.
  - Bounded history passed to adapters to a sliding window (`history_records[:-1][-8:]`).
- **[ingest.py](../backend/app/ingestion/ingest.py):**
  - Added title and source URL deduplication check in `ingest_transcript_from_text()`.
- **[main.py](../backend/app/main.py):**
  - Added automatic transcript index count check in FastAPI `lifespan` startup handler to trigger sample transcript ingestion if the database is unpopulated.
- **[app.js](../frontend/app.js):**
  - Implemented submission guard lock (`isSubmitting`) and disabled input + submit button during request lifecycle.
  - Added optimistic DOM rollback (`removeMessage(userMsgId)`) and input text restoration if API returns an error or network fails.
- **[test_api.py](../tests/test_api.py) & [test_ingestion.py](../tests/test_ingestion.py):**
  - Added regression tests covering fresh chat, existing session multi-turn history (`test_existing_session_multi_turn_history`), repeated identical queries (`test_existing_session_repeated_questions`), title update without `NameError`, orphan message cleanup, and transcript deduplication.

## 3. Empirical Test Results
- **Automated Test Suite:** 22/22 test cases PASSED (`python -m pytest tests/ -v`).
- **Live Multi-Turn Local Ollama Flow (4 Consecutive Turns in Session `bb78988a-2127-4bf7-a9a7-9e7ec7e83460`):**
  - **Turn 1 (Fresh Session):** *"What did Brian Chesky say about product marketing?"*
    - Status: HTTP 200 | Sources: 5 | Grounded answer referencing Brian Chesky's remarks on combining PM and product marketing.
  - **Turn 2 (Existing Session):** *"Why does Airbnb only launch features twice a year?"*
    - Status: HTTP 200 | Sources: 5 | Grounded answer citing the rolling two-year roadmap and May/October release cycles.
  - **Turn 3 (Repeated Question in Existing Session):** *"What did Brian Chesky say about product marketing?"*
    - Status: HTTP 200 | Sources: 5 | Successfully retrieved evidence and answered with citations without degenerating into negative repetition loop.
  - **Turn 4 (Out-of-Corpus in Existing Session):** *"What is quantum photolithography semiconductor manufacturing?"*
    - Status: HTTP 200 | Sources: 0 | Answered honestly: *"The available transcripts do not contain information to answer this question."* (Zero fabricated citations).
  - **Session Refresh Check:**
    - GET `/api/sessions/{session_id}/messages` returned all 8 messages in strict chronological order with matching source badges and no duplicates.
