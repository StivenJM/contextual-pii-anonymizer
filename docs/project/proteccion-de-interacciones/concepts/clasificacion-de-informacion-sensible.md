# Clasificación de información sensible

## Propósito

La clasificación ofrece un vocabulario común para describir la información que el sistema puede detectar y proteger. Su estructura se mantiene de forma controlada y no cambia desde la administración cotidiana.

## Grupos de información

| Grupo | Ejemplos |
|---|---|
| Persona | Nombre de una persona. |
| Contacto | Correo electrónico y teléfono. |
| Identidad digital | Nombre de usuario y dirección de un perfil personal. |
| Identificadores | Documento nacional e identificador estudiantil. |
| Información geográfica | Dirección, ubicación y nacionalidad. |
| Información demográfica | Edad. |
| Información temporal | Fechas relacionadas con una persona. |
| Afiliaciones | Relación educativa o laboral con una institución. |

## Niveles de detalle

Una detección puede utilizar un grupo general cuando no existe evidencia suficiente para una categoría más concreta. Por ejemplo, puede reconocer un identificador sin asegurar todavía si se trata de un documento nacional o un código estudiantil.

Cuando dos detecciones compatibles describen el mismo fragmento, el sistema puede conservar la categoría más específica respaldada por la evidencia.

## Alcance e identificabilidad

Además de su significado, una categoría puede indicar:

- si es relevante en cualquier contexto, especialmente en el dominio universitario o solo bajo ciertas circunstancias;
- si suele identificar directamente o si contribuye a identificar cuando se combina con otros datos.

Estas propiedades ayudan a interpretar la información, pero no deciden automáticamente si debe protegerse.

## Evolución

La clasificación puede evolucionar cuando datos reales muestran información sensible que no está representada. Una categoría nueva requiere evidencia, utilidad para la protección y una definición coherente; no se crean grupos genéricos para acumular casos desconocidos.
