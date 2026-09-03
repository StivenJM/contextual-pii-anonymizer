# Contextual PII Anonymizer

Sistema para detectar y proteger información personal identificable (PII) antes de enviarla a un modelo de lenguaje.

El entorno local incluye PostgreSQL, el servicio de inferencia y la API.

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
