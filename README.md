# The Lenny Growth Assistant

A full-stack, transcript-grounded conversational AI assistant for product managers and growth leaders. Built on real episodes of **Lenny's Podcast**, featuring repeatable transcript ingestion, semantic retrieval with verifiable source attributions, an isolated **Ship 30 for 30** writing skill, and a sandboxed **Artifact Viewer**.

---

## Table of Contents
- [1. Overview & Capabilities](#1-overview--capabilities)
- [2. System Architecture](#2-system-architecture)
- [3. Prerequisites & Environment Setup](#3-prerequisites--environment-setup)
- [4. Quickstart Guide (Local Demo)](#4-quickstart-guide-local-demo)
- [5. Transcript Ingestion & Knowledge Base](#5-transcript-ingestion--knowledge-base)
- [6. Model Providers (Local Ollama vs. Cloud Anthropic)](#6-model-providers-local-ollama-vs-cloud-anthropic)
- [7. Ship 30 for 30 Writing Skill (~1,250 Words)](#7-ship-30-for-30-writing-skill-1250-words)
- [8. Sandboxed Artifact Viewer & Security Boundary](#8-sandboxed-artifact-viewer--security-boundary)
- [9. Automated Testing & Verification](#9-automated-testing--verification)
- [10. Manual UI Evaluation Test Plan](#10-manual-ui-evaluation-test-plan)
- [11. Anti-Hardcoding & Dynamic Synthesis Invariant](#11-anti-hardcoding--dynamic-synthesis-invariant)
- [12. Troubleshooting & Known Limitations](#12-troubleshooting--known-limitations)
- [13. Deliverables & Submission Checklist](#13-deliverables--submission-checklist)

---

## 1. Overview & Capabilities

The Lenny Growth Assistant addresses high-friction product strategy queries by combining conversational AI with an authoritative knowledge base:
- **Grounded Chat with Real Citations:** Answers product management and growth questions using indexed transcripts from guests like Brian Chesky, Shreyas Doshi, Elena Verna, and Marty Cagan.
- **Explicit Citations:** Every claim is paired with episode titles, guest speaker labels, and chunk excerpts. Unsupported questions are acknowledged honestly rather than hallucinated.
- **Dedicated Ship 30 for 30 Writing Skill:** Synthesizes structured essays calibrated to ~1,250 words (1,100–1,400 word tolerance) adhering to the 5-part architecture (Hook, 5 Pillars, Skimmable Formatting, and Practical Takeaways).
- **In-App Sandboxed Artifact Viewer:** Renders generated Markdown and complete HTML/CSS components in a split-screen viewer beside the chat, enforcing strict iframe sandbox isolation (`null` origin) and backend `bleach` sanitization.
- **Local-First with Zero Silent Fallback:** Runs locally with Ollama (`qwen2.5:3b`) without requiring API keys, and includes a full Anthropic Claude Agent SDK adapter with visible UI switching and strict configuration validation.

---

## 2. System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                       Frontend UI                           │
│  - Modern Dark-Theme Workspace (HTML5, Vanilla CSS, JS)     │
│  - Split Screen: Multi-Turn Chat + Sandboxed Artifact Viewer│
│  - Visible Model/Provider Switcher & Health Status          │
└──────────────┬──────────────────────────────▲───────────────┘
               │ HTTP / JSON                  │
               ▼                              │
┌─────────────────────────────────────────────┴───────────────┐
│                      FastAPI Backend                        │
│  - Session Management & Isolated Conversation Histories    │
│  - Agent Dispatcher (Ollama Adapter / Claude SDK Adapter)   │
│  - Ingestion Pipeline & Semantic Chunking Engine            │
│  - Bleach HTML Sanitizer & Security Policy Enforcement       │
└──────────────┬──────────────────────────────▲───────────────┘
               │                              │
       ┌───────┴────────┐             ┌───────┴────────┐
       ▼                ▼             ▼                ▼
┌─────────────┐  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   SQLite /  │  │ BM25 TF-IDF │ │ Local Ollama│ │  Anthropic  │
│  PostgreSQL │  │  Retrieval  │ │ (qwen2.5:3b)│ │ Claude SDK  │
│  (Database) │  │   Service   │ │ (Port 11434)│ │   (Cloud)   │
└─────────────┘  └─────────────┘ └─────────────┘ └─────────────┘
```

- **Backend:** FastAPI (Python 3.11+ / 3.13), SQLAlchemy 2.0 ORM, Pydantic v2, Uvicorn.
- **Frontend:** Responsive vanilla HTML5/CSS/JavaScript with zero build step dependencies.
- **Database:** Full SQLAlchemy dual-support: **PostgreSQL 16** (assignment specification, pre-wired in `docker-compose.yml` and connectable via Supabase/Railway) and **SQLite** default for zero-setup local execution.
- **Retrieval Engine:** Custom BM25 TF-IDF RAG engine with speaker/timestamp chunking and cross-episode disambiguation.

---

## 3. Prerequisites & Environment Setup

### Required Tools:
1. **Python 3.11+** (Python 3.13 tested).
2. **Git** (version 2.40+).
3. **Ollama** installed and running with `qwen2.5:3b`:
   ```bash
   ollama pull qwen2.5:3b
   ollama serve
   ```

### Clone & Virtual Environment (Windows & Linux/macOS):
```bash
# Clone the repository
git clone https://github.com/your-username/lenny-growth-assistant.git
cd lenny-growth-assistant

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Windows Command Prompt:
.\venv\Scripts\activate.bat
# On Linux / macOS:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

---

## 4. Quickstart Guide (Local Demo)

### Step 1: Copy Environment Variables
```bash
cp .env.example .env
```
Default `.env` settings:
```ini
PROVIDER_TYPE=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
DATABASE_URL=sqlite:///./lenny_growth_assistant.db
ANTHROPIC_API_KEY=
```

### Step 2: Start the Application Server

**Option A — Local Python (SQLite or configured PostgreSQL):**
```bash
python run.py
```
*The server starts on `http://localhost:8000` with hot-reload enabled.*

**Option B — Docker Compose (PostgreSQL 16 + FastAPI):**
```bash
docker compose up --build
```
*This starts a containerized PostgreSQL 16 instance (`lenny-postgres`) and the FastAPI backend (`lenny-backend`).*

### Step 3: Open the Web Application
Navigate to `http://localhost:8000` in any modern web browser.
- Verify the header shows `Active Provider: Local Ollama (qwen2.5:3b)` and `Healthy`.
- Click **+ New Chat** or choose one of the quick starter prompts.

---

## 5. Transcript Ingestion & Knowledge Base

The application includes real transcripts from **Lenny's Podcast** (ChatPRD dataset) covering high-signal episodes:
- **Brian Chesky:** Airbnb release cycles, product roadmaps, and founder-led product management.
- **Shreyas Doshi:** Why execution problems are strategy problems, mental models, and radical focus.
- **Elena Verna:** Reducing onboarding friction in Product-Led Growth (PLG).
- **Marty Cagan:** Empowered product teams vs. feature factories.

### Running Ingestion Manually:
```bash
python -m backend.app.ingestion.ingest
```
Transcripts are parsed from Markdown with YAML frontmatter, split semantically on speaker/paragraph boundaries, and indexed into `transcripts` and `transcript_chunks` tables with full source attribution.

You can also trigger sample ingestion via API:
```bash
curl -X POST http://localhost:8000/api/ingest -H "Content-Type: application/json" -d "{\"mode\": \"sample\"}"
```

---

## 6. Model Providers (Local Ollama vs. Cloud Anthropic)

The application supports explicit, visible provider toggling via the UI header and `POST /api/chat` payload:

### A. Local Ollama (Default & Fully Tested)
- Uses local `qwen2.5:3b` running on `http://localhost:11434`.
- Zero cloud API key required.
- Generates grounded answers, calls tools (`search_transcripts`, `run_ship30_skill`, `create_artifact`), and refines citations.

### B. Anthropic Claude Agent SDK (Cloud)
- Implemented in `backend/app/agent/claude_agent.py` using `claude-agent-sdk`.
- Configured via `ANTHROPIC_API_KEY` in `.env`.
- **Strict Anti-Silent-Fallback Rule:** If the Cloud provider is selected and `ANTHROPIC_API_KEY` is not set, the server returns an explicit HTTP 400 error:
  ```json
  {"detail": "Configuration error: Anthropic Claude Agent SDK requires ANTHROPIC_API_KEY to be set in environment variables."}
  ```
  The system **never** silently falls back to Ollama.

---

## 7. Ship 30 for 30 Writing Skill (~1,250 Words)

The writing skill (`backend/app/skills/ship30.py`) synthesizes grounded product essays based on the principles in the official **Ship 30 for 30** framework ([docs/skills/SHIP30_WRITING_SKILL.md](docs/skills/SHIP30_WRITING_SKILL.md)):

### Structure & Progression:
1. **The Hook & Problem Statement:** Highlights a critical practitioner challenge.
2. **The 5-Pillar Narrative Arc:**
   - *Pillar 1:* The Core Problem / Root Cause
   - *Pillar 2:* The Mental Model Shift
   - *Pillar 3:* The Tactical Framework
   - *Pillar 4:* Common Traps to Avoid
   - *Pillar 5:* The Step-by-Step Implementation Roadmap
3. **High Skimmability:** Formatted with bolded anchor points, structured headers, and checklists.
4. **Actionable Takeaways:** Practitioner diagnostic checklist and "The Ultimate Takeaway".
5. **Transcript Grounding:** Incorporates verbatim excerpts and citations from the transcript database.
6. **Calibrated Depth:** Generates ~1,250 words (verified 1,220–1,295 words across arbitrary topics, sitting within the 1,100–1,400 word tolerance).

---

## 8. Sandboxed Artifact Viewer & Security Boundary

When a user requests an essay or HTML/CSS component, the application renders the result in an interactive side-by-side **Artifact Viewer**:

### Viewer Features:
- **Split-Screen Layout:** Appears beside the active chat without obstructing conversation history.
- **Preview / Code Tabs:** Toggle between formatted rendered presentation and raw source code.
- **One-Click Copy:** Instant clipboard copy with visual confirmation.

### Security Threat Model & Sandbox Execution Boundary:
Treating all generated HTML as untrusted code is a mandatory security invariant:
1. **Frontend Iframe Isolation:**
   - The preview `<iframe>` specifies `sandbox="allow-scripts"` and **strictly omits** `allow-same-origin`.
   - The browser forces the iframe into an opaque `null` origin.
   - Any script inside the artifact attempting to access `window.parent`, `top.location`, `document.cookie`, or `localStorage` fails immediately with a browser `SecurityError`.
2. **Backend HTML Sanitization:**
   - Content is sanitized through `bleach` and regex pattern neutralization before database persistence.
   - Malicious attributes (`onload`, `onerror`, `onclick`), dangerous protocols (`javascript:`, `data:text/html`), and parent-frame escape sequences are neutralized.
   - Full security specifications are documented in [docs/architecture.md](docs/architecture.md#4-artifact-sandbox-security-model).

---

## 9. Automated Testing & Verification

The project includes 50 comprehensive automated tests covering unit, integration, and regression requirements:

```bash
# Run the full test suite
python -m pytest tests/ -v
```

### Test Breakdown (50/50 Passed):
- `tests/test_agent.py` (5 tests): Provider dispatcher, missing key validation, HTTP 400 non-fallback check, Ollama tool calling and regex regression.
- `tests/test_api.py` (10 tests): Health check, config endpoint, session lifecycle, session isolation, title auto-generation, orphan message rollback, multi-turn history, repeated questions, provider sync persistence, and frontend theme/shortcut verification.
- `tests/test_artifacts.py` (5 tests): Markdown artifact domain, HTML sanitization, invalid type rejection, persistence API, iframe sandbox policy.
- `tests/test_grounding_regression.py` (12 tests): Grounded retrieval for Brian Chesky, Shreyas Doshi, Marty Cagan, Elena Verna; 4 paraphrased queries; out-of-corpus handling; session turn lifecycle; refresh consistency; timeout rollback.
- `tests/test_ingestion.py` (5 tests): Frontmatter parsing, semantic chunking, database persistence, deduplication, end-to-end ingestion and retrieval.
- `tests/test_retrieval.py` (6 tests): Grounded retrieval, novel paraphrases, empty database handling, type-safety regression (`int` query handling).
- `tests/test_skills.py` (7 tests): Ship 30 guide URL verification, essay structure, ~1,250 word count tolerance [1,100, 1,400], source attribution grounding, novel unseen topics.

---

## 10. Manual UI Evaluation Test Plan

Evaluators can follow [docs/manual-ui-test-plan.md](docs/manual-ui-test-plan.md) to manually verify all interactive states in the browser at `http://localhost:8000`:
1. **Grounded Chat:** Ask *"Why does Shreyas Doshi say that most execution problems are actually strategy problems?"* -> Observe answer with Shreyas Doshi citation badges.
2. **Multi-Turn Context:** Follow up with *"What framework does he recommend?"* -> Verifies conversational continuity.
3. **Cross-Episode Disambiguation:** Ask about Elena Verna or Brian Chesky -> Confirms zero cross-episode pollution.
4. **Unsupported Questions:** Ask about quantum physics -> Verifies honest acknowledgement with no fake citations.
5. **Ship 30 Essay Generation:** Request an essay on Airbnb release cycles -> Confirms Artifact Viewer opens with ~1,250 words.
6. **Artifact Viewer Tabs & Copy:** Toggle between Preview and Code tabs, click Copy.
7. **HTML Sandbox Security:** Attempt script injection -> Confirms isolation in iframe with opaque origin.
8. **Cloud Provider Selection:** Switch to Cloud without key -> Confirms explicit HTTP 400 error and no fallback.

---

## 11. Anti-Hardcoding & Dynamic Synthesis Invariant

In accordance with [docs/PROJECT_RULES.md](docs/PROJECT_RULES.md), the system implements zero hardcoded behavior:
- **No Keyword Routers:** Does not map user question strings or keywords to fixed responses.
- **No Canned Answers or Fake Citations:** Every response and source citation is dynamically retrieved and synthesized from SQLite/PostgreSQL chunks.
- **Dynamic Skill Synthesis:** The Ship 30 skill synthesizes any arbitrary topic or guest dynamically based on query parameters and retrieved evidence.
- **Rigorously Audited:** Verified against strict project rules documented in [docs/PROJECT_RULES.md](docs/PROJECT_RULES.md).

---

## 12. Troubleshooting & Known Limitations

- **Ollama Generation Speed:** On CPU-only systems, local inference with `qwen2.5:3b` may take 15–30 seconds. On GPU (CUDA/Metal), response times are typically under 3 seconds.
- **Port Conflicts:** If port 8000 is occupied, change the port in `run.py` or specify `--port <PORT>`.
- **Live Cloud Provider Testing:** Live Claude 3.5 Sonnet inference requires a valid `ANTHROPIC_API_KEY`. Without a key, the cloud adapter is fully tested using mocks, and attempts to invoke cloud mode safely produce a clear configuration error.

---

## 13. Deliverables & Submission Checklist

- [x] **Working Full-Stack Application:** FastAPI backend, database persistence, vanilla frontend with chat and Artifact Viewer.
- [x] **Source Transcript Ingestion & RAG:** Repeatable ingestion pipeline, 217 indexed chunks, hybrid BM25 retrieval.
- [x] **Ship 30 for 30 Skill:** Dedicated ~1,250-word structured writing skill grounded in real transcript evidence.
- [x] **Sandboxed Artifact Viewer:** Isolated iframe with `null` origin, `bleach` backend sanitization, Preview/Code tabs.
- [x] **Comprehensive Documentation:** `README.md`, `PRD.md`, `architecture.md`, `design.md`, `manual-ui-test-plan.md`.
- [x] **Automated Test Suite:** 50 passing automated tests (`pytest tests/ -v`).
- [x] **Clean Secrets & Environment:** `.env.example` with safe defaults, zero committed API keys.
- [ ] **Camera-On YouTube Demo:** 2–3 minute video demo walk-through per Section 6 of the assignment.
- [ ] **GitHub Repository Submission:** Push to public GitHub repository and submit via the assignment form.
