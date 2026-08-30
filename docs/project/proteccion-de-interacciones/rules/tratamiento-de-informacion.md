# Reglas de tratamiento de información

## Propósito

Estas reglas aseguran que la detección y la protección produzcan decisiones consistentes, comprensibles y seguras.

## Reglas

1. **Separar detección y tratamiento**: reconocer un dato no significa que deba ocultarse siempre; la regla vigente determina la acción.
2. **Priorizar reglas específicas**: una regla para una categoría concreta prevalece sobre una regla general que también pueda aplicarse.
3. **Conservar el sentido cuando sea posible**: el tratamiento debe reducir exposición sin destruir información necesaria para la tarea.
4. **Mantener coherencia**: una misma persona o valor debe recibir un seudónimo consistente dentro del alcance definido para la interacción o sesión.
5. **Evitar sustituciones reales**: los valores ficticios no deben elegirse para representar deliberadamente a personas reales conocidas.
6. **Proteger por defecto ante fallos**: un error de análisis o transformación no habilita el envío automático del texto original.
7. **Explicar la decisión**: la persona debe poder conocer la categoría detectada y el tratamiento propuesto sin exponer datos innecesarios en la advertencia.
8. **Distinguir versiones del texto**: el sistema diferencia el texto inicial, el protegido, el editado y el finalmente enviado.

## Casos especiales

- **Información dependiente del contexto**: puede conservarse cuando no representa información privada de la persona y la política lo permite.
- **Detecciones superpuestas**: se conserva una clasificación coherente y suficientemente específica.
- **Categoría no representada**: el hallazgo queda señalado para evaluación y no se convierte en una categoría genérica permanente.
- **Política crítica**: la decisión de la persona no permite enviar información que la política prohíbe.

## Resultado esperado

Cada fragmento recibe un tratamiento reproducible y la persona conoce qué versión del texto puede enviarse.
