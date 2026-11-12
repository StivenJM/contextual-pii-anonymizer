/* Isolated, dismissible notice for the research capture. ISOLATED world only. */
(function (root) {
  'use strict';

  const SUCCESS_TITLE = 'Captura activa';
  const SUCCESS_DESCRIPTION =
    'Consulta el estado y finaliza la sesión desde el icono de la extensión.';
  const INCIDENT_TITLE = 'Captura requiere atención';

  const STYLE = [
    ':host { all: initial; }',
    '[data-research-notice] .research-notice {',
    '  display: flex; align-items: flex-start; gap: 10px;',
    '  animation: research-notice-in 160ms ease-out;',
    '}',
    '[data-research-notice] .research-notice[data-tone="alert"] .research-notice-title { color: #ffd8a8; }',
    '[data-research-notice] .research-notice-close:hover { background: #3a3c42; color: #ffffff; }',
    '[data-research-notice] .research-notice-close:focus-visible {',
    '  outline: 2px solid #4f8cff; outline-offset: 2px;',
    '}',
    '@keyframes research-notice-in {',
    '  from { opacity: 0; transform: translateY(6px); }',
    '  to { opacity: 1; transform: none; }',
    '}',
    '@media (prefers-reduced-motion: reduce) {',
    '  [data-research-notice] .research-notice { animation: none; }',
    '}'
  ].join('\n');

  const LAYOUT = {
    host: 'position:fixed;bottom:16px;right:16px;z-index:2147483647;display:block;' +
      'max-width:min(340px,calc(100vw - 32px));font:13px/1.4 "Segoe UI",system-ui,sans-serif;' +
      'color:#e8e8ea',
    notice: 'display:flex;align-items:flex-start;gap:10px;padding:12px 12px 12px 14px;' +
      'border-radius:10px;background:#26272b;color:#e8e8ea;border:1px solid #3a3c42;' +
      'box-shadow:0 10px 28px rgba(0,0,0,0.35);font:13px/1.4 "Segoe UI",system-ui,sans-serif;' +
      'text-align:left',
    alert: 'background:#2e2417;border-color:#b26a00',
    body: 'display:grid;gap:4px;min-width:0;flex:1 1 auto',
    title: 'font-size:13px;font-weight:600;line-height:1.3;color:#ffffff',
    text: 'font-size:12px;line-height:1.45;color:#c8c9cf;overflow-wrap:anywhere',
    close: 'flex:0 0 auto;width:24px;height:24px;margin:-2px -2px 0 0;padding:0;' +
      'border:1px solid transparent;border-radius:6px;background:transparent;' +
      'color:#c8c9cf;font:16px/1 "Segoe UI",system-ui,sans-serif;cursor:pointer'
  };

  function createResearchNotice(document, options) {
    const doc = document;
    const settings = options || {};
    const delay = settings.setTimeout || ((fn, ms) => setTimeout(fn, ms));
    const cancel = settings.clearTimeout || (id => clearTimeout(id));
    const now = settings.now || (() => Date.now());
    const duration = Number.isFinite(settings.duration) ? settings.duration : 6000;

    let host = null;
    let rootNode = null;
    let noticeEl = null;
    let timer = null;
    let remaining = 0;
    let startedAt = 0;
    let mode = null;
    let currentIncident = null;
    const acknowledged = new Set();

    function build() {
      host = doc.createElement('div');
      host.setAttribute('data-research-notice', 'active');
      host.style.cssText = LAYOUT.host;
      if (typeof host.attachShadow === 'function') {
        rootNode = host.attachShadow({ mode: 'open' });
        const style = doc.createElement('style');
        style.textContent = STYLE;
        rootNode.append(style);
      } else {
        rootNode = doc.createElement('div');
      }
      (doc.body || doc.documentElement).append(host);
      host.addEventListener('pointerenter', pause);
      host.addEventListener('pointerleave', resume);
      host.addEventListener('focusin', pause);
      host.addEventListener('focusout', event => {
        if (!host.contains(event.relatedTarget)) resume();
      });
    }

    function clearTimer() {
      if (timer !== null) cancel(timer);
      timer = null;
    }

    function removeAll() {
      clearTimer();
      remaining = 0;
      const stale = host;
      host = null;
      rootNode = null;
      noticeEl = null;
      mode = null;
      currentIncident = null;
      if (stale) stale.remove();
    }

    function schedule(ms) {
      clearTimer();
      remaining = Math.max(0, ms);
      startedAt = now();
      timer = delay(() => {
        timer = null;
        removeAll();
      }, remaining);
    }

    function pause() {
      if (timer === null || mode !== 'success') return;
      clearTimer();
      remaining = Math.max(0, remaining - (now() - startedAt));
    }

    function resume() {
      if (mode !== 'success' || timer !== null || !noticeEl) return;
      schedule(remaining);
    }

    function present({ role, tone, title, text }) {
      build();
      noticeEl = doc.createElement('div');
      noticeEl.className = 'research-notice';
      noticeEl.style.cssText = LAYOUT.notice + (tone === 'alert' ? ';' + LAYOUT.alert : '');
      noticeEl.setAttribute('role', role);
      if (role === 'alert') noticeEl.setAttribute('aria-live', 'assertive');
      if (tone === 'alert') noticeEl.setAttribute('data-tone', 'alert');

      const body = doc.createElement('div');
      body.className = 'research-notice-body';
      body.style.cssText = LAYOUT.body;

      const titleEl = doc.createElement('div');
      titleEl.className = 'research-notice-title';
      titleEl.style.cssText = LAYOUT.title;
      titleEl.textContent = title;

      const textEl = doc.createElement('div');
      textEl.className = 'research-notice-text';
      textEl.style.cssText = LAYOUT.text;
      textEl.textContent = text;

      const close = doc.createElement('button');
      close.type = 'button';
      close.className = 'research-notice-close';
      close.style.cssText = LAYOUT.close;
      close.setAttribute('aria-label', 'Cerrar aviso');
      close.setAttribute('title', 'Cerrar aviso');
      close.textContent = '×';
      close.addEventListener('click', () => dismiss());

      body.append(titleEl, textEl);
      noticeEl.append(body, close);
      rootNode.append(noticeEl);
      host.setAttribute('data-research-notice', tone === 'alert' ? 'incident' : 'success');
    }

    // Only a confirmed activation may show the success notice, once per session.
    function showSuccess() {
      if (mode === 'incident') return false;
      removeAll();
      mode = 'success';
      present({ role: 'status', tone: 'active', title: SUCCESS_TITLE, text: SUCCESS_DESCRIPTION });
      schedule(duration);
      return true;
    }

    // Blocking incidents stay until the user closes them and never auto-dismiss.
    function showIncident(incident) {
      const id = incident && incident.id;
      if (!id) return false;
      if (mode === 'incident' && currentIncident === id) return false;
      if (acknowledged.has(id)) return false;
      removeAll();
      mode = 'incident';
      currentIncident = id;
      present({ role: 'alert', tone: 'alert', title: INCIDENT_TITLE, text: incident.text });
      return true;
    }

    function dismiss() {
      if (currentIncident) acknowledged.add(currentIncident);
      removeAll();
    }

    function dispose() {
      acknowledged.clear();
      removeAll();
    }

    return {
      showSuccess,
      showIncident,
      dismiss,
      dispose,
      get element() { return host; },
      get mode() { return mode; }
    };
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { createResearchNotice, SUCCESS_TITLE, SUCCESS_DESCRIPTION, INCIDENT_TITLE };
  } else {
    root.createResearchNotice = createResearchNotice;
  }
})(typeof globalThis !== 'undefined' ? globalThis : this);
