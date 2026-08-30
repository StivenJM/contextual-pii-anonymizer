# Límites de configuración

## Propósito

Estas reglas evitan que una configuración administrativa deje al sistema en un estado incoherente o elimine protecciones esenciales.

## Reglas

1. **Clasificación protegida**: la administración no crea, elimina ni renombra categorías de información sensible.
2. **Modelos declarados**: la administración puede seleccionar modelos disponibles, pero no cargar ni desplegar modelos nuevos.
3. **Relaciones válidas**: las categorías de un modelo solo pueden relacionarse con categorías existentes del sistema.
4. **Recursos clasificados**: todo reconocedor y diccionario habilitado declara qué información identifica.
5. **Tratamientos admitidos**: una regla solo utiliza acciones de protección disponibles.
6. **Prioridad específica**: una regla concreta prevalece sobre una regla general aplicable a la misma información.
7. **Última configuración válida**: una modificación rechazada no afecta las interacciones posteriores.
8. **Trazabilidad**: los cambios de modelo, mapeos y reglas pueden asociarse con los resultados que produjeron.

## Casos especiales

- **Mapeo incompleto**: el modelo no se activa hasta resolver las categorías pendientes.
- **Recurso deshabilitado**: deja de participar en nuevas interacciones sin perder necesariamente su definición histórica.
- **Categoría faltante**: se registra como una brecha que requiere una evolución controlada, no como una edición administrativa inmediata.

## Resultado esperado

La configuración puede evolucionar sin romper la clasificación común ni volver ambiguos los resultados del sistema.
