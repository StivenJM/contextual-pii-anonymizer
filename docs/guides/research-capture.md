# Ejecutar la captura para investigación sin el modelo

La implementación es un piloto local, no una aprobación institucional para trabajo de campo con datos identificables. Consulta los límites de validación y preparación que aparecen abajo antes de usarla.

Usa la API de investigación local independiente y la extensión del navegador existente. Esta guía no despliega un servicio, no crea un Google Form, no recluta estudiantes ni autoriza la recolección de datos personales reales.

Para la topología confirmada de equipos propiedad de los estudiantes, sigue el [despliegue en la red universitaria](research-campus-deployment.md). Añade un código de solo inscripción, HTTPS de confianza sobre IP privada y una copia generada de la extensión; no distribuyas la clave local del investigador a los estudiantes.

Para habilitar este mismo router dentro del stack local de Docker, con la API principal y el volumen persistente `research_archive`, consulta la sección 3.1 de [instalar la extensión y arrancar el sistema de desarrollo](developer-startup.md). Esa variante mantiene la inferencia en ejecución por el flujo de adjuntos, pero las peticiones de investigación no la invocan.

## Preparar la API local

Desde la raíz del repositorio en PowerShell:

~~~powershell
uv sync --directory api --frozen
$env:RESEARCH_ENABLED = "true"
$env:RESEARCH_API_KEY = (& api\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))").Trim()
$env:RESEARCH_STORAGE_PATH = Join-Path (Get-Location).Path "workspace\research\capture.sqlite3"
$env:RESEARCH_PROTOCOL_VERSION = "research-v1"
$env:RESEARCH_RETENTION_DAYS = "30"
uv run --directory api --no-sync python -m uvicorn app.research.application:app --host 127.0.0.1 --port 8000 --no-access-log
~~~

El primer comando instala las dependencias de desarrollo fijadas y puede contactar registros de paquetes. El último comando ejecuta el listener local en primer plano; no arranca PostgreSQL, BentoML, Docker ni el conversor. Detenlo con Ctrl+C. El puerto 8000 debe estar libre; no detengas un proceso ajeno de forma automática. El `compose.yaml` ordinario conserva su flujo respaldado por el modelo; esta aplicación independiente no lo modifica.

Mantén la clave en el canal seguro de configuración del operador y pégala en el campo de contraseña de la extensión. No la imprimas ni la envíes a un chat de IA, y no la pongas en Forms. El popup no la guarda después de iniciar. La extensión sí conserva una capacidad de sesión distinta para reintentos y retiro. Configura una retención aprobada antes de usar datos reales; «30» es un ejemplo de piloto, no una aprobación institucional.

El archivo de ejemplo está dentro del directorio `workspace/` ya ignorado. No muevas archivos reales a rutas versionadas. La API además exige una ruta absoluta. Usa almacenamiento local cifrado y aprobado por la institución y restringe los permisos; la aplicación por sí misma no ofrece cifrado en reposo. Para una operación supervisada y persistente, define estas variables en la configuración de secretos de la cuenta de servicio aprobada, no en archivos `.env` versionados.

Abre [la documentación local de la API](http://127.0.0.1:8000/docs). La aplicación independiente expone a propósito solo las rutas de investigación; `/api/research/health` comprueba la configuración del recolector y el acceso al archivo, mientras que `/api/health` y `/api/interactions/protect` no forman parte de ese punto de entrada. El mismo router `/api/research` también está montado en la aplicación principal ordinaria, pero esa aplicación conserva su requisito habitual de arranque con PostgreSQL.

## Extensión: ensayo sintético

1. Recarga `browser-extension/extension` como extensión descomprimida en un perfil de prueba dedicado de Chromium o Chrome. Los permisos de host existentes ya cubren los tres sitios comerciales compatibles y la API de loopback.
2. Abre un chat compatible nuevo y vacío, sin historial personal ni adjuntos cargados. Confirma manualmente el adaptador actual de editor, envío y respuesta antes de invitar estudiantes. Este trabajo no inició sesión ni operó una cuenta real de proveedor.
3. Abre la ventana de la extensión desde su icono o, si no está fijado, desde el menú de extensiones. Puedes fijar el icono a la barra del navegador; la ventana no se fija sola. En **Captura de chats**, introduce **Clave local del investigador** y el protocolo. La interfaz de investigación usa etiquetas y mensajes en español; la documentación técnica canónica sigue en inglés. Lee la advertencia de recolección sin procesar, marca el consentimiento de forma explícita y deja sin marcar el permiso opcional de entrenamiento salvo que se haya acordado aparte.
   Estos campos de configuración y consentimiento se deshabilitan al iniciar la sesión: cambiar una casilla no puede modificar en silencio un acuerdo ya almacenado. Usa **Descartar sesión** y el proceso aprobado del investigador para un cambio de consentimiento.
4. Pulsa **Iniciar en esta pestaña**. Cuando el controlador confirma la activación aparece un único aviso **Captura activa** en la página, con un botón **×** de cierre. El aviso desaparece solo tras unos seis segundos y suspende su cuenta atrás mientras el puntero o el foco están dentro. Cerrarlo no detiene, pausa, guarda ni descarta la sesión, y no vuelve a aparecer al enviar mensajes, al actualizar respuestas ni al abrir o cerrar la ventana. No deja burbujas ni controles flotantes: el estado se consulta solo desde la ventana de la extensión. La preferencia de protección de adjuntos se conserva; la protección se pausa solo en esa pestaña seleccionada mientras la captura graba o está en pausa. Las demás pestañas mantienen su comportamiento anterior.
   El popup muestra el progreso y los errores junto a la acción de inicio. Un inicio fallido conserva los campos actuales del formulario; una activación correcta limpia la clave. La clave no se persiste en el almacenamiento del navegador y cerrar el popup descarta los campos transitorios. El rechazo por historial y la ausencia de editor tienen mensajes separados. Un editor vacío puede no mostrar Enviar hasta que escribas; el arranque lo permite, pero el envío real sigue bloqueado salvo que exista un control de envío visible, habilitado y compatible, y el almacenamiento local confirme el prompt.
5. Define **Identificador de tarea** como A y pulsa **Asignar tarea**; después usa los identificadores de tarea siguientes que correspondan. Envía solo texto ficticio. El envío compatible espera el almacenamiento local; las respuestas se observan como instantáneas renderizadas. Espera a que termine la respuesta antes de cambiar de tarea o finalizar.
6. Pulsa **Finalizar y guardar**. Solo una respuesta confirmada de la API muestra el identificador guardado. Usa **Copiar identificador**; si el portapapeles falla, la ventana deja el identificador seleccionado para copiarlo manualmente. Guárdalo en un lugar seguro y pégalo en el último elemento del formulario aprobado del estudio.
7. Si la API no responde, la ventana muestra **Pendiente de guardar** y el motivo. Los datos permanecen en el navegador: usa **Reintentar guardado** sin volver a recolectar y sin borrar el perfil.
8. Para retirar un registro ya guardado, usa **Retirar sesión guardada**. Si el retiro no se confirma, la ventana queda en **Retiro pendiente** y ofrece **Reintentar retiro**; el texto sin anonimizar ya se eliminó del navegador.

El icono de la extensión resume el estado con una etiqueta y un texto descriptivo al pasar el cursor: sin etiqueta cuando no hay captura o el guardado está confirmado, `…` al iniciar, `REC` solo en la pestaña capturada, `!` ante una interrupción o un retiro pendiente, y `PEND` cuando la sesión está detenida esperando confirmación. Un incidente bloqueante tiene prioridad sobre la etiqueta de captura saludable. Los pendientes siguen visibles al cambiar de pestaña o cerrar la original. La extensión no define atajos de teclado propios: los botones de la ventana y el cierre del aviso bastan, y los controles conservan su comportamiento normal con teclado.

Cuando un envío se bloquea, un aviso cerrable explica el motivo sin desaparecer solo; cerrarlo no resuelve el incidente ni cambia las reglas de bloqueo, y el mismo incidente no reaparece en cada reintento. El detalle permanece consultable en la ventana de la extensión.

Una pestaña cerrada o recargada puede guardarse como INTERRUMPIDA; informa al investigador. Una sesión de grabación está atada a un documento, no a toda la actividad del navegador. Las rutas no compatibles de adjuntos, voz o imagen no se capturan. Las sesiones vacías deben descartarse, no «guardarse» falsamente.

La detección del editor de ChatGPT también reconoce el marcado suministrado `textarea[data-mobile-composer-prompt]`, sin depender de clases CSS generadas ni ampliar la detección a cualquier textarea. Los fixtures locales ejercitan la activación, el envío por clic o Enter y el archivado de texto exacto con ese editor; no establecen compatibilidad con los controles de envío, el historial ni el marcado de respuesta del layout real. Ensáyalos de forma independiente antes de recolectar con participantes.

## Acceso, retiro y retención

- El identificador de recibo tiene 32 caracteres base64url sensibles a mayúsculas. Identifica un registro; no permite leerlo sin la clave del investigador.
- El personal autorizado puede recuperar un registro con GET /api/research/records/{receipt_id} y X-Research-Key. Protege las exportaciones igual que el archivo original. No hay sincronización en vivo con formularios ni panel público de respuestas.
- **Descartar sesión** y **Retirar sesión guardada** piden confirmación, detienen la recolección y borran de inmediato el texto local sin procesar. Usa la capacidad de sesión para eliminar la sesión actual o el último registro guardado; si la API no está disponible, solo conserva los metadatos y la capacidad de eliminación, y la ventana queda en **Retiro pendiente** con **Reintentar retiro**. La protección ordinaria se reanuda durante una subida o un retiro pendiente. Las respuestas de Forms, el historial externo del chatbot, los respaldos y los modelos entrenados necesitan el [procedimiento separado de vinculación y retiro](../project/experimentacion/research-study/instruments.md).
- Para un retiro aprobado mediado por el investigador, DELETE /api/research/records/{receipt_id} con X-Research-Key elimina el registro archivado por código. Nunca expongas esta clave a una página de participante ni a un formulario.
- Las sesiones expiradas no se pueden completar ni exportar. Los operadores autorizados deben programar POST /api/research/purge-expired con X-Research-Key y alinear la expiración de los respaldos. No hay un programador instalado en silencio. Valida el conteo de eliminados; nunca supongas que la expiración ya borró los medios de respaldo.
- El popup conserva solo el último recibo y su capacidad tras un guardado correcto, no los eventos sin procesar. Cópialo antes de completar otra sesión. La institución debe mantener sus registros restringidos de vinculación y retiro.

## Repetición de desidentificación sin conexión

La recolección nunca llama al modelo. Después, los investigadores autorizados pueden usar el entorno ordinario de la API, con su base de datos, configuración y servicio de inferencia existentes, para evaluar el texto elegible de participantes archivado. Obtén el registro consentido mediante la autorización de investigador y después envía POST `{"text": "un prompt reservado enviado"}` a /api/interactions/protect en ese entorno, conservando un manifiesto separado de salida y ejecución. No envíes el formulario de identidad ni las capacidades de sesión al modelo.

Usa el [plan de análisis](../project/experimentacion/research-study/analysis-plan.md): particiones disjuntas por participante, etiquetas de referencia independientes, modelos y configuración congelados y reporte separado de utilidad y error. Esta guía no entrena un modelo ni envía automáticamente un conjunto de datos a ningún lugar.

## Comandos de verificación

~~~powershell
# Desde la raíz del repositorio; las pruebas usan solo fixtures sintéticos.
uv run --directory api --no-sync pytest -q
node --test browser-extension/tests/*.test.cjs
uv run --directory e2e --no-sync pytest -q -m "not integration"
# Regresión opcional de sistema completo ya existente; requiere Docker y compila imágenes.
uv run --directory e2e --no-sync pytest -q -m integration
~~~

Los casos de navegador de investigación arrancan un proceso real de API sin modelo en un puerto de loopback libre y accionan la extensión real en el Chromium incluido contra chats locales sintéticos. Verifican la finalización normal, los cambios de conversación, la pérdida de respuesta después de que la API confirma, un fallo de cuota local antes del envío, la recuperación tras recargar y la protección simultánea en otra pestaña. La recolección de investigación hace cero peticiones al conversor y de protección; la regresión deliberada de la otra pestaña hace una de cada una para demostrar que la ruta original sigue funcionando en otro lugar. No se llama a ningún chatbot en la nube. Instala las dependencias de e2e y Chromium como se describe en [pruebas de integración](integration-testing.md).

## Validación observada

Verificación funcional final el 2026-10-30:

La tabla siguiente registra el hito anterior de implementación local. Después de la adaptación al campus, la suite de la API pasó **70 pruebas con 2 omisiones por PostgreSQL local**, Node pasó **14**, y las comprobaciones de navegador y preparación sin contenedores pasaron **21 con 3 casos de Docker deseleccionados**. Un ensayo separado de Docker/TLS de producción también pasó. Consulta el [límite de prueba del despliegue en campus](research-campus-deployment.md#verificación-y-límites); las pruebas locales no establecen la preparación real de la universidad ni del proveedor.

| Comprobación | Resultado observado |
|---|---|
| Suite de la API | 66 pasadas, 2 omisiones que dependen de PostgreSQL local; 1 advertencia de deprecación preexistente de TestClient de Starlette/httpx |
| Suite de controlador y aislamiento en Node | 13 pasadas |
| Suite completa de Chromium | 14 pasadas, incluidos los seis casos de investigación y dos casos de integración con Docker |
| Revisión final de consentimiento e interfaz | 12 pasadas, 2 casos de Docker deseleccionados; las rutas de contenedor sin cambios ya habían pasado la suite completa |
| Contratos reales de PostgreSQL y API | Ejecutados correctamente dentro del contenedor aislado de la API por la suite de integración; las omisiones locales no cuentan como aprobadas |
| Diferencial base frente a eccf825 | Resultados idénticos en 4 comprobaciones de estado, 4 de mensajes de adjuntos y 4 de normalización de Markdown usando una copia temporal externa |
| Superficies Python modificadas | Lint de Ruff y comprobación de formato pasaron |
| JavaScript | El background y los tres scripts de investigación pasaron las comprobaciones de sintaxis |
| Documentación | 19 páginas Markdown nuevas o modificadas revisadas, cero destinos locales faltantes; 32 claves bibliográficas únicas con llaves BibTeX balanceadas |

El popup también se renderizó con datos sintéticos y se inspeccionó visualmente. No se lanzó ningún trabajador ni revisor de IA independiente, siguiendo la instrucción explícita del usuario de trabajar solo en línea; no se afirma una aprobación de revisión nativa.

Durante el desarrollo, la preparación de pruebas encontró primero acceso restringido al directorio temporal, una espera de cadena en una página de extensión que chocaba con la CSP y un doble de prueba de dos pestañas al que le faltaba un permiso de host en la copia de prueba. Se corrigieron en la preparación de pruebas sin debilitar la CSP ni los permisos del producto. Se reprodujeron con pruebas de regresión y se corrigieron un defecto real de mezcla de historial de conversación y defectos de aislamiento de la protección global y de estado pendiente. Los resultados finales anteriores superan esos fallos intermedios.

Sin verificar hasta que se autorice o realice por separado: adaptadores de proveedores reales y el comportamiento actual de las interfaces en la nube, Firefox, despliegue universitario real, confianza de clientes, enrutamiento, cifrado y política de respaldos, vinculación con Google Forms en vivo, estudiantes reales y comparaciones con modelos entrenados. Los comandos locales anteriores siguen apuntando a una sola estación de trabajo y un solo perfil. Los [artefactos separados de despliegue en campus](research-campus-deployment.md) preparan el recolector compartido con IP privada y la extensión específica del endpoint; no lo despliegan automáticamente en un equipo universitario.

## Diagnóstico

| Síntoma | Acción |
|---|---|
| 404 en rutas de investigación | Confirma `RESEARCH_ENABLED=true` en el proceso en ejecución; las rutas de salud normales no existen en la aplicación independiente |
| 503 de configuración | Usa una clave de al menos 32 caracteres, una ruta absoluta del archivo y una retención entre 1 y 365 días |
| 401 al crear o exportar una sesión | Revisa la clave de configuración; nunca la pegues en el chatbot |
| El inicio se queda en `starting` | La autorización o la activación se interrumpió; descarta esa configuración y empieza una sesión nueva y vacía |
| Adaptador no disponible | Usa una conversación nueva y revisa los selectores actuales del sitio; detén el piloto si no puedes verificar la captura |
| Pendiente / API inalcanzable | Arranca la misma API y el mismo archivo locales y reintenta la subida congelada; no borres el estado local |
| Retirando / API inalcanzable | El texto local sin procesar ya se borró; usa **Reintentar retiro** en la ventana de la extensión para que la capacidad conservada termine la eliminación en la API |
| 409 al completar | Conserva la copia local; investiga el desajuste, nunca sobrescribas el registro guardado |
| Límite local alcanzado | Detén y guarda; el envío compatible se bloquea en lugar de descartar texto en silencio |
| Recibo perdido | Contacta al personal aprobado del estudio; no busques registros de otros estudiantes ni adivines un código |

[Plan](../project/experimentacion/research-capture-plan.md) · [Arquitectura y decisiones](../architecture/backend/privacy-middleware/research-capture.md) · [Kit del estudio](../project/experimentacion/research-study/README.md)
