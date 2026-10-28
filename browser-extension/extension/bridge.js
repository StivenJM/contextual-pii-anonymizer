const browserAPI = typeof browser !== 'undefined' ? browser : chrome;

// MAIN → background (peticiones con respuesta)
window.addEventListener('message', (event) => {
  if (event.source !== window) return;
  if (!event.data || event.data.direction !== 'MAIN_TO_BACKGROUND') return;

  browserAPI.runtime.sendMessage(event.data.payload, (respuesta) => {
    if (browserAPI.runtime.lastError) {
      console.error('[Middleware] Bridge:', browserAPI.runtime.lastError.message);
      return;
    }

    window.postMessage({
      direction: 'BACKGROUND_TO_MAIN',
      requestId: event.data.requestId,
      respuesta
    }, '*');
  });
});

// background → MAIN (difusiones sin respuesta)
browserAPI.runtime.onMessage.addListener((message) => {
  if (message?.type !== 'ESTADO_CAMBIADO') return;

  window.postMessage({
    direction: 'BACKGROUND_TO_MAIN_BROADCAST',
    payload: message
  }, '*');
});
