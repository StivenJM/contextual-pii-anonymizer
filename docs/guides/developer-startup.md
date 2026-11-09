# Instalar la extensión y arrancar el sistema de desarrollo

Guía para Windows/PowerShell. Instala primero la extensión del navegador y después arranca **solo los servicios que necesita el flujo que vas a probar**. Usa datos ficticios en todo el procedimiento. Esta guía no autoriza un despliegue universitario ni la recolección de datos de estudiantes reales.

## 1. Instala primero la extensión del navegador

La extensión es JavaScript puro: esta instalación no requiere `npm install`, una compilación de JavaScript, un servicio de Docker ni un modelo en ejecución.

1. Abre Google Chrome con un perfil de desarrollo dedicado. Evita un perfil con historial de chats personales o cuentas sensibles ajenas al proyecto.
2. Abre `chrome://extensions` y activa el **modo de desarrollador**.
3. Pulsa **Cargar descomprimida** y selecciona **`browser-extension/extension` dentro de este repositorio**. Elige la carpeta que contiene `manifest.json`, no la raíz del repositorio, ni `browser-extension/backend`, ni una copia de prueba en `e2e/.build`.
4. Confirma que **PDF Middleware** aparece habilitada. Fija su icono en la barra si te resulta útil.
5. Copia el **ID** de la extensión que muestra la página de extensiones. El conversor usa ese ID como origen permitido del navegador; instalarla primero evita adivinar ese valor.
6. Abre el popup. Deben estar presentes la interfaz existente de adjuntos y la sección separada **Captura para investigación (solo texto)**. Sus controles y mensajes para participantes están en español. Instalar la extensión por sí sola no arranca ningún backend ni activa la captura para investigación.
7. Después de cargar o recargar la extensión, actualiza cualquier pestaña de chat compatible que ya estuviera abierta. Para las pruebas de captura, empieza una conversación nueva y vacía.

El manifest cubre ChatGPT, Claude y Gemini. Las pruebas sintéticas locales en Chromium no demuestran que las interfaces reales actuales funcionen; ensaya manualmente cada proveedor previsto antes del trabajo de campo. Firefox y otros navegadores no son la ruta validada en esta guía. Si la política universitaria deshabilita las extensiones sin empaquetar, consigue la ruta de instalación aprobada por TI en lugar de saltarte esa política.

Después de editar el JavaScript o el manifest de la extensión, vuelve a `chrome://extensions`, pulsa **Recargar** en su tarjeta y actualiza la pestaña del chat. Recargar el navegador no es una migración de datos: termina o descarta una sesión de investigación antes de cambiar la extensión o la configuración. No elimines la extensión ni borres su almacenamiento mientras haya una subida o un retiro pendiente.

Si Chrome informa un error de carga, revisa los detalles del error en la tarjeta de la extensión antes de continuar. Mantén la consola del service worker sin texto ni credenciales reales; una captura de pantalla de una instalación correcta no demuestra que el backend o el adaptador del sitio funcionen.

Procedimiento oficial de instalación: [Chrome: cargar una extensión descomprimida](https://developer.chrome.com/docs/extensions/get-started/tutorial/hello-world#load-unpacked).

## 2. Entiende los procesos antes de arrancarlos

| Componente | Origen | Qué hace | Dirección local por defecto |
|---|---|---|---|
| Extensión del navegador | `browser-extension/extension/` | Flujo existente de adjuntos más la captura de texto para investigación, habilitada de forma explícita | Barra del navegador |
| Conversor de adjuntos | `browser-extension/backend/` | Convierte adjuntos PDF/Office compatibles a Markdown | `http://localhost:5000/convertir` |
| API de privacidad original | `api/app/main.py` | Detección, política y desidentificación; PostgreSQL almacena la configuración | `http://127.0.0.1:8000` |
| Servicio de inferencia | `inference/` | Ejecuta el modelo de detección de privacidad que usa la API original | Dirección interna de Compose `http://inference:3000` |
| PostgreSQL | Servicio `db` del Compose raíz | Configuración de privacidad, mapeos de etiquetas, reconocedores, listas y reglas; no guarda chats de investigación | Dirección interna de Compose `db:5432` |
| API de investigación independiente | `api/app/research/application.py` | Autoriza la captura, guarda sesiones finalizadas en SQLite y devuelve identificadores | `http://127.0.0.1:8000` |

**SQLite pertenece al módulo de investigación, no al conversor.** El router de investigación también está montado en la API original, pero su punto de entrada independiente evita los requisitos de arranque de PostgreSQL e inferencia de la API original.

Dos flujos de desarrollo útiles:

- **Captura para investigación:** sigue la sección 3. No necesita conversor, PostgreSQL ni modelo de inferencia.
- **Conversión y protección de adjuntos original:** sigue la sección 4. Necesita el conversor **y** el stack principal de API/PostgreSQL/inferencia.

La API de investigación independiente y la API original usan por defecto el mismo puerto de host **8000**. No las arranques al mismo tiempo en ese puerto. La extensión de fuentes ordinaria usa la API de loopback; un despliegue en campus requiere una copia de extensión generada aparte y HTTPS de confianza, no cambiar la URL a HTTP plano sobre una IP privada.

## 3. Arrancar la captura para investigación sin modelo

### Requisitos

- `uv` instalado: [instrucciones oficiales de instalación](https://docs.astral.sh/uv/getting-started/installation/).
- Acceso de red para la primera instalación bloqueada de dependencias y de Python si no está en caché. La API requiere Python 3.14 o superior; `uv` puede provisionar un intérprete compatible.
- Puerto 8000 libre en el host y un perfil de navegador dedicado para pruebas locales.

Ejecuta desde la raíz del repositorio en la **terminal A**:

```powershell
uv sync --directory api --locked
$RepoRoot = (Get-Location).Path
$env:RESEARCH_ENABLED = "true"
$env:RESEARCH_API_KEY = (& api/.venv/Scripts/python.exe -c "import secrets; print(secrets.token_urlsafe(32))").Trim()
$env:RESEARCH_STORAGE_PATH = Join-Path $RepoRoot "workspace/research/capture.sqlite3"
$env:RESEARCH_PROTOCOL_VERSION = "research-v1"
$env:RESEARCH_RETENTION_DAYS = "7"
```

Siete días es un **ejemplo ficticio de desarrollo**, no un periodo de retención aprobado para un estudio real. La ruta del archivo es absoluta y está dentro de `workspace/`, que ya está ignorado; la documentación del proyecto sigue en `docs/`.

Usa una terminal dedicada y limpia. Si ya hay fuentes de secretos `_FILE` de investigación o ajustes de solo inscripción configurados, no mezcles fuentes de secretos en conflicto; usa la [guía detallada de captura](research-capture.md) o el runbook de campus. No sobrescribas credenciales institucionales para un ensayo local.

Solo para este ensayo local sintético, copia la clave de operador generada en el campo **Clave local del investigador** de la extensión. Transferirla por el portapapeles de PowerShell evita imprimirla en los logs del servicio:

```powershell
Set-Clipboard -Value $env:RESEARCH_API_KEY
```

Pégala únicamente en ese campo de la extensión, nunca en el chatbot ni en Forms. Esto coloca a propósito una credencial de desarrollo en el portapapeles; no uses historial ni sincronización en la nube para credenciales reales, y limpia el portapapeles y su historial después de transferirla. Este atajo de clave de operador local **no** debe distribuirse a estudiantes. Un paquete de campus usa un código de inscripción aparte.

Después arranca el recolector en la terminal A:

```powershell
uv run --directory api --no-sync python -m uvicorn app.research.application:app --host 127.0.0.1 --port 8000 --no-access-log
```

Mantén abierta la terminal A. En la **terminal B**, verifica la disponibilidad:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/research/health
```

Debes obtener `status: ready`. La documentación interactiva local de la API está en `http://127.0.0.1:8000/docs`. La aplicación independiente no expone las rutas originales `/api/health` ni `/api/interactions/protect`.

### Confirmar el flujo de investigación

1. Abre un chat compatible nuevo; usa las [tarjetas de escenario ficticias](../project/experimentacion/research-study/scenario-cards.md).
2. Abre el popup. Confirma que **API de investigación** apunta a `http://127.0.0.1:8000`, introduce la clave de desarrollo y `research-v1`, y revisa explícitamente el consentimiento de recolección. El permiso opcional de entrenamiento queda sin marcar salvo que se haya acordado aparte.
3. Pulsa **Iniciar en esta pestaña**. Confirma el indicador de grabación antes de enviar nada. El modo de investigación graba texto sin procesar; no lo desidentifica antes de que el chatbot externo lo reciba. Solo pausa la protección ordinaria de adjuntos en la pestaña seleccionada mientras graba o está en pausa.
   El progreso y los errores aparecen justo encima de ese botón. Una conversación existente se rechaza de forma explícita: abre un chat nuevo y vacío en lugar de intentar importar su historial. Un editor vacío visible puede no mostrar el botón de envío hasta que escribas; eso ya no impide la activación. Un editor o adaptador de página ausente es un error distinto. Los inicios fallidos conservan los campos de configuración en el popup actual; la clave solo se limpia después de una activación confirmada y nunca se guarda como configuración del popup. Cerrar el popup del navegador sigue descartando sus campos transitorios.
4. Define **Identificador de tarea** y pulsa **Asignar tarea**; envía texto ficticio y espera a que termine la respuesta. El modo de investigación es solo texto: no adjuntes archivos.
5. Pulsa **Finalizar y guardar / reintentar**. Una confirmación de la API debe mostrar un identificador. Usa **Copiar identificador**; no consideres que un búfer local es un guardado correcto en la API.
6. Si la subida falla, conserva el perfil y la extensión y reintenta. No borres el almacenamiento del navegador para resolver el error. **Descartar / retirar sesión** es la ruta explícita de eliminación, con su propia confirmación y semántica de reintento.

Los demás límites de la operación de investigación, el consentimiento, la exportación y los procedimientos de retiro están en [captura sin modelo](research-capture.md). Nada de este ensayo crea un Google Form ni autoriza reclutamiento.

## 4. Arrancar el flujo original de adjuntos y protección

Si el proceso independiente de investigación de la sección 3 está usando el puerto 8000, detenlo con **Ctrl+C en su propia terminal** después de resolver el trabajo pendiente. No termines un proceso ajeno de forma automática. No inicies una grabación de investigación durante este ensayo de adjuntos.

### 4.1 Preparar Docker y la configuración de la API principal

Instala o arranca Docker Desktop con contenedores Linux y una versión de Compose que admita `--watch` y entradas opcionales de `env_file`. Estos comandos compilan imágenes y el servicio de inferencia puede descargar y cachear un modelo grande en el primer arranque; dale tiempo, espacio en disco y acceso de red. No los ejecutes solo para comprobar un cambio de Markdown.

Las plantillas de Compose versionadas son:

- `api/.db.dev.env`: ajustes de base de datos. Dentro de Docker, `POSTGRES_HOST=db` es correcto.
- `api/.api.dev.env`: ajustes de inferencia. Dentro de Docker, `BENTOML_URL=http://inference:3000` es correcto.

Crea las sobreescrituras locales privadas **solo si no existen todavía**:

```powershell
if (-not (Test-Path api/.db.env)) {
    Copy-Item api/.db.dev.env api/.db.env
}
if (-not (Test-Path api/.api.env)) {
    Copy-Item api/.api.dev.env api/.api.env
}
```

Edita `api/.db.env` y reemplaza la contraseña de ejemplo por una contraseña de desarrollo solo local. Tanto la base de datos como la API cargan esa sobreescritura. Mantén estos archivos privados fuera de Git y no uses credenciales de producción. En el checkout actual no existe un `.env.example` en la raíz; no sigas instrucciones antiguas que lo mencionen.

Cambiar `POSTGRES_PASSWORD` en un archivo de entorno no cambia automáticamente las credenciales dentro de un volumen de base de datos ya inicializado. Para un entorno existente, conserva la configuración que coincide o usa un procedimiento autorizado de cambio de credenciales; no borres su volumen como atajo.

### 4.2 Arrancar PostgreSQL, la inferencia y la API de privacidad

Desde la raíz del repositorio en la terminal A:

```powershell
docker compose up --build --watch
```

Esto arranca `db`, `inference` y `api`. **No arranca el conversor.** La API espera los health checks de base de datos e inferencia y aplica las migraciones de Alembic antes de que arranque su servidor de desarrollo. Son cambios reales en la base de datos cuando el desarrollador ejecuta el comando; no se ejecutó ninguna migración solo por redactar esta guía.

En la terminal B:

```powershell
docker compose ps
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

La respuesta de salud original contiene `status: active`. Abre `http://127.0.0.1:8000/docs` para su API interactiva. PostgreSQL y la inferencia son solo internos en este Compose; no esperes conexiones desde el host a los puertos 5432 ni 3000, y no cambies el binding de loopback de la API para exponer la Admin API de desarrollo.

Administración de desarrollo opcional: reemplaza el comando de arranque por `docker compose --profile dev up --build --watch` para incluir pgAdmin en `http://127.0.0.1:9001`. Sus valores por defecto actuales son solo de desarrollo; no publiques ese servicio en la red del campus. Dentro de pgAdmin, el host de la base de datos es `db`, no el `localhost` del equipo con el navegador.

### 4.3 Arrancar el conversor por separado

El conversor necesita el ID de la extensión de Chrome de la sección 1 y un token de desarrollo que coincida con `SECRET_TOKEN` en `browser-extension/extension/background.js`. Ese token viene incluido en el código de la extensión y no es una credencial confidencial de producción. No lo confundas con las credenciales de inscripción, administración o sesión de investigación.

En la **terminal C**, desde la raíz del repositorio:

```powershell
$ExtensionId = "<copy the 32-character ID from chrome://extensions>"
if ($ExtensionId -notmatch '^[a-p]{32}$') {
    throw "Replace the placeholder with the actual Chrome extension ID."
}
$Background = Get-Content browser-extension/extension/background.js -Raw
$TokenMatch = [regex]::Match($Background, "(?m)^const SECRET_TOKEN = '([^']+)';")
if (-not $TokenMatch.Success) {
    throw "Read the current extension token configuration; do not invent a token."
}
$env:MIDDLEWARE_SECRET = $TokenMatch.Groups[1].Value
$env:EXTENSION_ID_CHROME = $ExtensionId
docker build -t contextual-pii-converter:dev browser-extension/backend
docker run --rm --name contextual-pii-converter-dev -p 127.0.0.1:5000:5000 --env MIDDLEWARE_SECRET --env EXTENSION_ID_CHROME contextual-pii-converter:dev
```

Esto usa el Dockerfile existente del conversor sin editar el Compose principal. Se ejecuta en primer plano y ata el listener del host al loopback. Su ruta existente `/convertir` espera el campo multipart `archivo` y la cabecera `X-Token`; la extensión los aporta. El CORS del conversor usa `EXTENSION_ID_CHROME`; si el ID de la extensión cargada cambia, reinicia el conversor con el ID correcto.

La documentación de la API del conversor está en `http://127.0.0.1:5000/docs`; eso solo demuestra que el proceso web es alcanzable, no que todos los formatos de documento se conviertan correctamente. Las dependencias vienen del archivo de requisitos actual del conversor; este servicio es un backend de desarrollo separado, no el archivo de investigación.

### 4.4 Confirmar el flujo de adjuntos con contenido ficticio

1. Confirma que responden las dos URLs de documentación local y que el Compose principal está saludable.
2. Actualiza una pestaña de chat compatible. Mantén la extensión **Activada**, con la captura para investigación inactiva.
3. Crea un documento PDF/Office pequeño y válido con texto ficticio y adjúntalo usando una ruta de selector o de arrastre compatible. El conversor admite `.pdf`, `.docx`, `.doc`, `.xlsx`, `.xls` y `.pptx`; un archivo `.txt` plano no sirve como prueba de humo del conversor.
4. Confirma la conversión, la protección de privacidad y el reemplazo del adjunto. Revisa los errores en lugar de suponer que el archivo original quedó protegido cuando una operación falló. El comportamiento del proveedor real todavía necesita validación manual.

La protección ordinaria actualmente se dirige a los adjuntos; el texto escrito en el chat no queda protegido en general solo porque el interruptor diga **Activada**. La captura para investigación es un modo aparte, de activación explícita, y no es protección. Consulta [pruebas de integración](integration-testing.md) para las regresiones sintéticas en navegador y las de Docker aislado.

## 5. Detener sin borrar los datos almacenados

| Proceso | Procedimiento de parada |
|---|---|
| API de investigación independiente | Ctrl+C en su propia terminal; el archivo de almacenamiento permanece |
| Conversor en primer plano | Ctrl+C en la terminal C; `--rm` elimina ese contenedor, no el archivo de investigación |
| Stack principal de desarrollo | Ctrl+C para detener su sesión en primer plano; desde la raíz del repositorio ejecuta `docker compose down` cuando quieras eliminar esos contenedores y redes |

No uses `down --volumes`, poda de volúmenes ni borres el perfil del navegador o el archivo de investigación para diagnosticar un despliegue del estudio. El `docker compose down` ordinario conserva los volúmenes nombrados de PostgreSQL y de la caché del modelo. Los logs y el historial del navegador no son un procedimiento de respaldo del archivo.

## 6. Diagnóstico

| Síntoma | Comprobación |
|---|---|
| La extensión no aparece | Carga la carpeta que contiene `manifest.json`; asegúrate de que la política permita extensiones de desarrollo sin empaquetar |
| La actualización de la extensión parece ignorarse | Recarga su tarjeta y después actualiza la pestaña del proveedor; no lo hagas a mitad de una sesión |
| El puerto 8000 ya está en uso | Elige un solo flujo local de API; no mates procesos ajenos ni supongas que aplica la ruta de salud de la otra aplicación |
| La salud de investigación devuelve 404/503 | Comprueba la habilitación explícita, la ruta absoluta, la retención y que no haya fuentes de secretos en conflicto en ese proceso |
| La captura se queda en `Iniciando` (`starting` internamente) | La autorización o activación se interrumpió; usa el procedimiento documentado de descarte y reintento, no borres el almacenamiento |
| El inicio dice que la conversación ya tiene mensajes | Abre una conversación nueva y vacía; el historial se excluye a propósito, no se importa ni se borra |
| El inicio no encuentra el editor del chat | Espera a que cargue la página; después de actualizar la extensión refresca la pestaña y usa un chat compatible nuevo. No confundas la ausencia del botón de envío en un editor vacío con un editor ausente |
| El conversor devuelve 401 | Su `MIDDLEWARE_SECRET` debe coincidir con el token de desarrollo de la extensión; las claves de investigación no lo sustituyen |
| Falla el CORS del conversor | Revisa el ID de la extensión cargada y reinicia el conversor después de cambiar su entorno de origen permitido |
| El conversor responde pero falla la protección | También debe estar disponible el stack principal de API/inferencia, no solo el puerto 5000 |
| La API principal sigue arrancando | Revisa `docker compose logs --tail 50 inference api`; la primera preparación del modelo puede tardar; no registres prompts reales |
| Falla la autenticación de la base de datos tras editar `.db.env` | Las credenciales del volumen existente pueden ser distintas; no borres la base de datos para resolver un desajuste de contraseña |
| El paquete de campus falla desde casa o fuera de la red | Es privado del campus a propósito; sigue el procedimiento aprobado de red y TLS, no desactives advertencias de certificado |

## 7. Verificación y lecturas siguientes

Los nombres de servicios, rutas y configuración, y la ayuda de la CLI de arranque, se revisaron al escribir esta guía. Las pruebas sintéticas locales de software están registradas en la guía de captura, incluida la recuperación tras un inicio fallido y un botón de envío que aparece solo después de escribir. Las instrucciones de prueba de humo del conversor y del proveedor real siguen requiriendo que el desarrollador haga el ensayo; no son una afirmación de que se haya probado una cuenta real de navegador, un host universitario ni un adaptador de proveedor.

- [Revisión de riesgos para el propietario del proyecto](../project/experimentacion/research-study/security-risk-review.md): riesgos condicionales, controles existentes y decisiones pendientes; no es aceptación de riesgo.
- [Captura local sin modelo](research-capture.md): ciclo de vida detallado, pruebas de API y procedimientos de acceso.
- [Despliegue en la red universitaria](research-campus-deployment.md): recolector de producción, HTTPS de confianza sobre IP privada y extensión de campus generada. No uses el stack de desarrollo para desplegar con estudiantes.
- [Infraestructura con Docker](infraestructura-local-con-docker.md): límites actuales de red, entorno y persistencia.
- [Pruebas de integración](integration-testing.md): verificación sintética real y requisitos del runner de pruebas.
- [README de la API](../../api/README.md): rutas y estructura del componente.
