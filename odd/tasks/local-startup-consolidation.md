# Consolidate local startup and optional research

Objective: one documented Compose command starts converter, privacy API, PostgreSQL and inference; local research is an explicit opt-in with a persistent archive; extension control copy states the exact scope. Branch: `feat/platform/consolidate-local-startup`; baseline: `c6bbffb`.
Delivery: ask-on-risk; forecast ~700 authored lines across four commits; no publishing authorized. Execution: inline by default; pytest, Node `node:test`, Playwright and `docker compose config`. Test runner: `uv run --directory api --no-sync pytest`, `node --test browser-extension/tests/*.test.cjs`, `uv run --directory e2e --no-sync pytest`.

## Specs

- S1: Default local environment. "Include the document converter in the normal Docker Compose startup." "After documented initial setup, one normal Compose command must start everything required for the ordinary protected-attachment workflow: Converter. Privacy API. PostgreSQL. Inference." "Keep their process boundaries." "Preserve loopback host bindings and internal-only services. Keep developer administration optional."
- S2: Optional local research. "Research remains disabled by default." "Provide a clearly documented, reproducible way to enable the EXISTING research module in the normal local API environment." "Configure persistent archive storage, required credentials, retention, and protocol settings." "Do not commit secrets or introduce insecure default research credentials." "Research requests must not be routed through inference." "Preserve existing authorization, consent, completion, retry, withdrawal, and retention semantics." "Do not silently change archive locations or leave existing data in ephemeral container storage."
- S3: Specialized deployment. "Retain the model-free campus collector and its restricted exposure. Do not replace it with the development API or make it depend on inference or PostgreSQL." "The default local environment may keep inference running even when research does not use it. Document this resource tradeoff."
- S4: Extension controls. "Reuse existing state and controls rather than adding a duplicate switch." Distinguish "Attachment protection enabled or disabled", "Research capture inactive, recording, paused, or awaiting completion/retry", and note "Backend availability, if displayed, is not the same as protection being enabled." "Do not imply that: Typed chat text is generally anonymized. Disabling protection disables every extension activity. Disabling protection authorizes recording. Starting research shuts down Docker." "Preserve current bypass semantics and per-tab isolation." "If 'convert without anonymizing' appears desirable, report it as a separate product decision."
- S5: Developer startup guide. "Prerequisites and initial setup." "One default local startup path." "Optional research configuration." "Existing extension controls and their exact scope." "Specialized model-free research deployment." "Safe shutdown and focused troubleshooting." "Earlier units must already include the instructions needed to use their changes."
- S6: Progressive delivery. "Do not implement everything first and commit everything at the end. Complete, verify, and commit each coherent work unit before starting the next." Units: converter orchestration; optional research; extension controls; guide consolidation. "Use Conventional Commits, without `Co-Authored-By` trailers or AI attribution." "Pushing, opening pull requests, merging, deploying, destructive operations, and accessing real research data are NOT authorized."
- S7: Verification. "Observe the expected failure before implementation when a meaningful runnable test exists." Verify default and research-enabled Compose resolution, attachment protection and bypass, research disabled by default, research without inference, archive persistence configuration, lifecycle semantics, per-tab isolation, standalone independence and documentation accuracy. "Distinguish configuration validation, simulated integration tests, real-model checks, and live-provider checks."
- S8: Preservation. "Preserve existing work." The pre-existing uncommitted wording change in `docs/guides/developer-startup.md` ("Dos flujos de desarrollo útiles:" to "Los flujos disponibles son:") is preserved in the rewritten guide rather than discarded.

## Tasks

- T1 [S1,S6,S7] inline — default Compose converter service, `.env.example`, Compose configuration regression, and startup infrastructure docs. Commit: pending.
- T2 [S2,S3,S6,S7] inline — research Compose override with named archive volume and required operator key; normal-app disabled/enabled tests; local research docs. Commit: pending.
- T3 [S4,S6,S7] inline — attachment-protection scope copy, research phase labels, Node state regression; bypass and per-tab tests retained. Commit: pending.
- T4 [S5,S6,S7,S8] inline — consolidated Spanish startup guide and cross-page consistency. Commit: pending.

## Log

### L1 — Original request (2026-11-10)

# Consolidate local startup without collapsing useful architectural boundaries

## Objective and authorization

Implement a cohesive local development workflow for `contextual-pii-anonymizer`, delivered through **progressive, reviewable local commits**.

The objective is to:
1. Include the document converter in the normal Docker Compose startup.
2. Make research an explicitly optional capability of that local environment.
3. Clarify extension controls for attachment protection and research capture.
4. Reorganize the developer startup guide around one default local workflow, retaining a clearly separated model-free research deployment.

Implementation and local commits are authorized. Pushing, opening pull requests, merging, deploying, destructive operations, and accessing real research data are NOT authorized.

**Do not implement everything first and commit everything at the end. Complete, verify, and commit each coherent work unit before starting the next.**

## Repository and working rules

Original workspace:

`C:\Users\stive\Documents\contextual-pii-anonymizer`

If the checkout is elsewhere, resolve its actual root and locate the corresponding files there.

Before changes:
- Read applicable `AGENTS.md` instructions and relevant installed skills.
- Inspect the branch, working tree, and staged changes.
- Record the starting commit and distinguish pre-existing changes from your work.
- Revalidate the architecture facts below against current code.
- Discover the existing test runners; do not invent commands.
- Use CodeGraph first for structural exploration when available, following repository instructions.

The previous inspection found a pre-existing modification to:

`C:\Users\stive\Documents\contextual-pii-anonymizer\docs\guides\developer-startup.md`

It may have changed since then. Preserve existing work. Do not overwrite, discard, or automatically include unrelated edits in your commits. If overlapping changes cannot be separated safely, ask one focused question.

Use English for new identifiers and code comments. Preserve the established language of touched UI and documentation rather than translating unrelated content.

## Architectural context to verify

The current system has these responsibilities:

- Browser extension: intercepts supported attachment flows and optionally captures research conversations.
- Converter: converts supported documents to Markdown.
- Privacy API: applies detection and protection using persisted configuration and, when enabled, inference.
- PostgreSQL: stores ordinary API configuration.
- Inference service: serves privacy models.
- Research module: manages consented sessions, raw conversation capture, completion receipts, withdrawal, and retention using SQLite.

Important findings from the previous read-only analysis:

1. The normal Compose stack starts PostgreSQL, inference, and the privacy API, with optional pgAdmin. It does NOT include the converter.
2. The extension currently calls the converter and privacy API separately. The converter does not directly invoke the privacy API.
3. Research already uses a shared router mounted in BOTH the normal API and a standalone model-free application. Do not duplicate or reinvent that implementation.
4. Research is disabled by default through `RESEARCH_ENABLED`. The normal Compose configuration lacks first-class research configuration and archive persistence.
5. The normal API verifies PostgreSQL during application startup. Compose additionally waits for inference health before starting the API. Research handlers themselves do not require inference.
6. The extension already has a global `activo` protection toggle. Turning it off bypasses attachment conversion and protection; it does not stop Docker.
7. Research capture has a separate session state. Recording or paused research suspends ordinary attachment protection only in the selected research tab.
8. Ordinary protection covers attachments, not general text typed into chats.
9. The campus research deployment intentionally avoids PostgreSQL and inference and has a narrower image and exposed route surface.
10. The test Compose configuration already coordinates converter, API, database, and simulated inference. It is a useful precedent, NOT a production-ready configuration to copy blindly.

These are starting facts to verify, not permission to ignore newer evidence.

## Relevant source map

Inspect the corresponding files in the actual checkout:

- `compose.yaml`
- `compose.test.yaml`
- `compose.research.yaml`
- `api/app/routers/__init__.py`
- `api/app/lifespan.py`
- `api/app/research/application.py`
- `api/app/research/router.py`
- `api/Dockerfile.research`
- `browser-extension/backend/app.py`
- `browser-extension/extension/background.js`
- `browser-extension/extension/popup.js`
- `docs/guides/developer-startup.md`

Relevant existing regression coverage includes research API tests and browser tests for disabled protection and per-tab research capture. Locate them and reuse their conventions.

## Target design

### Default local environment

After documented initial setup, one normal Compose command must start everything required for the ordinary protected-attachment workflow:

- Converter.
- Privacy API.
- PostgreSQL.
- Inference.

Keep their process boundaries unless current evidence demonstrates a necessary change. One startup command does not require one container, one process, or one browser-facing endpoint.

Preserve loopback host bindings and internal-only services. Keep developer administration optional.

### Optional local research

Provide a clearly documented, reproducible way to enable the EXISTING research module in the normal local API environment.

Requirements:
- Research remains disabled by default.
- Enabling server capability does not start recording or imply participant consent.
- Configure persistent archive storage, required credentials, retention, and protocol settings.
- Do not commit secrets or introduce insecure default research credentials.
- Research requests must not be routed through inference.
- Preserve existing authorization, consent, completion, retry, withdrawal, and retention semantics.
- Do not silently change archive locations or leave existing data in ephemeral container storage.

Choose the smallest configuration mechanism consistent with the repository. Remember: Compose profiles select optional services; they do not automatically modify an existing service’s environment or application behavior.

### Specialized research deployment

Retain the model-free campus collector and its restricted exposure. Do not replace it with the development API or make it depend on inference or PostgreSQL.

The default local environment may keep inference running even when research does not use it. Document this resource tradeoff. Do not introduce a universal conditional-lifespan refactor merely to avoid it.

### Extension controls

Reuse existing state and controls rather than adding a duplicate switch.

Make these distinctions understandable:
- Attachment protection enabled or disabled.
- Research capture inactive, recording, paused, or awaiting completion/retry.
- Backend availability, if displayed, is not the same as protection being enabled.

Do not imply that:
- Typed chat text is generally anonymized.
- Disabling protection disables every extension activity.
- Disabling protection authorizes recording.
- Starting research shuts down Docker.

Preserve current bypass semantics and per-tab isolation. If “convert without anonymizing” appears desirable, report it as a separate product decision; do not implement it silently.

## Progressive commit strategy

Create a feature branch when required by repository policy. Use Conventional Commits, without `Co-Authored-By` trailers or AI attribution.

Use these provisional work-unit boundaries:

### Unit 1 — Complete ordinary local orchestration

Integrate the converter into the normal Compose workflow, including its required configuration, appropriate availability checks, focused tests, and the corresponding startup instructions.

Commit only after verifying this unit.

### Unit 2 — Support optional research in the local stack

Add explicit research configuration and persistent archive support using the shared router. Include tests for disabled/enabled behavior, relevant data lifecycle invariants, and accompanying documentation.

Preserve the standalone collector.

Commit only after verifying this unit.

### Unit 3 — Clarify extension controls

Improve labels, explanations, or state presentation where needed, reusing existing behavior and state. Include regression tests for global bypass, research-tab isolation, and any changed visible behavior.

Commit only after verifying this unit.

### Unit 4 — Consolidate the startup guide

Finish the guide’s overall structure:
- Prerequisites and initial setup.
- One default local startup path.
- Optional research configuration.
- Existing extension controls and their exact scope.
- Specialized model-free research deployment.
- Safe shutdown and focused troubleshooting.

Earlier units must already include the instructions needed to use their changes. This final unit consolidates the guide rather than postponing all documentation until the end.

Commit after structural and command/configuration verification.

Adjust boundaries if current evidence requires it, but preserve progressive delivery. Do not split commits mechanically by file type or separate tests from their behavior. Prefer small coherent commits; do not remove tests or compress code to satisfy a line budget.

Do not automatically squash, amend unrelated commits, publish branches, or create PR chains.

## Verification discipline

For each behavior change, use a relevant deterministic regression test:
1. Observe the expected failure before implementation when a meaningful runnable test exists.
2. Implement the smallest change.
3. Observe success.
4. Refactor without changing behavior.

Explain exceptions honestly; do not invent RED/GREEN evidence.

Verify, as applicable:
- Default and research-enabled Compose configurations resolve correctly.
- Ordinary attachment conversion and protection still work.
- Disabled protection retains existing bypass behavior.
- Default startup does not enable research capture.
- Enabled research works without invoking inference.
- Research data survives ordinary container recreation.
- Authorization, retries, withdrawal, and retention remain intact.
- Research activity in one tab does not disable protection in another.
- The model-free deployment remains independent of ordinary-stack dependencies.
- Documentation matches actual commands and endpoint behavior.

Distinguish configuration validation, simulated integration tests, real-model checks, and live-provider checks. A stubbed test does not prove real-model behavior.

Use isolated synthetic data and test storage. Do not access real conversations, student records, production credentials, or campus systems. Do not use volume deletion, pruning, browser-storage clearing, or database recreation as troubleshooting shortcuts.

Before expensive builds or model downloads, provide a short resource/time forecast and follow applicable permission requirements.

Run focused checks per work unit and the applicable integrated suite at closure. Record exact commands and observed results. Identify baseline failures separately from regressions. Follow applicable independent verification and review requirements without bypassing required consent.

## Scope exclusions

Do not:
- Merge all services into one process or container.
- Add an API gateway, plugin framework, or custom orchestrator.
- Migrate research storage from SQLite to PostgreSQL merely to reduce component count.
- Rewrite inference or change anonymization algorithms.
- Expand protection to typed chat text.
- Modify unrelated browser adapters or security controls.
- Fix unrelated findings without authorization; report them separately.

## Completion report

Return:
1. What changed and how the resulting workflow behaves.
2. Each progressive commit’s hash and purpose.
3. Exact verified startup/configuration instructions.
4. Checks executed, with results.
5. Failed, skipped, unavailable, or pending checks and their consequences.
6. Remaining limitations and any decision genuinely needed.
7. Confirmation that unrelated changes and existing data were preserved.

Do not claim completion while required evidence is missing. If blocked, preserve completed commits and report the specific blocker.

Continue through authorized implementation, verification, documentation, and local commits without asking permission at every phase. Ask only when a consequential unresolved decision, safety boundary, or required consent prevents progress.
