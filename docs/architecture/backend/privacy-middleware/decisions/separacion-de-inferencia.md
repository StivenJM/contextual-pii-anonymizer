# Separación entre privacidad e inferencia

## Decisión

El middleware FastAPI conserva la detección basada en patrones y diccionarios, la adaptación semántica, la fusión, las políticas y la desidentificación. El servicio BentoML se limita a descubrir y ejecutar modelos de aprendizaje automático.

## Motivo

Los modelos y las políticas evolucionan por razones diferentes. Los modelos requieren un entorno especializado de inferencia, mientras que los reconocedores, la taxonomía, las reglas y las operaciones de protección forman parte del comportamiento estable del sistema.

Separar ambos límites evita que un modelo tenga que conocer la taxonomía canónica o la configuración administrativa. También permite sustituir o versionar modelos sin trasladar la lógica de privacidad a cada despliegue de inferencia.

## Consecuencias

- Cada modelo declara su propia taxonomía y el middleware mantiene el mapeo canónico.
- La solicitud de inferencia identifica explícitamente el modelo que debe ejecutarse.
- El servicio de inferencia ofrece descubrimiento de modelos, versiones y categorías nativas.
- Los detectores no basados en aprendizaje automático permanecen disponibles aunque cambie el modelo seleccionado.
- La comunicación entre ambos servicios añade una frontera remota que requiere errores explícitos, contratos versionados y observabilidad.

## Restricciones

- BentoML no selecciona el modelo activo a partir de configuración administrativa.
- BentoML no fusiona detecciones ni aplica reglas de protección.
- FastAPI no carga modelos de aprendizaje automático dentro del proceso del middleware.
- Una indisponibilidad de inferencia no habilita el envío silencioso de texto sin evaluar los demás controles de privacidad.
