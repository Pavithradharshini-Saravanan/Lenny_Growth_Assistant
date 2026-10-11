# Anti-Hardcoding Audit Checklist

Use this checklist in every phase, especially before declaring a feature complete.

## Search the code for
- Keyword/trigger lists used to determine user intent or workflow.
- `if/elif` chains matching particular user phrases or example commands.
- Hardcoded website/domain/app aliases or fixed site maps.
- Fixed transcript titles, passages, chunk IDs, citations, or query-to-source mappings.
- Canned assistant answers or demo-only fallback responses.
- Per-example workflows that duplicate what a general-purpose agent/tool can do.
- Tests that only repeat the exact prompts used to build the feature.

## What is allowed
- Security and validation rules (e.g. validate a URL, constrain file access, validate tool arguments).
- A finite registry of real tools/providers with typed schemas.
- Deterministic implementation inside a general-purpose tool.
- Reusable prompt/skill instructions that describe quality and safety constraints without hardcoding the output content.
- UI controls for explicit settings such as selecting Local or Cloud.
- Configuration-driven supported models, data sources and environment settings.

## Required test approach
For each agentic feature, test:
1. A normal request.
2. A different request requiring the same general capability.
3. A paraphrase or novel request not used during implementation.
4. An ambiguous or unsupported request that should be clarified or fail safely.

Confirm that behavior is produced by the same general-purpose mechanism, not a new phrase-specific branch.

## Review questions
- If the user changes the wording, will it still work?
- If the user asks about a transcript not used in demos, will retrieval search the actual corpus?
- If a new model is configured, can it be added through configuration/provider integration rather than rewriting task logic?
- Does an unknown request fail safely instead of triggering a guessed action?
- Are tests verifying general behavior rather than encouraging hardcoded demo outputs?

Record audit findings in the phase report. Any remaining special-case logic must be explained and justified.
