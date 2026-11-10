# Pruebas de integración de la extensión del navegador

Esta guía explica cómo ejecutar la suite automática de integración de la extensión del navegador y del Privacy Middleware. La suite carga la extensión real en Chromium, la acciona contra páginas locales que imitan el campo de adjuntos de un chat y verifica qué recibe la página.

La suite tiene dos niveles:

| Nivel | Comando | Requiere Docker | Tiempo |
|---|---|---|---|
| Rápido (por defecto) | `pytest -m "not integration"` | No | Segundos después de arrancar el navegador |
| Sistema completo | `pytest -m integration` | Sí | Minutos en la primera ejecución (compilación de imágenes) |
| Depuración | añadir `--headed`, `--slowmo MS` o `--pw-trace` | No | Interactivo |

## Qué demuestra cada nivel

| Prueba | Demuestra |
|---|---|
| `test_file_picker_converts_then_protects` | La ruta del selector de archivos convierte, limpia, protege y reemplaza el archivo |
| `test_converted_file_is_not_intercepted_again` | El control anti-bucle evita reprocesar el archivo |
| `test_drop_zone_converts_then_protects` | La ruta de arrastrar y soltar llega al mismo resultado sin un campo de archivo |
| `test_disabled_extension_delivers_the_original_file` | **Protección de adjuntos** desactivada deja pasar el archivo y no se llama a ningún backend |
| `test_conversion_failure_keeps_the_file_away_from_the_page` | Un fallo de conversión nunca expone el archivo original |
| `test_protection_failure_keeps_the_file_away_from_the_page` | Un fallo de protección nunca expone el archivo original |
| `test_full_system_protects_a_docx_attachment` | El middleware real pseudonimiza el texto extraído antes de que la página lo vea |

La prueba de sistema completo verifica tres condiciones de fuga: el correo del fixture, el nombre de la persona del fixture y el documento original nunca llegan a la página. También comprueba el dominio pseudonimizado que produce el motor real de desidentificación, de modo que un retorno silencioso al texto original hace fallar la prueba.

## Requisitos

- Python 3.12 o superior y `uv`.
- El Chromium de Playwright: `uv run --directory e2e playwright install chromium`.
- Docker con Compose, solo para el nivel de sistema completo.

Un Google Chrome instalado no sirve para probar la extensión: las compilaciones branded ignoran, desde Chrome 137, los flags que cargan una extensión sin empaquetar. El arnés siempre usa el Chromium que instala Playwright.

## Ejecutar el nivel rápido

```powershell
uv sync --directory e2e
uv run --directory e2e playwright install chromium
uv run --directory e2e pytest -v -m "not integration"
```

El nivel levanta dos dobles HTTP y un sitio estático en puertos locales libres, construye una copia parcheada de la extensión, abre Chromium con un perfil nuevo y cierra todo al terminar.

## Ejecutar el nivel de sistema completo

```powershell
uv run --directory e2e pytest -v -m integration
```

El nivel crea un proyecto Compose llamado `cpa-e2e-<aleatorio>`, compila la imagen de la API y la de conversión, inicia PostgreSQL y el stub de inferencia, aplica migraciones y expone la API y el servicio de conversión en puertos locales libres. El proyecto, sus contenedores y su base de datos se eliminan con `down -v` al terminar la prueba. El `compose.yaml` de desarrollo y su volumen nunca se tocan.

## Depurar una prueba que falla

Toda la depuración está apagada por defecto. Activa solo lo que necesite la sesión:

```powershell
# Ver el navegador mientras corre una prueba.
uv run --directory e2e pytest -v -k test_drop_zone --headed

# Ralentizar cada operación del navegador para poder seguir el flujo.
uv run --directory e2e pytest -v -k test_drop_zone --headed --slowmo 500

# Grabar una traza de las pruebas que fallan y abrirla después.
uv run --directory e2e pytest -v --pw-trace=retain-on-failure
uv run --directory e2e playwright show-trace e2e/test-results/<nombre>.zip

# Recorrer paso a paso con el Inspector (interactivo; espera por ti).
$env:PWDEBUG = "1"
uv run --directory e2e pytest -v -k test_drop_zone
Remove-Item Env:PWDEBUG
```

| Flag | Efecto |
|---|---|
| `--headed` | Muestra la ventana de Chromium; `PWDEBUG=1` lo implica |
| `--slowmo MS` | Ralentiza las operaciones del navegador en `MS` milisegundos |
| `--pw-trace=off\|on\|retain-on-failure` | Graba una traza por prueba; `off` es el valor por defecto |

Dos notas sobre los nombres:

- El flag de traza es `--pw-trace`, no `--trace`, porque pytest ya usa `--trace`.
- El modo `--ui` de Playwright pertenece al runner de Node. No existe para Python. `--headed` junto con `PWDEBUG=1` y el visor de trazas cubren aquí las mismas necesidades de depuración; ver la decisión D9 en la página de decisiones.

### Regla de manejo de artefactos

Las trazas serializan instantáneas del DOM, cabeceras de red, cookies y cuerpos de petición. En este repositorio la suite solo construye fixtures sintéticos y los archivos quedan en `e2e/test-results/`, que está ignorado por Git. No actives la traza en una prueba que use un documento real y no subas una traza grabada con datos reales.

## Cómo se construye la copia de la extensión

Las fuentes del producto en `browser-extension/extension/` nunca se modifican. El arnés las copia a `e2e/.build/extension-<nombre>/` y cambia exactamente cinco cosas:

1. El endpoint de conversión.
2. El endpoint de protección.
3. El token compartido, para que coincida con los dobles y con el stack de prueba.
4. La lista de sitios soportados, para que la página local sea elegible.
5. Los permisos del manifest, para que los orígenes locales sean alcanzables.

La fábrica del navegador también acepta orígenes adicionales opcionales para una prueba que necesita un segundo doble local (el caso de aislamiento de dos pestañas de investigación). Estos se añaden solo al manifest de la copia de prueba generada; no cambian los permisos entregados ni las cinco comprobaciones originales de conteo de reemplazos. Los casos de investigación usan además la [API real independiente y sin modelo](research-capture.md), sin proveedor en la nube.

Cada reemplazo registra su cantidad esperada y la observada. Si la extensión cambia de forma, la construcción falla en lugar de probar una suposición obsoleta. Cualquier otro cambio en la extensión aparecerá aquí y debe revisarse de forma deliberada.

## Ruff

```powershell
uv run --directory e2e ruff check .
uv run --directory e2e ruff format --check .
```

## Diagnóstico

| Síntoma | Causa | Acción |
|---|---|---|
| Se omite con `Docker is not available` | El daemon de Docker no está corriendo | Inicia Docker Desktop y vuelve a ejecutar |
| `content.js was not registered` | La extensión no se cargó | Revisa la salida de la construcción en `e2e/.build/`; confirma que el Chromium de Playwright está instalado |
| La extensión queda deshabilitada tras una recarga | Chromium exige el modo desarrollador para recargar | Reinicia la sesión; no llames a `chrome.runtime.reload()` dentro de una prueba |
| La prueba de sistema completo falla al arrancar el stack | Error de compilación de imagen o de migración | Ejecuta `docker compose -f compose.test.yaml -p cpa-e2e-debug up --build` y lee los logs |
| Puerto ya en uso | Se fijó un puerto a mano | No fijes los puertos; el arnés elige libres |

## Límites

- Los sitios de chat reales siguen siendo manuales. La suite verifica la frontera, no el DOM del sitio ni su comportamiento anti-bot.
- Firefox sigue siendo manual. Playwright no puede cargar extensiones en Firefox; la extensión conserva su manifest multiplataforma, pero esa ruta no está cubierta por esta suite.
- La protección ordinaria sigue centrada en adjuntos. Los casos separados de investigación, que se activan de forma explícita, cubren la captura de envíos de texto y respuestas renderizadas contra fixtures sintéticos de chat, incluida una API en modo campus que solo admite inscripción. Esto no valida los adaptadores de DOM de proveedores reales.
- El stub de inferencia es determinista por diseño. No mide la calidad del modelo; conserva el contrato que consume el middleware.

## Relacionado

- [Despliegue de investigación en la red universitaria](research-campus-deployment.md): ensayo de Docker/TLS de producción, empaquetado de la extensión con IP exacta e instalación de confianza en participantes. Sus pruebas por CLI y Docker no arrancan el fixture heredado del navegador. La sustitución opcional `research_origin` de la copia de prueba ejercita la inscripción por loopback sin cambiar la configuración de origen ni las cinco comprobaciones originales de conteo de reemplazos.

- [`Verificación automática de la extensión del navegador`](../architecture/frontend/browser-extension/decisions/verificacion-automatica.md): base de evidencia y justificación de cada decisión anterior.
- [`Infraestructura local con Docker`](infraestructura-local-con-docker.md): entorno de desarrollo, que esta guía no reemplaza.
