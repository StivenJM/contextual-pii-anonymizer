# Run research capture without the model

The implementation is a local pilot, not institutional approval for identifiable-data fieldwork. Consult the validation and readiness limits below before use.

Use the independent local research API and the existing browser extension. This guide does not deploy a service, create a Google Form, recruit students or authorize collection of real personal data.

For the confirmed student-owned-computer topology, follow [university-network deployment](research-campus-deployment.md). It adds an enrollment-only code, trusted private-IP HTTPS and a generated extension copy; do not distribute the local researcher key to students.

## Prepare the local API

From the repository root in PowerShell:

~~~powershell
uv sync --directory api --frozen
$env:RESEARCH_ENABLED = "true"
$env:RESEARCH_API_KEY = (& api\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))").Trim()
$env:RESEARCH_STORAGE_PATH = Join-Path (Get-Location).Path "workspace\research\capture.sqlite3"
$env:RESEARCH_PROTOCOL_VERSION = "research-v1"
$env:RESEARCH_RETENTION_DAYS = "30"
uv run --directory api --no-sync python -m uvicorn app.research.application:app --host 127.0.0.1 --port 8000 --no-access-log
~~~

The first command installs locked development dependencies and may contact package registries. The last command runs the local listener in the foreground; it does not start PostgreSQL, BentoML, Docker or the converter. Stop with Ctrl+C. Port 8000 must be free; do not stop an unrelated process automatically. The ordinary compose.yaml and its original model-backed behavior are unchanged.

Keep the key in the operator's secure setup channel and paste it into the extension's password field. Do not print/send it to an AI chat or put it in Forms. It is not saved by the popup after starting. The extension does retain a different session capability for retry/withdrawal. Configure approved retention before real use; “30” is a pilot example, not institutional approval.

The example archive is under the existing ignored workspace/ directory. Do not move real archives into tracked paths. The API additionally requires an absolute path. Use institution-approved encrypted local storage and restrict permissions; the application itself does not provide at-rest encryption. For persistent supervised operation, set these environment variables in the approved service account's secret configuration, not in committed .env files.

Open [the local API documentation](http://127.0.0.1:8000/docs). The separate app intentionally exposes research routes only; `/api/research/health` checks collector configuration/archive access, while the normal /api/health and /api/interactions/protect are not part of that entry point. The same /api/research router is also mounted by the ordinary main app, but that app still has its usual PostgreSQL startup requirement.

## Extension: synthetic rehearsal

1. Reload browser-extension/extension as an unpacked extension in a dedicated Chromium/Chrome test profile. Existing host permissions already cover the three supported commercial sites and loopback API.
2. Open a fresh, empty supported chat, without personal history or loaded attachments. Confirm the current editor/send/reply adapter manually before inviting students. This work did not log into or operate a real provider account.
3. Open the extension popup. In **Captura para investigación (solo texto)**, enter **Clave local del investigador** and the protocol. The research interface uses Spanish labels/messages; canonical technical documentation remains English. Read the raw-collection warning, check consent explicitly, and leave optional training permission unchecked unless separately agreed.
   These setup/consent fields are disabled once the session starts: changing a checkbox cannot silently amend an already stored agreement. Use **Descartar / retirar sesión** and the approved researcher process for a consent change.
4. Click **Iniciar en esta pestaña**. Confirm the in-page recording indicator. The attachment-protection preference is retained; protection is paused only on that selected tab while capture is recording/paused. Other tabs retain their previous behavior.
   The popup shows progress/errors beside the start action. A failed start keeps the current form inputs; successful activation clears the key. The key is not persisted in browser storage, and closing the popup discards transient inputs. History rejection and a missing editor have separate messages. An empty editor may lack Send until typing; startup permits this, but actual submission is still blocked unless a supported visible enabled send control exists and local storage acknowledges the prompt.
5. Set **Identificador de tarea** to A and click **Asignar tarea**, then use the appropriate next task IDs. Send only fictional text. The supported send waits for local buffering; replies are observed as rendered snapshots. Wait for the reply to finish before changing tasks or finishing.
6. Click **Finalizar y guardar / reintentar**. Only a confirmed API response displays the saved identifier. Use **Copiar identificador** and keep it somewhere safe; paste it into the last item of the approved study form.
7. On failure, keep the extension/profile installed and retry. Do not clear browser storage or repeat the activity just to get a new code. A pending session stops collecting; later prompts are outside that frozen session.

A closed/reloaded tab can be saved as INTERRUPTED; report it to the researcher. A recording session is bound to one document, not all browser activity. Unsupported attachment/voice/image paths are not captured. Empty sessions must be discarded rather than falsely “saved.”

ChatGPT editor detection also recognizes the supplied `textarea[data-mobile-composer-prompt]` markup, without depending on generated CSS classes or broadening detection to every textarea. Local fixtures exercise activation, click/Enter submission and exact-text archival with that editor; they do not establish compatibility with the live layout's send controls, history or reply markup. Rehearse those independently before participant collection.

## Access, withdrawal and retention

- The receipt is 32 case-sensitive base64url characters. It identifies a record; it cannot read it without the researcher key.
- Authorized staff can retrieve one record with GET /api/research/records/{receipt_id} and X-Research-Key. Protect exports exactly like the original archive. No live form sync or public response dashboard is implemented.
- **Descartar / retirar sesión** asks for confirmation, stops collection and clears raw local text immediately. It uses the session capability to delete the current session or last saved record; if the API is unavailable, only deletion metadata/capability is retained and the popup requests a retry. Ordinary protection resumes during pending upload/withdrawal. Forms responses, external chatbot history, backups and trained models need the separate [linkage/withdrawal procedure](../project/experimentacion/research-study/instruments.md).
- For an approved investigator-mediated withdrawal, DELETE /api/research/records/{receipt_id} with X-Research-Key deletes the archived record by code. Never expose this key to a participant page or form.
- Expired sessions cannot be completed or exported. Authorized operators must schedule POST /api/research/purge-expired using X-Research-Key and align backup expiry. There is no silently installed scheduler. Validate the deleted count; never assume expiry already erased backup media.
- The popup retains only the last receipt/capability after a successful save, not the raw events. Copy it before completing another session. The institution must maintain its restricted linkage/withdrawal records.

## Offline de-identification replay

Collection never calls the model. Later, authorized researchers may use the ordinary API environment with its existing database, configuration and inference service to evaluate eligible archived participant text. Fetch the consented record through researcher authorization, then POST {"text": "a held-out submitted prompt"} to /api/interactions/protect in that environment, preserving a separate output/run manifest. Do not send the identity form or session capabilities to the model.

Use [the analysis plan](../project/experimentacion/research-study/analysis-plan.md): participant-disjoint splits, independent gold labels, frozen models/configuration and separate utility/error reporting. This guide does not train a model or automatically send a dataset anywhere.

## Verification commands

~~~powershell
# From repository root; tests use synthetic fixtures only.
uv run --directory api --no-sync pytest -q
node --test browser-extension/tests/*.test.cjs
uv run --directory e2e --no-sync pytest -q -m "not integration"
# Optional pre-existing full-system regression; needs Docker and builds images.
uv run --directory e2e --no-sync pytest -q -m integration
~~~

The research browser cases start a real model-free API process on a free loopback port and drive the real extension in bundled Chromium against synthetic local chats. They verify normal finalization, conversation changes, a lost response after API commit, a local quota failure before send, reload recovery and simultaneous protection in another tab. Research collection makes zero converter/protection requests; the deliberate other-tab regression makes one of each to prove that the original path still works elsewhere. No cloud chatbot is called. Install the e2e dependencies/Chromium as described in [integration testing](integration-testing.md).

## Observed validation

Final functional verification on 2026-10-30:

The table below records the earlier local implementation milestone. After the campus adaptation, the API suite passed **70 tests with 2 local PostgreSQL skips**, Node passed **14**, and non-container browser/preparation checks passed **21 with 3 Docker cases deselected**. A separate production Docker/TLS rehearsal also passed. See [campus verification](research-campus-deployment.md#verification-and-limits) for the proof boundary; live university/provider readiness is not established by local tests.

| Check | Observed result |
|---|---|
| API suite | 66 passed, 2 local PostgreSQL-dependent skips; 1 pre-existing Starlette/httpx TestClient deprecation warning |
| Node controller/isolation suite | 13 passed |
| Complete Chromium suite | 14 passed, including all six research cases and two Docker integration cases |
| Final consent/UI recheck | 12 passed, 2 Docker cases deselected; the unchanged container paths had already passed the complete suite |
| Real PostgreSQL/API contracts | Executed successfully inside the isolated Docker API container by the integration suite; the local skips are not counted as passes |
| Baseline differential vs eccf825 | Identical outcomes in 4 state, 4 attachment-message and 4 Markdown-normalization checks using an external temporary copy |
| Changed Python surfaces | Ruff lint and check-only formatting passed |
| JavaScript | Background and all three research scripts passed parse checks |
| Documentation | 19 changed/new Markdown pages checked, zero missing local targets; 32 unique bibliography keys with balanced BibTeX braces |

The popup was also rendered with synthetic data and inspected visually. No independent AI worker/reviewer was launched, following the user's explicit inline-only instruction; no native review approval is claimed.

During development, test setup initially hit restricted temporary-directory access, an extension-page string wait conflicted with CSP, and an additional two-tab test double lacked a host permission in the test copy. These were corrected in test setup without weakening product CSP/permissions. A real conversation-history mixing defect and global/pending-state protection isolation defects were reproduced with regression tests and fixed. The final results above supersede those intermediate failures.

Unverified until separately authorized/performed: real-provider adapters and current cloud UI behavior, Firefox, actual university deployment/client trust/routing/encryption/backup policy, live Google Forms linkage, actual students and trained-model comparisons. The local commands above still target one workstation/profile. Separate [campus deployment artifacts](research-campus-deployment.md) prepare the shared private-IP collector and endpoint-specific extension; they do not automatically deploy it on a university computer.

## Troubleshooting

| Symptom | Action |
|---|---|
| 404 on research routes | Confirm RESEARCH_ENABLED=true in the running process; normal health paths do not exist in the standalone app |
| 503 configuration | Use a >=32-character key, absolute archive path and retention days between 1 and 365 |
| 401 on session creation/export | Check the setup key, never paste it into the chatbot |
| Start remains in starting | Authorization or activation was interrupted; discard that setup and start a new empty session |
| Adapter unavailable | Use a fresh conversation and check current site selectors; stop the pilot if capture cannot be verified |
| Pending / API unreachable | Start the same local API/archive and retry the frozen upload; do not delete local state |
| Withdrawing / API unreachable | Raw local text is already cleared; retry **Descartar / retirar sesión** so the retained capability can finish API deletion |
| 409 completion conflict | Preserve the local copy; investigate mismatch, never overwrite the saved record |
| Local limit reached | Stop/save; the supported send is blocked rather than silently dropping text |
| Receipt lost | Contact approved study staff; do not search other students' records or guess a code |

[Plan](../project/experimentacion/research-capture-plan.md) · [Architecture/decisions](../architecture/backend/privacy-middleware/research-capture.md) · [Study kit](../project/experimentacion/research-study/README.md)

