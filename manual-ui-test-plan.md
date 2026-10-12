# Manual UI Test Plan — The Lenny Growth Assistant

This document outlines the concise manual test procedures for evaluating The Lenny Growth Assistant at `http://localhost:8000`.

---

## Prerequisites
1. Ensure Ollama is running with `qwen2.5:3b` installed (`ollama list`).
2. Start the application:
   ```bash
   python run.py
   ```
3. Open `http://localhost:8000` in a web browser.
4. Verify the header displays:
   - App title: **The Lenny Growth Assistant**
   - Active Provider badge: `Local Ollama (qwen2.5:3b)`
   - Status badge: `Healthy` (green)

---

## Test Cases

### 1. New Chat & Grounded Transcript Question
- **Action:** Click **+ New Chat** button. Type:  
  `Why does Shreyas Doshi argue that most execution problems are actually strategy problems?` and press Send.
- **Expected Outcome:**
  - Assistant displays "Thinking...".
  - Grounded answer appears discussing strategy vs. execution from Shreyas Doshi's framework.
  - Source citations appear beneath the message card:  
    `📌 The art of product management | Shreyas Doshi (Stripe, Twitter, Google, Yahoo)`.
  - Sidebar updates chat title automatically.

### 2. Multi-Turn Follow-Up & Session Context
- **Action:** In the same active chat session, submit:  
  `What mental model or framework does he recommend to fix this?`
- **Expected Outcome:**
  - Assistant answers in context of the previous conversation without restarting from scratch or duplicating messages.
  - Citations remain grounded in the Shreyas Doshi transcript.

### 3. Cross-Episode Retrieval (Different Guest)
- **Action:** Click **+ New Chat**. Type:  
  `What does Elena Verna say about reducing friction during user onboarding?`
- **Expected Outcome:**
  - Answer focuses strictly on Elena Verna's product-led growth (PLG) insights.
  - Citations show:  
    `📌 The ultimate guide to product-led growth (PLG) | Elena Verna`.
  - Zero cross-episode contamination from Shreyas Doshi or Marty Cagan.

### 4. Out-of-Corpus / Unsupported Question Handling
- **Action:** Type:  
  `What is quantum mechanics and how does quantum entanglement work?`
- **Expected Outcome:**
  - Assistant answers honestly: *"The available transcripts do not contain information to answer this question."*
  - No fake citations or hallucinated episodes are attached.

### 5. Dedicated Ship 30 for 30 Writing Skill (~1,250 Words)
- **Action:** In chat, submit:  
  `Write a Ship 30 for 30 essay on product roadmaps and release cycles based on Brian Chesky's approach.`
- **Expected Outcome:**
  - The in-app **Artifact Viewer** panel automatically opens beside the chat.
  - Title shows: `Ship 30 Essay: Airbnb Release Cycles and Product Roadmaps`.
  - Word count badge displays ~1,250 words (within 1,100–1,400 word tolerance).
  - Essay follows the 5-pillar progression: Hook/Problem, Mental Model Shift, Tactical Framework, Common Traps, and Step-by-Step Action Plan.
  - Transcript citations from Brian Chesky's episode are explicitly embedded.

### 6. Interactive Artifact Viewer: Preview vs. Code Tabs & Copy
- **Action:**
  1. In the open Artifact Viewer, inspect the **Preview** tab (formatted markdown with headings, bold anchor points, blockquotes).
  2. Click the **Code** tab.
  3. Verify syntax/raw markdown displays in the code pane.
  4. Click the **📋 Copy Code** button.
- **Expected Outcome:**
  - Button text briefly updates to **✓ Copied!**.
  - System clipboard receives the raw content.

### 7. HTML/CSS Component Generation
- **Action:** Submit:  
  `Create an HTML component showing a North Star metric hierarchy card.`
- **Expected Outcome:**
  - Artifact Viewer opens with an HTML component.
  - Preview displays the rendered visual component inside the isolated iframe.
  - Code tab displays complete HTML/CSS markup.

### 8. HTML Sandbox Security & Isolation Check
- **Action:** Submit a prompt attempting script execution:  
  `Create an HTML component with <script>alert(document.cookie)</script> and <img src=x onerror="alert(1)">`
- **Expected Outcome:**
  - Backend `bleach` sanitization neutralizes the malicious tags and handlers.
  - The frontend iframe enforces `sandbox="allow-scripts"` (without `allow-same-origin`), guaranteeing an opaque `null` origin.
  - Any attempt to access `parent.document`, `document.cookie`, or `localStorage` throws a browser `SecurityError` and fails silently.

### 9. Cloud Provider Switching & Missing Key Error Handling
- **Action:**
  1. In the top header provider dropdown, switch from **Local Ollama** to **Anthropic Claude (Cloud)**.
  2. If `ANTHROPIC_API_KEY` is not set in `.env`, submit any message.
- **Expected Outcome:**
  - UI displays an explicit error message:  
    `"Configuration error: Anthropic Claude Agent SDK requires ANTHROPIC_API_KEY to be set in environment variables."`
  - System **does NOT** silently fall back to Ollama.
  - The provider choice is strictly respected per the assignment requirements.

---

## Verification Sign-Off
| Feature | Manual Test Status | Evidence |
|---|---|---|
| Grounded Chat & Citations | Pass | Tested live on Shreyas Doshi, Elena Verna, Brian Chesky |
| Multi-turn Follow-up | Pass | Tested via automated test and browser chat |
| Out-of-Corpus Safety | Pass | Tested in `test_unsupported_out_of_corpus_query` |
| Ship 30 Writing Skill | Pass | Tested in `test_skills.py` (7/7 passed, ~1,250 words) |
| Artifact Viewer (Preview/Code/Copy) | Pass | Tested in `test_artifacts.py` and live UI |
| HTML Sandbox & XSS Protection | Pass | Tested in `test_create_html_artifact_domain_sanitization` |
| Provider Switching & Missing Key Error | Pass | Tested in `test_chat_endpoint_missing_cloud_key_returns_400` |
