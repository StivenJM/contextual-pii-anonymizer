# Contextual PII Anonymizer API

FastAPI service entrypoint for the contextual PII anonymizer project.

## Structure

```text
app/
  main.py         # Composition root and ASGI entrypoint
  routers/        # HTTP route adapters
  schemas/        # HTTP request and response contracts
tests/            # HTTP boundary tests
```

## Run

```bash
uv run fastapi dev
```

The initial health endpoint is available at `GET /api/health`.

## Test

```bash
uv run python -m unittest discover -s tests -v
```
