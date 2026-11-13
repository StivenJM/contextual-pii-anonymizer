(function (root) {
  'use strict';

  const LABELS = {
    idle: 'Sin captura',
    starting: 'Iniciando la captura',
    recording: 'Captura activa',
    interrupted: 'Captura interrumpida',
    pending: 'Pendiente de guardar',
    saved: 'Sesión guardada',
    withdrawing: 'Retiro pendiente'
  };
  const REASONS = {
    conversation_changed: 'La conversación cambió o la página se recargó.',
    tab_closed: 'La pestaña de la captura se cerró.',
    page_paused: 'El documento autorizado cambió al recargarse la página.'
  };
  const SETUP_VISIBLE = new Set(['idle']);

  // Pure view model so state decisions stay testable without a browser.
  function describe(state) {
    const input = state || {};
    const view = Object.prototype.hasOwnProperty.call(LABELS, input.view) ? input.view : 'idle';
    const tab = input.tab || null;
    const tabMissing = view === 'recording' && !!tab && tab.exists === false;
    const otherTab = view === 'recording' && !!tab && tab.exists !== false && tab.active === false;
    const task = input.task && input.task !== 'unassigned' ? input.task : 'Sin asignar';
    const from = input.paused_from || '';
    const to = input.paused_to || '';
    const route = from || to ? ` (${from || '—'} → ${to || '—'})` : '';
    return {
      view,
      label: LABELS[view],
      sections: {
        setup: SETUP_VISIBLE.has(view),
        starting: view === 'starting',
        active: view === 'recording',
        interrupted: view === 'interrupted',
        pending: view === 'pending',
        saved: view === 'saved',
        withdrawing: view === 'withdrawing'
      },
      keyLabel: input.enrollment_only ? 'Código de participación del estudio' : 'Clave local del investigador',
      provider: input.provider || '—',
      task,
      count: Number.isInteger(input.count) ? input.count : 0,
      scope: otherTab ? 'Otra pestaña' : 'Esta pestaña',
      otherTab,
      tabMissing,
      canGoToTab: view === 'recording' && !!tab && tab.exists !== false && tab.active === false,
      canStart: view === 'idle' || view === 'saved',
      receipt: input.receipt_id || '',
      interruptReason: (REASONS[input.paused_reason] || 'La captura dejó de estar activa en esta conversación.') + route,
      pendingReason: input.last_error || 'La API todavía no ha confirmado el guardado de este lote.',
      withdrawalReason: input.last_error || 'La eliminación remota no se ha confirmado todavía.',
      scopeNotice: tabMissing
        ? 'La pestaña de la captura ya no existe. Guarda los datos disponibles o descarta la sesión.'
        : (otherTab ? 'La captura pertenece a otra pestaña. No puedes iniciar otra desde aquí.' : '')
    };
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { describe };
    return;
  }

  const api = typeof browser !== 'undefined' ? browser : chrome;
  const byId = id => document.getElementById(id);
  const SECTION_IDS = {
    setup: 'researchSetup',
    starting: 'researchStarting',
    active: 'researchActive',
    interrupted: 'researchInterrupted',
    pending: 'researchPending',
    saved: 'researchSaved',
    withdrawing: 'researchWithdrawing'
  };
  const inFlight = new Set();
  let setupRequested = false;
  let lastState = { view: 'idle' };

  function messageOf(error) {
    return error?.message || 'No se pudo completar la operación. Vuelve a intentarlo.';
  }
  function showError(ids, message) {
    for (const id of Array.isArray(ids) ? ids : [ids]) {
      const element = byId(id);
      if (!element) continue;
      element.textContent = message;
      element.hidden = false;
    }
  }
  function clearError(ids) {
    for (const id of Array.isArray(ids) ? ids : [ids]) {
      const element = byId(id);
      if (!element) continue;
      element.textContent = '';
      element.hidden = true;
    }
  }
  async function send(type, values = {}) {
    const result = await api.runtime.sendMessage({ type, ...values }).catch(() => {
      throw new Error('No se pudo comunicar con la extensión. Conserva este perfil y vuelve a intentarlo.');
    });
    if (!result?.ok) throw new Error(result?.error || 'El servicio de investigación no está disponible.');
    return result;
  }

  function setText(id, value) {
    const element = byId(id);
    if (element) element.textContent = value;
  }
  function setDisabled(id, disabled) {
    const element = byId(id);
    if (element) element.disabled = !!disabled;
  }
  function render(state) {
    const view = describe(state);
    if (view.view !== 'saved') setupRequested = false;
    for (const [key, id] of Object.entries(SECTION_IDS)) {
      const element = byId(id);
      if (!element) continue;
      element.hidden = !(view.sections[key] || (key === 'setup' && setupRequested));
    }
    const busy = inFlight.size > 0;
    setText('researchPhase', view.label);
    setText('researchKeyLabel', view.keyLabel);
    setText('researchProvider', view.provider);
    setText('researchScope', view.scope);
    setText('researchTaskValue', view.task);
    setText('researchCount', String(view.count));
    setText('researchInterruptReason', view.interruptReason);
    setText('researchPendingReason', view.pendingReason);
    setText('researchWithdrawPendingError', view.sections.withdrawing && state.last_error ? view.withdrawalReason : '');
    const withdrawError = byId('researchWithdrawPendingError');
    if (withdrawError) withdrawError.hidden = !(view.sections.withdrawing && state.last_error);
    if (view.view === 'starting' && state.last_error) {
      showError('researchStartingError', state.last_error);
    }

    const tabNotice = byId('researchTabNotice');
    if (tabNotice) {
      tabNotice.textContent = view.scopeNotice;
      tabNotice.hidden = !view.scopeNotice;
    }
    const goToTab = byId('researchGoToTab');
    if (goToTab) goToTab.hidden = !view.canGoToTab;

    const receipt = byId('researchReceipt');
    if (receipt) receipt.value = view.receipt;
    setDisabled('researchCopy', busy || !view.receipt);
    setDisabled('researchStart', busy || !view.canStart);
    setDisabled('researchSetTask', busy || view.view !== 'recording');
    setDisabled('researchTask', busy || view.view !== 'recording');
    setDisabled('researchFinish', busy || view.view !== 'recording');
    setDisabled('researchFinishInterrupted', busy || view.view !== 'interrupted');
    setDisabled('researchRetrySave', busy || view.view !== 'pending');
    setDisabled('researchRetryWithdraw', busy || view.view !== 'withdrawing');
    setDisabled('researchWithdrawReceipt', busy || !view.sections.saved);
    setDisabled('researchNewSession', busy || !view.canStart);
    setDisabled('researchGoToTab', busy || !view.canGoToTab);
    setDisabled('researchDiscardStarting', busy || view.view !== 'starting');
    for (const id of ['researchKey', 'researchProtocol', 'researchConsent', 'researchTraining']) {
      setDisabled(id, busy || !view.sections.setup);
    }
    setDisabled('toggleActivo', state.view !== 'idle' && state.view !== 'saved');
  }

  async function refresh() {
    const state = await send('RESEARCH_STATUS');
    lastState = state;
    render(state);
    return state;
  }

  async function run(key, operation, errorIds) {
    if (inFlight.has(key)) return;
    inFlight.add(key);
    clearError(errorIds);
    render(lastState);
    try {
      await operation();
    } catch (error) {
      showError(errorIds, messageOf(error));
    } finally {
      inFlight.delete(key);
      await refresh().catch(error => showError(errorIds, messageOf(error)));
    }
  }

  function confirmDiscard() {
    return confirm('¿Quieres descartar la sesión actual sin guardar o retirar la última sesión guardada? Esto elimina su registro de investigación local y en la API; no elimina respuestas de Google Forms, copias de seguridad, modelos entrenados ni el historial del proveedor de IA.');
  }

  byId('researchStart')?.addEventListener('click', () => run('start', async () => {
    const key = byId('researchKey').value;
    await send('RESEARCH_START', {
      key,
      consent: byId('researchConsent').checked,
      trainingConsent: byId('researchTraining').checked,
      protocol: byId('researchProtocol').value
    });
    // Keep failed setup editable in this popup only; never persist the key.
    byId('researchKey').value = '';
  }, ['researchStartError', 'researchStartingError']));

  byId('researchSetTask')?.addEventListener('click', () => run('task',
    () => send('RESEARCH_TASK', { task: byId('researchTask').value }), 'researchActionError'));

  byId('researchFinish')?.addEventListener('click', () => run('save',
    () => send('RESEARCH_FINISH'), 'researchActionError'));

  byId('researchFinishInterrupted')?.addEventListener('click', () => run('save',
    () => send('RESEARCH_FINISH'), 'researchInterruptedError'));

  byId('researchRetrySave')?.addEventListener('click', () => run('save',
    () => send('RESEARCH_FINISH'), 'researchPendingError'));

  byId('researchGoToTab')?.addEventListener('click', () => run('focus',
    () => send('RESEARCH_FOCUS'), 'researchActionError'));

  for (const [id, errorId] of [
    ['researchDiscard', 'researchActionError'],
    ['researchDiscardInterrupted', 'researchInterruptedError'],
    ['researchDiscardPending', 'researchPendingError'],
    ['researchWithdrawReceipt', 'researchWithdrawPendingError'],
    ['researchRetryWithdraw', 'researchWithdrawPendingError'],
    ['researchDiscardStarting', 'researchStartingError']
  ]) {
    byId(id)?.addEventListener('click', () => {
      if (!confirmDiscard()) return;
      run('discard', () => send('RESEARCH_DISCARD'), errorId);
    });
  }

  byId('researchCopy')?.addEventListener('click', async () => {
    clearError('researchCopyError');
    try {
      await navigator.clipboard.writeText(byId('researchReceipt').value);
    } catch {
      byId('researchReceipt').select();
      showError('researchCopyError', 'No se pudo copiar automáticamente. El identificador quedó seleccionado; cópialo manualmente.');
    }
  });

  byId('researchNewSession')?.addEventListener('click', () => {
    setupRequested = true;
    render(lastState);
  });

  if (api.storage?.onChanged) {
    api.storage.onChanged.addListener((changes, area) => {
      if (area !== 'local' || !('researchState' in changes)) return;
      refresh().catch(() => {});
    });
  }

  render(lastState);
  refresh().catch(error => showError(['researchStartError'], messageOf(error)));
})(typeof globalThis !== 'undefined' ? globalThis : this);
