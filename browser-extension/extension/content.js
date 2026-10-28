const TIPOS_SOPORTADOS = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
];

// ============================================================
// Estado de la extensión (controlado desde el popup)
// ============================================================
let middlewareActivo = true;

// Escuchamos cambios de estado difundidos por el background (vía bridge)
window.addEventListener('message', (event) => {
  if (event.source !== window) return;
  if (event.data?.direction !== 'BACKGROUND_TO_MAIN_BROADCAST') return;
  if (event.data.payload?.type !== 'ESTADO_CAMBIADO') return;

  middlewareActivo = event.data.payload.activo;
  console.log(`[Middleware] Extensión ${middlewareActivo ? 'ACTIVADA' : 'DESACTIVADA'}`);
});

function esSoportado(file) {
  return TIPOS_SOPORTADOS.includes(file.type);
}

// Anti-bucle: identifica archivos que ya pasaron por el middleware
function esArchivoConvertido(file) {
  return file.type === 'text/plain' && file.name.endsWith('_converted.txt');
}

// Durante un drag (antes del drop) no hay acceso al File completo,
// pero sí al MIME type vía dataTransfer.items
function dragContieneTipoSoportado(dataTransfer) {
  if (!dataTransfer?.items) return false;
  for (const item of dataTransfer.items) {
    if (item.kind === 'file') {
      if (TIPOS_SOPORTADOS.includes(item.type)) return true;
      // En Firefox, por seguridad, item.type es un string vacío durante dragenter/dragover.
      // Al no poder ver el tipo real, asumimos true para que el supresor de drag
      // actúe preventivamente y evite que se abra el overlay transparente del sitio.
      if (item.type === "") return true;
    }
  }
  return false;
}

// Manda mensaje al background a través del bridge y espera respuesta
function enviarAlBackground(payload) {
  return new Promise((resolve, reject) => {
    const requestId = Math.random().toString(36).slice(2);

    const handler = (event) => {
      if (event.data?.direction !== 'BACKGROUND_TO_MAIN') return;
      if (event.data.requestId !== requestId) return;
      window.removeEventListener('message', handler);

      if (event.data.respuesta?.ok) {
        resolve(event.data.respuesta);
      } else {
        reject(new Error(event.data.respuesta?.error || 'Error desconocido'));
      }
    };

    window.addEventListener('message', handler);

    window.postMessage({
      direction: 'MAIN_TO_BACKGROUND',
      requestId,
      payload
    }, '*');
  });
}

// Al cargar la página, consultamos el estado guardado.
// Reintentamos porque el bridge puede tardar unos ms en estar listo.
(function consultarEstadoInicial(intento = 0) {
  enviarAlBackground({ type: 'OBTENER_ESTADO' })
    .then(r => {
      middlewareActivo = r.activo;
      console.log(`[Middleware] Estado inicial: ${middlewareActivo ? 'ACTIVADA' : 'DESACTIVADA'}`);
    })
    .catch(() => {
      if (intento < 3) setTimeout(() => consultarEstadoInicial(intento + 1), 500);
    });
})();

async function processFile(file) {
  const TAMANO_MAXIMO = 20 * 1024 * 1024;
  if (file.size > TAMANO_MAXIMO) {
    console.error('[Middleware] Archivo demasiado grande:', file.size, 'bytes');
    return null;
  }
  console.log(`[Middleware] Interceptado: ${file.name}`);

  // Convertimos a base64
  const base64 = await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result.split(',')[1]);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });

  // Enviamos al background via bridge
  const respuesta = await enviarAlBackground({
    type: 'CONVERTIR_ARCHIVO',
    base64,
    nombre: file.name,
    mimeType: file.type
  });

  console.log('[Middleware] Conversión exitosa');
  console.log('[Middleware] Vista previa:', respuesta.markdown.substring(0, 300));

  const nombreSalida = file.name.replace(/\.[^.]+$/, '') + '_converted.txt';
  return new File([respuesta.markdown], nombreSalida, {
    type: 'text/plain',
    lastModified: Date.now()
  });
}

// ============================================================
// Interceptor: selector de archivos (botón "+")
// ============================================================
document.addEventListener('change', async (event) => {
  if (!middlewareActivo) return;

  const target = event.target;
  if (target.tagName !== 'INPUT' || target.type !== 'file') return;

  const file = target.files[0];
  if (!file || esArchivoConvertido(file) || !esSoportado(file)) return;

  // Anti-bucle: verificamos por nombre de archivo, no por flag fijo
  if (target.dataset.lastProcessed === file.name + file.size) return;

  event.preventDefault();
  event.stopImmediatePropagation();

  try {
    const archivoModificado = await processFile(file);
    if (!archivoModificado) return;

    const dt = new DataTransfer();
    dt.items.add(archivoModificado);
    target.files = dt.files;

    // Guardamos el identificador del archivo YA CONVERTIDO, que es el que
    // viajará en el evento change sintético que disparamos a continuación
    target.dataset.lastProcessed = archivoModificado.name + archivoModificado.size;
    target.dispatchEvent(new Event('change', { bubbles: true }));
  } catch (error) {
    console.error('[Middleware] Error en change:', error);
  }
}, true);

// ============================================================
// Utilidades para drag & drop
// ============================================================

// Crea un DragEvent con un dataTransfer real adjunto (con fallback para navegadores
// que no aceptan "dataTransfer" en el constructor de DragEventInit)
function crearDragEvent(type, dataTransfer, coords) {
  const init = {
    bubbles: true,
    cancelable: true,
    composed: true, // permite cruzar shadow DOM si la zona de drop lo usa
    clientX: coords.clientX,
    clientY: coords.clientY,
    screenX: coords.screenX,
    screenY: coords.screenY,
  };

  try {
    return new DragEvent(type, { ...init, dataTransfer });
  } catch (e) {
    const evt = new DragEvent(type, init);
    Object.defineProperty(evt, 'dataTransfer', { value: dataTransfer, configurable: true });
    return evt;
  }
}

function esperar(ms) {
  return new Promise(r => setTimeout(r, ms));
}

// Busca el input[type=file] oculto que usa el botón "+" del sitio.
// Algunos sitios lo crean tarde, así que reintentamos unas cuantas veces.
async function buscarFileInput(intentos = 4, espera = 250) {
  for (let i = 0; i < intentos; i++) {
    const inputs = Array.from(document.querySelectorAll('input[type="file"]'))
      .filter(el => el.isConnected);
    
    if (inputs.length > 0) {
      const validos = inputs.filter(el => {
        if (!el.accept) return true;
        const accept = el.accept.toLowerCase();
        return !(accept.includes('image/') && !accept.includes('*') && !accept.includes('text'));
      });

      if (validos.length > 0) {
        return validos.find(el => el.accept.includes('text') || el.accept.includes('*')) || validos[validos.length - 1];
      }
    }
    await esperar(espera);
  }
  return null;
}

// Busca el editor de texto del chat (contenteditable o textarea)
function buscarEditor() {
  return (
    document.querySelector('rich-textarea div[contenteditable="true"]') || // Gemini
    document.querySelector('#prompt-textarea') || // ChatGPT moderno
    document.querySelector('div[contenteditable="true"].ProseMirror') ||  // ChatGPT / Claude
    document.querySelector('div[contenteditable="true"]') ||
    document.querySelector('textarea')
  );
}

// Estrategia A: inyectar el archivo convertido en el input de archivos del sitio.
// Es el mismo camino que el selector convencional, que ya sabemos que funciona.
async function inyectarEnInput(archivo) {
  const input = await buscarFileInput();
  if (!input) return false;

  const dt = new DataTransfer();
  dt.items.add(archivo);

  input.value = '';
  input.files = dt.files;
  input.dataset.lastProcessed = archivo.name + archivo.size;

  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));
  return true;
}

// Estrategia B: paste sintético sobre el editor del chat.
// Es el mismo mecanismo por el que funciona pegar una imagen con Ctrl+V.
// Útil en sitios sin input[type=file] permanente en el DOM (Gemini).
function inyectarPorPaste(archivo) {
  const editor = buscarEditor();
  if (!editor) return false;

  const dt = new DataTransfer();
  dt.items.add(archivo);

  let pasteEvent;
  try {
    pasteEvent = new ClipboardEvent('paste', {
      bubbles: true,
      cancelable: true,
      composed: true,
      clipboardData: dt
    });
  } catch (e) {
    pasteEvent = new ClipboardEvent('paste', { bubbles: true, cancelable: true, composed: true });
    Object.defineProperty(pasteEvent, 'clipboardData', { value: dt, configurable: true });
  }

  editor.focus();
  editor.dispatchEvent(pasteEvent);
  return true;
}

// Estrategia C (último recurso): replicar drop (y opcionalmente dragenter/dragover)
// sobre un elemento que siga vivo en el DOM.
function despacharDropSintetico(archivo, coords, targetOriginal, omitirDragEnter = false) {
  const dt = new DataTransfer();
  dt.items.add(archivo);
  dt.effectAllowed = 'all';

  let target = targetOriginal;
  if (!target || !target.isConnected) {
    target = document.elementFromPoint(coords.clientX, coords.clientY) || document.body;
  }

  if (!omitirDragEnter) {
    target.dispatchEvent(crearDragEvent('dragenter', dt, coords));
    target.dispatchEvent(crearDragEvent('dragover', dt, coords));
  }
  
  target.dispatchEvent(crearDragEvent('drop', dt, coords));
  return true;
}

// ============================================================
// Supresor de drag: si se arrastra un tipo soportado, ocultamos
// el drag al sitio (nunca ve dragenter/dragover → no muestra su
// overlay ni arma su zona de drop). Hacemos preventDefault()
// nosotros mismos para que el navegador siga permitiendo el drop.
//
// IMPORTANTE: en window + captura, porque window recibe los eventos
// antes que document, ya que algunos sitios escuchan en window.
// Nuestro script corre en document_start, así que nos registramos
// antes que ellos y stopImmediatePropagation() sí los bloquea.
// ============================================================
['dragenter', 'dragover'].forEach((tipo) => {
  window.addEventListener(tipo, (event) => {
    if (!middlewareActivo) return;
    if (!dragContieneTipoSoportado(event.dataTransfer)) return;

    event.preventDefault();           // el navegador permite soltar aquí
    event.stopImmediatePropagation(); // el sitio no se entera del drag
    if (event.dataTransfer) event.dataTransfer.dropEffect = 'copy';
  }, true);
});

// ============================================================
// Interceptor: drag & drop
// ============================================================
window.addEventListener('drop', async (event) => {
  if (!middlewareActivo) return;
  if (!event.dataTransfer?.files?.length) return;

  const file = event.dataTransfer.files[0];

  // Anti-bucle: nunca interceptar archivos ya convertidos, ni tipos no soportados
  if (esArchivoConvertido(file) || !esSoportado(file)) return;

  event.preventDefault(); // Detiene el archivo antes de que llegue a la IA
  event.stopImmediatePropagation();

  const targetOriginal = event.target instanceof Element ? event.target : document.body;
  const coords = {
    clientX: event.clientX,
    clientY: event.clientY,
    screenX: event.screenX,
    screenY: event.screenY,
  };

  // En Firefox, el supresor de dragenter a veces no detecta los mimetypes y no bloquea el overlay.
  // Al cancelar el drop real, el overlay se queda pegado.
  // Despachamos un dragleave para engañar al sitio (React) y que cierre su overlay.
  const evtLeave = crearDragEvent('dragleave', event.dataTransfer, coords);
  targetOriginal.dispatchEvent(evtLeave);
  document.dispatchEvent(evtLeave);

  try {
    const archivoModificado = await processFile(file);
    if (!archivoModificado) return;

    const esFirefox = navigator.userAgent.toLowerCase().includes('firefox');
    const esChatGPT = window.location.hostname.includes('chatgpt.com');

    // En Firefox (para todos) y en ChatGPT (para todos los navegadores),
    // las Estrategias A y B fallan o son inestables (ej. agarran input multimodal).
    // Usamos la Estrategia C (Drop) como prioridad absoluta.
    if (esFirefox || esChatGPT) {
      // Si estamos en ChatGPT, omitimos dragenter para no dejar pegado el overlay.
      const omitirDragEnter = esChatGPT;
      if (despacharDropSintetico(archivoModificado, coords, targetOriginal, omitirDragEnter)) {
        console.log('[Middleware][C] Drop sintético despachado (Modo Optimizado):', archivoModificado.name);
        return;
      }
    } else {
      // MODO CHROME / EDGE (Flujo Original)
      // Restauramos el comportamiento original que funcionaba perfectamente en Chromium
      // para Claude, Gemini, etc.

      // 1. Estrategia A: input oculto
      if (await inyectarEnInput(archivoModificado)) {
        console.log('[Middleware][A] Drop redirigido al input de archivos:', archivoModificado.name);
        return;
      }

      // 2. Estrategia B: paste sintético (Gemini)
      if (inyectarPorPaste(archivoModificado)) {
        console.log('[Middleware][B] Archivo inyectado por paste sintético:', archivoModificado.name);
        return;
      }

      // 3. Estrategia C: Drop completo con dragenter (Claude y otros)
      // En Chrome Claude y Gemini requieren dragenter para activar su zona de drop, 
      // así que no lo omitimos.
      if (despacharDropSintetico(archivoModificado, coords, targetOriginal, false)) {
        console.log('[Middleware][C] Drop sintético completo despachado:', archivoModificado.name);
        return;
      }
    }
  } catch (error) {
    console.error('[Middleware] Error en drop:', error);
  }
}, true);
