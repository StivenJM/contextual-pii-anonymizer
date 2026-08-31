# Infraestructura de persistencia

## Propósito

El Privacy Middleware mantiene una única infraestructura asíncrona de conexión a PostgreSQL por instancia de aplicación. Esta base permite que futuras operaciones incorporen persistencia sin acoplar el núcleo a SQLAlchemy ni compartir sesiones entre solicitudes.

## Flujo

```mermaid
flowchart TD
    Configuracion[Configuración externa]
    Ciclo[Ciclo de vida de la aplicación]
    Infraestructura[Infraestructura asíncrona de base de datos]
    Factory[Factory de sesiones]
    Dependency[Resolución por solicitud]
    Sesion[Sesión de base de datos]
    PostgreSQL[(PostgreSQL)]

    Configuracion --> Ciclo
    Ciclo --> Infraestructura
    Infraestructura --> Factory
    Factory --> Dependency
    Dependency --> Sesion
    Sesion --> PostgreSQL
```

La configuración se valida antes de construir la infraestructura. Durante startup se crea el engine, se asocia una factory de sesiones y se ejecuta una consulta mínima independiente del schema. La API solo comienza a recibir solicitudes cuando PostgreSQL responde.

## Scopes

| Recurso | Scope | Motivo |
|---|---|---|
| Engine y pool | Aplicación | Son costosos y seguros para reutilizar entre solicitudes. |
| Factory de sesiones | Aplicación | Produce sesiones nuevas sobre el engine compartido. |
| Sesión | Solicitud | Conserva estado de una operación y debe cerrarse al finalizarla. |
| Repository futuro | Solicitud u operación | Quedará ligado a la sesión requerida por un caso de uso concreto. |

La factory compartida no equivale a una sesión compartida. Cada solicitud que necesita persistencia recibe una sesión propia mediante una dependency con cleanup garantizado.

## Ciclo de vida

```mermaid
sequenceDiagram
    participant Aplicacion as Aplicación FastAPI
    participant DB as Infraestructura de base de datos
    participant PostgreSQL

    Aplicacion->>DB: Inicializa engine y factory
    DB->>PostgreSQL: Verifica conectividad
    PostgreSQL-->>DB: Confirma disponibilidad
    DB-->>Aplicacion: Habilita recursos compartidos
    Aplicacion->>DB: Libera el engine durante shutdown
```

Una base inaccesible impide completar el startup. No se implementan reintentos, modo degradado ni pooling adicional sobre el que ya proporciona SQLAlchemy.

## Implementación actual

SQLAlchemy 2.0 administra el engine, el pool y las sesiones mediante su API asíncrona. Psycopg 3 proporciona el dialecto PostgreSQL. Las credenciales se entregan como configuración externa y la URL se construye de forma tipada para representar contraseñas con caracteres especiales sin concatenación manual.

El recurso compartido se construye dentro del lifespan de FastAPI y la factory queda disponible en el container de aplicación. Las dependencies de la frontera FastAPI crean y cierran cada sesión; el container nunca almacena la sesión actual.

En Windows, el runtime utiliza un event loop basado en selector porque Psycopg 3 async no es compatible con el loop Proactor predeterminado. Esta adaptación pertenece a la composición de la aplicación y no altera los contratos internos.

## Límites

- La dependency administra apertura y cierre, pero no hace commit automático.
- La estrategia transaccional se definirá cuando existan operaciones de aplicación reales.
- No existen repositories hasta que un use case necesite un contrato de persistencia.
- No existen modelos ORM, tablas, metadata de schema ni creación automática de estructuras.
- No existen migraciones porque todavía no hay un schema de aplicación.
- El endpoint general de health no consulta PostgreSQL en cada solicitud.
