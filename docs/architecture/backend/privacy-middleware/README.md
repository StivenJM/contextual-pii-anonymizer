# Middleware de privacidad

## Propósito técnico

El middleware de privacidad es el núcleo de decisión del sistema. Recibe texto desde la extensión, coordina mecanismos de detección heterogéneos, produce un conjunto coherente de entidades sensibles y aplica las políticas que determinan cómo protegerlas.

FastAPI constituye la frontera HTTP del módulo y permite mantener estas responsabilidades en un backend separado del entorno especializado de inferencia.

## Límites

El módulo es responsable de la detección basada en patrones y diccionarios, la adaptación de resultados de modelos, la fusión de detecciones, la evaluación de reglas y la desidentificación.

Quedan fuera de sus límites la interacción con las páginas de modelos comerciales, la ejecución de modelos de aprendizaje automático y la presentación de interfaces administrativas. Tampoco delega decisiones de protección al servicio de inferencia.

## Capacidades principales

- Coordinar detección híbrida mediante modelos, reconocedores estructurales y diccionarios.
- Traducir taxonomías nativas de modelos hacia la taxonomía canónica.
- Resolver solapamientos y producir entidades normalizadas.
- Evaluar reglas de protección sin modificar el texto.
- Ejecutar operaciones de etiquetado, enmascaramiento o seudonimización.
- Administrar la configuración que gobierna detectores y políticas.

## Documentación

### Capacidades

- [`deteccion-hibrida.md`](capabilities/deteccion-hibrida.md): colaboración entre fuentes de detección y reglas de fusión.
- [`configuracion-administrable.md`](capabilities/configuracion-administrable.md): configuración operativa disponible y sus invariantes.

### Flujos

- [`proteccion-de-interacciones.md`](flows/proteccion-de-interacciones.md): recorrido técnico desde la recepción del texto hasta su devolución protegida.

### Datos

- [`taxonomia-canonica.md`](data/taxonomia-canonica.md): contrato semántico compartido por detección, políticas y desidentificación.

### Decisiones

- [`separacion-de-inferencia.md`](decisions/separacion-de-inferencia.md): límites entre la orquestación de privacidad y la ejecución de modelos.

## Dependencias arquitectónicas

- [`Servicio de inferencia`](../inference-service/README.md): declara y ejecuta los modelos disponibles.
- [`Extensión del navegador`](../../frontend/browser-extension/README.md): entrega el texto y recibe el resultado protegido.
- [`Administración`](../../frontend/administration/README.md): permite modificar la configuración aceptada por el middleware.
