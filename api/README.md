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
  routers/          # HTTP route adapters
  schemas/          # HTTP request and response contracts
tests/              # Unit, HTTP, and opt-in integration tests
```

## Configure

The API and Docker Compose use the same root `.env` file for local PostgreSQL credentials:

```powershell
Copy-Item ..\.env.example ..\.env
```

Replace `POSTGRES_PASSWORD` with a local-only value before starting the services.

## Run

Start PostgreSQL from the repository root:

```powershell
docker compose up -d --wait postgres
```

Apply the database migrations from this directory:

```powershell
uv run --locked --env-file ../.env alembic upgrade head
```

Start BentoML from `inference/` in another terminal:

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m bentoml serve app.service:PiiInferenceService --port 3000
```

Then start FastAPI from `api/`:

```powershell
uv run --locked --env-file ../.env uvicorn app.main:app --reload --loop app.runtime:create_selector_event_loop
```

FastAPI validates the database configuration and verifies connectivity during startup. Startup fails if PostgreSQL is unavailable. The application disposes its connection pool during shutdown.

The explicit event loop factory keeps Psycopg 3 async compatible with Windows, whose default Proactor loop is unsupported by the driver.

The initial health endpoint is available at `GET /api/health`.

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
uv run --locked python -m unittest discover -s tests -v
```

The normal suite does not require Docker. The PostgreSQL integration test is skipped unless explicitly enabled.

## PostgreSQL Integration Verification

With PostgreSQL healthy and the root `.env` configured:

```powershell
$env:RUN_DATABASE_INTEGRATION='1'
uv run --locked --env-file ../.env python -m unittest tests.test_database_integration tests.test_privacy_integration -v
Remove-Item Env:RUN_DATABASE_INTEGRATION
```

This verification checks lifecycle connectivity plus real PostgreSQL-backed Admin CRUD and the complete interaction pipeline with a contract-compatible inference fake.
