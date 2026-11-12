/* ISOLATED world only. No credentials or transcripts cross window.postMessage. */
(function () {
  'use strict';
  const api = typeof browser !== 'undefined' ? browser : chrome;
  const documentNonce = crypto.randomUUID();
  const editorSelector = '[data-research-editor], #prompt-textarea, textarea[data-mobile-composer-prompt], div.ProseMirror[contenteditable="true"], rich-textarea [contenteditable="true"], [contenteditable="true"][role="textbox"]';
  const sendSelector = '[data-research-send], [data-testid="send-button"], [data-testid="send-message-button"], button[aria-label="Send prompt"], button[aria-label="Send message"], button[aria-label="Send Message"], button[aria-label="Enviar mensaje"], button[aria-label="Enviar"], button.send-button';
  const assistantSelector = '[data-research-role="assistant"], [data-message-author-role="assistant"], .font-claude-response, model-response';
  let recording = false;
  let paused = false;
  let replaying = false;
  let inFlight = Promise.resolve();
  let sending = false;
  let assistantQueue = Promise.resolve();
  let timer;
  const notice = typeof createResearchNotice === 'function' ? createResearchNotice(document) : null;
  let baseline = new WeakSet();
  let scopePath = location.pathname;
  let submittedCount = 0;
  let scopeInterrupted = false;
  const observed = new WeakMap();

  async function message(payload) {
    const response = await api.runtime.sendMessage(payload);
    if (!response?.ok) throw new Error(response?.error || 'El almacenamiento de la captura no está disponible.');
    return response;
  }
  const visible = selector => [...document.querySelectorAll(selector)].find(e => e.getClientRects().length);
  const textOf = node => 'value' in node ? node.value : node.innerText;
  // A blocking failure is deduplicated by the incident the controller persists.
  // The success notice never replaces an active incident, and never appears here.
  async function report(code) {
    let incident = null;
    try {
      const response = await message({ type: 'RESEARCH_INCIDENT', documentNonce, code });
      incident = response?.incident || null;
    } catch {
      incident = null;
    }
    if (!incident) {
      notice?.showIncident({ id: `local:${code}`, text: 'La captura necesita atención y las operaciones sobre la sesión no están disponibles. Revisa la extensión o recarga esta pestaña.' });
      return;
    }
    notice?.showIncident({ id: incident.id, text: incident.message });
  }
  function checkScope() {
    if (scopeInterrupted) return false;
    const next = location.pathname;
    if (next === scopePath) return true;
    // Providers assign the first newly created conversation an URL after send.
    // Permit that single known transition, never switching to a second history.
    const firstAssignment = submittedCount === 1 && (
      (location.hostname === 'chatgpt.com' && scopePath === '/' && /^\/c\/[^/]+$/.test(next)) ||
      (location.hostname === 'chatgpt.com' && /^\/g\/[^/]+$/.test(scopePath) && next.startsWith(scopePath + '/c/')) ||
      (location.hostname === 'claude.ai' && scopePath === '/new' && /^\/chat\/[^/]+$/.test(next)) ||
      (location.hostname === 'gemini.google.com' && scopePath === '/app' && /^\/app\/[^/]+$/.test(next))
    );
    if (firstAssignment) { scopePath = next; return true; }
    scopeInterrupted = true;
    recording = false;
    paused = true;
    clearTimeout(timer);
    message({ type: 'RESEARCH_INTERRUPTED', documentNonce, reason: 'conversation_changed' }).catch(() => {});
    report('conversation_changed');
    return false;
  }
  async function append(event) {
    return message({ type: 'RESEARCH_APPEND', documentNonce, event });
  }
  function assistantNodes() {
    return [...document.querySelectorAll(assistantSelector)].filter(node => !node.parentElement?.closest(assistantSelector));
  }
  function snapshotAssistants() {
    assistantQueue = assistantQueue.catch(() => {}).then(async () => {
      if (!checkScope()) throw new Error('La conversación cambió.');
      for (const node of assistantNodes()) {
        if (!checkScope()) throw new Error('La conversación cambió.');
        if (baseline.has(node)) continue;
        const text = node.innerText;
        if (!text?.trim()) continue;
        const previous = observed.get(node);
        if (previous?.text === text) continue;
        const event = {
          event_id: previous?.event_id || crypto.randomUUID(), role: 'assistant', text,
          captured_at: previous?.captured_at || new Date().toISOString()
        };
        await append(event);
        observed.set(node, event);
      }
    });
    return assistantQueue;
  }

  function intercept(event) {
    if (replaying || (!recording && !paused)) return;
    checkScope();
    const editor = visible(editorSelector);
    const send = visible(sendSelector);
    const isEnter = event.type === 'keydown' && event.key === 'Enter' && !event.shiftKey && !event.ctrlKey && !event.altKey && !event.metaKey && !event.isComposing && editor?.contains(event.target);
    const isClick = event.type === 'click' && event.target.closest?.(sendSelector);
    const isSubmit = event.type === 'submit' && event.target.contains(editor);
    if (!isEnter && !isClick && !isSubmit) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    if (paused || !editor || !send || send.disabled) { report('send_blocked'); return; }
    if (sending) return;
    const text = textOf(editor);
    if (!text?.trim()) return;
    sending = true;
    inFlight = (async () => {
      try {
        await snapshotAssistants();
        if (!checkScope()) throw new Error('La conversación cambió.');
        await append({ event_id: crypto.randomUUID(), role: 'user', text, captured_at: new Date().toISOString() });
        submittedCount += 1;
        if (!checkScope()) throw new Error('La conversación cambió.');
        if (textOf(editor) !== text) throw new Error('El borrador cambió antes de enviarse.');
        replaying = true;
        try { send.click(); } finally { replaying = false; }
      } catch { report('send_failed'); }
      finally { sending = false; }
    })();
  }
  for (const type of ['click', 'keydown', 'submit']) window.addEventListener(type, intercept, true);

  // Text-only research tasks must never fall into the model-backed file path.
  for (const type of ['change', 'drop', 'paste']) {
    window.addEventListener(type, event => {
      if (!recording && !paused) return;
      const files = event.target.files || event.dataTransfer?.files || event.clipboardData?.files;
      if (!files?.length) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      if (event.target.type === 'file') event.target.value = '';
      report('file_rejected');
    }, true);
  }

  api.runtime.onMessage.addListener((input, _sender, reply) => {
    if (input.type === 'RESEARCH_PREPARE') {
      baseline = new WeakSet(assistantNodes());
      scopePath = location.pathname;
      submittedCount = 0;
      scopeInterrupted = false;
      const hasHistory = document.querySelector('[data-message-author-role="user"], [data-research-role="user"], .user-query');
      // Empty editors may show a voice control instead of Send until typing.
      // Sending still requires a visible enabled send control in intercept().
      const reason = hasHistory ? 'history' : (!visible(editorSelector) ? 'editor_unavailable' : null);
      reply({ ready: !reason, reason, documentNonce });
      return;
    }
    if (input.type === 'RESEARCH_ACTIVATE' && input.documentNonce === documentNonce) {
      if (!checkScope()) { reply({ activated: false }); return; }
      recording = true; paused = false;
      // The success notice is only shown after the controller persists activation.
      reply({ activated: true });
      return;
    }
    if (input.type === 'RESEARCH_CONFIRM' && input.documentNonce === documentNonce) {
      if (!recording) { reply({ shown: false }); return; }
      notice?.showSuccess();
      reply({ shown: true });
      return;
    }
    if (input.type === 'RESEARCH_STOP') {
      recording = false; paused = false;
      clearTimeout(timer);
      notice?.dispose();
      reply({ stopped: true });
      return;
    }
    if (input.type === 'RESEARCH_FLUSH') {
      if (input.documentNonce !== documentNonce) { reply({ flushed: false }); return; }
      if (!checkScope()) { reply({ flushed: false }); return; }
      recording = false;
      paused = false;
      clearTimeout(timer);
      inFlight.then(snapshotAssistants).then(() => {
        notice?.dispose();
        reply({ flushed: true });
      }, () => { report('flush_failed'); reply({ flushed: false }); });
      return true;
    }
  });

  function noticeNodes(record) {
    const nodes = [...record.addedNodes, ...record.removedNodes];
    if (!nodes.length) return false;
    const host = notice?.element;
    return nodes.every(node => host && (node === host || host.contains(node)));
  }
  const observer = new MutationObserver(records => {
    if (!recording || records.every(noticeNodes)) return;
    if (!checkScope()) return;
    clearTimeout(timer);
    timer = setTimeout(() => snapshotAssistants().catch(() => report('send_failed')), 250);
  });
  observer.observe(document, { childList: true, subtree: true, characterData: true });
  message({ type: 'RESEARCH_STATUS', documentNonce }).then(state => {
    if (!recording) recording = state.recording;
    if (!paused) paused = state.paused;
    if (paused) {
      // The controller already recorded this interruption for this tab.
      notice?.showIncident({
        id: `page_paused:${documentNonce}`,
        text: 'Captura en pausa después de cambiar de página. Finaliza y guarda la sesión interrumpida o descártala desde la extensión.'
      });
    }
  }).catch(() => {});
})();
