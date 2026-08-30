# Visión funcional del Prompt Privacy System

El Prompt Privacy System ayuda a reducir la exposición de información sensible cuando una persona utiliza un modelo de lenguaje comercial. Analiza la interacción antes del envío, propone una protección comprensible y permite trabajar con una versión revisada del texto.

Esta documentación describe el producto objetivo completo. Su alcance combina protección de interacciones, configuración institucional y evaluación experimental en un contexto universitario ecuatoriano.

## ¿Para quién existe?

- **Participantes**: personas con o sin formación técnica que realizan tareas del estudio.
- **Investigadores**: responsables de configurar el estudio, supervisar sesiones y analizar resultados.
- **Administradores**: responsables de configurar y mantener el comportamiento de protección.

Una misma persona puede asumir los roles de investigación y administración cuando el despliegue sea pequeño.

## Capacidades del producto

- Detectar información sensible mediante varias formas de reconocimiento.
- Aplicar tratamientos diferentes según el tipo de información y las reglas vigentes.
- Permitir que la persona revise, edite y confirme el texto protegido.
- Evitar el envío cuando todavía se incumplen reglas obligatorias.
- Configurar modelos, reconocedores, diccionarios y reglas de protección.
- Ejecutar sesiones experimentales con grupos técnicos y no técnicos.
- Medir exposición, aceptación, tiempos, errores y utilidad del texto.
- Consultar y exportar resultados con datos minimizados y trazables.

## Alcance

El producto se concentra en texto en español, interacciones académicas y formatos relevantes para Ecuador. Puede obtener texto de adjuntos compatibles, pero no procesa imágenes, audio o video como contenido multimodal.

La protección reduce exposición, pero no garantiza anonimización irreversible ni reemplaza una evaluación legal completa para un despliegue institucional.

## Módulos funcionales

- [`proteccion-de-interacciones/`](proteccion-de-interacciones/README.md): detección, revisión y protección previa al envío.
- [`experimentacion/`](experimentacion/README.md): sesiones, grupos, mediciones y tratamiento de datos del estudio.
- [`administracion/`](administracion/README.md): configuración del comportamiento de detección y protección.
