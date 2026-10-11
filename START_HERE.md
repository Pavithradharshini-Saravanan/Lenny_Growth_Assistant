# Start Here — Antigravity Project Pack

## Your project
Build **The Lenny Growth Assistant**, a full-stack conversational web application based on Lenny’s Podcast/Newsletter transcripts. The assignment deadline is **12 October 2026, end of day**.

## What to do first
1. Open your project folder in Antigravity.
2. Create `docs/reference/`.
3. Put the original assignment file there as:
   `Forward_Deployed_Engineer_Take_Home_Assignment_12_Oct_2026.docx`
4. Copy the files from this pack into the project, preserving their folders.
5. Read `AGENTS.md` once. It tells the coding agent which project documents are authoritative.
6. Start with `docs/phases/PHASE_00_PLAN_AND_VERIFY.md`. Do not ask Antigravity to build everything in one giant prompt.
7. Review and approve the plan before it implements application code.
8. Work through one phase at a time. After each phase, run the tests and verify the acceptance checklist before moving on.

## What is Ship 30 for 30?
For this assignment, it means a repeatable writing skill inspired by the linked Ship 30 for 30 writing guide. Your app should use it to create an approximately 1,250-word essay from relevant, transcript-grounded information. It should have a strong hook, a logical narrative, skimmable formatting, and a useful takeaway. It does **not** mean you need to publish 30 essays in 30 days.

## Important: how to make Antigravity reread the rules
Do not assume the agent automatically reads every file on every turn. Keep `AGENTS.md` at the project root and use `docs/prompts/CONTINUE_WORK.md` as the first message when resuming. Ask Antigravity to confirm which phase is active and what it read before changing code.

## Local-first model setup
- The demo must work with Ollama on your computer.
- Include a cloud provider adapter in the code, but cloud credentials are optional for your development/demo.
- A user-selected provider must be visible.
- If Cloud is selected without valid credentials, show a clear error. Do not silently switch to Ollama.
- Never claim a live cloud request was tested if no valid cloud key was available.

## Suggested project layout
```text
project-root/
├── AGENTS.md
├── README.md
├── .env.example
├── .gitignore
├── docs/
│   ├── reference/
│   │   └── Forward_Deployed_Engineer_Take_Home_Assignment_12_Oct_2026.docx
│   ├── PROJECT_RULES.md
│   ├── PRD.md
│   ├── architecture.md
│   ├── design.md
│   ├── implementation-plan.md
│   ├── REQUIREMENTS_TRACEABILITY.md
│   ├── phases/
│   ├── skills/
│   └── prompts/
├── backend/
├── frontend/
├── tests/
└── agent-logs/
```
The agent may recommend a different sensible structure, but it must explain why and update the docs before diverging.
