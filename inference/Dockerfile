FROM python:3.14-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.12.9 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Leverage the Doker cache
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

COPY . .
RUN uv sync --locked

EXPOSE 3000

CMD ["uv", "run", "bentoml", "serve", "app.service:PiiInferenceService", "--host", "0.0.0.0", "--port", "3000", "--reload"]