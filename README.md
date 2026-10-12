# The Lenny Growth Assistant

A production-grade, transcript-grounded conversational AI assistant for product managers and growth leaders. Built on real episodes of **Lenny's Podcast**, featuring dynamic transcript ingestion, semantic retrieval with verifiable source attributions, an isolated **Ship 30 for 30** writing skill, and a sandboxed side-by-side **Artifact Viewer**.

---

## Table of Contents
- [1. Overview & Capabilities](#1-overview--capabilities)
- [2. System Architecture](#2-system-architecture)
- [3. Prerequisites & Environment Setup](#3-prerequisites--environment-setup)
- [4. Environment Variables Reference](#4-environment-variables-reference)
- [5. Local & Cloud Model Setup](#5-local--cloud-model-setup)
- [6. Run Commands & Quickstart](#6-run-commands--quickstart)
- [7. Transcript Ingestion & Knowledge Base](#7-transcript-ingestion--knowledge-base)
- [8. Ship 30 for 30 Writing Skill (~1,250 Words)](#8-ship-30-for-30-writing-skill-1250-words)
- [9. Sandboxed Artifact Viewer & Security Boundary](#9-sandboxed-artifact-viewer--security-boundary)
- [10. Automated Testing & Verification (65 Tests)](#10-automated-testing--verification-65-tests)
- [11. Manual UI Evaluation Test Plan](#11-manual-ui-evaluation-test-plan)
- [12. Troubleshooting & FAQ](#12-troubleshooting--faq)
- [13. Deliverables & Submission Checklist](#13-deliverables--submission-checklist)

---

## 1. Overview & Capabilities

The Lenny Growth Assistant addresses high-friction product strategy queries by combining agentic conversational AI with an authoritative knowledge base:
- **Grounded Chat with Real Citations:** Answers product management and growth questions using indexed transcripts from guests like Brian Chesky, Shreyas Doshi, Elena Verna, and Marty Cagan.
- **Traceable Source Attribution:** Every claim is paired with episode titles, guest speaker labels, and chunk excerpts. Unsupported questions outside the corpus are acknowledged honestly rather than hallucinated.
- **Dedicated Ship 30 for 30 Writing Skill:** Synthesizes structured essays calibrated to ~1,250 words (1,100–1,400 word tolerance) adhering to the 5-part architecture (Hook, 5 Pillars, Skimmable Formatting, and Practical Takeaways).
- **In-App Sandboxed Artifact Viewer:** Renders generated Markdown and complete HTML/CSS components in a split-screen viewer beside the chat, enforcing strict iframe sandbox isolation (`null` origin) and backend `bleach` sanitization.
- **Local-First with Zero Silent Fallback:** Runs locally with Ollama (`qwen2.5:3b` or `gemma3:4b`) without requiring API keys, and includes complete cloud adapters for the Anthropic Claude Agent SDK and Google Gemini with visible UI switching and strict configuration validation.

---

## 2. System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                       Frontend SPA                          │
│  - Modern Dark-Theme Workspace (HTML5, Vanilla CSS, JS)     │
│  - Split Screen: Multi-Turn Chat + Sandboxed Artifact Viewer│
│  - Live Model/Provider Switcher & Ingestion Status Card     │
│  - Hidden Scrollbars with Smooth Native Scrolling           │
└──────────────┬──────────────────────────────▲───────────────┘
               │ HTTP REST (JSON)             │
               ▼                              │
┌─────────────────────────────────────────────┴───────────────┐
│                      FastAPI Backend                        │
│  - Session Management & Isolated Conversation Histories    │
│  - Agent Dispatcher (Ollama / Claude SDK / Google Gemini)   │
│  - Ingestion Engine & Semantic Paragraph Chunking           │
│  - Bleach HTML Sanitizer & Defense-in-Depth Security        │
└──────────────┬──────────────────────────────▲───────────────┘
               │                              │
       ┌───────┴────────┐             ┌───────┴────────┐
       ▼                ▼             ▼                ▼
┌─────────────┐  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   SQLite /  │  │ BM25 TF-IDF │ │ Local Ollama│ │ Cloud Agents│
│  PostgreSQL │  │  Retrieval  │ │ (qwen2.5:3b │ │ (Anthropic /│
│  (Database) │  │   Service   │ │  gemma3:4b) │ │   Gemini)   │
└─────────────┘  └─────────────┘ └─────────────┘ └─────────────┘
```

- **Backend:** FastAPI (Python 3.11+ / 3.13), SQLAlchemy 2.0 ORM, Pydantic v2, Uvicorn ASGI server.
- **Frontend:** Responsive vanilla HTML5/CSS/JavaScript with zero build step dependencies.
- **Database:** Full SQLAlchemy dual-support: **PostgreSQL 16** (production / Docker Compose) and **SQLite** default for zero-setup local execution.
- **Retrieval Engine:** Custom BM25 TF-IDF RAG engine with speaker/timestamp chunking and cross-episode disambiguation.

---

## 3. Prerequisites & Environment Setup

### Required Tools
1. **Python 3.11+** (Python 3.13 fully verified).
2. **Git** (version 2.40+).
3. **Ollama** installed and running on `http://localhost:11434`.
4. **Docker & Docker Compose** *(optional, for containerized PostgreSQL deployment)*.

### Clone & Virtual Environment Setup

#### Windows (PowerShell)
```powershell
# Clone the repository
git clone https://github.com/your-username/lenny-growth-assistant.git
cd lenny-growth-assistant

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

#### Windows (Command Prompt)
```cmd
python -m venv venv
.\venv\Scripts\activate.bat
pip install -r requirements.txt
```

#### Linux / macOS
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 4. Environment Variables Reference

Copy the `.env.example` template to `.env` before running:
```bash
cp .env.example .env
```

| Variable | Default Value | Required? | Description |
|---|---|---|---|
| `PROVIDER_TYPE` | `ollama` | Yes | Default model provider: `ollama`, `cloud`, or `gemini`. |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Yes (for Ollama) | Base URL of local Ollama service. (Use `http://host.docker.internal:11434` inside Docker). |
| `OLLAMA_MODEL` | `qwen2.5:3b` | Yes (for Ollama) | Local model identifier (`qwen2.5:3b` or `gemma3:4b`). |
| `ANTHROPIC_API_KEY` | *(empty)* | Optional | Required only when `PROVIDER_TYPE=cloud`. |
| `CLOUD_MODEL` | `claude-3-5-sonnet-20241022` | Optional | Anthropic model identifier. |
| `GEMINI_API_KEY` | *(empty)* | Optional | Required only when `PROVIDER_TYPE=gemini`. |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Optional | Google Gemini model identifier. |
| `DATABASE_URL` | `sqlite:///./lenny_growth_assistant.db` | Yes | Database connection string. Use `postgresql://postgres:postgres@localhost:5432/lenny_assistant` for PostgreSQL. |

---

## 5. Local & Cloud Model Setup

### 5.1 Local Ollama Setup (Zero-Cost Local Evaluation)
1. Download and start [Ollama](https://ollama.com).
2. Pull the recommended local models:
   ```bash
   # Recommended default model (native function calling):
   ollama pull qwen2.5:3b

   # Alternative Google Gemma 3 model:
   ollama pull gemma3:4b
   ```
3. Verify Ollama is running and responding:
   ```bash
   curl http://localhost:11434/api/tags
   ```

### 5.2 Cloud Anthropic Claude Agent SDK Setup
1. Obtain an API key from [Anthropic Console](https://console.anthropic.com/).
2. Add your key to `.env`:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-api03-...
   ```
3. Set provider in `.env` or toggle via UI header dropdown.

### 5.3 Cloud Google Gemini Setup
1. Obtain an API key from [Google AI Studio](https://aistudio.google.com/).
2. Add your key to `.env`:
   ```bash
   GEMINI_API_KEY=AIzaSy...
   ```
3. Set provider in `.env` or toggle via UI header dropdown.

### 5.4 Zero Silent Fallback Policy
In strict compliance with assignment rules:
- If a cloud provider is selected but the corresponding API key is missing, the backend **never** silently falls back to Ollama.
- Instead, it raises a `ConfigurationError`, returns an explicit HTTP 400 Bad Request, and displays an actionable warning banner in the UI instructing the user to configure their key or switch to Local Ollama.

---

## 6. Run Commands & Quickstart

### Option A: One-Command Quickstart (Recommended)
Launch the unified server serving both the FastAPI REST backend and the frontend single-page application at `http://localhost:8000`:
```bash
python run.py
```
Open your browser to:
👉 **`http://localhost:8000`**

### Option B: Direct Uvicorn Launch
```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### Option C: Containerized Launch with Docker Compose
To run with a dedicated PostgreSQL 16 database container:
```bash
docker-compose up --build
```
The application will be accessible at `http://localhost:8000`.

---

## 7. Transcript Ingestion & Knowledge Base

The assistant connects dynamically to the authoritative upstream repository `ChatPRD/lennys-podcast-transcripts`:
- **Dynamic Edge Discovery:** Automatically scans upstream CDN directory APIs to discover all 303 episodes without hardcoded file lists.
- **Non-Blocking Background Worker:** Ingestion runs as an asynchronous background worker (`IngestionManager`), allowing the server to boot instantly and serve health checks within 50ms.
- **Semantic Chunking:** Splits transcripts along speaker turn and paragraph boundaries (~300–800 words per chunk), preserving guest names and context.
- **Idempotent Persistence:** Re-indexing existing transcripts detects duplicates and skips re-ingestion.
- **Real-Time UI Progress:** The header status card displays live progress percentage and episode counts:
  ```
  [● Library: Indexing Library (42%) • 128 / 303 episodes]
  ```

---

## 8. Ship 30 for 30 Writing Skill (~1,250 Words)

The assistant features an isolated, domain-specific writing skill adhering to the Ship 30 for 30 methodology:
1. **The Hook:** A high-leverage question or counter-intuitive claim arresting reader attention.
2. **The 5 Pillars:** Systematic breakdown of the core strategy with clear, skimmable subheadings (`##`).
3. **Skimmable Formatting:** Heavy use of bolded insights, bulleted frameworks, and whitespace.
4. **Practical Takeaways:** Actionable 1-page operational playbooks that PMs can apply immediately.
5. **Transcript Grounding:** Claims are explicitly linked to insights from real podcast guests.
6. **Calibrated Word Count:** Strictly targeted to ~1,250 words (tolerating 1,100 to 1,400 words).

---

## 9. Sandboxed Artifact Viewer & Security Boundary

Generated HTML and Markdown artifacts are treated as **untrusted third-party code**. The application enforces defense-in-depth across two distinct isolation layers:

### Layer 1: Backend Bleach Sanitization
- Strips dangerous inline event handlers (`onerror`, `onload`, `onclick`, `onmouseover`).
- Disallows `javascript:` pseudo-protocols and data URIs.
- Scans for and neutralizes sandbox escape attempts targeting `window.parent`, `top.location`, `document.cookie`, and `localStorage`.

### Layer 2: Frontend Iframe Sandbox Isolation
HTML components render inside an isolated iframe:
```html
<iframe id="artifactIframe" class="sandboxed-iframe" sandbox="allow-scripts" title="Artifact Sandbox"></iframe>
```
- **Opaque `null` Origin:** Browser assigns origin `null`. Under the Same-Origin Policy, it cannot access the host application's DOM.
- **Storage Theft Blocked:** Attempts to read `document.cookie` or `localStorage` throw a fatal browser `SecurityError`.
- **Top Navigation Hijacking Blocked:** Omission of `allow-top-navigation` prevents redirects away from the application.
- **Side-by-Side Co-location:** Artifacts appear beside the chat stream with **Preview** and **Code** tabs and a one-click **Copy Code** button.

---

## 10. Automated Testing & Verification (65 Tests)

Run the full automated test suite using pytest:
```bash
python -m pytest tests/ -v
```

### Test Suite Breakdown (65/65 Passed)
| Test Suite | Tests | Verification Focus |
|---|---|---|
| `tests/test_agent.py` | 9 | Dispatcher instantiation, missing key validation, HTTP 400 non-fallback check, Ollama tool calling, regex regression, Gemma model handling. |
| `tests/test_api.py` | 12 | Health endpoint, config discovery, session CRUD, session isolation, title auto-generation, orphan message rollback, multi-turn history, repeated questions, provider sync, frontend keyboard shortcuts, and scrollbar hiding verification. |
| `tests/test_artifacts.py` | 5 | Markdown artifact creation, HTML sanitization, invalid type rejection, artifact persistence API, iframe sandbox security policy. |
| `tests/test_full_ingestion.py` | 5 | Dynamic upstream discovery, ingestion status API, background ingestion triggering, idempotency / zero duplicates, failure isolation. |
| `tests/test_gemini.py` | 6 | Gemini adapter dispatcher, missing API key configuration error, HTTP 400 response, function-calling tool execution, Ship 30 tool mocking, rate limit backoff. |
| `tests/test_grounding_regression.py` | 15 | Grounded retrieval for Brian Chesky, Shreyas Doshi, Marty Cagan, Elena Verna; 4 paraphrased query assertions; out-of-corpus handling; turn lifecycle consistency; timeout rollback. |
| `tests/test_ingestion.py` | 5 | YAML frontmatter parsing, semantic chunking, database persistence, deduplication, end-to-end ingestion and retrieval. |
| `tests/test_retrieval.py` | 6 | Grounded retrieval, novel paraphrases, empty database handling, type-safety regression (`int` query handling). |
| `tests/test_skills.py` | 7 | Ship 30 guide URL verification, essay structure, ~1,250 word count tolerance [1,100, 1,400], source attribution grounding, novel unseen topics. |

---

## 11. Manual UI Evaluation Test Plan

Evaluators can follow [docs/manual-ui-test-plan.md](docs/manual-ui-test-plan.md) to manually verify all interactive states in the browser at `http://localhost:8000`:
1. **Grounded Chat:** Ask *"Why does Shreyas Doshi say that most execution problems are actually strategy problems?"* -> Observe answer with Shreyas Doshi citation badges.
2. **Multi-Turn Context:** Follow up with *"What framework does he recommend?"* -> Verifies conversational continuity.
3. **Cross-Episode Disambiguation:** Ask about Elena Verna or Brian Chesky -> Confirms zero cross-episode pollution.
4. **Unsupported Questions:** Ask about quantum computing -> Verifies honest acknowledgement with no fake citations.
5. **Ship 30 Essay Generation:** Request an essay on Airbnb release cycles -> Confirms Artifact Viewer opens with ~1,250 words.
6. **Artifact Viewer Tabs & Copy:** Toggle between Preview and Code tabs, click Copy.
7. **HTML Sandbox Security:** Inspect sandbox policy -> Confirms isolation in iframe with opaque origin.
8. **Cloud Provider Selection:** Switch to Cloud without key -> Confirms explicit HTTP 400 error and no fallback.
9. **Knowledge Base Ingestion Indicator:** Observe header progress bar and episode count.

---

## 12. Troubleshooting & FAQ

### Q: Ollama inference is slow on my machine.
- **Cause:** CPU-only inference without hardware acceleration.
- **Solution:** `qwen2.5:3b` is optimized for low-resource environments. On CPU, responses take 10–25 seconds. On GPU (NVIDIA CUDA or Apple Silicon Metal), responses complete in 2–4 seconds.

### Q: I get "Connection refused" when selecting Ollama.
- **Cause:** Ollama service is not running on port 11434.
- **Solution:** Run `ollama serve` in a separate terminal. Verify with `curl http://localhost:11434/api/tags`.

### Q: Can I run without paid API keys?
- **Yes!** The system is 100% functional locally using Ollama (`qwen2.5:3b`). Paid keys are only required if you explicitly choose to test Cloud Anthropic or Google Gemini modes.

### Q: Port 8000 is already in use.
- **Solution:** Run with a custom port: `uvicorn backend.app.main:app --port 8080`.

---

## 13. Deliverables & Submission Checklist

- [x] **Working Full-Stack Application:** FastAPI backend, database persistence, vanilla frontend with chat and Artifact Viewer.
- [x] **Source Transcript Ingestion & RAG:** Real dynamic ingestion of 303 episodes, semantic chunking, hybrid BM25 retrieval.
- [x] **Ship 30 for 30 Skill:** Dedicated ~1,250-word structured writing skill grounded in real transcript evidence.
- [x] **Sandboxed Artifact Viewer:** Isolated iframe with `null` origin, `bleach` backend sanitization, Preview/Code tabs.
- [x] **Comprehensive Documentation:** `README.md`, `PRD.md`, `architecture.md`, `design.md`, `manual-ui-test-plan.md`.
- [x] **Coding Agent Transcripts:** Full logs and failed attempt corrections in `agent-logs/` with zero committed secrets.
- [x] **Automated Test Suite:** 65 passing automated tests (`pytest tests/ -v`).
- [x] **Clean Secrets & Environment:** `.env.example` with safe defaults, zero committed API keys.
- [ ] **Camera-On YouTube Demo:** 2–3 minute video demo walk-through per Section 6 of the assignment.
- [ ] **GitHub Repository Submission:** Push to public GitHub repository and submit via the assignment form.
