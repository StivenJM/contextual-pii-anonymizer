const browserAPI = typeof browser !== 'undefined' ? browser : chrome;

const toggle = document.getElementById('toggleActivo');
const estadoTexto = document.getElementById('estadoTexto');
const estadoAlcance = document.getElementById('estadoAlcance');

function pintarEstado(activo) {
  estadoTexto.textContent = activo ? 'Activada' : 'Desactivada';
  estadoTexto.classList.toggle('on', activo);
  estadoTexto.classList.toggle('off', !activo);
  estadoAlcance.textContent = activo
    ? 'Convierte y protege los documentos adjuntos en los chats compatibles. No anonimiza el texto que escribes en el chat.'
    : 'Los adjuntos se envían sin convertir ni proteger. Docker y la captura para investigación siguen funcionando; desactivar esta protección no autoriza una grabación.';
}

// Cargar estado guardado (por defecto: activada)
browserAPI.storage.local.get({ activo: true }, ({ activo }) => {
  toggle.checked = activo;
  pintarEstado(activo);
});

// Guardar cambios. El background detecta el cambio y avisa a las pestañas abiertas.
toggle.addEventListener('change', () => {
  const activo = toggle.checked;
  browserAPI.storage.local.set({ activo });
  pintarEstado(activo);
});
