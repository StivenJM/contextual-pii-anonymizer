(function () {
  'use strict';
  const api = typeof browser !== 'undefined' ? browser : chrome;
  const element = id => document.getElementById(id);
  const status = element('researchStatus');
  const phaseLabels = {
    idle: 'Inactivo', starting: 'Iniciando', recording: 'Grabando',
    paused: 'En pausa', pending: 'Pendiente de guardar', withdrawing: 'Retiro pendiente'
  };
  let busy = false;
  function showError(error) {
    status.dataset.kind = 'error';
    status.textContent = error.message || 'No se pudo completar la operación. Revisa la sesión y vuelve a intentarlo.';
    status.scrollIntoView?.({ block: 'nearest' });
  }
  async function send(type, values = {}) {
    const result = await api.runtime.sendMessage({ type, ...values }).catch(() => {
      throw new Error('No se pudo comunicar con la extensión. Conserva este perfil y vuelve a intentarlo.');
    });
    if (!result?.ok) throw new Error(result?.error || 'El servicio de investigación no está disponible.');
    return result;
  }
  async function render() {
    const state = await send('RESEARCH_STATUS');
    element('researchReceipt').value = state.receipt_id;
    element('researchEndpoint').textContent = state.api_origin;
    element('researchKeyLabel').textContent = state.enrollment_only ? 'Código de participación del estudio' : 'Clave local del investigador';
    element('researchStart').disabled = busy || state.phase !== 'idle';
    element('researchFinish').disabled = busy || !['recording', 'paused', 'pending'].includes(state.phase);
    element('researchSetTask').disabled = busy || state.phase !== 'recording';
    element('researchDiscard').disabled = busy || (state.phase === 'idle' && !state.receipt_id);
    element('researchCopy').disabled = !state.receipt_id;
    element('toggleActivo').disabled = state.phase !== 'idle';
    for (const id of ['researchKey', 'researchProtocol', 'researchConsent', 'researchTraining']) {
      element(id).disabled = busy || state.phase !== 'idle';
    }
    status.textContent = `${phaseLabels[state.phase] || 'Estado desconocido'}: ${state.count} ${state.count === 1 ? 'mensaje guardado' : 'mensajes guardados'} en este navegador.`;
    if (state.phase === 'withdrawing') status.textContent = 'El texto sin desidentificar se eliminó de este navegador. El retiro en la API está pendiente; vuelve a pulsar Descartar / retirar sesión cuando la API esté disponible.';
    if (state.receipt_id) status.textContent += state.capture_status === 'interrupted'
      ? ' Sesión guardada como INTERRUMPIDA: podrían faltar respuestas. Guarda el identificador y avisa al investigador.'
      : ' Último guardado confirmado. Copia y guarda el identificador.';
    status.dataset.kind = busy ? 'busy' : 'status';
    if (busy) status.textContent = 'Procesando la solicitud...';
  }
  async function operation(action) {
    busy = true;
    status.dataset.kind = 'busy';
    status.textContent = 'Procesando la solicitud...';
    await render().catch(() => {});
    try {
      await action();
      busy = false;
      await render();
    } catch (error) {
      busy = false;
      await render().catch(() => {});
      showError(error);
    }
  }
  element('researchStart').addEventListener('click', () => operation(async () => {
    const key = element('researchKey').value;
    await send('RESEARCH_START', {
      key, consent: element('researchConsent').checked,
      trainingConsent: element('researchTraining').checked,
      protocol: element('researchProtocol').value
    });
    // Keep failed setup editable in this popup only; never persist the key.
    element('researchKey').value = '';
  }));
  element('researchSetTask').addEventListener('click', () => operation(() => send('RESEARCH_TASK', { task: element('researchTask').value })));
  element('researchFinish').addEventListener('click', () => operation(() => send('RESEARCH_FINISH')));
  element('researchDiscard').addEventListener('click', () => {
    if (confirm('¿Quieres descartar la sesión actual sin guardar o retirar la última sesión guardada? Esto elimina su registro de investigación local y en la API; no elimina respuestas de Google Forms, copias de seguridad, modelos entrenados ni el historial del proveedor de IA.')) {
      operation(() => send('RESEARCH_DISCARD'));
    }
  });
  element('researchCopy').addEventListener('click', async () => {
    status.dataset.kind = 'status';
    try {
      await navigator.clipboard.writeText(element('researchReceipt').value);
      status.textContent = 'Identificador copiado. Guárdalo en un lugar seguro.';
    } catch {
      element('researchReceipt').select();
      status.textContent = 'Selecciona el identificador y cópialo manualmente.';
    }
  });
  render().catch(showError);
})();
