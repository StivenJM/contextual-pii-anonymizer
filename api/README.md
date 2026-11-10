# Contextual PII Anonymizer API

FastAPI service entrypoint for the contextual PII anonymizer project.

## Structure

```text
app/
  main.py           # Composition root and ASGI entrypoint
  config.py         # Validated application configuration
  lifespan.py       # Application-scoped resource lifecycle
  container.py      # Application-scoped resource references
  dependencies/     # Request-scoped dependency providers
  domain/           # Canonical taxonomy and privacy contracts
  engines/          # Detection, fusion, policy, and transformation engines
  repositories/     # Persistence contracts and PostgreSQL adapters
  services/         # BentoML inference boundary
  use_cases/        # Application orchestration
  infrastructure/   # Database infrastructure and ORM models
  research/         # Independent model-free capture, authorization and SQLite archive
  routers/          # HTTP route adapters
  schemas/          # HTTP request and response contracts
tests/              # Unit, HTTP, and opt-in integration tests
```

## Configure

Begin with [extension installation and developer startup](../docs/guides/developer-startup.md). Install the extension before configuring the converter's allowed extension ID.

The root Compose loads `api/.api.dev.env` and `api/.db.dev.env`, followed by optional ignored overrides `api/.api.env` and `api/.db.env`. Create private overrides without overwriting existing files and replace the example database password with a local-only value. The root Compose also reads a private root `.env` for the converter's extension ID and development token; create it as described in the developer guide. The root `.env` is ignored by Git, and there is no root `.env.example` in the current checkout.

Inside Compose, the database host is `db` and inference is `http://inference:3000`. Neither has a published host port. Do not reuse obsolete host-connection instructions or delete an initialized volume after a password mismatch.

## Run

Start the default local stack — PostgreSQL, inference, the privacy API and the attachment converter — from the repository root:

```powershell
docker compose up --build --watch
```

This builds/downloads dependencies as needed, waits for healthy database/inference services, and applies Alembic migrations before starting the API. The converter remains its own process and loopback endpoint; the extension calls it separately from the privacy API.

FastAPI verifies database configuration/connectivity at startup and disposes its pool during shutdown. For specialized native Windows execution, `app.runtime:create_selector_event_loop` remains available for Psycopg async compatibility; the containerized sequence above does not need a host event-loop workaround or host database publication.

The health endpoint is `GET http://127.0.0.1:8000/api/health`. Research capture is disabled by default. To enable the existing research router inside the ordinary development API with a persistent archive volume, use `compose.research.dev.yaml` as described in the developer guide; research handlers do not call inference. To use research capture without the model/database at all, follow the [standalone capture guide](../docs/guides/research-capture.md); research uses SQLite and has its own `/api/research/health` route. The two local API entry points both default to port 8000 and must not occupy it simultaneously.

## Public APIs

- `POST /api/interactions/protect` runs model, pattern, and gazetteer detection; fusion; policy evaluation; and de-identification.
- `GET /api/admin/taxonomy` returns the read-only University PII Taxonomy v1.
- `/api/admin/models` manages discovery and active-model selection.
- `/api/admin/mappings` and model-scoped mapping routes manage native-to-canonical mappings and gaps.
- `/api/admin/patterns` manages structural recognizers.
- `/api/admin/gazetteers` manages gazetteers and entries.
- `/api/admin/detection-settings` manages detector switches, threshold, and priority.
- `/api/admin/protection-rules` manages hierarchical protection rules.

Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs`. The development Admin API intentionally has no authentication.

Example:

```powershell
$body = @{ text = 'Mi correo es ana@example.com' } | ConvertTo-Json
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/interactions/protect' -Method Post -ContentType 'application/json' -Body $body
```

## Unit Tests

```powershell
# From api/; dependency synchronization may contact package registries.
uv sync --locked
uv run --no-sync pytest -q
```

The normal suite does not require Docker. The real PostgreSQL-dependent tests are skipped unless explicitly enabled; report skips separately from passes.

## PostgreSQL Integration Verification

Use the [isolated integration harness](../docs/guides/integration-testing.md) rather than running mutating fixtures against the ordinary development database. It executes the real PostgreSQL/API contracts inside a separately named test stack, including Admin CRUD and the interaction pipeline with a contract-compatible inference fake. The current tests use pytest, not the old unittest module paths.
