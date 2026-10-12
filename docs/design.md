# Design Specification — The Lenny Growth Assistant

---

## 1. UI/UX Principles & Aesthetics

The Lenny Growth Assistant is designed as a focused, high-density professional workspace tailored for growth leaders and product managers. It eschews generic AI chatbot templates in favor of a cohesive, purpose-built product strategy cockpit.

### Core Visual Principles
1. **Restrained Editorial Tone:** A near-black canvas (`#090A0E`) combined with deep charcoal elevated surfaces (`#111318`, `#161920`) and restrained crimson/red accents (`#DC2626`). Red is reserved strictly for primary actions, active indicators, and critical signals to prevent visual fatigue.
2. **Side-by-Side Spatial Co-location:** High-leverage growth work requires referencing conversational context while inspecting essays or interactive tools. Generating an artifact does not displace the chat; it coexists side-by-side in real time.
3. **High Contrast & Skimmability:** Strict adherence to WCAG AA contrast standards. Text is crisp off-white (`#F8FAFC`) with muted slate secondary text (`#94A3B8`) for effortless long-session reading.
4. **Quiet, Distraction-Free Flow:** Scrollbars are completely hidden across modern browsers (`scrollbar-width: none; ::-webkit-scrollbar: none;`) to maximize screen real estate and reduce clutter, while retaining smooth native scrolling behavior.

### Design System Tokens

```css
:root {
    /* Foundations: Near-Black & Charcoal */
    --bg-canvas: #090A0E;
    --bg-surface: #111318;
    --bg-surface-elevated: #161920;
    --bg-surface-hover: #1D212A;
    --bg-surface-active: #242934;

    /* Borders & Dividers */
    --border-subtle: rgba(255, 255, 255, 0.07);
    --border-medium: rgba(255, 255, 255, 0.13);
    --border-focus: #B91C1C;
    --border-accent: #DC2626;

    /* Restrained Crimson & Red Accents */
    --accent-red-primary: #DC2626;
    --accent-red-hover: #EF4444;
    --accent-red-subtle: rgba(220, 38, 38, 0.12);
    --accent-red-border: rgba(220, 38, 38, 0.32);
    --accent-red-glow: rgba(220, 38, 38, 0.22);
    --gradient-red-brand: linear-gradient(135deg, #DC2626 0%, #991B1B 100%);

    /* High-Contrast Typography */
    --text-primary: #F8FAFC;
    --text-secondary: #94A3B8;
    --text-muted: #64748B;
    --text-inverse: #FFFFFF;

    /* Typography Hierarchy */
    --font-heading: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    --font-body: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
```

---

## 2. Layout & Information Architecture

The interface uses a 3-column split-screen layout designed for productivity, immediate context switching, and continuous spatial awareness.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│  APP HEADER                                                                                      │
│  [Logo] The Lenny Growth Assistant   | [● Library: Ready (303 eps)] | [Provider: Local Ollama] | [+ New Chat] │
├──────────────────┬────────────────────────────────────────────┬──────────────────────────────────┤
│  SIDEBAR         │  MAIN CHAT PANEL                           │  ARTIFACT VIEWER PANEL (50%)     │
│  (Session List)  │  (Scrollable Message Stream)               │  (Side-by-Side Co-location)      │
│                  │                                            │                                  │
│  • PLG Onboarding│  [User Message Card]                       │  ┌─────────────────────────────┐ │
│  • PMF Metrics   │  How do top PLG companies reduce friction? │  │ [MARKDOWN] Ship 30 Essay    │ │
│  • Growth Loops  │                                            │  │ [Preview] [Code] [📋 Copy] ✕ │ │
│  • Pricing Tier  │  [Assistant Message Card]                  │  ├─────────────────────────────┤ │
│                  │  According to Elena Verna, onboarding...   │  │ <iframe sandbox="allow-     │ │
│                  │                                            │  │  scripts" srcdoc="...">     │ │
│                  │  Sources:                                  │  │                             │ │
│                  │  [📌 Elena Verna • Onboarding Friction]    │  │                             │ │
│                  ├────────────────────────────────────────────┤  │                             │ │
│                  │  [Composer: Ask a question...        (↵)]  │  └─────────────────────────────┘ │
└──────────────────┴────────────────────────────────────────────┴──────────────────────────────────┘
```

### Component Breakdown
1. **App Header:**
   - **Logo & Title:** Brand identity with subtitle.
   - **Knowledge Base Status Card:** Real-time pulse dot, ingestion percentage, and episode progress indicator (`/api/ingest/status`).
   - **Provider Selector Badge:** Live dropdown allowing instant switching between Local Ollama, Cloud Anthropic, and Google Gemini, paired with connectivity status badge (Connected / Key Missing).
   - **New Chat Action:** Creates an independent session instantly.
2. **Sidebar (Chat Sessions):** Vertical session history listing active and past conversations. Allows switching sessions with one click and deleting obsolete threads.
3. **Main Chat Panel:** Multi-turn message stream with user bubble styling, assistant card styling, source citation badges, and a keyboard-friendly composer.
4. **Artifact Viewer Panel:** A collapsible right-hand workspace that renders generated Markdown or HTML/CSS artifacts beside the conversation.

---

## 3. Key Interaction States

### 3.1 Empty State & Quick Prompts
When a new session is launched, the chat panel displays an inviting empty state with three curated quick-prompt cards:
- **⚡ PLG Onboarding:** *"How do top PLG companies optimize user onboarding friction?"*
- **✍️ Ship 30 Essay:** *"Write a Ship 30 for 30 essay on product-market fit metrics."*
- **🎨 HTML Component:** *"Create an HTML dashboard component for tracking North Star metrics."*
Clicking any card immediately populates the input field and executes the query.

### 3.2 Thinking & Execution State
While the agent evaluates tools, searches transcripts, or drafts artifacts:
- The submit button is disabled to prevent duplicate submissions.
- The assistant displays a dynamic, pulsing status card indicating real-time progress.
- The user can still scroll through conversation history without interruption.

### 3.3 Message Card & Citation Badges
- **Assistant Responses:** Formatted with bold highlights, bulleted lists, and line breaks.
- **Source Citation Badges:** Each citation is rendered as an interactive pill badge (`📌 Elena Verna • Onboarding Friction`). Hovering reveals subtle crimson glowing borders, reinforcing trust and source traceability.

### 3.4 Artifact Viewer Split-Screen State
When the agent creates an essay or HTML component:
- The Artifact Viewer slides smoothly from the right side of the screen (`transform: translateX(0)`).
- The viewer includes an active **Preview** tab (rendered markdown or live interactive HTML) and a **Code** tab (syntax-highlighted raw source).
- A **Copy Code** button triggers clipboard capture with immediate visual confirmation (`✓ Copied!`).
- A close button (`✕`) dismisses the viewer without losing data; re-clicking previous turns re-opens the artifact.

### 3.5 Error & Missing Key Alerts
If a user switches to Cloud mode without credentials, or if a network error occurs:
- A non-blocking amber/red alert banner appears directly above the input box.
- The banner explains the exact issue clearly without jargon (e.g., *"⚠️ Anthropic Claude selected: ANTHROPIC_API_KEY is not set in .env. Configure your key or switch to Local Ollama."*).
- The user's input text is preserved so they can retry without retyping.

---

## 4. Responsive Behavior

| Viewport | Layout Strategy | Behavior Details |
|---|---|---|
| **Desktop (>1024px)** | 3-Column Split View | Sidebar (270px) + Chat Panel (Flexible) + Artifact Viewer (48% width). Both panels operate concurrently. |
| **Tablet (768px – 1024px)** | Adaptive 2-Column Split | Sidebar reduces width or docks horizontally; Artifact Viewer stacks beside or below chat. |
| **Mobile (<768px)** | Stacked Vertical Flow | Sidebar collapses into a top navigation bar (180px); Artifact Viewer occupies 50vh below chat with touch-friendly controls. |

---

## 5. Accessibility Considerations (a11y)

1. **High Contrast Ratios:** All body text (`#F8FAFC`) on dark surface (`#111318`) exceeds the 4.5:1 ratio required by WCAG 2.1 Level AA (achieving 14.2:1 contrast).
2. **Keyboard Ergonomics:**
   - `Enter`: Submits message.
   - `Shift + Enter`: Inserts clean newline for multi-line prompts.
   - `Tab` navigation: Full logical tab index order across inputs, provider selector, and artifact tabs.
   - Focus rings: Explicit high-visibility crimson focus outlines (`outline: 2px solid var(--accent-red-primary)`).
3. **Reduced Motion Support:** Built-in `@media (prefers-reduced-motion: reduce)` disables all transforms, slides, and pulsing animations for users with motion sensitivity.
4. **Semantic HTML5:** Strict utilization of native elements (`<header>`, `<aside>`, `<main>`, `<section>`, `<textarea>`, `<button>`, `<iframe>`).

---

## 6. Key Design Decisions & Rationale

| Decision | Alternative Considered | Rationale |
|---|---|---|
| **Side-by-Side Artifact Viewer** | Modal dialog / overlay | Modals obscure the conversation context. Growth operators need to cross-reference Lenny's quotes in the chat while reading the generated essay or using the HTML tool. |
| **Iframe Sandbox with `null` Origin** | Inline `dangerouslySetInnerHTML` | Untrusted HTML/JS could steal session data, read cookies, or hijack navigation. The `null` origin sandbox guarantees mathematical isolation under the browser's Same-Origin Policy. |
| **Hidden Scrollbars** | Visible OS default scrollbars | Default Windows scrollbars are wide, grey, and distracting on sleek dark themes. Hiding the scrollbar while maintaining mouse wheel / trackpad scrolling creates a clean, distraction-free aesthetic. |
| **Restrained Crimson Accent** | Generic electric blue / purple | Red evokes editorial urgency and focus, distinguishing the application from standard commodity chatbots while establishing a premium visual identity. |
| **Tabbed Preview vs. Code View** | Single preview-only view | Developers and growth marketers frequently need to copy raw HTML/Markdown into external CMSs (Substack, Ghost, Webflow). The Code tab makes extraction frictionless. |
