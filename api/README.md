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
  infrastructure/   # Concrete database infrastructure
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

Then start FastAPI from this directory:

```powershell
uv run --locked --env-file ../.env uvicorn app.main:app --reload --loop app.runtime:create_selector_event_loop
```

FastAPI validates the database configuration and verifies connectivity during startup. Startup fails if PostgreSQL is unavailable. The application disposes its connection pool during shutdown.

The explicit event loop factory keeps Psycopg 3 async compatible with Windows, whose default Proactor loop is unsupported by the driver.

The initial health endpoint is available at `GET /api/health`.

## Unit Tests

```powershell
uv run --locked python -m unittest discover -s tests -v
```

The normal suite does not require Docker. The PostgreSQL integration test is skipped unless explicitly enabled.

## PostgreSQL Integration Verification

With PostgreSQL healthy and the root `.env` configured:

```powershell
$env:RUN_DATABASE_INTEGRATION='1'
uv run --locked --env-file ../.env python -m unittest tests.test_database_integration -v
Remove-Item Env:RUN_DATABASE_INTEGRATION
```

This verification starts the FastAPI lifespan, performs the startup connectivity check, resolves a request-scoped async session, executes a schema-independent query, and shuts the application down.
