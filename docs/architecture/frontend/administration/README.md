# Administración

## Propósito técnico

La aplicación administrativa ofrece una interfaz para consultar y modificar la configuración operativa del Prompt Privacy System. Es la presentación de una capacidad transversal cuyo control y validación permanecen en el middleware.

## Límites

La aplicación permite editar recursos y parámetros admitidos. No ejecuta detección, no transforma texto, no despliega modelos y no modifica la taxonomía canónica.

La administración no participa en el flujo de una interacción de usuario. Sus cambios afectan solicitudes posteriores cuando el middleware acepta la nueva configuración.

## Capacidades principales

- Consultar el catálogo de modelos disponible a través del middleware.
- Seleccionar el modelo activo.
- Configurar el mapeo entre categorías nativas y canónicas.
- Crear, modificar, habilitar y deshabilitar reconocedores estructurales.
- Administrar diccionarios y sus entradas.
- Ajustar umbrales, detectores habilitados y prioridad entre fuentes.
- Definir operaciones de protección por categoría.

## Responsabilidades de interacción

- Presentar las restricciones de cada recurso antes de guardar cambios.
- Impedir referencias a modelos, categorías u operaciones inexistentes.
- Diferenciar claramente habilitar un recurso de eliminarlo.
- Mostrar errores de validación sin representar como activa una configuración rechazada.
- Advertir cuando un cambio deja incompleto el mapeo de un modelo.

## Restricciones

- La interfaz no ofrece operaciones para crear, eliminar o renombrar categorías canónicas.
- Los modelos visibles provienen del catálogo del servicio de inferencia; no pueden cargarse desde esta aplicación.
- La última configuración confirmada por el middleware es la única que se presenta como vigente.

## Documentación relacionada

- [`Configuración administrable`](../../backend/privacy-middleware/capabilities/configuracion-administrable.md): invariantes y responsabilidades del middleware.
- [`Taxonomía canónica`](../../backend/privacy-middleware/data/taxonomia-canonica.md): contrato semántico que la administración no puede modificar.
