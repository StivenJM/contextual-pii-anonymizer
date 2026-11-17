/* Non-blocking attachment processing status. ISOLATED world only. */
(function (root) {
  'use strict';

  const PROCESSING_TITLE = 'Procesando documento';
  const DONE_TITLE = 'Documento procesado';
  const ERROR_TITLE = 'No se pudo procesar el documento';

  const STYLE = [
    ':host { all: initial; }',
    '.attachment-status-card {',
    '  position: relative; display: flex; align-items: flex-start; gap: 12px;',
    '  padding: 12px 14px; border-radius: 12px; overflow: hidden;',
    '  background: linear-gradient(180deg, #2a2c31 0%, #222327 100%);',
    '  border: 1px solid #3a3c42;',
    '  box-shadow: 0 14px 36px rgba(0, 0, 0, 0.48), inset 0 1px 0 rgba(255, 255, 255, 0.05);',
    '  color: #e8e8ea; text-align: left;',
    '  animation: attachment-status-in 180ms ease-out;',
    '}',
    '.attachment-status-card::after {',
    '  content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 2px;',
    '  background: linear-gradient(90deg, transparent, #4f8cff, transparent);',
    '  opacity: 0.6;',
    '}',
    '.attachment-status-card[data-state="done"]::after {',
    '  background: linear-gradient(90deg, transparent, #3ecf8e, transparent);',
    '}',
    '.attachment-status-card[data-state="error"]::after {',
    '  background: linear-gradient(90deg, transparent, #e05c5c, transparent);',
    '}',
    '.attachment-status-icon {',
    '  position: relative; flex: 0 0 auto; width: 34px; height: 34px;',
    '  display: flex; align-items: center; justify-content: center;',
    '  border-radius: 50%; font-size: 17px; font-weight: 700; line-height: 1;',
    '}',
    '.attachment-status-card[data-state="processing"] .attachment-status-icon {',
    '  background: rgba(79, 140, 255, 0.12);',
    '  border: 1px solid rgba(79, 140, 255, 0.32);',
    '}',
    '.attachment-status-card[data-state="processing"] .attachment-status-icon::before {',
    '  content: ""; width: 16px; height: 16px; border-radius: 50%;',
    '  border: 2px solid rgba(122, 167, 255, 0.25); border-top-color: #7aa7ff;',
    '  animation: attachment-status-spin 800ms linear infinite;',
    '}',
    '.attachment-status-card[data-state="done"] .attachment-status-icon {',
    '  background: rgba(62, 207, 142, 0.12);',
    '  border: 1px solid rgba(62, 207, 142, 0.35); color: #3ecf8e;',
    '}',
    '.attachment-status-card[data-state="error"] .attachment-status-icon {',
    '  background: rgba(224, 92, 92, 0.12);',
    '  border: 1px solid rgba(224, 92, 92, 0.4); color: #ffd0d0;',
    '}',
    '.attachment-status-body {',
    '  display: grid; gap: 3px; min-width: 0; flex: 1 1 auto; padding-top: 1px;',
    '}',
    '.attachment-status-title {',
    '  font-size: 13px; font-weight: 600; line-height: 1.3; color: #ffffff;',
    '}',
    '.attachment-status-text {',
    '  font-size: 12px; line-height: 1.45; color: #9a9ba1;',
    '  overflow-wrap: anywhere;',
    '}',
    '@keyframes attachment-status-spin { to { transform: rotate(360deg); } }',
    '@keyframes attachment-status-in {',
    '  from { opacity: 0; transform: translateY(6px); }',
    '  to { opacity: 1; transform: none; }',
    '}',
    '@media (prefers-reduced-motion: reduce) {',
    '  .attachment-status-card { animation: none; }',
    '  .attachment-status-card[data-state="processing"] .attachment-status-icon::before { animation: none; }',
    '}'
  ].join('\n');

  const LAYOUT = {
    host: 'position:fixed;right:16px;bottom:16px;z-index:2147483647;display:block;' +
      'pointer-events:none;max-width:min(360px,calc(100vw - 32px));' +
      'font:13px/1.4 "Segoe UI",system-ui,sans-serif;color:#e8e8ea;text-align:left'
  };

  function createAttachmentStatus(document, options) {
    const doc = document;
    const settings = options || {};
    const delay = settings.setTimeout || ((fn, ms) => setTimeout(fn, ms));
    const cancel = settings.clearTimeout || (id => clearTimeout(id));
    const delayMs = Number.isFinite(settings.delay) ? settings.delay : 150;
    const doneDuration = Number.isFinite(settings.doneDuration) ? settings.doneDuration : 2500;
    const errorDuration = Number.isFinite(settings.errorDuration) ? settings.errorDuration : 8000;

    let host = null;
    let rootNode = null;
    let card = null;
    let icon = null;
    let title = null;
    let text = null;
    let startTimer = null;
    let removeTimer = null;
    let pendingName = '';
    let state = 'idle';

    function clearStart() {
      if (startTimer !== null) cancel(startTimer);
      startTimer = null;
    }

    function clearRemove() {
      if (removeTimer !== null) cancel(removeTimer);
      removeTimer = null;
    }

    function removeAll() {
      clearStart();
      clearRemove();
      const stale = host;
      host = null;
      rootNode = null;
      card = null;
      icon = null;
      title = null;
      text = null;
      pendingName = '';
      state = 'idle';
      if (stale) stale.remove();
    }

    function scheduleRemove(ms) {
      clearRemove();
      removeTimer = delay(() => {
        removeTimer = null;
        removeAll();
      }, ms);
    }

    function mount() {
      host = doc.createElement('div');
      host.setAttribute('data-attachment-status', 'processing');
      host.style.cssText = LAYOUT.host;
      if (typeof host.attachShadow === 'function') {
        rootNode = host.attachShadow({ mode: 'open' });
        const style = doc.createElement('style');
        style.textContent = STYLE;
        rootNode.append(style);
      } else {
        rootNode = doc.createElement('div');
      }

      card = doc.createElement('div');
      card.className = 'attachment-status-card';
      card.setAttribute('data-state', 'processing');
      icon = doc.createElement('span');
      icon.className = 'attachment-status-icon';
      icon.setAttribute('aria-hidden', 'true');

      const body = doc.createElement('div');
      body.className = 'attachment-status-body';
      title = doc.createElement('div');
      title.className = 'attachment-status-title';
      text = doc.createElement('div');
      text.className = 'attachment-status-text';
      body.append(title, text);
      card.append(icon, body);
      rootNode.append(card);
      (doc.body || doc.documentElement).append(host);
      state = 'processing';
    }

    function setState(next, message) {
      state = next;
      host.setAttribute('data-attachment-status', next);
      card.setAttribute('data-state', next);
      if (next === 'processing') {
        card.setAttribute('role', 'status');
        card.setAttribute('aria-live', 'polite');
        card.setAttribute('aria-busy', 'true');
        icon.textContent = '';
        title.textContent = PROCESSING_TITLE;
        text.textContent = pendingName
          ? `Preparando ${pendingName} para el chat…`
          : 'Preparando el documento para el chat…';
        return;
      }

      card.setAttribute('aria-busy', 'false');
      if (next === 'done') {
        card.setAttribute('role', 'status');
        card.setAttribute('aria-live', 'polite');
        icon.textContent = '✓';
        title.textContent = DONE_TITLE;
        text.textContent = 'El documento está procesado y listo para el chat.';
        return;
      }

      card.setAttribute('role', 'alert');
      card.setAttribute('aria-live', 'assertive');
      icon.textContent = '!';
      title.textContent = ERROR_TITLE;
      text.textContent = typeof message === 'string' && message
        ? message
        : 'Vuelve a intentarlo.';
    }

    function start(name) {
      removeAll();
      pendingName = typeof name === 'string' ? name.trim() : '';
      state = 'processing';
      startTimer = delay(() => {
        startTimer = null;
        mount();
        setState('processing');
      }, delayMs);
    }

    function done() {
      clearStart();
      if (!host) {
        state = 'idle';
        pendingName = '';
        return;
      }
      if (state === 'error') return;
      setState('done');
      scheduleRemove(doneDuration);
    }

    function fail(message) {
      clearStart();
      if (!host) mount();
      setState('error', message);
      scheduleRemove(errorDuration);
    }

    function dispose() {
      removeAll();
    }

    return {
      start,
      done,
      fail,
      dispose,
      get element() { return host; },
      get state() { return state; }
    };
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      createAttachmentStatus,
      PROCESSING_TITLE,
      DONE_TITLE,
      ERROR_TITLE
    };
    return;
  }

  const status = createAttachmentStatus(document);
  window.addEventListener('message', event => {
    if (event.source !== window) return;
    const data = event.data;
    if (!data || data.direction !== 'MAIN_TO_ATTACHMENT_STATUS') return;
    if (data.action === 'start') status.start(typeof data.name === 'string' ? data.name : '');
    else if (data.action === 'done') status.done();
    else if (data.action === 'error') status.fail(typeof data.message === 'string' ? data.message : '');
  });
  root.attachmentStatus = status;
})(typeof globalThis !== 'undefined' ? globalThis : this);
