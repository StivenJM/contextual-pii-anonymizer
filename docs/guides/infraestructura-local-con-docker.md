# Operar la infraestructura local con Docker

Para la secuencia completa, empieza por [instalar la extensión y arrancar el sistema de desarrollo](developer-startup.md). Esta página describe el **Compose de desarrollo actual**, no un despliegue de producción ni una topología de solo PostgreSQL.

## Servicios y límites

| Servicio de Compose | Responsabilidad | Exposición en el host |
|---|---|---|
| `db` | Configuración de privacidad en PostgreSQL | Sin puerto publicado; interno `db:5432` |
| `inference` | Inferencia de modelos con BentoML | Sin puerto publicado; interno `inference:3000` |
| `api` | API de privacidad y rutas de administración | Loopback `127.0.0.1:8000` |
| `converter` | Conversión de adjuntos PDF/Office a Markdown | Loopback `127.0.0.1:5000` |
| `pgadmin`, perfil `dev` | Administración de desarrollo opcional | Loopback `127.0.0.1:9001` |

El conversor es su propio proceso dentro del Compose de desarrollo; no está fusionado con la API ni llama a la API de privacidad. La investigación sin modelo sigue usando un punto de entrada y un Compose separados, y SQLite, no esta base de datos PostgreSQL.

## Configuración

Las plantillas versionadas actuales son `api/.api.dev.env` y `api/.db.dev.env`. Las sobreescrituras opcionales e ignoradas son `api/.api.env` y `api/.db.env`, que se cargan después de las plantillas. Créalas sin sobrescribir archivos locales existentes, siguiendo la guía de arranque, y elige credenciales solo locales.

La raíz del repositorio también usa un `.env` privado e ignorado por Git para `EXTENSION_ID_CHROME` y, si cambia, `MIDDLEWARE_SECRET`. El ID es el de la extensión descomprimida cargada en el navegador; el token de desarrollo debe coincidir con `SECRET_TOKEN` en `browser-extension/extension/background.js`. Sin `EXTENSION_ID_CHROME`, Compose detiene el arranque en lugar de iniciar el conversor con un origen permitido vacío.

Dentro de Docker, conserva `POSTGRES_HOST=db` y `BENTOML_URL=http://inference:3000`. Un proceso del host no puede usar esas direcciones internas como si fueran servicios publicados en localhost. El nombre de servicio `postgres` y la base de datos publicada en el host que describía una versión anterior de esta página ya no coinciden con el checkout.

Cambiar la contraseña en un archivo de entorno no restablece la contraseña de un volumen de base de datos ya inicializado. Conserva las credenciales existentes o usa un procedimiento de cambio de credenciales de base de datos autorizado de forma explícita; nunca elimines el volumen para resolver un desajuste sin aprobación.

## Arrancar e inspeccionar

Desde la raíz del repositorio:

```powershell
# Arranca el stack completo de desarrollo; puede descargar y compilar imágenes y un modelo grande.
docker compose up --build --watch
```

En otra terminal:

```powershell
docker compose ps
docker compose logs --tail 50 db inference api converter
Invoke-RestMethod http://127.0.0.1:8000/api/health
(Invoke-WebRequest -UseBasicParsing http://127.0.0.1:5000/docs).StatusCode
```

La API espera a que PostgreSQL e inferencia estén saludables y ejecuta `alembic upgrade head` antes de que arranque su servidor de desarrollo. Por lo tanto, arrancar aplica migraciones reales a esa base de datos de desarrollo. La respuesta de salud de la API original informa `status: active`; no es la ruta de salud de la investigación independiente. El conversor escucha en el loopback del host y su documentación interactiva solo demuestra que el proceso web responde, no que todos los formatos se conviertan correctamente.

Para una operación de contenedor solo de base de datos, el nombre del servicio es `db`:

```powershell
docker compose up -d --wait db
docker compose exec db sh -c 'pg_isready -h 127.0.0.1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

Esto no publica PostgreSQL en el host ni arranca ninguna API. Desarrollar aplicaciones nativas en el host requeriría una configuración de conectividad revisada por separado; arrancar este contenedor no lo implica.

Para pgAdmin opcional, arranca el stack completo con `docker compose --profile dev up --build --watch`. Registra la base de datos con el host `db` y las mismas credenciales configuradas. No expongas la administración de desarrollo fuera del loopback.

## Detener y conservar los datos

```powershell
docker compose stop
# O elimina los contenedores y redes de este proyecto conservando los volúmenes nombrados:
docker compose down
```

Los datos de PostgreSQL y la caché del modelo son volúmenes nombrados. No uses `down --volumes` ni poda de volúmenes cuando debas conservar su contenido. Reiniciar con `up` reutiliza esos volúmenes; no crea un respaldo ni demuestra una recuperación.

## Pruebas y producción

- [Pruebas de integración](integration-testing.md) usan recursos de prueba aislados y con nombres separados. No apuntes fixtures destructivos a la base de datos de desarrollo ordinaria.
- [Captura sin modelo](research-capture.md) arranca sin PostgreSQL ni inferencia y usa el mismo puerto de host 8000 por defecto; no arranques las dos APIs locales en ese puerto.
- [Despliegue de investigación en campus](research-campus-deployment.md) es la configuración separada con HTTPS y CA interna. El Compose de desarrollo, su proceso de recarga y su Admin API local sin autenticación no son un despliegue de producción de campus.

Estas instrucciones se conciliaron con `compose.yaml`, las dos plantillas de entorno versionadas y la configuración y ayuda de la CLI. No se ejecutó ningún servicio, migración ni descarga de modelo para esta actualización de documentación.
