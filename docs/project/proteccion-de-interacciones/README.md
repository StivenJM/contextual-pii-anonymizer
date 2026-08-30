# Protección de interacciones

## ¿Para qué sirve?

Este módulo evita que una persona envíe información sensible sin advertirlo. Examina el prompt y el texto extraído de adjuntos compatibles, identifica fragmentos relevantes y prepara una versión protegida para su revisión.

## ¿Quiénes participan?

- **Persona usuaria**: redacta, revisa y confirma el contenido que desea enviar.
- **Administrador**: define las reglas y recursos que orientan la protección.

## Capacidades principales

- Reconocer información sensible por su significado, estructura o pertenencia a colecciones conocidas.
- Resolver detecciones repetidas o superpuestas.
- Reemplazar, enmascarar, seudonimizar o conservar fragmentos según las reglas vigentes.
- Explicar qué tipo de información fue detectada y qué tratamiento se propone.
- Volver a analizar un texto después de una edición manual.
- Impedir que una interacción incumpla una regla obligatoria.

## Conceptos importantes

- **Información sensible**: dato que puede identificar, contactar, ubicar o describir de forma privada a una persona.
- **Detección**: fragmento que el sistema reconoce como perteneciente a una categoría conocida.
- **Tratamiento**: acción aplicada a una detección para reducir su exposición.
- **Texto protegido**: versión revisada que puede enviarse al modelo comercial.

## Más información

- [Detección y protección](capabilities/deteccion-y-proteccion.md)
- [Revisión y envío](flows/revision-y-envio.md)
- [Reglas de protección](rules/tratamiento-de-informacion.md)
- [Clasificación de información sensible](concepts/clasificacion-de-informacion-sensible.md)
