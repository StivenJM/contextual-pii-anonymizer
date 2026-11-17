const browserAPI = typeof browser !== 'undefined' ? browser : chrome;

const toggle = document.getElementById('toggleActivo');
const estadoTexto = document.getElementById('estadoTexto');
const chatToggle = document.getElementById('toggleChats');
const estadoChats = document.getElementById('estadoChats');

function pintarEstado(element, activo) {
  element.textContent = activo ? 'Activada' : 'Desactivada';
  element.classList.toggle('on', activo);
  element.classList.toggle('off', !activo);
}

// Cargar estado guardado (adjuntos activos; protección de chats desactivada por defecto)
browserAPI.storage.local.get({ activo: true, chatProtection: false }, ({ activo, chatProtection }) => {
  toggle.checked = activo;
  pintarEstado(estadoTexto, activo);
  chatToggle.checked = chatProtection === true;
  pintarEstado(estadoChats, chatProtection === true);
});

// Guardar cambios. El background detecta el cambio y avisa a las pestañas abiertas.
toggle.addEventListener('change', () => {
  const activo = toggle.checked;
  browserAPI.storage.local.set({ activo });
  pintarEstado(estadoTexto, activo);
});

chatToggle.addEventListener('change', () => {
  const chatProtection = chatToggle.checked;
  browserAPI.storage.local.set({ chatProtection });
  pintarEstado(estadoChats, chatProtection);
});
