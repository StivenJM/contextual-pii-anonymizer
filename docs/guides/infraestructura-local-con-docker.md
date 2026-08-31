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
| `POSTGRES_PORT` | Puerto publicado en `127.0.0.1`; el valor inicial es `5432`. |

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
| Imagen | PostgreSQL `18.4-alpine`, con versión explícita. |
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

## Fuera de alcance

Este entorno no configura SQLAlchemy, drivers PostgreSQL, tablas, migraciones, Alembic, APIs administrativas, autenticación ni servicios de frontend. Tampoco modifica la inferencia ML ni introduce mapping canónico o fusión de detecciones.

La conexión del Privacy Middleware mediante SQLAlchemy 2.0 pertenece al siguiente paso de desarrollo.
