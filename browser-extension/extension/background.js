const browserAPI = typeof browser !== 'undefined' ? browser : chrome;

const SECRET_TOKEN = 'mi-proyecto-middleware-2024-epn';

const SERVIDOR_CONVERSION = 'http://localhost:5000/convertir';
const SERVIDOR_ANONIMIZACION =
  'http://127.0.0.1:8000/api/interactions/protect';

const SITIOS_SOPORTADOS = [
  'https://chatgpt.com/*',
  'https://claude.ai/*',
  'https://gemini.google.com/*'
];

const CONTENT_SCRIPT_ID = 'content-main';

// ============================================================
// Registro de content.js en MAIN world
// ============================================================

async function registrarContentPrincipal() {
  try {
    const registrados =
      await browserAPI.scripting.getRegisteredContentScripts({
        ids: [CONTENT_SCRIPT_ID]
      });

    if (registrados.length > 0) {
      await browserAPI.scripting.unregisterContentScripts({
        ids: [CONTENT_SCRIPT_ID]
      });
    }

    await browserAPI.scripting.registerContentScripts([
      {
        id: CONTENT_SCRIPT_ID,
        matches: SITIOS_SOPORTADOS,
        js: ['content.js'],
        runAt: 'document_start',
        world: 'MAIN'
      }
    ]);
  } catch (error) {
    console.error(
      '[Middleware] No se pudo registrar content.js:',
      error
    );
  }
}

browserAPI.runtime.onInstalled.addListener(() => {
  registrarContentPrincipal();
});

// ============================================================
// Estado de la extensión
// ============================================================

async function obtenerEstado() {
  const { activo } =
    await browserAPI.storage.local.get({ activo: true });

  return activo;
}

browserAPI.storage.onChanged.addListener((changes, area) => {
  if (area !== 'local' || !('activo' in changes)) return;

  const activo = changes.activo.newValue;

  browserAPI.tabs.query(
    { url: SITIOS_SOPORTADOS },
    (tabs) => {
      for (const tab of tabs) {
        browserAPI.tabs
          .sendMessage(
            tab.id,
            {
              type: 'ESTADO_CAMBIADO',
              activo
            }
          )
          .catch(() => { });
      }
    }
  );
});

// ============================================================
// Conversión PDF/DOCX -> Markdown
// ============================================================

async function convertirArchivo(formData) {
  const inicio = performance.now();
  const respuesta = await fetch(
    SERVIDOR_CONVERSION,
    {
      method: 'POST',
      headers: {
        'X-Token': SECRET_TOKEN
      },
      body: formData
    }
  );

  const texto = await respuesta.text();

  let data;

  try {
    data = JSON.parse(texto);
  } catch {
    throw new Error(
      'El servidor de conversión devolvió una respuesta no válida: ' +
      texto
    );
  }

  if (!respuesta.ok || !data.ok) {
    throw new Error(
      data.error ||
      `Error en servidor de conversión (${respuesta.status})`
    );
  }

  if (
    typeof data.markdown !== 'string' ||
    data.markdown.length === 0
  ) {
    throw new Error(
      'El servidor de conversión no devolvió Markdown válido.'
    );
  }
  //Medir tiempo
  const fin = performance.now();
  const segundos = ((fin - inicio) / 1000).toFixed(2);

  console.log(
    `[Middleware][TIEMPO] Conversión: ${segundos} segundos`
  );

  return data.markdown;
}

// ============================================================
// Limpieza del Markdown antes de enviarlo al anonimizador
// ============================================================

//LIMPIEZA PARA EXCEL

function limpiarTablasExcelMarkdown(texto) {
  const pareceExcel =
    /^##\s+Sheet\b/im.test(texto) ||
    /\|\s*Unnamed:\s*\d+/i.test(texto);

  if (!pareceExcel) {
    return texto;
  }

  // Convierte una fila Markdown en un array de celdas
  // | NaN | Elena Torres | 1727315029 | - ["NaN", "Elena Torres", "1727315029"]

  function obtenerCeldas(linea) {
    let contenido = linea.trim();

    if (contenido.startsWith('|')) {
      contenido = contenido.slice(1);
    }

    if (contenido.endsWith('|')) {
      contenido = contenido.slice(0, -1);
    }

    return contenido
      .split('|')
      .map(celda => celda.trim());
  }

  // Detecta la fila separadora de Markdown:
  // | --- | --- | --- |

  function esSeparador(celdas) {
    return (
      celdas.length > 0 &&
      celdas.every(celda =>
        /^:?-{3,}:?$/.test(celda.trim())
      )
    );
  }

  // Limpia una celda individual

  function limpiarCelda(celda) {
    const valor = celda.trim();

    // Celda vacía de Excel
    if (/^NaN$/i.test(valor)) {
      return '';
    }

    // Encabezados artificiales creados al convertir Excel: Unnamed: 0 - BORRADO
    if (
      /^Unnamed:\s*\d+(?:\.\d+)?(?:_level_\d+)?$/i.test(valor)
    ) {
      return '';
    }

    return valor;
  }

  const lineas = texto.split('\n');
  const resultado = [];

  let i = 0;

  while (i < lineas.length) {

    // Si no estamos en una tabla Markdown, copiamos la línea normalmente.
    if (!lineas[i].trim().startsWith('|')) {
      resultado.push(lineas[i]);
      i++;
      continue;
    }
    // --------------------------------------------------------
    // Recoger todo el bloque de tabla
    // --------------------------------------------------------
    const bloqueTabla = [];

    while (
      i < lineas.length &&
      lineas[i].trim().startsWith('|')
    ) {
      bloqueTabla.push(lineas[i]);
      i++;
    }

    // Tabla Markdown normal necesita:encabezado + separador.
    if (bloqueTabla.length < 2) {
      resultado.push(...bloqueTabla);
      continue;
    }

    const filas = bloqueTabla.map(obtenerCeldas);

    // Si la segunda fila no es "---", probablemente no sea
    // una tabla Markdown normal. No la tocamos.
    if (!esSeparador(filas[1])) {
      resultado.push(...bloqueTabla);
      continue;
    }

    // Igualar número de columnas

    const maxColumnas = Math.max(
      ...filas.map(fila => fila.length)
    );

    const filasNormalizadas = filas.map(
      (fila, indiceFila) => {

        const nuevaFila = [];

        for (let columna = 0; columna < maxColumnas; columna++) {
          nuevaFila.push(fila[columna] ?? '');
        }

        // No limpiar la fila "---"
        if (indiceFila === 1) {
          return nuevaFila;
        }

        return nuevaFila.map(limpiarCelda);
      }
    );

    // Detectar columnas completamente vacías Si columna tiene
    // Unnamed: 0
    // NaN
    // NaN
    // NaN
    // desaparece completamente.

    const columnasUtiles = [];

    for (
      let columna = 0;
      columna < maxColumnas;
      columna++
    ) {

      let contieneInformacion = false;

      for (
        let fila = 0;
        fila < filasNormalizadas.length;
        fila++
      ) {

        // Ignorar fila separadora ---
        if (fila === 1) {
          continue;
        }

        if (
          filasNormalizadas[fila][columna]
            .trim()
            .length > 0
        ) {
          contieneInformacion = true;
          break;
        }
      }

      if (contieneInformacion) {
        columnasUtiles.push(columna);
      }
    }

    // Si toda la tabla estaba vacía, eliminarla.
    if (columnasUtiles.length === 0) {
      continue;
    }

    // Reconstruir encabezado

    const encabezado = columnasUtiles.map(
      columna => filasNormalizadas[0][columna]
    );

    resultado.push(
      `| ${encabezado.join(' | ')} |`
    );

    // Reconstruir separador

    resultado.push(
      `| ${columnasUtiles.map(() => '---').join(' | ')} |`
    );

    // Reconstruir filas de datos

    for (
      let fila = 2;
      fila < filasNormalizadas.length;
      fila++
    ) {

      const celdas = columnasUtiles.map(
        columna =>
          filasNormalizadas[fila][columna]
      );

      // Si todas las celdas de esta fila están vacías, no añadir la fila
      const filaVacia = celdas.every(
        celda => celda.trim() === ''
      );

      if (filaVacia) {
        continue;
      }

      resultado.push(
        `| ${celdas.join(' | ')} |`
      );
    }
  }

  return resultado.join('\n');
}

function limpiarMarkdown(markdown) {
  let texto = markdown;

  // 1. Normalizar saltos de línea

  texto = texto.replace(/\r\n?/g, '\n');

  // 2. Reparar palabras partidas por maquetación del documento
  // De 
  // "credencia-
  // les"
  // pasa a: "credenciales"
  texto = texto.replace(
    /\b([A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{3,})-\n\s*([a-záéíóúüñ]{2,})\b/g,
    '$1$2'
  );

  // 3. Eliminar referencias Markdown a imágenes
  // Ejemplo: ![/home/claude/icons/globe.png](Image3.jpg)
  texto = texto.replace(
    /!\[[^\]]*\]\([^)]*\)/g,
    ''
  );

  // 4. Convertir comentarios de PowerPoint en encabezados practicos
  // De: <!-- Slide number: 4 --> pasa a: ## Diapositiva 4
  texto = texto.replace(
    /<!--\s*Slide number:\s*(\d+)\s*-->/gi,
    '## Diapositiva $1'
  );

  // 5. Eliminar encabezado "Notes" generado por PowerPoint
  texto = texto.replace(
    /^\s*###\s*Notes:\s*$/gmi,
    ''
  );

  // 6. Eliminar contadores de diapositivas aislados
  // Ejemplos: 4 / 13
  texto = texto.replace(
    /^\s*\d+\s*\/\s*\d+\s*$/gm,
    ''
  );

  // 7. Eliminar simbolos de fuentes iconos (de Font Awesome)
  texto = texto.replace(
    /[\uE000-\uF8FF]/g,
    ''
  );

  // 8. Eliminar caracteres de control invisibles
  // Conservamos:
  // \n = salto de línea
  // \t = tabulación
  // Elimina cosas como form feed (\f).
  texto = texto.replace(
    /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g,
    ''
  );

  // 9. Sustituir espacios no separables por espacios normales
  texto = texto.replace(/\u00A0/g, ' ');
  texto = limpiarTablasExcelMarkdown(texto);

  // 10. Limpiar cada línea
  // - quita espacios al inicio/final
  // - reduce bloques enormes de espacios
  texto = texto
    .split('\n')
    .map((linea) => {
      return linea
        .replace(/[ \t]{3,}/g, ' ')
        .trim();
    })
    .join('\n');
 
  // 11. Limitar exceso de líneas vacías

  // 5, 6, 7... saltos seguidos, pasan a máximo una línea vacía entre bloques.
  texto = texto.replace(/\n{3,}/g, '\n\n');

  // 12. Limpiar inicio y final
  texto = texto.trim();

  return texto;
}

// ============================================================
// Anonimización Markdown -> protected_text
// ============================================================

async function anonimizarMarkdown(markdown) {
  console.log(
    '[Middleware] Enviando Markdown al anonimizador...'
  );
  const inicio = performance.now();

  const respuesta = await fetch(
    SERVIDOR_ANONIMIZACION,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },

      // JSON.stringify convierte automáticamente
      // los saltos de línea reales en \n para transportarlos
      // correctamente dentro del JSON.
      body: JSON.stringify({
        text: markdown
      })
    }
  );

  const textoRespuesta = await respuesta.text();

  let data;

  try {
    data = JSON.parse(textoRespuesta);
  } catch {
    throw new Error(
      'El servidor de anonimización devolvió una respuesta no válida: ' +
      textoRespuesta
    );
  }

  if (!respuesta.ok) {
    let detalle = '';

    if (data.message) {
      detalle = data.message;
    } else if (data.detail) {
      detalle =
        typeof data.detail === 'string'
          ? data.detail
          : JSON.stringify(data.detail);
    }

    throw new Error(
      detalle ||
      `Error en servidor de anonimización (${respuesta.status})`
    );
  }

  if (
    typeof data.protected_text !== 'string' ||
    data.protected_text.length === 0
  ) {
    throw new Error(
      'El anonimizador no devolvió protected_text válido.'
    );
  }

  const fin = performance.now();
  const segundos = ((fin - inicio) / 1000).toFixed(2);

  console.log(
    `[Middleware][TIEMPO] Anonimización: ${segundos} segundos`
  );

  console.log(
    '[Middleware] Anonimización completada correctamente.'
  );

  return data.protected_text;
}

// ============================================================
// Mensajería con content.js
// ============================================================

browserAPI.runtime.onMessage.addListener(
  (message, sender, sendResponse) => {

    // --------------------------------------------------------
    // Consultar estado
    // --------------------------------------------------------

    if (message.type === 'OBTENER_ESTADO') {
      obtenerEstado()
        .then((activo) => {
          sendResponse({
            ok: true,
            activo
          });
        })
        .catch((error) => {
          sendResponse({
            ok: false,
            error: error.message
          });
        });

      return true;
    }

    // --------------------------------------------------------
    // Solo procesar archivos
    // --------------------------------------------------------

    if (message.type !== 'CONVERTIR_ARCHIVO') {
      return;
    }

    const {
      base64,
      nombre,
      mimeType
    } = message;

    // --------------------------------------------------------
    // Validación de tamaño
    // --------------------------------------------------------

    if (base64.length > 27 * 1024 * 1024) {
      sendResponse({
        ok: false,
        error: 'Archivo demasiado grande'
      });

      return true;
    }

    // --------------------------------------------------------
    // Procesamiento completo
    // PDF/DOCX -> Markdown -> Anonimización
    // --------------------------------------------------------

    (async () => {
      try {
        console.log(
          `[Middleware] Procesando archivo: ${nombre}`
        );

        // Base64 -> Blob
        const byteCharacters = atob(base64);

        const byteNumbers =
          new Uint8Array(byteCharacters.length);

        for (
          let i = 0;
          i < byteCharacters.length;
          i++
        ) {
          byteNumbers[i] =
            byteCharacters.charCodeAt(i);
        }

        const blob = new Blob(
          [byteNumbers],
          {
            type: mimeType
          }
        );

        const formData = new FormData();

        formData.append(
          'archivo',
          blob,
          nombre
        );

        // ====================================================
        // PASO 1
        // PDF / DOCX / XLSX / PPTX -> Markdown
        // ====================================================

        console.log(
          '[Middleware] Paso 1/2: convirtiendo documento...'
        );

        const markdown =
          await convertirArchivo(formData);

        console.log(
          '[Middleware] Conversión completada.'
        );

        console.log(
          '[Middleware] Vista previa Markdown ORIGINAL:',
          markdown.substring(0, 300)
        );

        // ====================================================
        // LIMPIEZA
        // ====================================================

        const inicioLimpieza = performance.now();

        const markdownLimpio =
          limpiarMarkdown(markdown);

        const finLimpieza = performance.now();

        const segundosLimpieza =
          ((finLimpieza - inicioLimpieza) / 1000).toFixed(4);

        console.log(
          `[Middleware][TIEMPO] Limpieza: ${segundosLimpieza} segundos`
        );

        console.log(
          '[Middleware] Vista previa Markdown LIMPIO:',
          markdownLimpio.substring(0, 500)
        );

        // ====================================================
        // PASO 2
        // Markdown limpio -> Texto anonimizado
        // ====================================================

        console.log(
          '[Middleware] Paso 2/2: anonimizando información...'
        );

        const protectedText =
          await anonimizarMarkdown(markdownLimpio);

        console.log(
          '[Middleware] Vista previa anonimizada:',
          protectedText.substring(0, 300)
        );

        // ====================================================
        // DEVOLVER RESULTADO A content.js
        // ====================================================

        sendResponse({
          ok: true,
          markdown: protectedText
        });

      } catch (error) {
        console.error(
          '[Middleware] Error durante el procesamiento:',
          error
        );

        sendResponse({
          ok: false,
          error:
            error?.message ||
            'Error desconocido durante el procesamiento'
        });
      }
    })();

    // Mantiene abierto el canal para sendResponse
    // mientras terminan los dos fetch.
    return true;
  }
);