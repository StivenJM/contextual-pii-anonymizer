# Contextual PII Anonymizer

Sistema para detectar y proteger información personal identificable (PII) antes de enviarla a un modelo de lenguaje.

El entorno local incluye PostgreSQL, el servicio de inferencia, la API y el conversor de adjuntos.

## Developer startup

Start with [extension installation and developer startup](docs/guides/developer-startup.md).
The default Compose stack starts the attachment converter alongside the API, PostgreSQL and inference.
For model-free research capture, use the separate model-free deployment documented in that guide instead of starting inference.

## Requisitos

- Docker con Docker Compose.

## Desarrollo

Desde la raíz del proyecto, inicia el entorno con reconstrucción y sincronización automática de cambios:

```bash
docker compose up --build --watch
```

La API queda disponible en:

- Documentación interactiva: http://127.0.0.1:8000/docs
- Estado del servicio: http://127.0.0.1:8000/api/health

La primera ejecución puede tardar mientras se descarga el modelo de inferencia.

## Desarrollo con pgAdmin

Para iniciar también pgAdmin, activa el perfil `dev`:

```bash
docker compose --profile dev up --build --watch
```

pgAdmin queda disponible en http://127.0.0.1:9001.

## Detener el entorno

```bash
docker compose down
```

Este comando conserva los datos almacenados en los volúmenes de Docker.

## Documentación

La documentación funcional, técnica y las guías de desarrollo están en [`docs/`](docs/).

## Research capture

The optional [model-free capture workflow](docs/guides/research-capture.md) stores
consented text research sessions independently of the protection model. The same
router can be enabled inside the local Compose stack with `compose.research.dev.yaml`
and a persistent `research_archive` volume; research requests do not call inference.
Start with the [research plan](docs/project/experimentacion/research-capture-plan.md) and
[student study kit](docs/project/experimentacion/research-study/README.md); institutional
approval and live-provider adapter checks remain prerequisites for real fieldwork.

For student-owned computers, use the [university-network deployment guide](docs/guides/research-campus-deployment.md)
to prepare the separate collector, private-IP HTTPS and endpoint-specific extension copy.
