# Instalar la extensión y arrancar el sistema de desarrollo

## 0. Elementos del sistema

El sistema cuenta con 6 elementos de los cuales 5 son servicios que corren en docker y 1 es la extensión del navegador:

1. Servicio db - base de datos
2. Servicio inference - servicio fastapi que sirve modelos con BentoML
3. Servicio converter - servicio para cambiar adjuntos por markdown
4. Servicio pgadmin - servicio solo en "desarrollo" para acceso a la BD
5. Servicio api - servicio de anonimización
6. Extensión de navegador

## 1. Requisitos y preparación inicial

### 1.1 Requisitos

- Docker Desktop y Compose.
- Google Chrome con un perfil de desarrollo dedicado. Evita un perfil con historial de chats personales o cuentas sensibles ajenas al proyecto.
- Opcional: `uv` y Python para ejecutar las pruebas de la API o la aplicación independiente sin modelo de IA.

> El primer arranque compila imágenes y el servicio de inferencia puede descargar y cachear un modelo grande. Necesita de tiempo, espacio en disco y acceso de red.

### 1.2 Instalar la extensión del navegador

La extensión es JavaScript puro: esta instalación no requiere `npm install`, una compilación de JavaScript ni un servicio de Docker.

1. Abre `chrome://extensions` y activa el **modo de desarrollador**.
2. Pulsa **Load unpacked** y selecciona **`browser-extension/extension` dentro de este repositorio**.
3. Confirma que **IA Middleware** aparece habilitada. Fija su icono en la barra si te resulta útil.
4. Copia el **ID** de la extensión que muestra la página de extensiones. El conversor usa ese ID como origen permitido del navegador; instalarla primero evita adivinar ese valor.
5. Abre el popup. Deben estar presentes la interfaz existente de adjuntos y la sección separada **Captura para investigación (solo texto)**.
6. Después de cargar o recargar la extensión, actualiza cualquier pestaña de chat compatible que ya estuviera abierta. Para las pruebas de captura, empieza una conversación nueva y vacía.

> NOTA. Instalar la extensión por sí sola no arranca ningún backend, esos servicios deben estar activos antes.

El manifest cubre ChatGPT, Claude y Gemini.

Después de editar el JavaScript o el manifest de la extensión, vuelve a `chrome://extensions`, pulsa **Recargar** en su tarjeta y actualiza la pestaña del chat.

Procedimiento oficial de instalación: [Chrome: cargar una extensión descomprimida](https://developer.chrome.com/docs/extensions/get-started/tutorial/hello-world#load-unpacked).

### 1.3 Crear la configuración local privada

Los servicios (mirar la sección 0) que necesitan de configuración de variables de entorno son:
1. Servicio db
2. Servicio api
3. Servicio converter

Las plantillas de Compose versionadas son:

- `api/.db.dev.env`: ajustes de base de datos.
- `api/.api.dev.env`: ajustes de api de anonimizacion.
- `browser-extension/backend/.dev.env`: ajustes de backend del conversor

Crea las sobreescrituras locales privadas **solo si no existen todavía**:

```powershell
if (-not (Test-Path api/.db.env)) {
    Copy-Item api/.db.dev.env api/.db.env
}
if (-not (Test-Path api/.api.env)) {
    Copy-Item api/.api.dev.env api/.api.env
}
if (-not (Test-Path browser-extension/backend/.env)) {
    Copy-Item browser-extension/backend/.dev.env browser-extension/backend/.env
}
```

Edita las variables por una configuración conveniente.

> **NOTA.** El conversor necesita el ID de la extensión de Chrome de la sección 1.2 y un token de desarrollo que coincida con `SECRET_TOKEN` en `browser-extension/extension/background.js`. 
> `MIDDLEWARE_SECRET` vacío usa el token de desarrollo incluido en la extensión. Si `background.js` cambia ese token, escribe el valor nuevo en `.env` y reinicia el conversor. `.env` está ignorado por Git; no lo publiques ni lo confirmes.

## 2. Arranque local por defecto

Los flujos disponibles son:

- **Conversión y protección de adjuntos:** es el flujo por defecto de este apartado. Necesita el stack local completo.
- **Captura para investigación opcional:** se habilita en la sección 3. No se inicia sola al arrancar el stack.
- **Investigación sin PostgreSQL ni inferencia:** usa la aplicación independiente o el recolector de campus de la sección 5.

### 2.1 Un comando para el flujo ordinario

Desde la raíz del repositorio en la terminal A:

```powershell
docker compose up --build --watch
```

Esto arranca cuatro procesos separados:

| Servicio | Responsabilidad | Exposición local |
|---|---|---|
| `db` | Configuración de privacidad en PostgreSQL | Interna `db:5432`, sin puerto de host |
| `inference` | Modelos de inferencia con BentoML | Interna `inference:3000`, sin puerto de host |
| `api` | Detección, política y desidentificación | Loopback `127.0.0.1:8000` |
| `converter` | Conversión de adjuntos PDF/Office a Markdown | Loopback `localhost:5000` |

La API espera los health checks de base de datos e inferencia y aplica las migraciones de Alembic antes de que arranque su servidor de desarrollo. Son cambios reales en la base de datos cuando el desarrollador ejecuta el comando; no se ejecutó ninguna migración solo por redactar esta guía. El conversor queda disponible cuando responde su health check en `http://127.0.0.1:5000/docs`. `--watch` sincroniza y reinicia el conversor al cambiar `browser-extension/backend/app.py`, y reconstruye su imagen si cambia `requirements.txt`.

El conversor sigue siendo su propio proceso y endpoint; la extensión lo llama antes de la API de privacidad. Su ruta `/convertir` espera el campo multipart `archivo` y la cabecera `X-Token`; la extensión los aporta. El CORS usa `EXTENSION_ID_CHROME`; si cambias el ID de la extensión cargada, actualiza `.env` y ejecuta `docker compose up -d converter`.

### 2.2 Verificar el arranque

En la terminal B:

```powershell
docker compose ps
Invoke-RestMethod http://127.0.0.1:8000/api/health
(Invoke-WebRequest -UseBasicParsing http://127.0.0.1:5000/docs).StatusCode
```

La respuesta de salud de la API contiene `status: active` y el código del conversor debe ser `200`. Abre `http://127.0.0.1:8000/docs` para la API interactiva y `http://127.0.0.1:5000/docs` para la del conversor. La documentación del conversor solo demuestra que el proceso web es alcanzable, no que todos los formatos se conviertan correctamente.

PostgreSQL y la inferencia son solo internos en este Compose; no esperes conexiones desde el host a los puertos 5432 ni 3000, y no cambies el binding de loopback de la API ni del conversor para exponer la Admin API de desarrollo.

Administración de desarrollo opcional: reemplaza el comando de arranque por `docker compose --profile dev up --build --watch` para incluir pgAdmin en `http://127.0.0.1:9001`. Sus valores por defecto actuales son solo de desarrollo; no publiques ese servicio en la red del campus. Dentro de pgAdmin, el host de la base de datos es `db`, no el `localhost` del equipo con el navegador.

### 2.3 Prueba de humo con un adjunto ficticio

1. Confirma que responden las dos URLs de documentación local y que el Compose está saludable.
2. Actualiza una pestaña de chat compatible. Mantén **Protección de adjuntos** en **Activada**, con la captura para investigación inactiva.
3. Crea un documento PDF/Office pequeño y válido con texto ficticio y adjúntalo usando una ruta de selector o de arrastre compatible. El conversor admite `.pdf`, `.docx`, `.doc`, `.xlsx`, `.xls` y `.pptx`; un archivo `.txt` plano no sirve como prueba de humo del conversor.
4. Confirma la conversión, la protección de privacidad y el reemplazo del adjunto. Revisa los errores en lugar de suponer que el archivo original quedó protegido cuando una operación falló. El comportamiento del proveedor real todavía necesita validación manual.

Consulta [pruebas de integración](integration-testing.md) para las regresiones sintéticas en navegador y las de Docker aislado. La sección 4 describe el alcance exacto del interruptor.

## 3. Captura para investigación opcional

La captura está deshabilitada por defecto. Habilitar la API no inicia una grabación ni implica consentimiento; la extensión exige consentimiento explícito al iniciar cada sesión. El mismo router `/api/research` existe en la API principal y en la aplicación independiente sin modelo.

### 3.1 Habilitarla dentro del stack local

La sobreescritura `compose.research.dev.yaml` habilita el router existente en la API y guarda el archivo SQLite en el volumen nombrado `research_archive`, sin fusionar servicios ni mover datos existentes.

Añade una sola vez estos valores al `.env` privado de la raíz. Genera una clave de operador local de al menos 32 caracteres sin depender de `uv`:

```powershell
$Bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($Bytes)
$ResearchKey = [Convert]::ToBase64String($Bytes).Replace('+','-').Replace('/','_').TrimEnd('=')
Add-Content .env "RESEARCH_API_KEY=$ResearchKey"
Add-Content .env "RESEARCH_RETENTION_DAYS=7"
Add-Content .env "RESEARCH_PROTOCOL_VERSION=research-v1"
```

Siete días es un **ejemplo ficticio de desarrollo**, no un periodo de retención aprobado para un estudio real. No confirmes `.env` en Git ni reutilices credenciales institucionales. Si el archivo ya contiene esas claves, edítalas en lugar de añadir líneas duplicadas.

Arranca el stack completo con la sobreescritura:

```powershell
docker compose -f compose.yaml -f compose.research.dev.yaml up --build --watch
```

Si el stack ya estaba arrancado, vuelve a ejecutar ese mismo comando: Compose recrea la API cuando cambian las variables de entorno.

En la terminal B, confirma la disponibilidad:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/research/health
```

Debes obtener `status: ready`. El archivo queda en `/data/research/capture.sqlite3` dentro del volumen `research_archive`; `docker compose down` lo conserva y `down --volumes` lo elimina. No es el mismo archivo que la ruta `workspace/research/` de la aplicación independiente de la sección 5.1.

El servicio de inferencia sigue arrancando porque el stack local lo necesita para proteger adjuntos, y la API espera su health check. Las peticiones de investigación no lo invocan. Si solo necesitas captura sin modelo, usa la aplicación independiente o el recolector de campus de la sección 5.

### 3.2 Flujo en la extensión

1. Abre un chat compatible nuevo; usa las [tarjetas de escenario ficticias](../project/experimentacion/research-study/scenario-cards.md).
2. Abre el popup. Confirma que **API de investigación** apunta a `http://127.0.0.1:8000`, introduce la **Clave local del investigador** y `research-v1`, y revisa explícitamente el consentimiento de recolección. El permiso opcional de entrenamiento queda sin marcar salvo que se haya acordado aparte.
3. Pulsa **Iniciar en esta pestaña**. Confirma el indicador de grabación antes de enviar nada. El modo de investigación graba texto sin procesar; no lo desidentifica antes de que el chatbot externo lo reciba. Solo pausa la protección ordinaria de adjuntos en la pestaña seleccionada mientras graba o está en pausa.
   El progreso y los errores aparecen justo encima de ese botón. Una conversación existente se rechaza de forma explícita: abre un chat nuevo y vacío en lugar de intentar importar su historial. Un editor vacío visible puede no mostrar el botón de envío hasta que escribas; eso no impide la activación. Un editor o adaptador de página ausente es un error distinto. Los inicios fallidos conservan los campos de configuración en el popup actual; la clave solo se limpia después de una activación confirmada y nunca se guarda como configuración del popup. Cerrar el popup del navegador descarta sus campos transitorios.
4. Define **Identificador de tarea** y pulsa **Asignar tarea**; envía texto ficticio y espera a que termine la respuesta. El modo de investigación es solo texto: no adjuntes archivos.
5. Pulsa **Finalizar y guardar / reintentar**. Una confirmación de la API debe mostrar un identificador. Usa **Copiar identificador**; no consideres que un búfer local es un guardado correcto en la API.
6. Si la subida falla, conserva el perfil y la extensión y reintenta. No borres el almacenamiento del navegador para resolver el error. **Descartar / retirar sesión** es la ruta explícita de eliminación, con su propia confirmación y semántica de reintento.

Los demás límites de la operación de investigación, el consentimiento, la exportación y los procedimientos de retiro están en [captura sin modelo](research-capture.md). Nada de este ensayo crea un Google Form ni autoriza reclutamiento.

## 4. Controles de la extensión y su alcance exacto

La extensión reutiliza un único interruptor global y un estado de investigación separado. No hay un segundo interruptor de protección.

| Control o estado | Qué significa | Qué no hace |
|---|---|---|
| **Protección de adjuntos: Activada** | Convierte los adjuntos compatibles a Markdown y los envía a la API para desidentificarlos antes de reemplazarlos en el chat | No anonimiza el texto que escribes en el chat; solo cubre adjuntos |
| **Protección de adjuntos: Desactivada** | Los adjuntos se envían sin convertir ni proteger | No detiene Docker, no desactiva la API de investigación y no autoriza una grabación |
| **Sin captura** | No hay una sesión de investigación activa en esta pestaña | No impide el flujo ordinario de adjuntos |
| **Iniciando** | La autorización de la sesión está en curso; todavía no se recolecta | No confirma el consentimiento por sí solo |
| **Grabando** | La sesión archiva el texto enviado y las respuestas visibles en la pestaña elegida | No protege ni desidentifica ese texto |
| **En pausa** | La sesión quedó atada a un documento que ya no está activo; la protección de adjuntos sigue pausada en esa pestaña | No borra la sesión ni la guarda |
| **Pendiente de guardar o reintentar** | La sesión está congelada esperando la API; la protección ordinaria se reanuda | No confirma un guardado sin un identificador de la API |
| **Retiro pendiente** | El texto local ya se borró y falta confirmar la eliminación remota | No elimina respaldos externos, formularios ni historial del proveedor |

La captura en una pestaña pausa **solo** la protección de esa pestaña mientras graba o está en pausa. Las demás pestañas conservan su comportamiento. Una sesión pendiente de guardar o en retiro reanuda la protección ordinaria. El interruptor global se deshabilita mientras hay una sesión de investigación activa para evitar cambiar la política a mitad de la captura.

Que la API o el conversor respondan no significa que la protección esté activada. El pie del popup indica qué backends necesita el flujo; el estado real es el del interruptor **Protección de adjuntos**. Tampoco existe un modo para convertir sin anonimizar: añadirlo sería una decisión de producto separada, no una variante silenciosa del flujo actual.

## 5. Despliegue de investigación sin modelo

### 5.1 Aplicación independiente local

La aplicación independiente evita PostgreSQL, inferencia, conversor y Docker. Usa el mismo router de investigación y un archivo SQLite local.

Requisitos:

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

En la **terminal B**, verifica la disponibilidad:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/research/health
```

Debes obtener `status: ready`. La documentación interactiva local está en `http://127.0.0.1:8000/docs`. La aplicación independiente no expone las rutas originales `/api/health` ni `/api/interactions/protect`. No la arranques al mismo tiempo que el stack local ni otra API en el puerto 8000.

### 5.2 Recolector de campus

El despliegue de campus conserva su Compose separado, su imagen restringida, HTTPS de confianza sobre una IP privada y una copia de extensión generada aparte. No arranca PostgreSQL, inferencia ni conversor, y no se reemplaza por el stack de desarrollo. Sigue el [despliegue en la red universitaria](research-campus-deployment.md); no uses el stack de desarrollo para desplegar con estudiantes.

## 6. Detención segura y diagnóstico

### 6.1 Detener sin borrar los datos almacenados

| Proceso | Procedimiento de parada |
|---|---|
| Stack local (incluido el conversor y la investigación habilitada) | Ctrl+C para detener la sesión en primer plano; después `docker compose down` desde la raíz del repositorio |
| Aplicación independiente de investigación | Ctrl+C en su propia terminal; el archivo de `workspace/research/` permanece |
| Recolector de campus | Sigue el procedimiento del runbook de campus; no lo detengas desde este checkout de desarrollo |

No uses `down --volumes`, poda de volúmenes ni borres el perfil del navegador o el archivo de investigación para diagnosticar un despliegue del estudio. El `docker compose down` ordinario conserva los volúmenes nombrados `postgres_data`, `huggingface_cache` y, cuando se usa la sobreescritura, `research_archive`. Los logs y el historial del navegador no son un procedimiento de respaldo del archivo.

### 6.2 Diagnóstico

| Síntoma | Comprobación |
|---|---|
| La extensión no aparece | Carga la carpeta que contiene `manifest.json`; asegúrate de que la política permita extensiones de desarrollo sin empaquetar |
| La actualización de la extensión parece ignorarse | Recarga su tarjeta y después actualiza la pestaña del proveedor; no lo hagas a mitad de una sesión |
| Compose se detiene pidiendo `EXTENSION_ID_CHROME` | Crea o corrige el `.env` de la raíz con el ID de la extensión cargada; Compose falla de forma explícita en vez de permitir un origen vacío |
| El puerto 8000 ya está en uso | Elige un solo flujo local de API: stack con investigación o aplicación independiente. No mates procesos ajenos ni supongas que aplica la ruta de salud de la otra aplicación |
| La salud de investigación devuelve 404 | La captura está deshabilitada por defecto; arranca con `compose.research.dev.yaml` o define `RESEARCH_ENABLED=true` en la aplicación independiente |
| La salud de investigación devuelve 503 | Revisa la clave de al menos 32 caracteres, la ruta absoluta, la retención entre 1 y 365 días y que no haya fuentes de secretos en conflicto |
| La captura se queda en `Iniciando` (`starting` internamente) | La autorización o activación se interrumpió; usa el procedimiento documentado de descarte y reintento, no borres el almacenamiento |
| El inicio dice que la conversación ya tiene mensajes | Abre una conversación nueva y vacía; el historial se excluye a propósito, no se importa ni se borra |
| El inicio no encuentra el editor del chat | Espera a que cargue la página; después de actualizar la extensión refresca la pestaña y usa un chat compatible nuevo. No confundas la ausencia del botón de envío en un editor vacío con un editor ausente |
| El conversor devuelve 401 | Su `MIDDLEWARE_SECRET` debe coincidir con el token de desarrollo de la extensión; las claves de investigación no lo sustituyen |
| Falla el CORS del conversor | Revisa `EXTENSION_ID_CHROME` en `.env` y ejecuta `docker compose up -d converter` después de cambiar el ID |
| El conversor responde pero falla la protección | También debe estar disponible la API de privacidad y su inferencia, no solo el puerto 5000 |
| La API principal sigue arrancando | Revisa `docker compose logs --tail 50 inference api converter`; la primera preparación del modelo puede tardar; no registres prompts reales |
| Falla la autenticación de la base de datos tras editar `.db.env` | Las credenciales del volumen existente pueden ser distintas; no borres la base de datos para resolver un desajuste de contraseña |
| El archivo de investigación desapareció tras `down` | `down --volumes` elimina el volumen `research_archive`; no lo uses para conservar datos y restaura solo desde un respaldo aprobado |
| El paquete de campus falla desde casa o fuera de la red | Es privado del campus a propósito; sigue el procedimiento aprobado de red y TLS, no desactives advertencias de certificado |

## 7. Verificación y lecturas siguientes

Los nombres de servicios, rutas, variables y comandos de esta guía se contrastaron con los archivos de Compose, la configuración de la API y la extensión. Las pruebas de configuración de Compose, las pruebas de la API y las pruebas de estado de la extensión son sintéticas; no demuestran el comportamiento de una cuenta real de proveedor, un host universitario ni un adaptador de campus. Las instrucciones de prueba de humo del conversor y del proveedor real siguen requiriendo que el desarrollador haga el ensayo.

- [Revisión de riesgos para el propietario del proyecto](../project/experimentacion/research-study/security-risk-review.md): riesgos condicionales, controles existentes y decisiones pendientes; no es aceptación de riesgo.
- [Captura local sin modelo](research-capture.md): ciclo de vida detallado, pruebas de API y procedimientos de acceso.
- [Despliegue en la red universitaria](research-campus-deployment.md): recolector de producción, HTTPS de confianza sobre IP privada y extensión de campus generada. No uses el stack de desarrollo para desplegar con estudiantes.
- [Infraestructura con Docker](infraestructura-local-con-docker.md): límites actuales de red, entorno y persistencia.
- [Pruebas de integración](integration-testing.md): verificación sintética real y requisitos del runner de pruebas.
- [README de la API](../../api/README.md): rutas y estructura del componente.
