# System Architecture — The Lenny Growth Assistant

---

## 1. High-Level Architecture Overview

The Lenny Growth Assistant follows a decoupled, modular full-stack architecture built for local-first zero-cost execution with Ollama while supporting production cloud agents (Anthropic Claude Agent SDK and Google Gemini).

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                          FRONTEND (SPA)                                          │
│  ┌────────────────────────────────────────┐          ┌────────────────────────────────────────┐  │
│  │   Chat Stream & Session Management     │          │   Sandboxed Artifact Viewer (Side-by-  │  │
│  │   (HTML5 / Vanilla CSS & JavaScript)   │          │   Side Iframe with Opaque null Origin) │  │
│  └───────────────────┬────────────────────┘          └───────────────────▲────────────────────┘  │
└──────────────────────┼───────────────────────────────────────────────────┼───────────────────────┘
                       │ HTTP REST (JSON)                                  │ Render (HTML/Markdown)
                       ▼                                                   │
┌──────────────────────────────────────────────────────────────────────────┴───────────────────────┐
│                                       FASTAPI BACKEND SERVICE                                    │
│  ┌───────────────────────────────────┐             ┌──────────────────────────────────────────┐  │
│  │  REST API Routing & Middleware    │             │  Agent Strategy Dispatcher               │  │
│  │  (/chat, /sessions, /ingest)      │             │  (Selects Provider Adapter dynamically)  │  │
│  └─────────────────┬─────────────────┘             └────────────────────┬─────────────────────┘  │
│                    │                                                    │                        │
│                    ▼                                                    ▼                        │
│  ┌───────────────────────────────────┐             ┌──────────────────────────────────────────┐  │
│  │  Session & Persistence Service    │             │  Agent Adapters                          │  │
│  │  (SessionService / SQLAlchemy ORM)│             │  - OllamaAgentAdapter (Local Native/Tool)│  │
│  └─────────────────┬─────────────────┘             │  - ClaudeAgentSDKAdapter (Anthropic SDK) │  │
│                    │                               │  - GeminiAgentAdapter (Google REST API)  │  │
│                    ▼                               └────────────────────┬─────────────────────┘  │
│  ┌───────────────────────────────────┐                                  │                        │
│  │  Database Storage Engine          │                                  ▼                        │
│  │  (PostgreSQL 16 / SQLite dual)    │             ┌──────────────────────────────────────────┐  │
│  │  - sessions, messages, artifacts  │             │  Shared Core Domain Tools                │  │
│  │  - transcripts, transcript_chunks │             │  - search_transcripts_domain             │  │
│  └─────────────────▲─────────────────┘             │  - run_ship30_skill_domain               │  │
│                    │                               │  - create_artifact_domain                │  │
│                    │                               └────────────┬─────────────────────────────┘  │
│                    │                                            │                                │
│                    │                                            ▼                                │
│  ┌─────────────────┴─────────────────┐             ┌──────────────────────────────────────────┐  │
│  │  Dynamic Ingestion Manager        │             │  Hybrid RAG Retrieval Engine             │  │
│  │  (Detached Background Worker)     ├────────────►│  (BM25 TF-IDF Relevance Scoring &        │  │
│  │  - Discovers 303 upstream episodes│             │   Speaker Excerpt Extraction)            │  │
│  └───────────────────────────────────┘             └──────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Boundaries & Responsibilities

### 2.1 Frontend Single Page Application (`frontend/`)
- **Technology:** Pure HTML5, modern CSS3, and vanilla ES6+ JavaScript with zero compilation/bundling steps.
- **Responsibilities:** Renders conversation history, tracks session switching, monitors background ingestion progress, formats markdown into structured HTML, handles Enter-to-send keyboard shortcuts, and renders generated artifacts inside an isolated iframe.
- **Boundary Invariant:** The frontend never communicates directly with LLM providers; all requests route through the FastAPI backend.

### 2.2 FastAPI Application Layer (`backend/app/api/`)
- **Technology:** FastAPI, Uvicorn ASGI server, Pydantic v2 request/response schemas.
- **Responsibilities:**
  - `/api/chat`: Validates session existence, persists user inputs, delegates to the agent adapter, persists assistant responses and artifacts, and updates session titles.
  - `/api/sessions`: CRUD operations for independent multi-turn conversation sessions.
  - `/api/ingest`: Dynamic discovery and ingestion endpoints (`/api/ingest`, `/api/ingest/status`).
  - `/api/health` & `/api/config`: System status, database health, provider connectivity, and model discovery.

### 2.3 Agent Layer & Strategy Dispatcher (`backend/app/agent/`)
- **`BaseAgentAdapter`:** Abstract base class defining common execution interfaces (`run_agent`), provider names, and SDK attributes.
- **`AgentDispatcher`:** Factory that instantiates the active adapter based on user selection:
  1. `OllamaAgentAdapter`: Executes local multi-turn function calling against Ollama (`qwen2.5:3b` / `gemma3:4b`). Supports native function calling and capability-detected JSON parsing.
  2. `ClaudeAgentSDKAdapter`: Integrates the official Anthropic Claude Agent SDK (`claude-agent-sdk`) using `@tool` registrations.
  3. `GeminiAgentAdapter`: Executes Google Gemini via OpenAI-compatible REST endpoints.
- **Strict Non-Fallback Rule:** If a user selects a cloud provider without configuring the required API key, the adapter immediately raises `ConfigurationError`, translating to an HTTP 400 error. The system never silently defaults to another provider.

### 2.4 Domain Tools Layer (`backend/app/tools/`)
Contains pure Python domain functions decoupled from any specific LLM provider:
- `search_transcripts_domain(query, top_k)`: Queries the retrieval service and returns grounded evidence chunks.
- `run_ship30_skill_domain(topic, audience)`: Generates structured ~1,250-word essays adhering to Ship 30 principles.
- `create_artifact_domain(title, artifact_type, content)`: Sanitizes HTML/Markdown code using `bleach` and structures the artifact payload.

### 2.5 Ingestion & RAG Retrieval Engine (`backend/app/ingestion/` & `backend/app/services/`)
- **`IngestionManager`:** Non-blocking background worker that dynamically discovers all 303 episodes from the upstream GitHub/CDN repository, parses YAML frontmatter, semantically chunks paragraphs by speaker boundaries, and persists them idempotently.
- **`RetrievalService`:** Custom BM25 TF-IDF engine calculating term frequency, inverse document frequency, length normalization, and speaker attribution.

---

## 3. Database Schema (PostgreSQL & SQLite)

The system supports dual persistence: **PostgreSQL 16** for production/Docker environments, and **SQLite** for local development.

```sql
-- 1. Sessions Table (Independent Multi-Turn Conversations)
CREATE TABLE sessions (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL DEFAULT 'New Chat',
    provider VARCHAR(50) NOT NULL DEFAULT 'ollama',
    model VARCHAR(100) NOT NULL DEFAULT 'qwen2.5:3b',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSON DEFAULT '{}'
);

-- 2. Messages Table (Conversation History with Source Attribution)
CREATE TABLE messages (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    sources JSON DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Transcripts Table (Ingested Podcast Episodes)
CREATE TABLE transcripts (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(512) NOT NULL,
    source_url VARCHAR(1024),
    episode_number INTEGER,
    publish_date DATE,
    raw_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Transcript Chunks Table (Semantic Chunks for Retrieval)
CREATE TABLE transcript_chunks (
    id VARCHAR(36) PRIMARY KEY,
    transcript_id VARCHAR(36) NOT NULL REFERENCES transcripts(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    speaker VARCHAR(255),
    metadata JSON DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Artifacts Table (Generated Markdown & HTML Components)
CREATE TABLE artifacts (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    message_id VARCHAR(36) REFERENCES messages(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    artifact_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. API Endpoints Specification

| Method | Endpoint | Description | Request Body | Response Model |
|---|---|---|---|---|
| `GET` | `/health` | System health, database connection, and Ollama reachability. | None | `HealthResponse` |
| `GET` | `/api/config` | Active provider, active model, cloud API key status. | None | `ConfigResponse` |
| `GET` | `/api/sessions` | List all conversation sessions ordered by last updated. | None | `list[SessionResponse]` |
| `POST` | `/api/sessions` | Create a new conversation session. | `SessionCreate` | `SessionResponse` |
| `GET` | `/api/sessions/{id}` | Retrieve specific session metadata. | None | `SessionResponse` |
| `PATCH` | `/api/sessions/{id}` | Update session title or provider. | `SessionUpdate` | `SessionResponse` |
| `DELETE` | `/api/sessions/{id}` | Delete session and cascade delete messages and artifacts. | None | `{"status": "deleted"}` |
| `GET` | `/api/sessions/{id}/messages` | Retrieve conversation turn history for a session. | None | `list[MessageResponse]` |
| `GET` | `/api/sessions/{id}/artifacts` | Retrieve all artifacts generated in a session. | None | `list[ArtifactResponse]` |
| `POST` | `/api/chat` | Send prompt, execute agent, return grounded answer. | `ChatRequest` | `ChatResponse` |
| `POST` | `/api/ingest` | Trigger transcript library ingestion. | `{"sample_only": bool}` | `{"status": "started"}` |
| `GET` | `/api/ingest/status` | Real-time ingestion progress, processed count, total count. | None | `IngestionStatus` |

---

## 5. Ingestion & Retrieval Pipeline

```
Upstream GitHub/CDN (ChatPRD/lennys-podcast-transcripts)
                  │
                  ▼
Dynamic Discovery (303 episode Markdown files discovered without hardcoded lists)
                  │
                  ▼
YAML Frontmatter Extraction (title, guest, date, YouTube URL)
                  │
                  ▼
Semantic Chunking (Split by paragraph & speaker changes; ~300–800 words/chunk)
                  │
                  ▼
Relational Persistence (Stored in PostgreSQL/SQLite `transcripts` & `transcript_chunks`)
                  │
                  ▼
Query Runtime: BM25 TF-IDF Vector Retrieval (Calculates query term match, speaker weighting)
                  │
                  ▼
Top-K Relevance Scoring & Excerpt Formatting (Passed into Agent function calling context)
```

---

## 6. Agent Routing & Model Toggle

1. **Provider Selection:** Users toggle between Local Ollama, Cloud Anthropic, and Google Gemini via the UI header dropdown. The selection is stored in session metadata.
2. **Zero Silent Fallback Invariant:**
   - If Cloud Anthropic is requested without `ANTHROPIC_API_KEY`, the adapter raises `ConfigurationError("Anthropic Claude Agent SDK requires ANTHROPIC_API_KEY in environment")`.
   - If Google Gemini is requested without `GEMINI_API_KEY`, the adapter raises `ConfigurationError("Google Gemini requires GEMINI_API_KEY in environment")`.
   - The API converts `ConfigurationError` into HTTP 400 Bad Request. The server never silently routes cloud queries to Ollama.
3. **Session Consistency:** Re-opening an existing session automatically restores its configured provider and model, ensuring multi-turn coherence.

---

## 7. Security Architecture & Sandbox Isolation Boundary

Generated HTML and Markdown artifacts are treated as **untrusted third-party code**. The system enforces two independent layers of security isolation:

```
[Agent Generates HTML/Markdown]
              │
              ▼
[Layer 1: Backend Bleach Sanitization]
- Strips dangerous inline handlers (onerror, onload, onclick)
- Neutralizes window.parent, top.location, document.cookie, localStorage
- Disallows javascript: pseudo-protocols and data: URIs
              │
              ▼
[Layer 2: Frontend Iframe Sandbox Isolation]
<iframe sandbox="allow-scripts" srcdoc="...">
- Opaque null Origin: Browser assigns origin "null"; Same-Origin Policy blocks host DOM access.
- Storage Theft Blocked: Access to document.cookie, localStorage, sessionStorage throws SecurityError.
- Top Navigation Blocked: window.top.location redirection is prohibited.
- Popups/Modals Blocked: window.open and modal dialogs are suppressed.
```

---

## 8. Deployment Topology

### Topology A: Local Bare-Metal (Evaluator Default)
- **Host OS:** Windows 10/11, macOS, or Linux.
- **Process 1:** Ollama serving on `http://localhost:11434` with `qwen2.5:3b` or `gemma3:4b`.
- **Process 2:** Python virtual environment running FastAPI via Uvicorn on port 8000 (`python run.py`).
- **Database:** Local SQLite (`lenny_growth_assistant.db`).

### Topology B: Containerized Docker Compose
- **Service 1 (`db`):** PostgreSQL 16 container on port 5432 with health check.
- **Service 2 (`backend`):** Multi-stage Debian-slim container exposing port 8000, communicating with host Ollama via `host.docker.internal:11434` and PostgreSQL via container network.
- **Launch Command:** `docker-compose up --build`.
