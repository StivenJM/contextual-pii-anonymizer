# Guías de desarrollo

Estas guías explican procedimientos recurrentes para preparar y operar el proyecto durante el desarrollo.

## Empieza aquí

- [Instalar la extensión y arrancar el sistema de desarrollo](developer-startup.md): instalación inicial, un arranque local por defecto para adjuntos y la captura para investigación opcional.

## Datos

- [`Conjuntos de datos y auditorías`](datasets-and-audits.md): registra un conjunto de datos con DVC y convierte cada auditoría en evidencia reproducible y revisable.

## Flujo de trabajo

- [`Nombres de ramas`](nombres-de-ramas.md): define cómo identificar el tipo, el alcance y el resultado de cada rama en el monorepo.

## Calidad de código

- [`Calidad de código con Ruff`](calidad-de-codigo-con-ruff.md): ejecuta linting, formateo y verificaciones de calidad con `uv`.

## Pruebas

- [`Pruebas de integración`](integration-testing.md): ejecuta la suite de la extensión contra páginas locales y, opcionalmente, el stack completo de Compose.

## Entorno local

- [`Infraestructura local con Docker`](infraestructura-local-con-docker.md): opera los contenedores de base de datos, inferencia, API y conversor, sus redes privadas y sus volúmenes persistentes.

## Recolección para investigación

- [Captura para investigación sin modelo](research-capture.md): ejecuta la API local separada y el modo de captura de la extensión, con procedimientos de acceso, reintento y retiro.
- [Despliegue en la red universitaria](research-campus-deployment.md): prepara Docker de producción separado, HTTPS con IP privada y confianza de clientes, y un paquete de extensión específico para participantes.
- [Kit del estudio con estudiantes](../project/experimentacion/research-study/README.md): evidencia, tarjetas de escenario, protocolo propuesto, instrumentos y materiales de análisis y reporte.
- [Borrador de revisión de riesgos de seguridad](../project/experimentacion/research-study/security-risk-review.md): riesgos pendientes, evaluación proporcional del cifrado en reposo y decisiones del propietario aún abiertas.
