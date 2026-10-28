const browserAPI = typeof browser !== 'undefined' ? browser : chrome;

const toggle = document.getElementById('toggleActivo');
const estadoTexto = document.getElementById('estadoTexto');

function pintarEstado(activo) {
  estadoTexto.textContent = activo ? 'Activada' : 'Desactivada';
  estadoTexto.classList.toggle('on', activo);
  estadoTexto.classList.toggle('off', !activo);
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
