# Product Requirements Document (PRD) — The Lenny Growth Assistant

---

## 1. Executive Summary & Problem Brief

### 1.1 Target Users & Personas
- **Primary Persona: Growth Leads & Product Managers (PMs):** Professionals making high-stakes decisions on user onboarding, activation funnels, product-market fit (PMF), pricing tiers, and retention loops who need authoritative, battle-tested tactics rather than generic advice.
- **Secondary Persona: Early-Stage Founders & Tech Leads:** Leaders looking to transform raw product concepts into structured strategy documents, Ship 30 for 30–style essays, and interactive UI artifacts.
- **Tertiary Persona: Product Marketing Managers (PMMs):** Professionals drafting thought leadership, competitive positioning memos, and launch frameworks grounded in proven market wisdom.

### 1.2 Core Problem Statement
Lenny’s Podcast and Newsletter represent one of the world's most valuable archives of product strategy, containing over 300+ episodes and hundreds of hours of interviews with world-class operators (Brian Chesky, Shreyas Doshi, Elena Verna, Marty Cagan, etc.).
However:
1. **High Search & Discovery Friction:** Finding specific tactics across transcripts is painfully manual and slow.
2. **LLM Hallucination & Lack of Attribution:** Standard conversational LLMs frequently hallucinate metrics, attribute quotes to the wrong guests, or blend unrelated frameworks.
3. **Absence of Actionable Outputs:** General-purpose chatbots produce shallow text summaries instead of publishable essays or interactive computational growth tools.
4. **Cloud API Cost & Privacy Roadblocks:** Many growth teams cannot share internal strategy prompts with paid third-party cloud APIs.

### 1.3 Value Proposition
**The Lenny Growth Assistant** is a self-hosted, full-stack conversational workspace that ingests Lenny's real transcripts, performs semantic retrieval with traceable citations, drafts ~1,250-word Ship 30 for 30 essays, and renders interactive, sandboxed HTML/CSS growth tools side-by-side in real time—with 100% local Ollama execution as well as cloud provider support.

---

## 2. Success Metrics & Key Results (OKRs)

| Metric | Target | Measurement Method |
|---|---|---|
| **Grounding Accuracy** | 100% | Every factual claim is paired with episode title, guest speaker, and chunk excerpt metadata. |
| **Retrieval Relevance** | ≥ 90% | Relevant transcript chunks retrieved for domain queries within top-5 results. |
| **Unsupported Honesty** | 100% | Out-of-corpus queries explicitly acknowledge lack of evidence with zero fabricated citations. |
| **Artifact Security** | 0% Escape | Zero DOM access, cookie leakage, or top navigation from untrusted HTML artifacts (opaque `null` origin sandbox). |
| **Zero-Cost Local Readiness** | 100% Operational | Full chat, RAG, and artifact generation run locally using Ollama (`qwen2.5:3b` / `gemma3:4b`) without paid API keys. |
| **Provider Integrity** | Zero Silent Fallback | Cloud mode without API keys immediately returns an explicit HTTP 400 error rather than silently routing to Ollama. |
| **Test Suite Health** | 100% Passing | Automated pytest suite covers API, agents, skills, artifacts, and ingestion. |

---

## 3. Assumptions & Operating Constraints

1. **Transcript Corpus Source:** Ingested from the public upstream repository `ChatPRD/lennys-podcast-transcripts` (303 episodes in Markdown with YAML frontmatter).
2. **Local Execution Environment:** Operates locally on Windows, macOS, or Linux using Ollama on `http://localhost:11434`. Default local model is `qwen2.5:3b` or `gemma3:4b`.
3. **Cloud Agent Frameworks:**
   - **Anthropic Claude Agent SDK:** Implemented via `claude-agent-sdk` with `@tool` registration for Cloud mode.
   - **Google Gemini:** Implemented via OpenAI-compatible REST API for multi-provider flexibility.
4. **Hardware Constraints:** Development runs on standard consumer hardware without requiring dedicated discrete GPUs.
5. **Zero Silent Fallback Invariant:** If a user selects a cloud provider without configuring the required API key in `.env`, the system must show a clear, actionable error banner rather than silently defaulting to local Ollama.

---

## 4. Product Scope

### In-Scope
- **FastAPI Async Backend:** High-performance REST API for chat, session persistence, transcript ingestion, and health monitoring.
- **Relational Persistence:** PostgreSQL (production / Docker) and SQLite (zero-setup local development) with SQLAlchemy ORM.
- **Dynamic Ingestion Pipeline:** Automatic background discovery and ingestion of 303 episodes, YAML metadata parsing, semantic paragraph chunking, and deduplication.
- **Hybrid RAG Retrieval Engine:** BM25 TF-IDF scoring with speaker attribution and cross-episode disambiguation.
- **Dedicated Ship 30 for 30 Skill:** Structured long-form essay generation (~1,250 words, hook, 5 pillars, skimmable formatting, grounded takeaways).
- **In-App Sandboxed Artifact Viewer:** Side-by-side rendering of Markdown and complete HTML/CSS components with tabbed Preview/Code views and one-click copying.
- **Strict Defense-in-Depth Security:** Backend `bleach` sanitization and frontend iframe isolation with opaque `null` origin.
- **Clean UI Workspace:** Premium Dark-Theme interface (Near-Black, Deep Charcoal, Crimson accents) with hidden scrollbars, Enter-to-send keyboard handling, and real-time ingestion progress indicator.

### Out-of-Scope (Deliberate Trade-offs)
- Multi-tenant enterprise SSO (OAuth/SAML) — focuses on single-operator or local team evaluation.
- Distributed message broker (Celery/Kafka) — background tasks are managed cleanly via FastAPI async workers and SQLAlchemy.
- Voice/Audio transcription pipeline — transcripts are ingested from the authoritative upstream text archive.

---

## 5. End-to-End User Flows

```
Flow 1: Ingestion & Library Readiness
[App Startup] ──> [Background IngestionManager] ──> [Dynamic CDN/GitHub Discovery (303 eps)]
                           │                                  │
                           ▼                                  ▼
                 [Header Status: 15%] ─────────────> [Header Status: Library Ready (303 eps)]

Flow 2: Grounded Conversation
[User Inputs Prompt] ──> [Chat Form (Enter)] ──> [Session Service Persists Msg]
                                                        │
                                                        ▼
                                             [Agent Strategy Dispatcher]
                                            ┌───────────┴───────────┐
                                            ▼                       ▼
                                      [Local Ollama]          [Cloud Provider]
                                            │                       │
                                            └───────────┬───────────┘
                                                        │
                                                        ▼
                                             [search_transcripts Tool]
                                                        │
                                                        ▼
                                            [BM25 TF-IDF Hybrid RAG]
                                                        │
                                                        ▼
                                        [Synthesize Grounded Response]
                                                        │
                                                        ▼
                                      [Render Answer + Source Badges]

Flow 3: Ship 30 Essay & Artifact Inspection
[User Requests Essay/HTML Component] ──> [run_ship30_skill / create_artifact]
                                                        │
                                                        ▼
                                           [Backend Bleach Sanitization]
                                                        │
                                                        ▼
                                          [Side-by-Side Artifact Viewer]
                                            ┌───────────┴───────────┐
                                            ▼                       ▼
                                    [Preview Iframe (null)]   [Raw Code Tab]
```

### Detailed Flow Descriptions
- **Flow 1: New Session & Grounded Query:** User enters a query (e.g., *"How do top PLG companies reduce onboarding friction?"*). The system persists the message, triggers `search_transcripts`, retrieves Elena Verna's transcript chunks, and formats the response with clickable citation badges.
- **Flow 2: Ship 30 for 30 Long-Form Essay:** User requests an essay on a growth topic. The agent executes `run_ship30_skill`, generates a ~1,250-word structured piece with hook and takeaway, persists the artifact, and automatically slides open the Artifact Viewer.
- **Flow 3: Interactive HTML Artifact Generation:** User asks for an interactive metrics calculator or visual dashboard. The agent generates valid HTML/CSS, the backend sanitizes script escape patterns, and the frontend renders it inside an isolated `<iframe>` with `sandbox="allow-scripts"`.
- **Flow 4: Provider Switching & Credential Validation:** User toggles the header dropdown to *Google Gemini* or *Anthropic Claude*. If credentials are missing, the UI displays an actionable warning banner and prevents silent degradation.

---

## 6. Acceptance Criteria

| ID | Category | Requirement Description | Verification Method |
|---|---|---|---|
| **AC-01** | **Backend API** | FastAPI serves `/health`, `/api/config`, `/api/sessions`, and `/api/chat`. | Automated pytest & HTTP status 200. |
| **AC-02** | **Persistence** | Sessions, messages, and artifacts persist across page reloads in PostgreSQL / SQLite. | Multi-turn API tests and session reload. |
| **AC-03** | **Local Execution** | Runs end-to-end locally using Ollama (`qwen2.5:3b` / `gemma3:4b`) without cloud API keys. | Local demo test execution. |
| **AC-04** | **Cloud Integration**| Anthropic Claude SDK & Google Gemini selectable in UI with strict key validation. | Mocked agent unit tests and UI state check. |
| **AC-05** | **Zero Fallback** | Selecting Cloud mode without API key returns explicit HTTP 400 error. | `test_chat_endpoint_missing_cloud_key_returns_400`. |
| **AC-06** | **RAG Grounding** | Answers cite real transcript episodes; unsupported queries explicitly acknowledge limits. | `test_grounding_regression.py`. |
| **AC-07** | **Ship 30 Skill** | Essay conforms to Ship 30 format, 1,100–1,400 words, with grounded takeaways. | `test_skills.py` word-count assertions. |
| **AC-08** | **Sandbox Security**| Untrusted HTML rendered in iframe with `null` origin; DOM manipulation is blocked. | `test_artifacts.py` sandbox policy checks. |
| **AC-09** | **UI Experience** | Dark theme, hidden scrollbars, Enter-to-send, copy button, live ingestion progress bar. | UI evaluation & `test_api.py`. |

---

## 7. Risk Assessment & Mitigation Strategy

| Risk | Impact | Likelihood | Mitigation Strategy |
|---|---|---|---|
| **Model Hallucination** | High | Medium | Strict BM25 TF-IDF retrieval scoring, prompt grounding instructions, and explicit citation schemas. |
| **Local CPU Inference Lag** | Medium | Medium | Default to lightweight 3B/4B models (`qwen2.5:3b`, `gemma3:4b`), stream responses, and provide sliding context window (last 8 messages). |
| **Malicious HTML Artifacts** | Critical | Low | Two-layer defense: backend `bleach` sanitization stripping escape vectors, and frontend iframe `sandbox="allow-scripts"` with opaque `null` origin. |
| **Cloud API Rate Limits** | Medium | Medium | Graceful backoff retries on transient 5xx errors; immediate actionable error messaging on 401/403/429. |
| **Upstream Transcript Drift** | Low | Low | Resilient YAML frontmatter parser handling missing fields and fallback speaker heuristics. |

---

## 8. Implementation Plan & Milestone Roadmap

- **Phase 0 — Understand & Plan (COMPLETED):** Audited assignment requirements, evaluated `claude-agent-sdk`, established dual-adapter strategy, created initial PRD, architecture, and project rules.
- **Phase 1 — Runnable Foundation (COMPLETED):** Built FastAPI backend, SQLAlchemy database models, session management CRUD, provider selector, and verified test suite.
- **Phase 2 — Transcript Ingestion & RAG (COMPLETED):** Implemented repeatable transcript ingestion, semantic paragraph chunking, BM25 TF-IDF search, and grounded Q&A with citations.
- **Phase 3 — Writing Skill & Sandboxed Viewer (COMPLETED):** Created Ship 30 for 30 skill (~1,250 words), Bleach HTML sanitizer, side-by-side Artifact Viewer, and security tests.
- **Phase 4 — Hardening & Containerization (COMPLETED):** Created Dockerfile, docker-compose.yml, requirements.txt, manual UI test plan, and resolved Ollama edge cases.
- **Phase 5 — Complete Ingestion & Multi-Cloud (COMPLETED):** Added dynamic background ingestion for all 303 episodes, Google Gemini REST adapter, real-time progress indicator, and cross-browser scrollbar polish.
