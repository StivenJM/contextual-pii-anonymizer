# Cómo operar la infraestructura local con Docker

Esta guía prepara los recursos compartidos que las aplicaciones necesitan durante el desarrollo. Actualmente Docker Compose levanta únicamente PostgreSQL; el Privacy Middleware y el ML Inference Service conservan sus propios flujos de ejecución fuera de Docker.

Este entorno es exclusivamente local. No representa una configuración de producción.

## Requisitos

- Docker Desktop o Docker Engine con Docker Compose moderno.
- El puerto local elegido para PostgreSQL disponible.

Los servicios de aplicación usan actualmente los puertos `8000` y `3000`. PostgreSQL utiliza `5432` por defecto, por lo que no existe una colisión entre ellos.

## Configuración inicial

Desde la raíz del repositorio, crea tu configuración local:

```powershell
Copy-Item .env.example .env
```

Edita `.env` y reemplaza `POSTGRES_PASSWORD` con una contraseña exclusiva para desarrollo local. El archivo `.env` está ignorado por Git y no debe contener credenciales de producción.

| Variable | Uso |
|---|---|
| `POSTGRES_DB` | Base de datos creada al inicializar el volumen. |
| `POSTGRES_USER` | Usuario propietario de la base de desarrollo. |
| `POSTGRES_PASSWORD` | Credencial local no versionada. |
| `POSTGRES_HOST` | Host utilizado por el Privacy Middleware; localmente es `127.0.0.1`. |
| `POSTGRES_PORT` | Puerto publicado en `127.0.0.1`; el valor inicial es `5432`. |
| `BENTOML_URL` | URL local del ML Inference Service; el valor inicial es `http://127.0.0.1:3000`. |
| `BENTOML_TIMEOUT_SECONDS` | Tiempo máximo de espera para una inferencia. |

La plantilla es configuración compartible. Los valores efectivos de `.env`, especialmente la contraseña, pertenecen a cada entorno local.

## Operaciones habituales

### Iniciar y esperar disponibilidad

```powershell
docker compose up -d --wait postgres
```

El comando finaliza correctamente cuando PostgreSQL acepta conexiones, no solo cuando el contenedor está iniciado.

### Consultar estado

```powershell
docker compose ps
```

El servicio debe aparecer con estado `healthy`.

### Ver logs

```powershell
docker compose logs -f postgres
```

Presiona `Ctrl+C` para dejar de seguir los logs sin detener PostgreSQL.

### Comprobar conectividad

```powershell
docker compose exec postgres sh -c 'pg_isready -h 127.0.0.1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
docker compose exec postgres sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" psql -h 127.0.0.1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;"'
```

Desde procesos ejecutados directamente en el equipo, PostgreSQL está disponible en `127.0.0.1` y en el puerto configurado por `POSTGRES_PORT`.

### Aplicar migraciones

Con PostgreSQL saludable, ejecuta desde `api/`:

```powershell
uv run --locked --env-file ../.env alembic upgrade head
```

Este paso crea el esquema versionado y la configuración inicial administrable. El startup no sustituye las migraciones mediante creación automática de tablas.

### Iniciar el ML Inference Service

Desde `inference/`:

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m bentoml serve app.service:PiiInferenceService --port 3000
```

Comprueba disponibilidad en `http://127.0.0.1:3000/readyz` y el catálogo mediante `POST http://127.0.0.1:3000/models` con un objeto JSON vacío.

### Iniciar el Privacy Middleware

Con PostgreSQL saludable, inicia FastAPI desde `api/` cargando la misma configuración local:

```powershell
uv run --locked --env-file ../.env uvicorn app.main:app --reload --loop app.runtime:create_selector_event_loop
```

El startup verifica una conexión real mediante SQLAlchemy. Si PostgreSQL no está disponible o la configuración es inválida, la aplicación no comienza a aceptar solicitudes.

La factory explícita conserva un loop compatible con Psycopg 3 async también en Windows, donde el loop Proactor predeterminado no está soportado por el driver.

### Ejecutar verificaciones

La suite normal no requiere Docker:

```powershell
uv run --locked python -m unittest discover -s tests -v
```

Las comprobaciones reales contra PostgreSQL se activan explícitamente:

```powershell
$env:RUN_DATABASE_INTEGRATION='1'
uv run --locked --env-file ../.env python -m unittest tests.test_database_integration tests.test_privacy_integration -v
Remove-Item Env:RUN_DATABASE_INTEGRATION
```

### Detener sin eliminar datos

```powershell
docker compose down
```

Este comando elimina el contenedor y la red local creada por Compose, pero conserva el volumen nombrado. La siguiente ejecución de `docker compose up -d --wait postgres` reutiliza los mismos datos.

### Reiniciar el servicio

```powershell
docker compose restart postgres
docker compose ps
```

Si el entorno estaba detenido mediante `down`, vuelve a iniciarlo con el comando de inicio.

### Eliminar deliberadamente la base local

```powershell
docker compose down --volumes
```

La opción `--volumes` elimina de forma irreversible el volumen de PostgreSQL. La próxima inicialización creará una base vacía con los valores actuales de `.env`.

Detener el entorno y destruir la base son operaciones distintas. No uses `--volumes` para una detención cotidiana.

## Decisiones del entorno

| Tema | Decisión local |
|---|---|
| Imagen | PostgreSQL `18.6-alpine`, con versión explícita. |
| Persistencia | Volumen nombrado administrado por Compose. |
| Disponibilidad | Healthcheck con `pg_isready`. |
| Exposición | Solo `127.0.0.1`, mediante el puerto configurado. |
| Red | Red predeterminada y aislada de Compose, sin topología adicional. |
| Aplicaciones | Se ejecutan fuera de Docker durante este paso. |

Compose puede incorporar otros recursos cuando exista una necesidad real. La configuración actual no anticipa contenedores, redes ni dependencias para componentes que todavía no existen.

## Invariantes

- Mantén `.env` fuera del control de versiones.
- No reutilices las credenciales locales en producción.
- Espera el estado saludable antes de usar PostgreSQL.
- Conserva el volumen durante las detenciones normales.
- Elimina el volumen únicamente como una acción consciente de reinicio total.

### Comprobar las APIs

- Health: `GET http://127.0.0.1:8000/api/health`.
- Administración: `http://127.0.0.1:8000/docs` o rutas bajo `/api/admin`.
- Protección: `POST http://127.0.0.1:8000/api/interactions/protect` con `{"text":"..."}`.

### Cargar la extensión

1. Abre la administración de extensiones del navegador.
2. Activa el modo desarrollador.
3. Carga sin empaquetar la carpeta `Tesis3_SinCopilot/extension`.
4. Recarga una pestaña de ChatGPT, Claude o Gemini.
5. Mantén PostgreSQL, BentoML y FastAPI activos antes de enviar un prompt.

La extensión reemplaza el editor por `protected_text` y continúa el envío una sola vez. Si la API falla, mantiene el envío bloqueado y muestra un error. Los adjuntos TXT se protegen; PDF y Office permanecen bloqueados hasta incorporar extracción binaria local.

## Fuera de alcance

El entorno local no implementa autenticación administrativa ni un Admin Frontend. Tampoco empaqueta las aplicaciones en contenedores ni incorpora extractores locales para adjuntos PDF/Office.
