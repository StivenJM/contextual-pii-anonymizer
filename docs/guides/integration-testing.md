# Integration testing of the browser extension

This guide runs the automated integration suite for the browser extension and the
Privacy Middleware. The suite loads the real extension into Chromium, drives it against
local pages that mimic a chat attachment input, and asserts what the page receives.

The suite has two tiers:

| Tier | Command | Needs Docker | Time |
|---|---|---|---|
| Fast (default) | `pytest -m "not integration"` | No | Seconds after the browser starts |
| Full system | `pytest -m integration` | Yes | Minutes on the first run (image build) |
| Debug | add `--headed`, `--slowmo MS`, or `--pw-trace` | No | Interactive |

## What each tier proves

| Test | Proves |
|---|---|
| `test_file_picker_converts_then_protects` | The picker path converts, cleans, protects, and replaces the file |
| `test_converted_file_is_not_intercepted_again` | The anti-loop check prevents reprocessing |
| `test_drop_zone_converts_then_protects` | The drop path reaches the same outcome without a file input |
| `test_disabled_extension_delivers_the_original_file` | The switch disables interception and no backend call happens |
| `test_conversion_failure_keeps_the_file_away_from_the_page` | A conversion failure never leaks the original file |
| `test_protection_failure_keeps_the_file_away_from_the_page` | A protection failure never leaks the original file |
| `test_full_system_protects_a_docx_attachment` | The real middleware pseudonymizes the extracted text before the page sees it |

The full-system test asserts three leak conditions: the fixture email, the fixture person
name, and the original document never reach the page. It also asserts the pseudonymized
domain produced by the real de-identification engine, so a silent fallback to the
original text fails the test.

## Prerequisites

- Python 3.12 or newer and `uv`.
- Playwright's Chromium: `uv run --directory e2e playwright install chromium`.
- Docker with Compose, only for the full-system tier.

An installed Google Chrome cannot be used for extension testing: branded builds since
Chrome 137 ignore the flags that side-load an unpacked extension. The harness always uses
the Chromium build installed by Playwright.

## Run the fast tier

```powershell
uv sync --directory e2e
uv run --directory e2e playwright install chromium
uv run --directory e2e pytest -v -m "not integration"
```

The tier starts two HTTP doubles and one static site on free local ports, builds a
patched copy of the extension, launches Chromium with a fresh profile, and closes
everything on exit.

## Run the full-system tier

```powershell
uv run --directory e2e pytest -v -m integration
```

The tier creates a Compose project named `cpa-e2e-<random>`, builds the API image and
the conversion image, starts PostgreSQL and the inference stub, applies migrations, and
exposes the API and conversion service on free local ports. The project, its containers,
and its database are removed with `down -v` when the test ends. The development
`compose.yaml` and its volume are never touched.

## Debug a failing test

All debugging stays off by default. Turn on only what the session needs:

```powershell
# Watch the browser while one test runs.
uv run --directory e2e pytest -v -k test_drop_zone --headed

# Slow every browser operation so the flow is followable.
uv run --directory e2e pytest -v -k test_drop_zone --headed --slowmo 500

# Record a trace for failing tests and open it afterwards.
uv run --directory e2e pytest -v --pw-trace=retain-on-failure
uv run --directory e2e playwright show-trace e2e/test-results/<name>.zip

# Step through with the Inspector (interactive; it waits for you).
$env:PWDEBUG = "1"
uv run --directory e2e pytest -v -k test_drop_zone
Remove-Item Env:PWDEBUG
```

| Flag | Effect |
|---|---|
| `--headed` | Shows the Chromium window; `PWDEBUG=1` implies it |
| `--slowmo MS` | Slows browser operations by `MS` milliseconds |
| `--pw-trace=off\|on\|retain-on-failure` | Records a per-test trace; `off` is the default |

Two naming notes:

- The trace flag is `--pw-trace`, not `--trace`, because pytest already owns `--trace`.
- Playwright's `--ui` mode belongs to the Node test runner. It does not exist for
  Python. `--headed` plus `PWDEBUG=1` and the trace viewer cover the same debugging
  needs here; see decision D9 in the decision page.

### Artifact handling rule

Traces serialize DOM snapshots, network headers, cookies, and request bodies. In this
repository the suite only builds synthetic fixtures, and the archives land in
`e2e/test-results/`, which is git-ignored. Do not enable tracing for a test that uses a
real document, and do not upload a trace recorded from real data.

## How the extension copy is built

The product sources under `browser-extension/extension/` are never modified. The harness
copies them to `e2e/.build/extension-<name>/` and changes exactly five things:

1. The conversion endpoint.
2. The protection endpoint.
3. The shared token, so it matches the doubles and the test stack.
4. The supported-site allowlist, so the local page is eligible.
5. The manifest permissions, so the local origins are reachable.

The browser factory also accepts optional additional_origins for a test that needs a
second local double (the research two-tab isolation case). These are added only to
the manifest of the generated test copy; they do not change delivered permissions
or the original five replacement-count checks. The research cases additionally use
the [real standalone model-free API](research-capture.md), without a cloud provider.

Each replacement records its expected and observed count. If the extension changes shape,
the build fails instead of testing a stale assumption. Any other edit to the extension
will surface here and must be reviewed deliberately.

## Ruff

```powershell
uv run --directory e2e ruff check .
uv run --directory e2e ruff format --check .
```

## Troubleshooting

| Symptom | Cause | Action |
|---|---|---|
| `Docker is not available` skip | Docker daemon is not running | Start Docker Desktop and rerun |
| `content.js was not registered` | The extension failed to load | Check the build output under `e2e/.build/`; confirm the Chromium build is installed |
| Extension disabled after a reload | Chromium requires developer mode for reloads | Restart the session; do not call `chrome.runtime.reload()` in a test |
| Full-system test fails while the stack starts | Image build or migration error | Run `docker compose -f compose.test.yaml -p cpa-e2e-debug up --build` and read the logs |
| Port already in use | A fixed port is configured by hand | Do not fix the ports; the harness picks free ones |

## Boundaries

- Real chat sites stay manual. The suite verifies the boundary, not the site's DOM and
  not its anti-bot behavior.
- Firefox stays manual. Playwright cannot load extensions in Firefox; the extension keeps
  its cross-browser manifest, but that path is not covered by this suite.
- Ordinary protection still targets attachments. Separate opt-in research cases cover
  typed submission capture and rendered replies against synthetic chat fixtures,
  including an enrollment-only campus-mode API. This does not validate live provider DOM adapters.
- The inference stub is deterministic by design. It does not measure model quality; it
  preserves the contract the middleware consumes.

## Related

- [University-network research deployment](research-campus-deployment.md): production
  Docker/TLS rehearsal, exact-IP extension packaging and participant trust installation.
  Its CLI/Docker-only tests do not launch the inherited browser fixture. The optional
  `research_origin` test-copy override exercises enrollment over loopback without changing
  source configuration or the five original replacement-count checks.

- [`Automated verification of the browser extension`](../architecture/frontend/browser-extension/decisions/verificacion-automatica.md):
  evidence base and rationale for every decision above.
- [`Local infrastructure with Docker`](infraestructura-local-con-docker.md): development
  environment, which this guide does not replace.
