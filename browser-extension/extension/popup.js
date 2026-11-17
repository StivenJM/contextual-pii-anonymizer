const browserAPI = typeof browser !== 'undefined' ? browser : chrome;

const toggle = document.getElementById('toggleActivo');
const estadoTexto = document.getElementById('estadoTexto');
const chatToggle = document.getElementById('toggleChats');
const estadoChats = document.getElementById('estadoChats');
const attachmentCard = document.getElementById('attachmentProtectionCard');
const chatCard = document.getElementById('chatProtectionCard');
let disabledByCapture = false;
let preferences = { activo: true, chatProtection: false };

function pintarEstado(element, activo) {
  const effective = disabledByCapture ? false : activo;
  element.textContent = effective ? 'Activada' : 'Desactivada';
  element.classList.toggle('on', effective);
  element.classList.toggle('off', !effective);
}

function pintarPreferencias() {
  toggle.checked = disabledByCapture ? false : preferences.activo;
  chatToggle.checked = disabledByCapture ? false : preferences.chatProtection === true;
  pintarEstado(estadoTexto, preferences.activo);
  pintarEstado(estadoChats, preferences.chatProtection === true);
  for (const card of [attachmentCard, chatCard]) {
    if (card?.setAttribute) card.setAttribute('data-disabled', String(disabledByCapture));
  }
}

function setDisabledByCapture(value) {
  disabledByCapture = value === true;
  pintarPreferencias();
}

// Cargar estado guardado (adjuntos activos; protección de chats desactivada por defecto)
browserAPI.storage.local.get({ activo: true, chatProtection: false }, result => {
  preferences = {
    activo: result.activo !== false,
    chatProtection: result.chatProtection === true
  };
  pintarPreferencias();
});

// Guardar cambios. El background detecta el cambio y avisa a las pestañas abiertas.
toggle.addEventListener('change', () => {
  preferences.activo = toggle.checked;
  browserAPI.storage.local.set({ activo: preferences.activo });
  pintarPreferencias();
});

chatToggle.addEventListener('change', () => {
  preferences.chatProtection = chatToggle.checked;
  browserAPI.storage.local.set({ chatProtection: preferences.chatProtection });
  pintarPreferencias();
});

globalThis.protectionUi = { setDisabledByCapture };
