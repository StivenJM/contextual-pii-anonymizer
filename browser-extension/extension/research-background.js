/* Research collection is deliberately separate from the attachment pipeline. */
(function (root) {
  'use strict';

  function createResearchController({ read, write, request }) {
    let queue = Promise.resolve();
    const serial = operation => {
      const result = queue.then(operation);
      queue = result.catch(() => {});
      return result;
    };
    const snapshot = async () => ({ session: null, receipt: null, ...await read() });
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
        await write({ ...state, session });
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
        await write(state);
      }),
      pause: (tabId, nonce) => serial(async () => {
        const state = await snapshot();
        const session = state.session;
        if (!session || session.tabId !== tabId || session.documentNonce !== nonce) {
          throw new Error('La captura no corresponde a esta pestaña o documento.');
        }
        if (session.phase === 'recording') {
          session.phase = 'paused';
          await write(state);
        }
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
        await write(state);
        return { stored: true };
      }),
      task: task => serial(async () => {
        if (!/^[A-Za-z0-9_-]{1,64}$/.test(task)) throw new Error('El identificador de tarea no es válido.');
        const state = await snapshot();
        if (state.session?.phase !== 'recording') throw new Error('No hay una sesión en grabación.');
        state.session.task = task;
        await write(state);
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
        await write(state);
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
        await write({ session: null, receipt });
        return { receipt_id: receipt.receipt_id, capture_status: receipt.capture_status };
      }),
      discard: () => serial(async () => {
        const state = await snapshot();
        const target = state.session || state.receipt;
        if (!target) return;
        // Withdrawal stops collection and removes raw text even while offline.
        // Retain only the capability/identity needed to retry remote deletion.
        const pending = { ...state, withdrawing: true };
        if (state.session) pending.session = {
          id: target.id, token: target.token, tabId: target.tabId,
          origin: target.origin, documentNonce: target.documentNonce,
          apiOrigin: target.apiOrigin,
          phase: 'withdrawing', events: []
        };
        await write(pending);
        await request(`/sessions/${target.id || target.session_id}`, {
          method: 'DELETE', headers: { Authorization: `Bearer ${target.token}` }
        }, target.apiOrigin);
        await write({ session: null, receipt: state.session ? state.receipt : null });
      })
    };
  }

  if (typeof module !== 'undefined') module.exports = { createResearchController };
  else root.createResearchController = createResearchController;
})(globalThis);

if (typeof chrome !== 'undefined' && chrome.runtime) {
  (function () {
    const api = typeof browser !== 'undefined' ? browser : chrome;
    // Only the trusted packaged configuration can select a new session's API.
    // Legacy sessions stay at their original local API, even after repackaging.
    const localOrigin = new URL(SERVIDOR_ANONIMIZACION).origin;
    const campusOrigin = globalThis.RESEARCH_API_ORIGIN;
    const ready = api.storage.local.setAccessLevel
      ? api.storage.local.setAccessLevel({ accessLevel: 'TRUSTED_CONTEXTS' })
      : Promise.resolve();
    const controller = createResearchController({
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

    async function handle(message, sender) {
      const popup = sender.url === api.runtime.getURL('popup.html');
      const state = await controller.snapshot();
      if (message.type === 'RESEARCH_STATUS') {
        if (!popup) return {
          recording: state.session?.phase === 'recording' && state.session.tabId === sender.tab?.id && state.session.documentNonce === message.documentNonce,
          paused: !!state.session && state.session.tabId === sender.tab?.id && state.session.documentNonce !== message.documentNonce
        };
        return {
          phase: state.withdrawing ? 'withdrawing' : state.session?.phase || 'idle', count: state.session?.events.length || 0,
          api_origin: state.session?.apiOrigin || state.receipt?.apiOrigin || campusOrigin || localOrigin,
          enrollment_only: !!campusOrigin,
          receipt_id: !state.session && !state.withdrawing ? state.receipt?.receipt_id || '' : '',
          capture_status: !state.session && !state.withdrawing ? state.receipt?.capture_status || '' : ''
        };
      }
      if (message.type === 'RESEARCH_APPEND') {
        if (new URL(sender.url).origin !== state.session?.origin) throw new Error('El origen de la captura no coincide con el de esta sesión.');
        return controller.append(sender.tab?.id, message.documentNonce, message.event);
      }
      if (message.type === 'RESEARCH_INTERRUPTED') {
        return controller.pause(sender.tab?.id, message.documentNonce);
      }
      if (!popup) throw new Error('Solo el panel de la extensión puede controlar una sesión.');
      if (message.type === 'RESEARCH_START') {
        if (state.session || state.withdrawing) throw new Error('Primero finaliza o descarta la sesión actual.');
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
        await controller.activate(tab.id, prepared.documentNonce);
        return result;
      }
      if (message.type === 'RESEARCH_TASK') return controller.task(message.task);
      if (message.type === 'RESEARCH_FINISH') {
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
        return controller.upload();
      }
      if (message.type === 'RESEARCH_DISCARD') {
        if (state.session) {
          await api.tabs.sendMessage(state.session.tabId, { type: 'RESEARCH_STOP' }).catch(() => {});
        }
        return controller.discard();
      }
      throw new Error('La operación de investigación no es válida.');
    }

    api.runtime.onMessage.addListener((message, sender, reply) => {
      if (!message?.type?.startsWith('RESEARCH_')) return;
      handle(message, sender).then(result => reply({ ok: true, ...result }), error => reply({ ok: false, error: error.message || 'No se pudo completar la operación de investigación; los datos se conservan en este navegador.' }));
      return true;
    });
  })();
}
