/* Research collection is deliberately separate from the attachment pipeline. */
(function (root) {
  'use strict';

  const INCIDENTS = Object.freeze({
    send_blocked: 'La captura está en pausa o la conversación cambió. Este envío se bloqueó: finaliza y guarda la sesión o descártala desde la extensión.',
    send_failed: 'No se pudo guardar este envío en este navegador. El mensaje se bloqueó; vuelve a intentarlo o revisa la captura desde la extensión.',
    flush_failed: 'No se pudo guardar la última respuesta. La captura quedó detenida; reintenta el guardado desde la extensión.',
    file_rejected: 'La captura de investigación solo admite texto. No adjuntes archivos, imágenes, audio ni video.',
    conversation_changed: 'Captura en pausa: cambió la conversación. Finaliza y guarda esta sesión interrumpida o descártala desde la extensión.',
    page_paused: 'Captura en pausa después de cambiar de página. Finaliza y guarda la sesión interrumpida o descártala antes de continuar.',
    tab_closed: 'La pestaña de la captura se cerró. Guarda los datos disponibles o descarta la sesión desde la extensión.'
  });

  function createResearchController({ read, write, request, onChange }) {
    let queue = Promise.resolve();
    const serial = operation => {
      const result = queue.then(operation);
      queue = result.catch(() => {});
      return result;
    };
    const snapshot = async () => ({ session: null, receipt: null, incident: null, ...await read() });
    const persist = async state => {
      await write(state);
      if (onChange) { try { await onChange(state); } catch { /* the badge is best effort */ } }
    };
    return {
      snapshot,
      start: input => serial(async () => {
        if (input.consent !== true) throw new Error('Debes dar tu consentimiento para iniciar la captura.');
        const state = await snapshot();
        if (state.session || state.withdrawing) throw new Error('Primero finaliza o descarta la sesión actual.');
        const session = {
          id: crypto.randomUUID(),
          token: crypto.randomUUID().replaceAll('-', '') + crypto.randomUUID().replaceAll('-', ''),
          tabId: input.tabId,
          origin: input.origin,
          documentNonce: input.documentNonce,
          apiOrigin: input.apiOrigin,
          provider: input.provider,
          protocol: input.protocol,
          trainingConsent: input.trainingConsent === true,
          phase: 'starting', task: 'unassigned', events: []
        };
        // Save the capability first: an interrupted authorization can be discarded.
        await persist({ ...state, session, lastError: null });
        await request('/sessions', {
          method: 'POST', headers: { [input.enrollmentOnly ? 'X-Research-Enrollment' : 'X-Research-Key']: input.key },
          body: JSON.stringify({
            session_id: session.id, upload_token: session.token,
            protocol_version: session.protocol, provider: session.provider,
            consent: true, training_consent: session.trainingConsent
          })
        }, session.apiOrigin);
        return { session_id: session.id };
      }),
      activate: (tabId, nonce) => serial(async () => {
        const state = await snapshot();
        const session = state.session;
        if (session?.phase !== 'starting' || session.tabId !== tabId || session.documentNonce !== nonce) {
          throw new Error('No se pudo confirmar la activación de esta sesión. Descarta la configuración incompleta.');
        }
        session.phase = 'recording';
        session.pausedReason = null;
        state.lastError = null;
        await persist(state);
      }),
      pause: (tabId, nonce, reason) => serial(async () => {
        const state = await snapshot();
        const session = state.session;
        if (!session || session.tabId !== tabId || session.documentNonce !== nonce) {
          throw new Error('La captura no corresponde a esta pestaña o documento.');
        }
        if (session.phase === 'recording') {
          session.phase = 'paused';
          session.pausedReason = reason || 'conversation_changed';
          await persist(state);
        }
      }),
      // A closed capture tab cannot continue; keep the collected text available.
      interrupt: (reason, tabId) => serial(async () => {
        const state = await snapshot();
        const session = state.session;
        if (!session || session.phase !== 'recording') return { interrupted: false };
        if (tabId !== undefined && session.tabId !== tabId) return { interrupted: false };
        session.phase = 'paused';
        session.pausedReason = reason || 'tab_closed';
        await persist(state);
        return { interrupted: true };
      }),
      incident: (tabId, nonce, code) => serial(async () => {
        const state = await snapshot();
        const session = state.session;
        if (!session || session.tabId !== tabId || session.documentNonce !== nonce) {
          throw new Error('No se está grabando este documento.');
        }
        const message = INCIDENTS[code];
        if (!message) throw new Error('El incidente no es válido.');
        const current = state.incident;
        const incident = current && current.code === code
          ? current
          : { id: crypto.randomUUID(), code, message, at: Date.now() };
        if (incident !== current) {
          state.incident = incident;
          await persist(state);
        }
        return { incident: { id: incident.id, code, message } };
      }),
      append: (tabId, nonce, event) => serial(async () => {
        const state = await snapshot();
        const session = state.session;
        if (!session || session.phase !== 'recording' || session.tabId !== tabId || session.documentNonce !== nonce) {
          throw new Error('No se está grabando este documento.');
        }
        if (!event || !['user', 'assistant'].includes(event.role) || typeof event.text !== 'string' || !event.text.trim() || event.text.length > 100000 || !/^[a-f0-9-]{36}$/i.test(event.event_id) || !Number.isFinite(Date.parse(event.captured_at))) {
          throw new Error('El mensaje no es compatible o supera el tamaño permitido.');
        }
        const index = session.events.findIndex(e => e.event_id === event.event_id);
        const item = {
          event_id: event.event_id, role: event.role, text: event.text,
          captured_at: event.captured_at,
          task_id: index >= 0 ? session.events[index].task_id : (event.role === 'assistant' ? session.events.findLast(e => e.role === 'user')?.task_id || session.task : session.task)
        };
        if (index >= 0) {
          const previous = session.events[index];
          if (previous.role !== item.role || (item.role === 'user' && previous.text !== item.text)) {
            throw new Error('No se puede sobrescribir un mensaje que ya se envió.');
          }
          session.events[index] = item;
        } else {
          session.events.push(item);
        }
        if (session.events.length > 1000 || new TextEncoder().encode(JSON.stringify(session.events)).length > 800000) {
          throw new Error('Se alcanzó el límite local de la sesión. Finaliza y guarda antes de continuar.');
        }
        // A send that the controller accepted resolves the blocking incident.
        state.incident = null;
        state.lastError = null;
        await persist(state);
        return { stored: true };
      }),
      task: task => serial(async () => {
        if (!/^[A-Za-z0-9_-]{1,64}$/.test(task)) throw new Error('El identificador de tarea no es válido.');
        const state = await snapshot();
        if (state.session?.phase !== 'recording') throw new Error('No hay una sesión en grabación.');
        state.session.task = task;
        await persist(state);
      }),
      freeze: captureStatus => serial(async () => {
        const state = await snapshot();
        if (state.withdrawing) throw new Error('El retiro está pendiente; vuelve a intentar la eliminación.');
        if (!state.session) throw new Error('No hay una sesión para guardar.');
        if (state.session.phase === 'pending') return;
        if (!state.session.events.some(e => e.role === 'user')) throw new Error('No hay mensajes enviados. Descarta la sesión vacía.');
        const interrupted = state.session.phase === 'paused';
        state.session.phase = 'pending';
        state.session.batch = { schema_version: 1, capture_status: interrupted ? 'interrupted' : captureStatus, events: state.session.events };
        state.incident = null;
        state.lastError = null;
        await persist(state);
      }),
      upload: () => serial(async () => {
        const state = await snapshot();
        const session = state.session;
        if (session?.phase !== 'pending') throw new Error('Detén la grabación antes de enviar la sesión a la API.');
        const result = await request(`/sessions/${session.id}/complete`, {
          method: 'PUT', headers: { Authorization: `Bearer ${session.token}` },
          body: JSON.stringify(session.batch)
        }, session.apiOrigin);
        if (!/^[A-Za-z0-9_-]{32}$/.test(result.receipt_id) || result.event_count !== session.batch.events.length) {
          throw new Error('La confirmación de guardado no es válida. Los datos se conservan en este navegador.');
        }
        const receipt = {
          receipt_id: result.receipt_id, session_id: session.id,
          token: session.token, capture_status: session.batch.capture_status, apiOrigin: session.apiOrigin
        };
        await persist({ session: null, receipt, incident: null, lastError: null });
        return { receipt_id: receipt.receipt_id, capture_status: receipt.capture_status };
      }),
      // Keep the last failed operation discoverable after the popup is reopened.
      fail: message => serial(async () => {
        const state = await snapshot();
        state.lastError = typeof message === 'string' && message ? message.slice(0, 300) : 'No se pudo completar la operación.';
        await persist(state);
      }),
      discard: () => serial(async () => {
        const state = await snapshot();
        const target = state.session || state.receipt;
        if (!target) return;
        // Withdrawal stops collection and removes raw text even while offline.
        // Retain only the capability/identity needed to retry remote deletion.
        const pending = { ...state, withdrawing: true, incident: null };
        if (state.session) pending.session = {
          id: target.id, token: target.token, tabId: target.tabId,
          origin: target.origin, documentNonce: target.documentNonce,
          apiOrigin: target.apiOrigin,
          phase: 'withdrawing', events: []
        };
        await persist(pending);
        await request(`/sessions/${target.id || target.session_id}`, {
          method: 'DELETE', headers: { Authorization: `Bearer ${target.token}` }
        }, target.apiOrigin);
        await persist({ session: null, receipt: state.session ? state.receipt : null, incident: null, lastError: null });
      })
    };
  }

  function describeView(state) {
    if (state?.withdrawing) return 'withdrawing';
    const session = state?.session;
    if (!session) return state?.receipt ? 'saved' : 'idle';
    if (session.phase === 'starting') return 'starting';
    if (session.phase === 'recording') return 'recording';
    if (session.phase === 'paused') return 'interrupted';
    if (session.phase === 'pending') return 'pending';
    if (session.phase === 'withdrawing') return 'withdrawing';
    return 'idle';
  }

  const BADGE_TITLES = Object.freeze({
    idle: 'Sin captura de investigación',
    saved: 'Sesión guardada: el identificador está en la ventana de la extensión',
    starting: 'Iniciando la captura de investigación',
    recording: 'Captura activa en esta pestaña',
    attention: 'La captura necesita atención: abre la ventana de la extensión',
    interrupted: 'Captura interrumpida: abre la ventana de la extensión para guardar o descartar',
    pending: 'Sesión detenida y pendiente de guardar: abre la ventana de la extensión',
    withdrawing: 'Retiro pendiente de confirmar: abre la ventana de la extensión'
  });
  const BADGE_COLORS = Object.freeze({
    idle: '#4a4b52', saved: '#4a4b52', starting: '#2f6fdd',
    recording: '#2f7d4f', attention: '#b26a00', pending: '#b26a00'
  });

  // The badge is derived from persisted state so a service-worker restart
  // rebuilds it, and a blocking incident outranks a healthy capture.
  function badgeForState(state) {
    const view = describeView(state);
    if (state?.incident && state?.session) {
      return { view: 'attention', text: '!', title: BADGE_TITLES.attention, color: BADGE_COLORS.attention, tabId: null };
    }
    if (view === 'recording') {
      return { view, text: 'REC', title: BADGE_TITLES.recording, color: BADGE_COLORS.recording, tabId: state.session.tabId };
    }
    if (view === 'starting') {
      return { view, text: '…', title: BADGE_TITLES.starting, color: BADGE_COLORS.starting, tabId: null };
    }
    if (view === 'interrupted' || view === 'withdrawing') {
      return { view: 'attention', text: '!', title: view === 'interrupted' ? BADGE_TITLES.interrupted : BADGE_TITLES.withdrawing, color: BADGE_COLORS.attention, tabId: null };
    }
    if (view === 'pending') {
      return { view, text: 'PEND', title: BADGE_TITLES.pending, color: BADGE_COLORS.pending, tabId: null };
    }
    return { view, text: '', title: view === 'saved' ? BADGE_TITLES.saved : BADGE_TITLES.idle, color: BADGE_COLORS.idle, tabId: null };
  }

  function createBadgeSync(browserApi) {
    let previousTabId = null;
    const call = async (method, details) => {
      try { await browserApi.action[method](details); } catch { /* unavailable in an older browser */ }
    };
    return async function syncBadge(state) {
      const badge = badgeForState(state);
      if (previousTabId !== null && previousTabId !== badge.tabId) {
        await call('setBadgeText', { tabId: previousTabId, text: '' });
        await call('setTitle', { tabId: previousTabId, title: '' });
      }
      previousTabId = badge.tabId;
      if (badge.tabId !== null) {
        // A per-tab label must never claim that another tab is being captured.
        await call('setBadgeText', { text: '' });
        await call('setTitle', { title: BADGE_TITLES.idle });
        await call('setBadgeText', { tabId: badge.tabId, text: badge.text });
        await call('setBadgeBackgroundColor', { tabId: badge.tabId, color: badge.color });
        await call('setTitle', { tabId: badge.tabId, title: badge.title });
        return;
      }
      await call('setBadgeText', { text: badge.text });
      await call('setBadgeBackgroundColor', { color: badge.color });
      await call('setTitle', { title: badge.title });
      // Clear labels left on chat tabs by a previous service-worker lifetime.
      let tabs = [];
      const supported = typeof SITIOS_SOPORTADOS !== 'undefined' ? SITIOS_SOPORTADOS : [];
      try { tabs = await browserApi.tabs.query({ url: supported }); } catch { tabs = []; }
      for (const tab of tabs) {
        if (tab.id === undefined) continue;
        await call('setBadgeText', { tabId: tab.id, text: '' });
        await call('setTitle', { tabId: tab.id, title: '' });
      }
    };
  }

  if (typeof module !== 'undefined') {
    module.exports = { createResearchController, describeView, badgeForState, createBadgeSync, INCIDENTS };
  } else {
    root.createResearchController = createResearchController;
    root.researchUi = { describeView, badgeForState, createBadgeSync };
  }
})(globalThis);

if (typeof chrome !== 'undefined' && chrome.runtime) {
  (function () {
    const api = typeof browser !== 'undefined' ? browser : chrome;
    // This wiring lives outside the controller closure; the UI helpers are
    // published on the global object by the branch above.
    const { createBadgeSync } = globalThis.researchUi;
    const describeView = globalThis.researchUi.describeView;
    const createController = globalThis.createResearchController;
    // Only the trusted packaged configuration can select a new session's API.
    // Legacy sessions stay at their original local API, even after repackaging.
    const localOrigin = new URL(SERVIDOR_ANONIMIZACION).origin;
    const campusOrigin = globalThis.RESEARCH_API_ORIGIN;
    const ready = api.storage.local.setAccessLevel
      ? api.storage.local.setAccessLevel({ accessLevel: 'TRUSTED_CONTEXTS' })
      : Promise.resolve();
    const syncBadge = createBadgeSync(api);
    const controller = createController({
      read: async () => {
        try {
          await ready;
          return (await api.storage.local.get('researchState')).researchState || {};
        } catch {
          throw new Error('No se pudo leer el almacenamiento de la captura. Conserva este perfil y vuelve a intentarlo.');
        }
      },
      write: async state => {
        try {
          await ready;
          await api.storage.local.set({ researchState: state });
        } catch {
          throw new Error('No se pudo actualizar el almacenamiento de la captura. No borres los datos del navegador; revisa la sesión en la extensión.');
        }
      },
      onChange: syncBadge,
      request: async (path, options, apiOrigin) => {
        const origin = apiOrigin || localOrigin;
        const url = new URL(origin);
        if (url.origin !== origin || (url.protocol !== 'https:' && origin !== localOrigin)) {
          throw new Error('La configuración de la API de investigación no es válida.');
        }
        const response = await fetch(origin + '/api/research' + path, {
          ...options,
          headers: { 'Content-Type': 'application/json', ...options.headers },
          signal: AbortSignal.timeout(15000), redirect: 'error', cache: 'no-store', credentials: 'omit'
        }).catch(() => {
          throw new Error('No se pudo conectar con la API de investigación. Verifica la conexión y vuelve a intentarlo desde la extensión; no borres los datos del navegador.');
        });
        if (!response.ok && !(options.method === 'DELETE' && response.status === 404)) {
          throw new Error(`La API de investigación respondió con el código ${response.status}. Revisa la sesión y vuelve a intentarlo desde la extensión.`);
        }
        return response.status === 204 || response.status === 404 ? {} : response.json().catch(() => {
          throw new Error('La API no devolvió una respuesta válida. Conserva este perfil y vuelve a intentarlo desde la extensión.');
        });
      }
    });

    // Rebuild the action indicator from the persisted session after a restart.
    controller.snapshot().then(syncBadge).catch(() => {});

    async function tabFacts(tabId) {
      try {
        const tab = await api.tabs.get(tabId);
        let active = false;
        try {
          const [focused] = await api.tabs.query({ active: true, lastFocusedWindow: true });
          active = focused?.id === tabId;
        } catch { active = false; }
        return { id: tabId, exists: true, active, windowId: tab.windowId };
      } catch {
        return { id: tabId, exists: false, active: false };
      }
    }

    async function handle(message, sender) {
      const popup = sender.url === api.runtime.getURL('popup.html');
      const state = await controller.snapshot();
      if (message.type === 'RESEARCH_STATUS') {
        if (!popup) {
          const ownTab = !!state.session && state.session.tabId === sender.tab?.id;
          const paused = ownTab && state.session.documentNonce !== message.documentNonce;
          if (paused && state.session.phase === 'recording') {
            // The authorized document was replaced (reload/navigation).
            await controller.interrupt('page_paused', sender.tab.id).catch(() => {});
          }
          return {
            recording: ownTab && !paused && state.session.phase === 'recording',
            paused,
            incident: state.incident ? { code: state.incident.code, message: state.incident.message } : null
          };
        }
        const session = state.session;
        return {
          phase: state.withdrawing ? 'withdrawing' : session?.phase || 'idle',
          view: describeView(state),
          count: session?.events.length || 0,
          provider: session?.provider || '',
          task: session?.task || '',
          paused_reason: session?.pausedReason || '',
          api_origin: session?.apiOrigin || state.receipt?.apiOrigin || campusOrigin || localOrigin,
          enrollment_only: !!campusOrigin,
          receipt_id: !session && !state.withdrawing ? state.receipt?.receipt_id || '' : '',
          capture_status: !session && !state.withdrawing ? state.receipt?.capture_status || '' : '',
          has_receipt: !!state.receipt && !state.withdrawing,
          last_error: state.lastError || '',
          tab: session ? await tabFacts(session.tabId) : null,
          incident: state.incident ? { code: state.incident.code, message: state.incident.message } : null
        };
      }
      if (message.type === 'RESEARCH_APPEND') {
        if (new URL(sender.url).origin !== state.session?.origin) throw new Error('El origen de la captura no coincide con el de esta sesión.');
        return controller.append(sender.tab?.id, message.documentNonce, message.event);
      }
      if (message.type === 'RESEARCH_INCIDENT') {
        if (new URL(sender.url).origin !== state.session?.origin) throw new Error('El origen de la captura no coincide con el de esta sesión.');
        return controller.incident(sender.tab?.id, message.documentNonce, message.code);
      }
      if (message.type === 'RESEARCH_INTERRUPTED') {
        return controller.pause(sender.tab?.id, message.documentNonce, message.reason);
      }
      if (!popup) throw new Error('Solo el panel de la extensión puede controlar una sesión.');
      if (message.type === 'RESEARCH_FOCUS') {
        const session = state.session;
        if (!session) throw new Error('No hay una sesión en captura.');
        try {
          const tab = await api.tabs.get(session.tabId);
          await api.tabs.update(tab.id, { active: true });
          if (tab.windowId !== undefined) await api.windows.update(tab.windowId, { focused: true });
          return { focused: true };
        } catch {
          throw new Error('La pestaña de captura ya no está disponible. Finaliza y guarda los datos disponibles o descarta la sesión.');
        }
      }
      if (message.type === 'RESEARCH_START') {
        if (state.session || state.withdrawing) throw new Error('Primero finaliza o descarta la sesión actual.');
        try {
          const [tab] = await api.tabs.query({ active: true, currentWindow: true });
          const origin = new URL(tab.url).origin;
          const providers = { 'https://chatgpt.com': 'chatgpt', 'https://claude.ai': 'claude', 'https://gemini.google.com': 'gemini' };
          const provider = providers[origin] || (SITIOS_SOPORTADOS.includes(origin + '/*') ? 'chatgpt' : null);
          if (!provider) throw new Error('Primero abre una pestaña de chat compatible.');
          const prepared = await api.tabs.sendMessage(tab.id, { type: 'RESEARCH_PREPARE' }).catch(() => null);
          if (prepared?.reason === 'history') throw new Error('Esta conversación ya tiene mensajes. Abre una conversación nueva y vacía para iniciar la captura.');
          if (prepared?.reason === 'editor_unavailable') throw new Error('No se encontró el editor del chat. Espera a que cargue la página o abre una conversación nueva compatible.');
          if (!prepared?.ready) throw new Error('No se pudo acceder al editor o al botón de envío. Usa una conversación nueva en un chat compatible.');
          const result = await controller.start({ ...message, tabId: tab.id, origin, provider, documentNonce: prepared.documentNonce,
            apiOrigin: campusOrigin || localOrigin, enrollmentOnly: !!campusOrigin });
          const activated = await api.tabs.sendMessage(tab.id, { type: 'RESEARCH_ACTIVATE', documentNonce: prepared.documentNonce }).catch(() => null);
          if (!activated?.activated) throw new Error('No se pudo activar la captura. Descarta la configuración incompleta.');
          try {
            await controller.activate(tab.id, prepared.documentNonce);
          } catch (error) {
            await api.tabs.sendMessage(tab.id, { type: 'RESEARCH_STOP' }).catch(() => {});
            throw error;
          }
          // Success is announced only after the activation was persisted.
          api.tabs.sendMessage(tab.id, { type: 'RESEARCH_CONFIRM', documentNonce: prepared.documentNonce }).catch(() => {});
          return result;
        } catch (error) {
          const current = await controller.snapshot();
          if (current.session?.phase === 'starting') await controller.fail(error?.message).catch(() => {});
          throw error;
        }
      }
      if (message.type === 'RESEARCH_TASK') return controller.task(message.task);
      if (message.type === 'RESEARCH_FINISH') {
        try {
          if (state.session?.phase === 'recording') {
            let status = 'complete';
            try {
              const result = await api.tabs.sendMessage(state.session.tabId, { type: 'RESEARCH_FLUSH', documentNonce: state.session.documentNonce });
              if (!result?.flushed) throw new Error('Flush unavailable');
            } catch {
              // Do not label a closed/reloaded page as a complete transcript.
              status = 'interrupted';
            }
            await controller.freeze(status);
          }
          if (state.session?.phase === 'paused') await controller.freeze('interrupted');
          return await controller.upload();
        } catch (error) {
          await controller.fail(error?.message).catch(() => {});
          throw error;
        }
      }
      if (message.type === 'RESEARCH_DISCARD') {
        try {
          if (state.session) {
            await api.tabs.sendMessage(state.session.tabId, { type: 'RESEARCH_STOP' }).catch(() => {});
          }
          return await controller.discard();
        } catch (error) {
          await controller.fail(error?.message).catch(() => {});
          throw error;
        }
      }
      throw new Error('La operación de investigación no es válida.');
    }

    api.runtime.onMessage.addListener((message, sender, reply) => {
      if (!message?.type?.startsWith('RESEARCH_')) return;
      handle(message, sender).then(result => reply({ ok: true, ...result }), error => reply({ ok: false, error: error.message || 'No se pudo completar la operación de investigación; los datos se conservan en este navegador.' }));
      return true;
    });

    if (api.tabs?.onRemoved) {
      api.tabs.onRemoved.addListener(tabId => {
        controller.interrupt('tab_closed', tabId).catch(() => {});
      });
    }
  })();
}
