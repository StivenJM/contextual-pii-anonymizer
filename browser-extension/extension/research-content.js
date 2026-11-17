/* ISOLATED world only. No credentials or transcripts cross window.postMessage. */
(function () {
  'use strict';
  const api = typeof browser !== 'undefined' ? browser : chrome;
  const chat = typeof chatProtection !== 'undefined' ? chatProtection : null;
  const documentNonce = crypto.randomUUID();
  const editorSelector = '[data-research-editor], #prompt-textarea, textarea[data-mobile-composer-prompt], div.ProseMirror[contenteditable="true"], rich-textarea [contenteditable="true"], [contenteditable="true"][role="textbox"]';
  const sendSelector = '[data-research-send], [data-testid="send-button"], [data-testid="send-message-button"], button[aria-label="Send prompt"], button[aria-label="Send message"], button[aria-label="Send Message"], button[aria-label="Enviar mensaje"], button[aria-label="Enviar"], #composer-submit-button, form button[type="submit"], button[aria-label*="Send" i], button[aria-label*="Enviar" i], button.send-button';
  const assistantSelector = '[data-research-role="assistant"], [data-message-author-role="assistant"], [data-message-author="assistant"], [data-testid="assistant-message"], [data-testid="assistant-turn"], [data-chatgpt-search-unit-key$=":assistant"], [data-content-search-unit-key$=":assistant"], [data-markdown-text-style="assistant-message"], .font-claude-response, .response-content, model-response, .model-response-text, message-content';
  let recording = false;
  let paused = false;
  let replaying = false;
  let inFlight = Promise.resolve();
  let sending = false;
  let assistantQueue = Promise.resolve();
  let timer;
  let generationTimer = null;
  let generationPoll = null;
  let sawGenerating = false;
  const notice = typeof createResearchNotice === 'function' ? createResearchNotice(document) : null;
  let baseline = new WeakMap();
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
  function composerForm(editor) {
    return editor.closest?.('form') || null;
  }
  // "ready": a visible enabled control; "form": the provider renamed the control
  // but the composer still submits; "hidden"/"disabled"/"missing": do not send.
  function sendReadiness(editor) {
    const form = composerForm(editor);
    const candidates = [...(form || document).querySelectorAll(sendSelector)];
    const button = candidates.find(element => element.getClientRects().length);
    if (button) return button.disabled ? 'disabled' : 'ready';
    if (candidates.length) return 'hidden';
    return form?.requestSubmit ? 'form' : 'missing';
  }
  function replaySend(editor) {
    const form = composerForm(editor);
    const button = [...(form || document).querySelectorAll(sendSelector)].find(element => element.getClientRects().length);
    if (button && !button.disabled) { button.click(); return true; }
    if (!button && form?.requestSubmit) { form.requestSubmit(); return true; }
    return false;
  }
  const textOf = node => 'value' in node ? node.value : node.innerText;
  const userNodeSelector = '[data-message-author-role="user"], [data-research-role="user"], [data-testid="user-message"], [data-chatgpt-search-unit-key$=":user"], [data-content-search-unit-key$=":user"], [data-user-message-bubble="true"], [data-markdown-text-style="user-message"], .user-query';
  // A provider publishes the conversation URL after the first submission, and
  // may replace a temporary identifier with the final one. Follow those changes
  // only while the message we captured is still the conversation on screen.
  const EMPTY_CHAT_PATHS = new Set(['/', '/new', '/app']);
  let sentText = '';

  function normalizeText(value) {
    return (value || '').replace(/\s+/g, ' ').trim();
  }
  // Ignore markdown punctuation so a rendered message still matches what was typed.
  function normalizeForMatch(value) {
    return normalizeText(value).replace(/[^\p{L}\p{N}\s]/gu, '').replace(/\s+/g, ' ').trim();
  }
  function conversationRoot() {
    return document.querySelector('main, [role="main"]') || document;
  }
  function visibleUserNodes() {
    const root = conversationRoot();
    return [...root.querySelectorAll(userNodeSelector)]
      .filter(node => node.getClientRects?.().length && !node.closest?.('form'));
  }
  function transcriptReadable() {
    return visibleUserNodes().length > 0;
  }
  function stillShowsSentMessage() {
    const wanted = normalizeForMatch(sentText).slice(0, 80);
    if (!wanted) return false;
    return visibleUserNodes()
      .some(node => normalizeForMatch(textOf(node)).includes(wanted));
  }
  function acceptsAssignment(next) {
    if (EMPTY_CHAT_PATHS.has(next)) return false;
    // Unknown provider markup: the URL is the only available signal.
    if (!transcriptReadable()) return true;
    // The provider may rename the URL; accept only while our message is shown.
    return stillShowsSentMessage();
  }
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
    // Empty-chat routes may be normalised before the first message.
    if (EMPTY_CHAT_PATHS.has(scopePath) && EMPTY_CHAT_PATHS.has(next)) { scopePath = next; return true; }
    if (acceptsAssignment(next)) { scopePath = next; return true; }
    scopeInterrupted = true;
    recording = false;
    paused = true;
    clearTimeout(timer);
    clearGenerationTracking();
    message({ type: 'RESEARCH_INTERRUPTED', documentNonce, reason: 'conversation_changed', from: scopePath, to: next }).catch(() => {});
    report('conversation_changed');
    return false;
  }
  async function append(event) {
    return message({ type: 'RESEARCH_APPEND', documentNonce, event });
  }
  function assistantNodes() {
    const root = conversationRoot();
    const visible = nodes => nodes.filter(node => node.getClientRects?.().length);
    const directText = visible([...root.querySelectorAll('[data-markdown-text-style="assistant-message"]')]);
    if (directText.length) return directText;
    return visible([...root.querySelectorAll(assistantSelector)]
      .filter(node => !node.parentElement?.closest(assistantSelector)));
  }
  function assistantText(node) {
    const answer = node.matches?.('[data-markdown-text-style="assistant-message"]')
      ? node
      : node.querySelector?.('[data-markdown-text-style="assistant-message"]');
    return (answer || node).innerText || '';
  }
  function currentUserNode() {
    const nodes = visibleUserNodes();
    const wanted = normalizeForMatch(sentText).slice(0, 80);
    if (wanted) {
      const matches = nodes.filter(node => normalizeForMatch(textOf(node)).includes(wanted));
      if (matches.length) return matches[matches.length - 1];
    }
    return nodes[nodes.length - 1] || null;
  }
  function resetBaseline() {
    baseline = new WeakMap();
    for (const node of assistantNodes()) baseline.set(node, assistantText(node));
  }
  function generationSelectors() {
    const host = location.hostname;
    if (host.includes('chatgpt.com')) {
      return '[data-testid="stop-button"], button[aria-label="Stop streaming"], button[aria-label="Stop generating"], button[aria-label="Detener"], button[aria-label="Detener respuesta"]';
    }
    if (host.includes('claude.ai')) {
      return '[data-is-streaming="true"], button[aria-label="Stop response"], button[aria-label="Stop"]';
    }
    if (host.includes('gemini.google.com')) {
      return '[data-is-streaming="true"], button[aria-label="Stop response"], button[aria-label="Stop"], button[aria-label="Detener"]';
    }
    return '[data-is-streaming="true"], [data-testid="stop-button"], button[aria-label*="Stop" i], button[aria-label*="Detener" i]';
  }
  function isGenerating() {
    return [...document.querySelectorAll(generationSelectors())]
      .some(element => element.getClientRects().length > 0);
  }
  function clearGenerationTracking() {
    if (generationTimer !== null) clearTimeout(generationTimer);
    generationTimer = null;
    if (generationPoll !== null) clearInterval(generationPoll);
    generationPoll = null;
    sawGenerating = false;
  }
  function checkGenerationState() {
    if (!recording) return;
    const generating = isGenerating();
    if (generating) {
      sawGenerating = true;
      return;
    }
    if (!sawGenerating) return;
    sawGenerating = false;
    if (generationTimer !== null) clearTimeout(generationTimer);
    generationTimer = setTimeout(() => {
      generationTimer = null;
      if (recording) snapshotAssistants().catch(() => report('send_failed'));
    }, 200);
  }
  function startGenerationTracking() {
    clearGenerationTracking();
    sawGenerating = isGenerating();
    generationPoll = setInterval(checkGenerationState, 500);
  }
  function snapshotAssistants() {
    assistantQueue = assistantQueue.catch(() => {}).then(async () => {
      if (!checkScope()) throw new Error('La conversación cambió.');
      const anchor = currentUserNode();
      if (!anchor && !isGenerating()) return;
      for (const node of assistantNodes()) {
        if (!checkScope()) throw new Error('La conversación cambió.');
        // 4 is Node.DOCUMENT_POSITION_FOLLOWING.
        if (anchor?.compareDocumentPosition &&
            !(anchor.compareDocumentPosition(node) & 4)) {
          continue;
        }
        const text = assistantText(node);
        if (!text?.trim()) continue;
        if (baseline.has(node) && baseline.get(node) === text) continue;
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
    if (replaying) return;
    const chatEnabled = !!chat?.enabled && !recording && !paused;
    if (!chatEnabled && !recording && !paused) return;
    if ((recording || paused) && !checkScope()) return;
    const editor = visible(editorSelector);
    const isEnter = event.type === 'keydown' && event.key === 'Enter' && !event.shiftKey && !event.ctrlKey && !event.altKey && !event.metaKey && !event.isComposing && editor?.contains(event.target);
    const isClick = event.type === 'click' && !!event.target.closest?.(sendSelector);
    const isSubmit = event.type === 'submit' && !!editor && event.target.contains(editor);
    if (!isEnter && !isClick && !isSubmit) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    if (paused) { report('send_blocked'); return; }
    if (!editor) { if (recording) report('send_blocked'); return; }
    // The composer may hide or rename its send control; never send uncaptured.
    const readiness = sendReadiness(editor);
    if (readiness === 'hidden' || readiness === 'disabled') {
      if (recording) report('send_blocked');
      return;
    }
    if (readiness === 'missing') {
      if (recording) report('send_control_missing');
      return;
    }
    if (sending) return;
    const editorText = () => chat?.enabled && chat.readText ? chat.readText(editor) : textOf(editor);
    const originalText = editorText();
    if (!originalText?.trim()) return;
    sending = true;
    inFlight = (async () => {
      let text = originalText;
      let researchAttempt = false;
      try {
        if (chatEnabled) {
          const outcome = await chat.authorize({
            editor,
            text: originalText,
            conversation: location.href
          });
          if (outcome.status !== 'send') return;
          text = outcome.text;
          if (!chat.enabled) return;
        }
        if (!recording && !paused) {
          if (editorText() !== text) throw new Error('El borrador cambió antes de enviarse.');
          replaying = true;
          try {
            if (!replaySend(editor)) throw new Error('No se encontró el control de envío.');
          } finally { replaying = false; }
          return;
        }
        researchAttempt = true;
        await snapshotAssistants();
        if (!checkScope()) throw new Error('La conversación cambió.');
        await append({ event_id: crypto.randomUUID(), role: 'user', text, captured_at: new Date().toISOString() });
        sentText = text;
        submittedCount += 1;
        if (!checkScope()) throw new Error('La conversación cambió.');
        if (editorText() !== text) throw new Error('El borrador cambió antes de enviarse.');
        replaying = true;
        try {
          if (!replaySend(editor)) throw new Error('No se encontró el control de envío.');
        } finally { replaying = false; }
        startGenerationTracking();
      } catch {
        if (researchAttempt) report('send_failed');
      } finally { sending = false; }
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
      clearGenerationTracking();
      resetBaseline();
      scopePath = location.pathname;
      submittedCount = 0;
      scopeInterrupted = false;
      sentText = '';
      const hasHistory = visibleUserNodes().length > 0;
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
      reply({ activated: true, path: location.pathname });
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
      clearGenerationTracking();
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
      clearGenerationTracking();
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
    checkGenerationState();
    clearTimeout(timer);
    timer = setTimeout(() => snapshotAssistants().catch(() => report('send_failed')), 250);
  });
  observer.observe(document, { childList: true, subtree: true, characterData: true });
  message({ type: 'RESEARCH_STATUS', documentNonce, path: location.pathname }).then(state => {
    if (state.adopted) {
      // The provider navigated to the conversation it assigned.
      resetBaseline();
      scopePath = location.pathname;
      submittedCount = 0;
      sentText = '';
      scopeInterrupted = false;
    }
    if (!recording) recording = state.recording;
    if (!paused) paused = state.paused;
    if (state.paused) {
      // The controller already recorded this interruption for this tab.
      notice?.showIncident({
        id: `page_paused:${documentNonce}`,
        text: 'Captura en pausa después de cambiar de página. Finaliza y guarda la sesión interrumpida o descártala desde la extensión.'
      });
    }
  }).catch(() => {});
})();
