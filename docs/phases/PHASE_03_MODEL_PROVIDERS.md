# Phase 3 — Ollama Local Model and Optional Cloud Provider

## Goal
Make the local demo work and provide a real, separately configurable cloud-provider implementation.

## Prompt for Antigravity
Apply the anti-hardcoding rules. Provider selection must come from explicit configuration/UI state and a reusable provider registry/interface, not from keyword detection in user messages or special cases for particular prompts. Do not silently change providers.
Read `AGENTS.md`, project rules, architecture, implementation plan, traceability checklist, and this phase file. Inspect the current agent integration and prove compatibility before making broad changes. Implement Phase 3 only.

Requirements:
1. Implement a shared provider interface with separate Ollama and one cloud-provider adapter (Anthropic Claude or OpenAI).
2. Read provider/model/base URL/key from environment configuration or an explicit user choice. Do not hardcode secrets.
3. Local Ollama mode must work without any cloud API key. Check installed models instead of assuming a model is present.
4. Expose the active provider in the UI and/or configuration, and make provider selection explicit.
5. Cloud mode must validate configuration and return a clear error if credentials are absent/invalid. Never silently switch to Ollama.
6. Use mocks to test cloud adapter behavior if no live cloud key is available. Clearly label live cloud inference as untested in that case.
7. Verify whether the chosen required agent framework can work with Ollama and cloud providers and its tool/function-calling needs. If not, stop, describe the conflict and propose the smallest compliant solution before changing the framework.
8. Add routing tests: local selection routes locally; cloud selection routes to cloud; missing cloud credentials cause a clear error; no fallback occurs.
9. Add safe logs for provider/model/errors without logging keys or sensitive prompt content.

Acceptance checks:
- At least one real local Ollama chat request succeeds on this machine.
- Provider selection is visible and reflected in the request path.
- Cloud adapter exists and has tests.
- Missing cloud credentials do not break local mode.
- Selecting cloud without credentials does not secretly use local mode.
- Documentation distinguishes tested local behavior from mocked/unverified live cloud behavior.
