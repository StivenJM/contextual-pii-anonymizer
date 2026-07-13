# Contextual PII Anonymizer API

FastAPI service entrypoint for the contextual PII anonymizer project.

## Structure

```text
src/
  app.py          # Creates and configures the FastAPI application
  main.py         # ASGI entrypoint and local development runner
  routes/         # HTTP route declarations with APIRouter
  controllers/    # HTTP-facing orchestration
  use_cases/      # Application actions
  schemas/        # Request and response models
```

## Run

```bash
uv run fastapi dev src/main.py
```

The initial health endpoint is available at `GET /api/health`.
