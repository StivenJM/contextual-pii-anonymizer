# Install the extension and start the development system

Windows/PowerShell developer guide. Install the browser extension first, then start **only the services required by the flow you are testing**. Use fictional data throughout this procedure. This guide does not authorize a university deployment or real-student collection.

## 1. Install the browser extension first

The extension is plain JavaScript: this installation needs no `npm install`, JavaScript build, Docker service or running model.

1. Open Google Chrome in a dedicated development profile. Avoid a profile containing personal chat history or unrelated sensitive accounts.
2. Open `chrome://extensions` and enable **Developer mode**.
3. Click **Load unpacked** and select **`browser-extension/extension` inside this repository**. Select the folder containing `manifest.json`, not the repository root, `browser-extension/backend`, or an `e2e/.build` test copy.
4. Confirm that **PDF Middleware** appears enabled. Pin its toolbar icon if useful.
5. Copy the extension **ID** shown on the extensions page. The converter uses this ID for its allowed browser origin; installing first avoids guessing that value.
6. Open the popup. The existing attachment interface and separate **Captura para investigación (solo texto)** section should be present. Its participant-facing controls and messages are in Spanish. Installing the extension alone does not start either backend and does not activate research capture.
7. After loading/reloading the extension, refresh any already-open supported chat tab. For capture tests, start a fresh empty conversation.

The manifest covers ChatGPT, Claude and Gemini. Local synthetic Chromium tests do not prove the current live interfaces work; manually rehearse each intended provider before fieldwork. Firefox and other browsers are not the validated route in this guide. If university policy disables unpacked extensions, obtain IT's approved installation route rather than bypassing that policy.

After editing extension JavaScript or its manifest, return to `chrome://extensions`, click **Reload** on its card, then refresh the chat tab. A browser reload is not a data migration: finish or discard a research session before changing extension/configuration. Do not remove the extension or clear its storage while an upload/withdrawal is pending.

If Chrome reports a load error, inspect the extension card's error details before proceeding. Keep its service-worker console free of real text/credentials; a screenshot of a successful installation is not proof that the backend or site adapter works.

Official installation procedure: [Chrome: load an unpacked extension](https://developer.chrome.com/docs/extensions/get-started/tutorial/hello-world#load-unpacked).

## 2. Understand the processes before starting them

| Component | Source | What it does | Default local address |
|---|---|---|---|
| Browser extension | `browser-extension/extension/` | Existing attachment workflow plus explicitly enabled text research capture | Browser toolbar |
| Attachment converter | `browser-extension/backend/` | Converts supported PDF/Office attachments to Markdown | `http://localhost:5000/convertir` |
| Original privacy API | `api/app/main.py` | Detection, policy and de-identification; PostgreSQL stores configuration | `http://127.0.0.1:8000` |
| Inference service | `inference/` | Runs the privacy detection model used by the original API | Internal Compose address `http://inference:3000` |
| PostgreSQL | Root Compose service `db` | Privacy settings, entity-label mappings, recognizers, lookup lists and rules; not research chats | Internal Compose address `db:5432` |
| Independent research API | `api/app/research/application.py` | Authorizes capture, stores finalized raw sessions in SQLite and returns receipts | `http://127.0.0.1:8000` |

**SQLite belongs to the research module, not the converter.** The research router is also mounted in the original API, but its standalone entry point avoids the original API's PostgreSQL/inference startup requirements.

Two useful development flows:

- **Research capture:** follow section 3. No converter, PostgreSQL or inference model is needed.
- **Original attachment conversion and protection:** follow section 4. It needs the converter **and** the main API/PostgreSQL/inference stack.

The standalone research API and original API both use host port **8000** by default. Do not start them simultaneously on that port. The ordinary source extension uses the loopback API; a campus deployment requires a separately generated extension copy and trusted HTTPS, not editing the URL to plain HTTP on a private IP.

## 3. Start model-free research capture

### Prerequisites

- `uv` installed: [official installation instructions](https://docs.astral.sh/uv/getting-started/installation/).
- Network access for the first locked dependency/Python installation if not cached. The API requires Python 3.14 or later; `uv` can provision a compatible interpreter.
- Host port 8000 free and a dedicated local test browser profile.

Run from the repository root in **terminal A**:

```powershell
uv sync --directory api --locked
$RepoRoot = (Get-Location).Path
$env:RESEARCH_ENABLED = "true"
$env:RESEARCH_API_KEY = (& api/.venv/Scripts/python.exe -c "import secrets; print(secrets.token_urlsafe(32))").Trim()
$env:RESEARCH_STORAGE_PATH = Join-Path $RepoRoot "workspace/research/capture.sqlite3"
$env:RESEARCH_PROTOCOL_VERSION = "research-v1"
$env:RESEARCH_RETENTION_DAYS = "7"
```

Seven days is a **fictional-development example**, not an approved real-study retention period. The archive path is absolute and under the existing ignored `workspace/`; project documentation remains under `docs/`.

Use a clean dedicated terminal. If research `_FILE` secret sources or enrollment-only settings are already configured, do not mix conflicting secret sources; use the [detailed capture guide](research-capture.md) or the campus runbook instead. Do not overwrite institutional credentials for a local rehearsal.

For this local synthetic rehearsal only, copy the generated operator key into the extension's **Clave local del investigador** field. A PowerShell clipboard transfer avoids printing it in service logs:

```powershell
Set-Clipboard -Value $env:RESEARCH_API_KEY
```

Paste only into that extension field, not the chatbot or Forms. This intentionally places a development credential on the clipboard; do not use clipboard history/cloud sync for real credentials, and clear the clipboard/history after the transfer. This local operator-key shortcut must **not** be distributed to students. A campus package uses a separate enrollment code.

Then start the collector in terminal A:

```powershell
uv run --directory api --no-sync python -m uvicorn app.research.application:app --host 127.0.0.1 --port 8000 --no-access-log
```

Keep terminal A open. In **terminal B**, verify availability:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/research/health
```

Expect `status: ready`. The local interactive API documentation is at `http://127.0.0.1:8000/docs`. The standalone app does not expose the original `/api/health` or `/api/interactions/protect` routes.

### Confirm the research flow

1. Open a fresh supported chat; use the [fictional scenario cards](../project/experimentacion/research-study/scenario-cards.md).
2. Open the popup. Confirm that **API de investigación** points to `http://127.0.0.1:8000`, enter the development key and `research-v1`, and explicitly review collection consent. Optional training permission stays unchecked unless separately agreed.
3. Click **Iniciar en esta pestaña**. Confirm the recording indicator before submitting anything. Research mode records raw text; it does not de-identify it before the external chatbot receives it. It pauses ordinary attachment protection only on the selected recording/paused tab.
   Progress/errors appear immediately above this button. An existing conversation is rejected explicitly: open a new empty chat rather than trying to import its history. A visible empty editor may not show a send button until you type; this alone no longer prevents activation. A missing editor/page adapter is a different error. Failed starts keep the setup fields in the current popup; the key is cleared only after acknowledged activation and is never saved as popup configuration. Closing the browser popup still discards its transient form inputs.
4. Set **Identificador de tarea** and click **Asignar tarea**; submit fictional text and wait for the reply to finish. Research mode is text-only; do not attach files.
5. Click **Finalizar y guardar / reintentar**. A confirmed API acknowledgement should display an identifier. Use **Copiar identificador**; do not treat the mere existence of a local buffer as a successful API save.
6. If upload fails, keep the profile/extension and retry. Do not clear browser storage to resolve the error. **Descartar / retirar sesión** is the explicit deletion route, with its own confirmation and retry semantics.

The other research-operation limits, consent, export and withdrawal procedures are in [model-free capture](research-capture.md). Nothing in this rehearsal creates a Google Form or authorizes recruitment.

## 4. Start the original attachment/protection flow

If the standalone research process from section 3 is using port 8000, stop it with **Ctrl+C in its own terminal** after resolving pending work. Do not terminate an unrelated process automatically. Do not start research recording during this attachment rehearsal.

### 4.1 Prepare Docker and the main API configuration

Install/start Docker Desktop with Linux containers and a Compose version supporting `--watch` and optional `env_file` entries. These commands build images and the inference service may download/cache a large model on first startup; allow time, disk space and network access. Do not run them solely to check a Markdown edit.

The tracked Compose templates are:

- `api/.db.dev.env`: database settings. Inside Docker, `POSTGRES_HOST=db` is correct.
- `api/.api.dev.env`: inference settings. Inside Docker, `BENTOML_URL=http://inference:3000` is correct.

Create private local overrides **only if they do not already exist**:

```powershell
if (-not (Test-Path api/.db.env)) {
    Copy-Item api/.db.dev.env api/.db.env
}
if (-not (Test-Path api/.api.env)) {
    Copy-Item api/.api.dev.env api/.api.env
}
```

Edit `api/.db.env` and replace the example password with a local-only development password. Both database and API load that override. Keep these private files out of Git and do not use production credentials. There is no root `.env.example` in the current checkout; do not follow older instructions that reference one.

Changing `POSTGRES_PASSWORD` in an environment file does not automatically change credentials inside an already-initialized database volume. For an existing environment, retain its matching configuration or use an authorized credential-change procedure; do not delete its volume as a shortcut.

### 4.2 Start PostgreSQL, inference and the privacy API

From the repository root in terminal A:

```powershell
docker compose up --build --watch
```

This starts `db`, `inference` and `api`. It **does not start the converter**. The API waits for the database/inference health checks and applies Alembic migrations before its development server starts. These are real database changes when the developer runs the command; no migration was executed merely to author this guide.

In terminal B:

```powershell
docker compose ps
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

The original health response contains `status: active`. Open `http://127.0.0.1:8000/docs` for its interactive API. PostgreSQL and inference are internal-only in this Compose; do not expect host connections to ports 5432 or 3000, and do not change the API's loopback binding to expose the development Admin API.

Optional development administration: replace the startup command with `docker compose --profile dev up --build --watch` to include pgAdmin at `http://127.0.0.1:9001`. Its current defaults are development-only; do not publish that service to the campus network. Inside pgAdmin, the database host is `db`, not the browser computer's `localhost`.

### 4.3 Start the converter separately

The converter requires the Chrome extension ID from section 1 and a development token matching `SECRET_TOKEN` in `browser-extension/extension/background.js`. That token is bundled in extension source and is not a confidential production credential. Do not confuse it with research enrollment/admin/session credentials.

In **terminal C**, from the repository root:

```powershell
$ExtensionId = "<copy the 32-character ID from chrome://extensions>"
if ($ExtensionId -notmatch '^[a-p]{32}$') {
    throw "Replace the placeholder with the actual Chrome extension ID."
}
$Background = Get-Content browser-extension/extension/background.js -Raw
$TokenMatch = [regex]::Match($Background, "(?m)^const SECRET_TOKEN = '([^']+)';")
if (-not $TokenMatch.Success) {
    throw "Read the current extension token configuration; do not invent a token."
}
$env:MIDDLEWARE_SECRET = $TokenMatch.Groups[1].Value
$env:EXTENSION_ID_CHROME = $ExtensionId
docker build -t contextual-pii-converter:dev browser-extension/backend
docker run --rm --name contextual-pii-converter-dev -p 127.0.0.1:5000:5000 --env MIDDLEWARE_SECRET --env EXTENSION_ID_CHROME contextual-pii-converter:dev
```

This uses the existing converter Dockerfile without editing the main Compose. It runs in the foreground and binds the host listener to loopback. Its existing `/convertir` route expects the multipart field `archivo` and header `X-Token`; the extension supplies those. Converter CORS uses `EXTENSION_ID_CHROME`; if the loaded extension ID changes, restart the converter with the matching ID.

The converter's API documentation is at `http://127.0.0.1:5000/docs`; this only proves the web process is reachable, not that every document format converts successfully. Dependencies come from the current converter requirements file; this service is a separate development backend, not the research archive.

### 4.4 Confirm the attachment flow with fictional content

1. Confirm both local documentation URLs respond and the main Compose is healthy.
2. Refresh a supported chat tab. Keep the extension **Activada**, with research capture idle.
3. Create a small valid PDF/Office document containing fictional text and attach it using a supported picker/drop path. The converter permits `.pdf`, `.docx`, `.doc`, `.xlsx`, `.xls` and `.pptx`; a plain `.txt` file is not a converter smoke test.
4. Confirm conversion, privacy protection and replacement of the attachment. Check errors instead of assuming the original file was protected when an operation failed. Actual provider behavior still needs manual validation.

Ordinary protection currently targets attachments; typed chat text is not generally protected just because the toggle says **Activada**. Research capture is a different opt-in mode and is not protection. See [integration testing](integration-testing.md) for synthetic browser and isolated Docker regressions.

## 5. Stop without deleting stored data

| Process | Stop procedure |
|---|---|
| Standalone research API | Ctrl+C in its own terminal; archive file remains |
| Foreground converter | Ctrl+C in terminal C; `--rm` removes that container, not the research archive |
| Main development stack | Ctrl+C to stop its foreground session; from the repository root run `docker compose down` when removing those containers/networks is intended |

Do not use `down --volumes`, volume pruning or delete the browser profile/archive to troubleshoot a study deployment. Ordinary `docker compose down` preserves the named PostgreSQL/model-cache volumes. Logs and browser history are not an archive-backup procedure.

## 6. Troubleshooting

| Symptom | Check |
|---|---|
| Extension does not appear | Load the folder containing `manifest.json`; ensure policy permits unpacked development extensions |
| Extension update seems ignored | Reload its card, then refresh the provider tab; do not do this mid-session |
| Port 8000 already in use | Select one local API flow; do not kill unrelated processes or assume the other app's health route applies |
| Research health returns 404/503 | Check explicit enablement, absolute path, retention and nonconflicting secret sources in that process |
| Capture stays at `Iniciando` (`starting` internally) | Authorization/activation was interrupted; use the documented discard/retry procedure, not storage deletion |
| Start says the conversation already has messages | Open a new empty conversation; history is deliberately excluded, not imported or erased |
| Start cannot find the chat editor | Wait for the page to load; after an extension update refresh the tab, then use a fresh supported chat. Do not confuse an absent empty-editor Send button with a missing editor |
| Converter 401 | Its `MIDDLEWARE_SECRET` must match the extension's development token; research keys do not substitute for it |
| Converter CORS failure | Check the loaded extension ID and restart converter after changing its allowed-origin environment |
| Converter reachable, protection fails | The original main API/inference stack must also be available, not just port 5000 |
| Main API still starting | Inspect `docker compose logs --tail 50 inference api`; first model setup can take time; do not log real prompts |
| Database authentication fails after editing `.db.env` | Existing volume credentials may differ; do not erase the database to fix a password mismatch |
| Campus package fails from home/off-network | It is intentionally campus-private; follow the approved network/TLS procedure, not certificate-warning bypasses |

## 7. Verification and next reading

Service names/paths/configuration and startup CLI help were checked when writing this guide. Local synthetic software tests are recorded in the capture guide, including failed-start recovery and a send button that appears only after typing. The converter/live-provider smoke-test instructions still require the developer to perform the actual rehearsal; they are not a claim that a real browser account, university host or provider adapter was tested.

- [Risk review for the project owner](../project/experimentacion/research-study/security-risk-review.md): conditional risks, existing controls and pending decisions; not risk acceptance.
- [Local model-free capture](research-capture.md): detailed lifecycle, API tests and access procedures.
- [University-network deployment](research-campus-deployment.md): production collector, trusted private-IP HTTPS and generated campus extension. Do not use the development stack for student deployment.
- [Docker infrastructure](infraestructura-local-con-docker.md): current network, environment and persistence boundaries.
- [Integration tests](integration-testing.md): actual synthetic verification and test-runner requirements.
- [API README](../../api/README.md): routes and component structure.
