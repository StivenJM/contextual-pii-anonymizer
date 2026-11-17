# Unify research-capture authentication on a participant enrollment code

Branch: `new-branch` (no commits requested). Test runners: `node --test browser-extension/tests/*.test.cjs`, `uv run --directory api --no-sync pytest`, `uv run --directory e2e --no-sync pytest`.
Delivery: user explicitly forbade commit, push and publication; work units stay in the working tree.

## Specs

- S1. The extension always displays the exact participant input label `Código de participación`.
- S2. The extension always sends the participation code using `X-Research-Enrollment`.
- S3. Remove extension authentication branches based on `enrollmentOnly`, `enrollment_only`, API origin, or entered key type.
- S4. `POST /api/research/sessions` must accept only a valid participation code.
- S5. `X-Research-Key` must be rejected for `POST /api/research/sessions`, even when it contains the valid researcher key.
- S6. Remove the `RESEARCH_REQUIRE_ENROLLMENT` compatibility mode. Enrollment must always be required when research capture is enabled.
- S7. Require `RESEARCH_ENROLLMENT_KEY` in the research API configuration and keep it distinct from `RESEARCH_API_KEY`. Missing, invalid, or identical secrets must fail closed without exposing their values.
- S8. Preserve `RESEARCH_API_KEY` exclusively for privileged investigator/operator endpoints: record export, investigator-mediated record deletion, expired-record purge.
- S9. A participation code must never authorize those privileged endpoints.
- S10. Do not move credentials into query parameters or request bodies. Do not weaken the existing API-origin validation, HTTPS requirements for remote APIs, consent checks, session capabilities, storage protections, or retention behavior.
- S11. Do not persist or log the participation code in extension storage, API records, errors, or console output.
- S12. Update tests and documentation, including the fail-closed migration order, and finish with an independent security-focused verification. Risk item 2 (authentication and privileged credential separation).

Acceptance criteria and checks:

- S1/S2/S3: popup HTML, view model, and browser E2E assert the exact label; the controller always sends `X-Research-Enrollment` without an authentication-mode branch. No separate extension-asset absence scan is required.
- S4/S5: API unit tests prove enrollment starts succeed and `X-Research-Key` starts (including the valid researcher key) return 401.
- S6/S7: missing, invalid and identical enrollment configuration return 503 without echoing values.
- S8/S9: existing privileged-route tests keep passing and enrollment headers/values still return 401 on export, investigator delete and purge.
- S10/S11: no request bodies/query strings gain credentials; storage shape unchanged; existing consent/completion/withdrawal/retry/receipt tests stay green.
- S12: E2E local and remote-origin scenarios use the single enrollment path. Docs describe a fail-closed rollout: 1) provision a distinct `RESEARCH_ENROLLMENT_KEY`, 2) deploy the enrollment-only API, accepting that older extensions cannot start sessions during this window, 3) deploy the unified extension, 4) remove the now-ignored `RESEARCH_REQUIRE_ENROLLMENT` setting. Rollback must not restore the legacy API with capture enabled. Documentation must not claim that absent production deployment artifacts exist in this checkout.

## Tasks

- T1. API fail-closed enrollment configuration and participant-only enrollment auth; RED then GREEN in `api/tests/unit/research/test_capture.py` and `api/app/research/router.py`. Status: completed. RED: 3 targeted failures (legacy `X-Research-Key` start returned 201, missing enrollment returned 200, normal mount accepted the researcher key). GREEN: 24 passed focused.
- T2. Extension controller always sends `X-Research-Enrollment`; remove `enrollmentOnly`/`enrollment_only` branches; RED then GREEN in `browser-extension/tests/research-background.test.cjs` and `research-background.js`. Status: completed. RED: 2 targeted failures showed `X-Research-Key`. GREEN included in 73 passed.
- T3. Popup always labels the participation code; static HTML and view model; RED then GREEN in `browser-extension/tests/research-popup.test.cjs`, `popup.html`, `research-popup.js`. Status: completed. RED: label mismatch. GREEN included in 73 passed; audit follow-up corrected the exact label to `Código de participación` and removed the separate static asset scan.
- T4. E2E and Compose configuration contracts use one enrollment path; `e2e/tests/test_research_capture.py`, `e2e/tests/test_compose_configuration.py`, `compose.yaml`/`api/.api.dev.env`. Status: completed. RED: Compose research contract lacked `RESEARCH_ENROLLMENT_KEY`. GREEN: 2 Compose research tests passed; 15 browser E2E tests passed including remote origin.
- T5. Documentation and migration order across participant, developer, architecture, deployment, protocol, and risk guides. Status: completed. The follow-up corrected the API-first rollout and rollback, exact field label, and claims about absent production artifacts.
- T6. Focused and full suites plus security-focused verification and final diff inspection. Status: completed for the local change, with evidence in L4-L5 and L7. The independent verifier's `pass` in L5 applies to the authentication candidate before the UI/documentation follow-up; L7 records the later checks separately and does not claim a second independent verdict.

## Log

### L1 — user request (verbatim)

Implement a security-focused authentication unification for the research-capture browser extension.

Repository:
C:\Users\stive\Documents\contextual-pii-anonymizer

## Objective

The browser extension must use exactly one participant-facing authentication flow in every environment: a study participation code.

The privileged researcher/operator key must never be entered into, stored by, or transmitted from the browser extension.

## Current verified behavior

- `browser-extension/extension/research-background.js` chooses between:
  - `X-Research-Enrollment`
  - `X-Research-Key`
- `browser-extension/extension/research-popup.js` dynamically shows:
  - `Código de participación del estudio`
  - `Clave local del investigador`
- `api/app/research/router.py::participant` accepts the researcher key as a legacy fallback when enrollment is not required.
- `RESEARCH_API_KEY` is also used by privileged investigator operations such as export, purge, and investigator-mediated deletion.

## Required behavior

1. The extension must always display:
   `Código de participación del estudio`

2. The extension must always send the participation code using:
   `X-Research-Enrollment`

3. Remove extension authentication branches based on:
   - `enrollmentOnly`
   - `enrollment_only`
   - API origin
   - entered key type

4. `POST /api/research/sessions` must accept only a valid participation code.

5. `X-Research-Key` must be rejected for `POST /api/research/sessions`, even when it contains the valid researcher key.

6. Remove the `RESEARCH_REQUIRE_ENROLLMENT` compatibility mode. Enrollment must always be required when research capture is enabled.

7. Require `RESEARCH_ENROLLMENT_KEY` in the research API configuration and keep it distinct from `RESEARCH_API_KEY`. Missing, invalid, or identical secrets must fail closed without exposing their values.

8. Preserve `RESEARCH_API_KEY` exclusively for privileged investigator/operator endpoints:
   - record export
   - investigator-mediated record deletion
   - expired-record purge

9. A participation code must never authorize those privileged endpoints.

10. Do not move credentials into query parameters or request bodies. Do not weaken the existing API-origin validation, HTTPS requirements for remote APIs, consent checks, session capabilities, storage protections, or retention behavior.

11. Do not persist or log the participation code in extension storage, API records, errors, or console output.

## Expected implementation areas

Inspect before editing, but expect changes in:

- `browser-extension/extension/research-background.js`
- `browser-extension/extension/research-popup.js`
- `browser-extension/extension/popup.html`
- `browser-extension/tests/research-background.test.cjs`
- `browser-extension/tests/research-popup.test.cjs`
- `api/app/research/router.py`
- `api/tests/unit/research/test_capture.py`
- `e2e/tests/test_research_capture.py`
- Compose/environment configuration tests
- Research-capture and local-development documentation

Update additional files only when required by verified references.

## Test-first requirements

Use RED → GREEN → REFACTOR where deterministic tests exist.

Add or update tests proving that:

- The popup always shows the exact label `Código de participación`.
- The extension always sends `X-Research-Enrollment`.
- The extension never sends `X-Research-Key`.
- A valid participation code can start a session locally and remotely.
- Missing or incorrect participation codes return an authorization failure.
- The researcher key cannot start a session.
- The participation code cannot export, purge, or delete investigator-managed records.
- The researcher key retains its existing privileged operations.
- Missing enrollment configuration fails closed.
- Enrollment and researcher secrets must be distinct.
- Existing consent, completion, withdrawal, retry, and receipt behavior remains unchanged.
- Local and remote E2E capture flows still work through the single enrollment path.

Run the focused extension and API tests, then the applicable full suites. Report every command and its observed result.

## Documentation and migration

Update documentation so local development generates and uses a separate participation code. Remove instructions telling users to paste the researcher key into the extension.

Document a fail-closed migration order:

1. Configure a distinct `RESEARCH_ENROLLMENT_KEY` in every environment.
2. Deploy the unified extension flow.
3. Remove the legacy researcher-key fallback and obsolete configuration flag.

Do not provide a silent fallback during migration.

## Security verification

Before completion, inspect the final diff and verify:

- `RESEARCH_API_KEY` is not referenced by participant-facing extension code.
- No privileged key is bundled into extension assets.
- No authentication value is written to logs or persistent extension state.
- Administrative authorization boundaries remain intact.
- No unrelated public API behavior changed.

This is a high-risk security change: Risk item 2. After the implementation’s own tests, perform an independent security-focused verification.

Do not commit, push, or publish unless explicitly requested.

Finish with:
- Files changed
- RED/GREEN evidence
- Test results
- Security invariants verified
- Remaining risks or skipped checks
- `Risk: item 2 (authentication and privileged credential separation)`

### L2 — baseline evidence (2026-11-16)

- `node --test browser-extension/tests/*.test.cjs`: 71 passed, 0 failed.
- `uv run --directory api --no-sync pytest -q tests/unit/research/test_capture.py`: 23 passed.
- `uv run --directory e2e --no-sync pytest -q tests/test_research_capture.py -k campus`: 1 passed, 14 deselected. The test copy patches the protection URL to the research API, so its loopback origin equals the extension's local origin; remote-origin validation stays intact.

### L3 — implementation decisions

- Keep privileged `X-Research-Key` handling on `researcher()` only; remove it entirely from `participant()` so the header cannot authorize a session even with the valid key.
- Make `configuration()` require `RESEARCH_ENROLLMENT_KEY` unconditionally and compare it to `RESEARCH_API_KEY`; both missing or identical fail with 503.
- Keep the extension's `apiOrigin` routing (local vs packaged remote) but delete every authentication branch derived from it.
- Keep the request body and session capability flow unchanged.
- Add a regression test scanning `browser-extension/extension` for `X-Research-Key` so the privileged header cannot re-enter participant-facing assets.
- No commits: the user explicitly forbade them.

### L4 — verification evidence (2026-11-16)

- `node --test browser-extension/tests/*.test.cjs`: 73 passed, 0 failed.
- `uv run --directory api --no-sync pytest -q tests/unit/research/test_capture.py`: 24 passed.
- `uv run --directory api --no-sync pytest -q`: 73 passed, 2 skipped (PostgreSQL-dependent), 1 pre-existing Starlette/httpx warning.
- `uv run --directory e2e --no-sync pytest -q tests/test_research_capture.py`: 15 passed, including the remote-origin (`campus`) scenario.
- `uv run --directory e2e --no-sync pytest -q -m "not integration"`: 22 passed, 6 deselected.
- `uv run --directory e2e --no-sync pytest -q tests/test_compose_configuration.py -k research`: 2 passed, 2 deselected.
- `uv run --directory e2e --no-sync pytest -q tests/test_compose_configuration.py`: 2 failed, 2 passed. One failure is the new enrollment contract before the `.api.dev.env` fix (now green in the `-k research` run). The remaining failure is pre-existing and environment-dependent: `test_default_stack_starts_converter_with_extension_configuration` reads the untracked local `browser-extension/backend/.env` (real extension ID) instead of the synthetic interpolation value; our diff does not touch that assertion.
- `uv run --directory api --no-sync ruff check app/research/router.py tests/unit/research/test_capture.py`: passed.
- `node --check` for both extension scripts: passed.
- `ruff` on the E2E file reports only pre-existing E501/format findings in lines not changed by this task; the API file is formatted.

### L5 — independent verification and correction (2026-11-16)

- First verifier verdict: `blockers`. Blocker: `docs/project/experimentacion/research-study/protocol.md:46` still instructed moderators to enter the researcher key in the extension. Advisories only: pre-existing broken links to the removed campus guide, committed local dev defaults, unused `api_origin` status field.
- Correction: changed the run sheet to enter the study participation code; added `e2e/tests/test_research_documentation.py`; added durable API query/body and archive-secret probes plus an extension persistence/body probe.
- Recheck verdict: `pass`, no remaining blockers; docs guard observed 1 passed.
- Post-correction suites: extension 74 passed; API full 75 passed, 2 skipped; E2E non-integration 23 passed, 6 deselected; Compose 3 passed, 1 pre-existing environment-dependent failure.
- Final scan: no `RESEARCH_API_KEY`, `X-Research-Key`, `enrollmentOnly` or `enrollment_only` in `browser-extension/extension`; no `console.` in the research scripts.

### L6 — audit follow-up (2026-11-16)

- Exact UI copy changed to `Código de participación` in the popup, view model, E2E assertion and guides that quote the field.
- Removed the static extension-asset scan and the documentation scan file; behavior tests for enrollment, invalid codes, archive non-persistence, extension state non-persistence and administrative authorization remain.
- Rewrote migration/rollback to deploy the enrollment-only API before the extension, accept older extensions failing closed with 401, and prohibit rolling back to the privileged-key fallback. Verified against `router.py`: invalid/missing enrollment 401, invalid config 503, disabled capture 404, `RESEARCH_REQUIRE_ENROLLMENT` ignored.
- Corrected documentation links/claims for absent `research-campus-deployment.md`, `compose.research.yaml` and `deployment/research/prepare.py`; replaced them with explicit "not included in this checkout" statements. No production infrastructure was invented.

### L7 — final follow-up evidence and plan reconciliation (2026-11-16)

- The follow-up agent reported: extension 73 passed; focused API 26 passed; full API 75 passed and 2 skipped; E2E non-integration 22 passed and 6 deselected, including 15 research browser scenarios; Compose research checks 2 passed; full Compose 3 passed and 1 pre-existing environment-dependent failure caused by the untracked `browser-extension/backend/.env`; local Markdown link check found 0 broken links in 50 files; `git diff --check`, API Ruff, and popup syntax check passed. Docker integration and production deployment were not tested.
- A subsequent read-only audit independently reran the full extension suite (73 passed) and `git diff --check` (no whitespace errors), confirmed the exact popup label, the API-first migration and rollback instructions, and the absence of the former campus-artifact links. The auditor could not reproduce Python checks in this sandbox; their results above remain the follow-up agent's reported evidence, not an independently observed second run.
- Reconciled current acceptance criteria and T5-T6 with the implemented follow-up. L1-L5 retain historical requests and earlier test results; they are not instructions to restore the removed asset scan or the obsolete extension-first migration.
- The local authentication objective is implemented. This checkout still lacks a production collector, TLS/client-trust setup, and participant packaging; production readiness is outside this completed local change.

