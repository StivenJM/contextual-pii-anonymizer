# Detección y protección

## ¿Qué permite hacer?

Permite encontrar información sensible en una interacción y preparar una versión que reduzca el riesgo de exposición sin perder innecesariamente el sentido del texto.

## ¿Quién puede utilizarla?

Las personas participantes la utilizan durante sus interacciones. Los administradores determinan qué formas de detección y tratamientos están disponibles.

## ¿Cómo funciona?

1. El sistema recibe el prompt y el texto de adjuntos compatibles.
2. Busca información sensible mediante modelos, reconocedores estructurales y diccionarios.
3. Combina los resultados y conserva un conjunto coherente de fragmentos.
4. Determina el tratamiento aplicable a cada fragmento.
5. Genera el texto protegido y lo presenta para revisión cuando corresponde.

## Tratamientos disponibles

- **Reemplazo por etiqueta**: sustituye el dato por una descripción como `<PERSONA>` o `<CORREO>`.
- **Enmascaramiento**: oculta una parte o la totalidad del dato.
- **Seudonimización**: utiliza un valor ficticio compatible con el contexto.
- **Conservación**: mantiene el fragmento cuando la regla permite enviarlo.

## Reglas importantes

- Una coincidencia estructural puede requerir validación o palabras de contexto antes de considerarse válida.
- Una colección administrada siempre representa una categoría conocida de información sensible.
- Una detección no determina por sí sola el tratamiento; las reglas vigentes toman esa decisión.
- Un fragmento no reconocido por la clasificación disponible no debe ignorarse silenciosamente.
- El mismo texto se vuelve a analizar después de una edición cuando todavía puede contener información sensible.

## Resultado

La persona obtiene una versión protegida del texto, junto con información suficiente para comprender y revisar las modificaciones propuestas.
