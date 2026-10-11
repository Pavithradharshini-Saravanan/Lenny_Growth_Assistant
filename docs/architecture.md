# System Architecture — The Lenny Growth Assistant (Revised & Clarified)

## 1. High-Level Architecture Overview

The Lenny Growth Assistant follows a modular, decoupled full-stack architecture designed for local execution with Ollama while integrating the mandatory **Anthropic Claude Agent SDK** for cloud agent execution.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                             Frontend (UI)                               │
│  ┌─────────────────────────────┐       ┌─────────────────────────────┐  │
│  │   Chat Interface (Stream)   │       │   Sandboxed Artifact Viewer │  │
│  └──────────────┬──────────────┘       └──────────────▲──────────────┘  │
└─────────────────┼─────────────────────────────────────┼─────────────────┘
                  │ HTTP / REST API                     │ Render (HTML/MD)
                  ▼                                     │
┌───────────────────────────────────────────────────────┴─────────────────┐
│                       FastAPI Backend Service                           │
│  ┌────────────────────────┐         ┌────────────────────────────────┐  │
│  │ API Routing & Sessions │         │    Agent Strategy Dispatcher   │  │
│  └───────────┬────────────┘         └───────────────┬────────────────┘  │
│              │                                      │                   │
│              ▼                                      │                   │
│  ┌────────────────────────┐                         │                   │
│  │  PostgreSQL Storage    │                         │                   │
│  │  (Sessions, Messages)  │                         │                   │
│  └────────────────────────┘                         │                   │
│                                                     │                   │
│              ┌──────────────────────────────────────┴────────────┐      │
│              │                                                   │      │
│              ▼ (Cloud Mode)                                      ▼ (Local Mode)
│  ┌───────────────────────────────────┐               ┌──────────────────┐
│  │ ClaudeAgentSDKAdapter             │               │ OllamaAgent      │
│  │ (claude-agent-sdk / Client)       │               │ Adapter          │
│  │ - Uses claude-agent-sdk library   │               │ - Native Ollama  │
│  │ - Wraps bundled binary & API key  │               │   tool-calling   │
│  │ - Registered via @tool decorator  │               │ - qwen2.5:3b     │
│  └─────────────────┬─────────────────┘               └─────────┬────────┘
│                    │                                           │
│                    └─────────────────────┬─────────────────────┘
│                                          ▼
│                        ┌──────────────────────────────────┐
│                        │ Shared Core Domain Tools         │
│                        │ (backend/app/tools/)             │
│                        │ - search_transcripts             │
│                        │ - run_ship30_skill               │
│                        │ - create_artifact                │
│                        └─────────────────┬────────────────┘
│                                          │
│                                          ▼
│                        ┌──────────────────────────────────┐
│                        │ Transcript Knowledge Base        │
│                        │ (Ingested Chunks & Metadata)     │
│                        └──────────────────────────────────┘
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Agent Framework Technical Verification & Architectural Clarifications

### 2.1 Claude Agent SDK Requirements & Runtime Behavior
Verified against official Anthropic documentation (`https://code.claude.com/docs/en/agent-sdk/quickstart`):
- **Runtime Dependencies:** The `claude-agent-sdk` Python package bundles platform binary wheels for supported OS environments (macOS, Linux, x86_64 Windows). It operates by launching and communicating with a background binary runtime process via subprocess IPC transport (`Transport`).
- **Authentication & Setup:** Requires `ANTHROPIC_API_KEY` set in the environment (or cloud platform credentials like AWS Bedrock / GCP Vertex). It does not automatically parse `.env` files, so the FastAPI backend explicitly loads configuration into environment variables before invocation.

### 2.2 Structural Testing of Cloud Agent Without Paid Key
- The `ClaudeAgentSDKAdapter` is fully implemented in `backend/app/agent/claude_agent.py` and unit-tested using mocks/spies to verify structural compliance without making live API calls.
- If selected at runtime without `ANTHROPIC_API_KEY`, `ClaudeAgentSDKAdapter` raises `ConfigurationError("Anthropic Claude Agent SDK requires ANTHROPIC_API_KEY in environment")`.
- Local Ollama mode remains 100% operational and zero-cost, completely independent of cloud key status.

### 2.3 Ollama Adapter Dynamic Tool Execution
- The `OllamaAgentAdapter` performs a genuine, multi-step LLM function-calling agent loop.
- Tool schemas (`search_transcripts`, `run_ship30_skill`, `create_artifact`) are passed in the Ollama `/api/chat` call.
- The adapter parses `tool_calls` returned by `qwen2.5:3b`, executes the requested domain tool, appends the tool message to history, and loops back to the LLM until completion. No keyword routing or regex triggers are used.

### 2.4 Tool Code Sharing & Honest Attribution
- **Core Domain Logic (`backend/app/tools/`):** Pure Python functions implementing search, Ship 30 essay generation, and artifact creation.
- **`ClaudeAgentSDKAdapter`:** Registers core tools via `@tool` decorators for `ClaudeSDKClient`.
- **`OllamaAgentAdapter`:** Exposes core tools as JSON Schema function declarations for Ollama.
- **Attribution:** Telemetry and UI logs explicitly differentiate between `ClaudeAgentSDKAdapter` (Cloud mode via SDK) and `OllamaAgentAdapter` (Local mode via Ollama API), eliminating false framework claims.

---

## 3. Database Schema (PostgreSQL)

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Sessions Table
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL DEFAULT 'New Chat',
    provider VARCHAR(50) NOT NULL DEFAULT 'ollama',
    model VARCHAR(100) NOT NULL DEFAULT 'qwen2.5:3b',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Messages Table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    sources JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Transcripts Table
CREATE TABLE IF NOT EXISTS transcripts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(512) NOT NULL,
    source_url VARCHAR(1024),
    episode_number INT,
    publish_date DATE,
    raw_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Transcript Chunks Table
CREATE TABLE IF NOT EXISTS transcript_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transcript_id UUID NOT NULL REFERENCES transcripts(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    speaker VARCHAR(255),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Artifacts Table
CREATE TABLE IF NOT EXISTS artifacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    artifact_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. Security & Artifact Viewer Isolation Boundary

Generated HTML and Markdown artifacts are treated as **untrusted user-facing code**. The architecture implements defense-in-depth across both backend sanitization and frontend browsing context sandboxing.

### 4.1 Frontend Sandboxed Execution Model
HTML/CSS artifacts are rendered in an isolated `<iframe>` configured strictly with:
```html
<iframe id="artifactIframe" class="sandboxed-iframe" sandbox="allow-scripts" title="Artifact Sandbox"></iframe>
```

#### What the Viewer Permits:
1. **Interactive Client Scripts (`allow-scripts`):** Allows client-side JavaScript execution inside the iframe so interactive calculators, dynamic UI components, state machines, canvas elements, and SVG chart renderers function properly.
2. **Safe CSS & Layout Styling:** Full CSS styling, flexbox, grid, animations, transitions, and web typography.
3. **Semantic HTML5 & Visual Markup:** Tables, lists, forms, buttons, cards, SVGs, and containers.

#### What the Viewer Strictly Blocks:
1. **Opaque `null` Origin Isolation (Omission of `allow-same-origin`):** The browser assigns the sandboxed iframe a unique opaque origin (`null`). It cannot match the parent application's origin under the Same-Origin Policy.
2. **Parent DOM & Window Access:** Any script invoking `window.parent`, `window.top`, or accessing parent document objects immediately fails with a fatal browser error: `SecurityError: Blocked a frame with origin "null" from accessing a cross-origin frame.`
3. **Cookie & Local Storage Theft:** The sandboxed frame cannot access `document.cookie`, `localStorage`, or `sessionStorage` of the host app. Attempts throw `SecurityError: Access to Storage is not allowed for this document.`
4. **Top Navigation Hijacking (Omission of `allow-top-navigation`):** The iframe cannot redirect the user's browser away from the application (`window.top.location = ...`).
5. **Popups and Modals (Omission of `allow-popups` & `allow-modals`):** Prevents phishing popups, new window opening, or modal prompt spam.
6. **Backend Credential Isolation:** The sandboxed context carries no bearer tokens, session cookies, or parent headers, preventing CSRF or unauthorized backend mutations.

### 4.2 Backend HTML Sanitization Layer
Before any artifact is persisted to PostgreSQL or transmitted over the API, `backend/app/tools/base.py` (`create_artifact_domain`) enforces strict sanitization:
1. **Neutralizes Sandbox Escape Vectors:** Scans for and neutralizes patterns targeting `window.parent`, `top.location`, `document.cookie`, and web storage.
2. **Protocol Restrictions:** Disallows `javascript:` pseudo-protocols and `data:text/html` MIME types.
3. **Attribute Sanitization:** Strips dangerous inline event handlers (`onerror`, `onload`, `onclick`, `onmouseover`) using `bleach.clean`.
4. **Tag Whitelisting:** Permits standard layout, typography, SVG, and presentation tags while stripping dangerous elements.

