# Product Requirements Document (PRD) — The Lenny Growth Assistant (Revised)

## 1. Executive Summary & Discovery Brief

### 1.1 User and Problem
**Target User:** Product Managers, Growth Leads, Founders, and Product Marketing Managers seeking authoritative, practical growth advice.  
**Core Problem:** Lenny’s Podcast and Newsletter contain hundreds of hours of high-value advice, but searching raw transcripts is time-consuming and generic LLMs hallucinate inaccurate advice.  
**Value Proposition:** "The Lenny Growth Assistant" is an internal conversational workspace that ingests Lenny's transcripts, provides grounded answers with source citations, drafts ~1,250-word Ship 30 for 30–style essays, and renders interactive Markdown/HTML visual artifacts in a side-by-side UI.

### 1.2 Success Metrics
- **Grounding Accuracy:** 100% of claims cite indexed transcript metadata (episode, speaker, chunk ID).
- **Retrieval Precision:** ≥ 90% relevance on domain queries.
- **Honest Unsupported Response:** 100% acknowledgement when queries fall outside transcript corpus.
- **Artifact Security:** 0% script execution leak from untrusted HTML artifacts (strict iframe sandbox).
- **Local Operational Readiness:** 100% functional local execution using Ollama (`qwen2.5:3b`) without paid API keys.

### 1.3 Key Assumptions & Constraints
1. **Corpus Source:** Transcripts loaded from `https://github.com/ChatPRD/lennys-podcast-transcripts`.
2. **Local Demo:** Local execution operates on Ollama (`qwen2.5:3b`) on `http://localhost:11434`.
3. **Mandatory Agent SDK:** Cloud agentic execution is powered by **Anthropic Claude Agent SDK** (`claude-agent-sdk`).
4. **Zero Silent Fallback:** Selecting Cloud mode without `ANTHROPIC_API_KEY` returns an explicit error without falling back to Ollama.

### 1.4 Scope Choices
| In Scope | Out of Scope (Intentional) | Rationale |
|---|---|---|
| FastAPI backend with async endpoints | Complex microservices mesh | Minimizes evaluation complexity. |
| PostgreSQL persistence (sessions, messages, artifacts) | Redis caching layer | PostgreSQL provides simple, robust persistence. |
| Anthropic Claude Agent SDK integration for Cloud mode | Native Anthropic SDK execution for local Ollama | `claude-agent-sdk` requires Anthropic API endpoints; Ollama adapter handles local mode with shared tool definitions. |
| Side-by-side Chat + Sandboxed Artifact Viewer | Multi-tenant auth / SSO | Focuses on core assistant capabilities. |
| Ship 30 for 30 grounded writing skill | Generic unstructured essay generation | Encodes specific writing principles (~1,250 words, hook, takeaway). |

---

## 2. Core Requirements

### 2.1 Backend API & Persistence
- **FastAPI Framework:** REST API for sessions, chat, ingestion, and config.
- **PostgreSQL Database:** Persists `sessions`, `messages`, `artifacts`, `transcripts`, and `transcript_chunks`.
- **Independent Sessions:** Each session maintains isolated history.

### 2.2 Agent Architecture & Model Providers
- **Anthropic Claude Agent SDK (`claude-agent-sdk`):** Official agent layer for Cloud mode using `ClaudeSDKClient` and `@tool` decorators.
- **Ollama Agent Adapter:** Local agent implementation for Ollama (`qwen2.5:3b`) using identical tool schemas (`search_transcripts`, `run_ship30_skill`, `create_artifact`).
- **Provider Visibility:** UI header displays selected provider and SDK status. Missing cloud key throws an explicit error.

### 2.3 Grounded Retrieval & Citation
- **Ingestion & Inverted Index:** Parses transcripts, chunks text semantically, and indexes chunks in PostgreSQL.
- **Source Citation:** Answers cite transcript title, URL, and chunk metadata.

### 2.4 Content Skill & Artifact Viewer
- **Ship 30 Skill:** Implements principles from Ship 30 guide (~1,250 words, hook, progression, takeaway, transcript claims).
- **Sandboxed Viewer:** Side-by-side HTML/Markdown viewer using isolated `<iframe>` (`sandbox="allow-scripts"` and `srcdoc`).

---

## 3. Acceptance Criteria

1. **FastAPI & Health:** Backend starts cleanly and exposes `/health` and `/api/config`.
2. **Anthropic Claude Agent SDK Integration:** Cloud agent uses `claude-agent-sdk` Python library with `@tool` definition.
3. **Local Ollama Execution:** Local mode answers queries with `qwen2.5:3b` without cloud keys.
4. **PostgreSQL Persistence:** All sessions, messages, and artifacts are stored in PostgreSQL with UUIDs.
5. **No Silent Fallback:** Selecting Cloud mode without `ANTHROPIC_API_KEY` returns a clear error.
6. **Transcript Grounding:** Answers include real source metadata; out-of-corpus queries yield explicit unsupported status.
7. **Ship 30 Skill:** Generates ~1,100–1,400 word essay with hook, takeaway, and transcript evidence.
8. **Artifact Security:** HTML artifacts render securely in an isolated iframe sandbox.
