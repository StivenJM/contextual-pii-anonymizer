# Integration test harness for the browser extension

Branch: `test/platform/add-integration-test-harness`
Delivery strategy: `ask-on-risk` (sliced into behaviour units; chained PRs only if the branch grows into independent deliverables).
Test runner: `pytest` (Python) for the harness; `pytest`/`uv` for the API.

## Specs

S1. The harness loads the real browser extension from a patched copy (user option 1) and drives it in Chromium. The extension sources under `browser-extension/extension/` are never modified.
S2. The harness proves the attachment pipeline: file picker and drag-and-drop interception, Markdown conversion, Markdown cleanup, middleware protection call, and replacement of the original file with the protected text file.
S3. The harness proves the disable switch: with the extension deactivated, the page receives the original file and no backend call happens.
S4. The harness proves failure containment: when conversion or protection fails, the page never receives the original file.
S5. The harness provides a full-system tier marked `integration`: real Privacy Middleware, real conversion service, PostgreSQL, and a deterministic inference stub. It requires Docker.
S6. At least 30 papers per investigation support the decisions, and they are recorded with identifiers in the architecture decision page.
S7. Documentation follows the repository documentation contract: architecture decisions under `docs/architecture/`, executable procedures under `docs/guides/`, navigation indexes updated.
S8. The development `compose.yaml` is not modified; the test stack is additive.
S9. Tests are deterministic: explicit wait conditions and bounded negative assertions, no retry loops, no arbitrary sleeps used as synchronization.

## Tasks

| ID | Spec | Route | Status |
|---|---|---|---|
| T1 | Research corpora and decision record | inline | done |
| T2 | Patched extension build and browser fixtures | inline | done: `0c0d296` |
| T3 | Fake chat pages and HTTP stubs | inline | done: `0c0d296` |
| T4 | Attachment, toggle, and failure tests (no Docker) | inline | done: `b0d5beb` |
| T5 | Test compose stack, inference stub, converter image | inline | done: `43af0ed` |
| T6 | Full-system integration test | inline | done: `43af0ed` |
| T7 | Documentation and navigation indexes | inline | done |
| T8 | Verification and work-unit commit | inline | done |

## Log

L1 (user request, verbatim):
"por ahora me gustaría la opción 1 para las pruebas de integración, igual como verás ya hay un docker que es para desarrollo, así que hace falta que hagas la parte completa para las pruebas de integración, y para eso no olvides que para que veas la mejor manera de hacer eso consultes a papers por lo menos quiero 30 papers y vayas tomando las mejores decisiones, también documenta todo de acuerdo a los parámetros de documentación que estamos siguiendo, y también recuerda que yo solo te pido esta tarea pero realmente siempre en el camino suelen surgir muchos problemas y detalles que tal vez yo ni los imagino y por eso tienes que realizar investigación primero antes de resolver esos detalles para que tomes las mejores decisiones, para cada investigación quiero por lo menos 30 papers y como te digo que todas las decisiones tomadas y documentación en general esté bien documentado donde debe."

L2. Scope fixed by the previous turn: option 1 (patched copy), no real chat sites, no Firefox coverage in this unit. Prompt-level interception stays out of scope because the extension does not implement it.
L3. Documentation language: the repository documentation contract requires English for repository documentation, so new pages are English and existing Spanish pages keep their language. Recorded as an accepted inconsistency with the surrounding corpus.
L4. Research executed through OpenAlex (2026-10-28) with four investigation topics: extension/E2E testing, test doubles and integration architecture, test flakiness and CI reliability, and privacy/PII evaluation. Corpora and decisions are recorded in `docs/architecture/frontend/browser-extension/decisions/verificacion-automatica.md`.
L5. Decisions taken from evidence (summary): Playwright with bundled Chromium; generic boundary page instead of real sites; two tiers with an explicit stub seam; deterministic waits; isolated profile per session; privacy leak oracle on the delivered file; compose overlay instead of a second orchestration tool.
L6. Verification evidence (2026-10-28):
- `uv run --directory e2e ruff check .` -> all checks passed; `ruff format --check .` -> 12 files already formatted.
- `uv run --directory e2e pytest -q -m "not integration"` -> 6 passed in 14.86s.
- `uv run --directory e2e pytest -q tests/test_system_integration.py -m integration` -> 1 passed in 279.05s (first run, image build included).
- `uv run --directory e2e pytest -q -m integration` -> 1 passed in 96.56s (cached images, after the fixture refactor).
- `uv run --directory e2e pytest -q` -> 7 passed in 161.22s.
- `docker compose -f compose.test.yaml config --quiet` -> 0; `docker compose -f compose.yaml config --quiet` -> 0.
- Toolchain observed: Playwright 1.64.1 with bundled Chromium, Docker 29.8.2, Python 3.14.8 host.
- Over-budget note: the harness exceeds the 400-line heuristic per slice once generated lockfile lines are included; it was sliced by behavior instead of by file type, and no test or doc was removed to fit the budget.
- Documentation language: new pages are English per the documentation contract; the pre-existing pages remain Spanish, so the corpus is mixed by design until a dedicated translation unit exists.
