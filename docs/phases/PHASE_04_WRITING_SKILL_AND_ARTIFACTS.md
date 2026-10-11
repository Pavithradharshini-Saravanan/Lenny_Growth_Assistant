# Phase 4 — Ship 30 for 30 Writing Skill and Artifact Viewer

## Goal
Add two user-facing capabilities: reusable grounded essay writing and in-app artifact rendering.

## Prompt for Antigravity
Apply the anti-hardcoding rules. The writing skill and artifact generation must operate on the current request, retrieved evidence and conversation state—not on a set of canned topics, fixed essay templates that dictate content, hardcoded citations, or special-case prompts. Reusable structural guidance is allowed; hardcoded content/answers are not.
Read `AGENTS.md`, project rules, implementation plan, traceability checklist, `docs/skills/SHIP30_WRITING_SKILL.md`, and this phase file. Inspect the current code. Implement Phase 4 only.

### Writing skill
- Read the actual Ship 30 for 30 guide linked in the assignment and refine the skill file with principles supported by that guide. Record the source URL and do not fabricate details.
- Create a distinct, reusable skill/tool/service; do not rely on an unstructured one-off prompt.
- Use retrieved transcript evidence as the factual basis.
- Target approximately 1,250 words with a strong hook, coherent narrative, headings, selective bold/bullets and a practical takeaway.
- Do not invent claims, quotes, or source citations. Make uncertainty clear.
- Test structure, source grounding and reasonable word-count tolerance.

### Artifact generation and viewer
- Support requests to create Markdown and complete HTML/CSS artifacts from the current conversation.
- Show the artifact beside chat in an in-app viewer; include empty/loading/error states.
- Treat generated HTML as untrusted. Use an isolated sandboxed iframe with restrictive permissions and/or robust sanitization. Prevent access to the parent app, cookies, local storage, secrets and backend.
- Explain exactly what the viewer permits and blocks in `docs/architecture.md` or a security note.
- Add a test/manual test with potentially unsafe HTML and record expected behavior.

Acceptance checks:
- User can trigger the dedicated writing skill.
- Output is approximately 1,250 words and has the required structure.
- Claims have transcript source support; no fake citations.
- User can generate Markdown and HTML/CSS.
- Artifact appears beside chat and is not executed with parent-app privileges.
- Update traceability, tests and docs; do not start final hardening without review.
