# Design Specification — The Lenny Growth Assistant

## 1. UI/UX Principles & Aesthetics

The Lenny Growth Assistant features a high-grade dark-themed web interface built using modern CSS layout principles, glassmorphism visual accents, vibrant color palettes, subtle animations, and clear typography.

### Design System Tokens
- **Theme:** Deep space slate (`#0B0F17`) background with glass cards (`rgba(22, 30, 46, 0.75)`).
- **Primary Accent:** Electric Cyan (`#00F2FE` -> `#4FACFE` gradient) for buttons and active states.
- **Secondary Accent:** Violet Purple (`#7F00FF` -> `#E100FF` gradient) for writing skills and artifact badges.
- **Surface & Cards:** Dark slate background with `backdrop-filter: blur(12px)` and `border: 1px solid rgba(255, 255, 255, 0.08)`.
- **Typography:** Inter / Outfit system sans-serif font family.

---

## 2. Layout & Information Architecture

The interface uses a split-screen desktop layout designed for productivity and clear side-by-side content generation.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  HEADER: App Title | Active Model Badge [ Local Ollama (qwen2.5:3b) v ] | New Chat +   │
├───────────────┬───────────────────────────────────────────┬────────────────────────────┤
│  SIDEBAR      │  CHAT PANEL (55% Width)                   │ ARTIFACT PANEL (45% Width) │
│               │                                           │                            │
│  Session 1    │  [Assistant]                              │ ┌────────────────────────┐ │
│  Session 2    │  Here is an analysis of PLG onboarding... │ │ Artifact: PLG Essay    │ │
│  Session 3    │  Sources: [Lenny Episode #84]             │ │ [Preview] [Code] [Copy]│ │
│               │                                           │ ├────────────────────────┤ │
│               │  [User]                                   │ │ <iframe sandbox=...>   │ │
│               │  Turn this into a Ship 30 essay & visual! │ │                        │ │
│               │                                           │ │                        │ │
│               ├───────────────────────────────────────────┤ └────────────────────────┘ │
│               │  [ Input Message Field               (Send)]                           │
└───────────────┴───────────────────────────────────────────┴────────────────────────────┘
```

---

## 3. Key Interaction States

1. **Empty Chat State:** Displays quick-start prompt cards (e.g., "Analyze PLG Onboarding", "Ship 30 Essay on Pricing", "Growth Framework Visual").
2. **Provider Selector State:** Modal/Dropdown allowing user to toggle between `Local Ollama` and `Cloud Provider` (Anthropic / OpenAI). Displays status indicators (Ollama status: Connected / Cloud API Key: Configured).
3. **Generating / Streaming State:** Pulsing cyan loading animation with live status step labels ("Searching transcripts...", "Drafting essay...", "Building artifact...").
4. **Unsupported Query Warning:** Displayed with an amber alert badge stating that the transcript knowledge base does not contain relevant material.
5. **Missing Cloud Key Error State:** Clear red alert banner inside chat panel explaining that Cloud Provider requires an API key in `.env` without falling back silently.

---

## 4. Artifact Viewer UX & Isolation

- **Positioning:** Renders alongside the main chat on desktop screens (or switches to a dedicated tab on mobile viewports).
- **Controls:** Tab buttons for `Preview` (rendered HTML/Markdown), `Raw Code`, `Copy Code`, and `Expand Fullscreen`.
- **Sandbox Security:** The HTML preview container uses an isolated `<iframe>` with `sandbox="allow-scripts"` and `srcdoc` rendering to prevent parent DOM manipulation or credential access.

---

## 5. Accessibility & Responsive Rules

- **Semantic HTML:** Native `<header>`, `<nav>`, `<main>`, `<aside>`, `<section>`, `<article>`, `<button>`, and `<iframe>` elements.
- **Keyboard Navigation:** Full tab navigation and clear focus rings across input fields, provider dropdowns, and artifact tabs.
- **Contrast & Hierarchy:** Minimum contrast ratio of 4.5:1 for standard body text against dark slate surface.
- **Responsive Breakpoints:**
  - Desktop (>1024px): 3-column layout (Sidebar + Chat + Artifact Viewer).
  - Tablet (768px - 1023px): Collapsible sidebar + Chat and Artifact Viewer in split mode.
  - Mobile (<767px): Stacked view with tab bar to toggle between Chat and Artifact Viewer.
