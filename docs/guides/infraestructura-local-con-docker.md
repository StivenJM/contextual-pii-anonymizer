# Operate the local Docker infrastructure

For the complete sequence, start with [installing the extension and developer startup](developer-startup.md). This page describes the **current development Compose**, not a production deployment or a PostgreSQL-only topology.

## Services and boundaries

| Compose service | Responsibility | Host exposure |
|---|---|---|
| `db` | PostgreSQL privacy configuration | No published host port; internal `db:5432` |
| `inference` | BentoML model inference | No published host port; internal `inference:3000` |
| `api` | Privacy API and Admin routes | Loopback `127.0.0.1:8000` |
| `pgadmin`, profile `dev` | Optional development administration | Loopback `127.0.0.1:9001` |

The attachment converter is **not** a service in this Compose. Run it separately as documented in the startup guide. Model-free research uses a separate entry point/Compose and SQLite, not this PostgreSQL database.

## Configuration

The current tracked templates are `api/.api.dev.env` and `api/.db.dev.env`. Optional ignored overrides are `api/.api.env` and `api/.db.env`, loaded after the templates. Create them without overwriting existing local files, using the startup guide, and choose local-only credentials.

Inside Docker, retain `POSTGRES_HOST=db` and `BENTOML_URL=http://inference:3000`. A host process cannot use those internal addresses as if they were published localhost services. The root `.env.example`, service name `postgres` and host-published database described by an earlier version of this page no longer match the checkout.

Changing an environment-file password does not reset an initialized database volume's password. Preserve existing credentials or use an explicitly authorized database credential-change procedure; never remove the volume to solve a mismatch without approval.

## Start and inspect

From the repository root:

```powershell
# Starts the full development stack; may download/build images and a large model.
docker compose up --build --watch
```

In another terminal:

```powershell
docker compose ps
docker compose logs --tail 50 db inference api
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

The API waits for healthy PostgreSQL/inference and runs `alembic upgrade head` before its development server starts. Running startup therefore applies real migrations to that development database. The original API health response reports `status: active`; it is not the standalone research health route.

For a database-only container operation, the service name is `db`:

```powershell
docker compose up -d --wait db
docker compose exec db sh -c 'pg_isready -h 127.0.0.1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

This does not publish PostgreSQL to the host or start either API. Native host application development would need a separately reviewed connectivity setup; it is not implied by starting this container.

For optional pgAdmin, start the full stack with `docker compose --profile dev up --build --watch`. Register the database using host `db` and the same configured database credentials. Do not expose development administration outside loopback.

## Stop and preserve data

```powershell
docker compose stop
# Or remove this project's containers/networks while preserving named volumes:
docker compose down
```

PostgreSQL data and the model cache are named volumes. Do not use `down --volumes` or volume pruning when their contents must be preserved. Restarting with `up` reuses those volumes; it does not create a backup or prove recovery.

## Tests and production

- [Integration testing](integration-testing.md) uses separately named, isolated test resources. Do not point destructive test fixtures at the ordinary development database.
- [Model-free capture](research-capture.md) starts without PostgreSQL/inference and uses the same host port 8000 by default; do not start both local APIs on that port.
- [Campus research deployment](research-campus-deployment.md) is the separate internal-CA HTTPS setup. The development Compose, its reload process and unauthenticated local Admin API are not a campus production deployment.

These instructions were reconciled against `compose.yaml`, the two tracked environment templates and CLI configuration/help. No service, migration or model download was run for this documentation update.
