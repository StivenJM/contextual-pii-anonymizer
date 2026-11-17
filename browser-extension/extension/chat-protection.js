/* Chat send protection. ISOLATED world only. */
(function (root) {
  'use strict';

  const HIGHLIGHT_NAME = 'chat-pii-protected';
  const HIGHLIGHT_STYLE_ID = 'chat-protection-highlight-style';
  const DESCRIPTION_ID = 'chat-protection-card-description';
  const BLOCK_TAGS = new Set([
    'ADDRESS', 'ARTICLE', 'ASIDE', 'BLOCKQUOTE', 'DIV', 'DL', 'FIELDSET',
    'FIGCAPTION', 'FIGURE', 'FOOTER', 'FORM', 'H1', 'H2', 'H3', 'H4', 'H5',
    'H6', 'HEADER', 'LI', 'MAIN', 'NAV', 'OL', 'P', 'PRE', 'SECTION', 'TABLE', 'UL'
  ]);
  const CARD_STYLE = [
    ':host { all: initial; }',
    '.chat-protection-card {',
    '  display: flex; flex-direction: column; gap: 10px;',
    '  max-width: min(360px, calc(100vw - 24px)); min-width: 270px;',
    '  padding: 12px 14px; border-radius: 12px;',
    '  background: linear-gradient(180deg, #2a2c31 0%, #222327 100%);',
    '  border: 1px solid #3a3c42;',
    '  box-shadow: 0 14px 36px rgba(0, 0, 0, 0.48), inset 0 1px 0 rgba(255, 255, 255, 0.05);',
    '  color: #e8e8ea; font: 13px/1.4 "Segoe UI", system-ui, sans-serif;',
    '  text-align: left; animation: chat-protection-in 160ms ease-out;',
    '}',
    '.chat-protection-head { display: flex; align-items: flex-start; gap: 10px; }',
    '.chat-protection-icon {',
    '  display: flex; align-items: center; justify-content: center;',
    '  flex: 0 0 auto; width: 30px; height: 30px; border-radius: 50%;',
    '  background: rgba(79, 140, 255, 0.12); border: 1px solid rgba(79, 140, 255, 0.32);',
    '  font-size: 15px; font-weight: 700; color: #9fc0ff;',
    '}',
    '.chat-protection-card[data-state="reviewing"] .chat-protection-icon::before {',
    '  content: ""; width: 14px; height: 14px; border-radius: 50%;',
    '  border: 2px solid rgba(122, 167, 255, 0.25); border-top-color: #7aa7ff;',
    '  animation: chat-protection-spin 800ms linear infinite;',
    '}',
    '.chat-protection-card[data-state="changes"] .chat-protection-icon { color: #ffd0d0; border-color: rgba(224, 92, 92, 0.42); background: rgba(224, 92, 92, 0.12); }',
    '.chat-protection-card[data-state="error"] .chat-protection-icon, .chat-protection-card[data-state="warning"] .chat-protection-icon { color: #ffd0d0; border-color: rgba(224, 92, 92, 0.42); background: rgba(224, 92, 92, 0.12); }',
    '.chat-protection-body { display: grid; gap: 3px; min-width: 0; flex: 1 1 auto; }',
    '.chat-protection-title { font-size: 13px; font-weight: 600; line-height: 1.3; color: #ffffff; }',
    '.chat-protection-text { font-size: 12px; line-height: 1.45; color: #9a9ba1; overflow-wrap: anywhere; }',
    '.chat-protection-actions { display: flex; gap: 8px; flex-wrap: wrap; }',
    '.chat-protection-actions button {',
    '  flex: 1 1 130px; min-height: 32px; padding: 6px 8px; border-radius: 6px;',
    '  border: 1px solid #527bbd; background: #295eb0; color: #ffffff;',
    '  font: 12px/1.2 "Segoe UI", system-ui, sans-serif; cursor: pointer;',
    '}',
    '.chat-protection-actions button.secondary { background: #35373e; border-color: #555965; }',
    '.chat-protection-actions button:hover { filter: brightness(1.08); }',
    '.chat-protection-actions button:focus-visible { outline: 2px solid #4f8cff; outline-offset: 2px; }',
    '.chat-protection-actions button:disabled { opacity: 0.6; cursor: default; }',
    '@keyframes chat-protection-spin { to { transform: rotate(360deg); } }',
    '@keyframes chat-protection-in { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }',
    '@media (prefers-reduced-motion: reduce) {',
    '  .chat-protection-card { animation: none; }',
    '  .chat-protection-card[data-state="reviewing"] .chat-protection-icon::before { animation: none; }',
    '}'
  ].join('\n');

  function codePointOffsets(text) {
    const offsets = [0];
    let units = 0;
    for (const character of text) {
      units += character.length;
      offsets.push(units);
    }
    return offsets;
  }

  function operationProtects(operation) {
    if (!operation || operation.action === 'KEEP') return false;
    return operation.mapping_gap === true || operation.replacement !== operation.original_text;
  }

  // API offsets are Python code-point indexes; JS strings use UTF-16 units.
  function protectedSpans(text, operations) {
    const offsets = codePointOffsets(text);
    const limit = offsets.length - 1;
    const spans = [];
    for (const operation of Array.isArray(operations) ? operations : []) {
      if (!operationProtects(operation)) continue;
      const start = operation.start;
      const end = operation.end;
      if (!Number.isInteger(start) || !Number.isInteger(end)) continue;
      if (start < 0 || end > limit || end <= start) continue;
      spans.push({ start: offsets[start], end: offsets[end] });
    }
    spans.sort((left, right) => left.start - right.start || left.end - right.end);
    const merged = [];
    for (const span of spans) {
      const previous = merged[merged.length - 1];
      if (previous && span.start < previous.end) {
        previous.end = Math.max(previous.end, span.end);
      } else {
        merged.push({ ...span });
      }
    }
    return merged;
  }

  function evaluateProtection(text, result) {
    if (!result || typeof result !== 'object') {
      throw new Error('La revisión no devolvió un resultado válido.');
    }
    if (result.original_text !== text) {
      throw new Error('La revisión no corresponde al borrador enviado.');
    }
    if (typeof result.protected_text !== 'string') {
      throw new Error('La revisión no devolvió texto protegido.');
    }
    if (
      !Array.isArray(result.detections) ||
      !Array.isArray(result.operations) ||
      !Array.isArray(result.mapping_gaps) ||
      !Array.isArray(result.warnings)
    ) {
      throw new Error('La revisión devolvió una respuesta incompleta.');
    }

    const limit = codePointOffsets(text).length - 1;
    for (const operation of result.operations) {
      if (!operationProtects(operation)) continue;
      if (!Number.isInteger(operation.start) ||
          !Number.isInteger(operation.end) ||
          operation.start < 0 ||
          operation.end > limit ||
          operation.end <= operation.start) {
        throw new Error('La revisión devolvió operaciones inconsistentes.');
      }
    }
    const spans = protectedSpans(text, result.operations);
    const changed = result.protected_text !== text;
    if (spans.length > 0 && !changed) {
      throw new Error('La revisión propone cambios pero no devolvió texto protegido.');
    }
    if (spans.length === 0 && changed) {
      throw new Error('La revisión devolvió texto distinto sin operaciones aplicadas.');
    }
    if (spans.length === 0 && result.warnings.length > 0) {
      return { kind: 'warning', warnings: result.warnings, spans: [] };
    }
    if (spans.length > 0) {
      return {
        kind: 'changes',
        spans,
        count: spans.length,
        warnings: result.warnings,
        result
      };
    }
    return { kind: 'clean', warnings: [] };
  }

  function isTextControl(editor) {
    return typeof editor?.value === 'string' &&
      (editor.tagName === 'TEXTAREA' || editor.tagName === 'INPUT');
  }

  function isContentEditable(editor) {
    return editor?.isContentEditable === true ||
      editor?.getAttribute?.('contenteditable') === 'true';
  }

  function collectEditor(editor) {
    const parts = [];
    const segments = [];
    let length = 0;

    function appendText(node) {
      const value = node.nodeValue || '';
      if (!value) return;
      segments.push({ node, start: length, end: length + value.length });
      parts.push(value);
      length += value.length;
    }

    function appendNewline() {
      if (!length || parts[parts.length - 1].endsWith('\n')) return;
      parts.push('\n');
      length += 1;
    }

    function walk(node) {
      for (const child of node.childNodes || []) {
        if (child.nodeType === 3) {
          appendText(child);
          continue;
        }
        if (child.nodeType !== 1) continue;
        if (child.tagName === 'BR') {
          appendNewline();
          continue;
        }
        const block = BLOCK_TAGS.has(child.tagName);
        if (block) appendNewline();
        walk(child);
        if (block) appendNewline();
      }
    }

    walk(editor);
    let text = parts.join('');
    if (text.endsWith('\n')) {
      text = text.slice(0, -1);
      const last = segments[segments.length - 1];
      if (last && last.end > text.length) {
        last.end = text.length;
        if (last.end <= last.start) segments.pop();
      }
    }
    return { text, segments };
  }

  function readEditor(editor) {
    if (!editor) return { kind: 'unknown', text: '', segments: [] };
    if (isTextControl(editor)) {
      return { kind: 'text', text: editor.value, segments: [] };
    }
    if (isContentEditable(editor)) {
      return { kind: 'contenteditable', ...collectEditor(editor) };
    }
    return {
      kind: 'unknown',
      text: typeof editor.innerText === 'string' ? editor.innerText : String(editor.textContent || ''),
      segments: []
    };
  }

  function rangesForSpans(document, segments, spans) {
    const ranges = [];
    for (const span of spans) {
      for (const segment of segments) {
        const start = Math.max(span.start, segment.start);
        const end = Math.min(span.end, segment.end);
        if (start >= end) continue;
        try {
          const range = document.createRange();
          range.setStart(segment.node, start - segment.start);
          range.setEnd(segment.node, end - segment.start);
          ranges.push(range);
        } catch { /* a detached node cannot be highlighted */ }
      }
    }
    return ranges;
  }

  function setEditorText(document, editor, kind, text) {
    if (kind === 'text') {
      const prototype = Object.getPrototypeOf(editor);
      const descriptor = Object.getOwnPropertyDescriptor(prototype, 'value');
      if (descriptor?.set) descriptor.set.call(editor, text);
      else editor.value = text;
      const EventCtor = document.defaultView?.Event;
      if (EventCtor) editor.dispatchEvent(new EventCtor('input', { bubbles: true }));
      return editor.value === text;
    }
    if (kind === 'contenteditable') {
      editor.focus?.();
      const selection = document.getSelection?.();
      if (selection) {
        const range = document.createRange();
        range.selectNodeContents(editor);
        selection.removeAllRanges();
        selection.addRange(range);
      }
      let inserted = false;
      try {
        inserted = document.execCommand?.('insertText', false, text) === true;
      } catch { inserted = false; }
      if (!inserted) {
        if ('innerText' in editor) editor.innerText = text;
        else editor.textContent = text;
        const EventCtor = document.defaultView?.InputEvent || document.defaultView?.Event;
        if (EventCtor) {
          editor.dispatchEvent(new EventCtor('input', {
            bubbles: true,
            inputType: 'insertText',
            data: text
          }));
        }
      }
      return readEditor(editor).text === text;
    }
    return false;
  }

  function createChatProtection(options) {
    const document = options.document;
    const window = options.window || document.defaultView;
    const api = options.api;
    const location = options.location || window?.location;
    const getAttachmentState = options.getAttachmentState || (() => null);
    const setTimeoutFn = options.setTimeout || window?.setTimeout?.bind(window) || setTimeout;
    const clearTimeoutFn = options.clearTimeout || window?.clearTimeout?.bind(window) || clearTimeout;
    const setIntervalFn = options.setInterval || window?.setInterval?.bind(window) || setInterval;
    const clearIntervalFn = options.clearInterval || window?.clearInterval?.bind(window) || clearInterval;

    let enabled = options.enabled === true;
    let active = null;
    let sequence = 0;
    let cardHost = null;
    let cardRoot = null;
    let cardDescription = null;
    let cardCleanup = [];
    let highlightCleanup = null;
    let blockedTimer = null;
    let updatingEditor = false;

    function currentConversation() {
      return location?.href || '';
    }

    function setEnabled(next) {
      enabled = next === true;
      if (!enabled && active) invalidate(active);
      if (!enabled) clearCard();
    }

    function start() {
      if (api?.runtime?.onMessage?.addListener) {
        api.runtime.onMessage.addListener(message => {
          if (message?.type === 'ESTADO_CAMBIADO' && typeof message.chatProtection === 'boolean') {
            setEnabled(message.chatProtection);
          }
        });
      }
      if (api?.runtime?.sendMessage) {
        api.runtime.sendMessage({ type: 'OBTENER_ESTADO' })
          .then(result => {
            if (result?.ok) setEnabled(result.chatProtection === true);
          })
          .catch(() => {});
      }
    }

    function clearCard() {
      for (const remove of cardCleanup) remove();
      cardCleanup = [];
      if (blockedTimer !== null) {
        clearTimeoutFn(blockedTimer);
        blockedTimer = null;
      }
      const stale = cardHost;
      cardHost = null;
      cardRoot = null;
      cardDescription = null;
      if (stale) stale.remove();
    }

    function clearHighlights() {
      if (window?.CSS?.highlights) window.CSS.highlights.delete(HIGHLIGHT_NAME);
      if (highlightCleanup) {
        highlightCleanup();
        highlightCleanup = null;
      }
    }

    function restoreDescription(editor) {
      if (editor) {
        const previous = editor.__chatProtectionDescription;
        if (previous) editor.setAttribute('aria-describedby', previous);
        else editor.removeAttribute?.('aria-describedby');
        delete editor.__chatProtectionDescription;
      }
      document.getElementById?.(DESCRIPTION_ID)?.remove();
    }

    function describeEditor(editor) {
      if (!editor || !cardDescription) return;
      let description = document.getElementById?.(DESCRIPTION_ID);
      if (!description) {
        description = document.createElement('div');
        description.id = DESCRIPTION_ID;
        description.setAttribute('role', 'status');
        description.setAttribute('aria-live', 'polite');
        description.style.cssText =
          'position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);' +
          'white-space:nowrap;border:0;padding:0;margin:-1px;';
        (document.body || document.documentElement).append(description);
      }
      description.textContent = cardDescription.textContent || '';
      editor.__chatProtectionDescription =
        editor.getAttribute?.('aria-describedby') || '';
      editor.setAttribute('aria-describedby', DESCRIPTION_ID);
    }

    function clearItem(item) {
      for (const remove of item.cleanup || []) remove();
      item.cleanup = [];
      if (item.timer !== null) {
        clearIntervalFn(item.timer);
        item.timer = null;
      }
      clearHighlights();
      restoreDescription(item.editor);
      clearCard();
    }

    function resolveItem(item, outcome) {
      const resolve = item.resolve;
      clearItem(item);
      if (active === item) active = null;
      if (resolve) resolve(outcome);
    }

    function invalidate(item) {
      if (!item || item.cancelled) return;
      item.cancelled = true;
      resolveItem(item, { status: 'cancelled' });
    }

    function isCurrent(item) {
      return active === item &&
        !item.cancelled &&
        enabled &&
        currentConversation() === item.conversation &&
        readEditor(item.editor).text === item.text;
    }

    function attachInvalidation(item) {
      const onInput = () => {
        if (active !== item || updatingEditor) return;
        if (readEditor(item.editor).text !== item.text) invalidate(item);
      };
      document.addEventListener('input', onInput, true);
      document.addEventListener('beforeinput', onInput, true);
      const onNavigation = () => {
        if (active === item && currentConversation() !== item.conversation) invalidate(item);
      };
      window?.addEventListener?.('popstate', onNavigation);
      window?.addEventListener?.('hashchange', onNavigation);
      window?.navigation?.addEventListener?.('navigate', onNavigation);
      let observer = null;
      if (window?.MutationObserver) {
        observer = new window.MutationObserver(() => {
          if (active !== item || updatingEditor) return;
          if (!item.editor.isConnected || readEditor(item.editor).text !== item.text) {
            invalidate(item);
            return;
          }
          if (item.result?.kind === 'changes') applyHighlights(item, item.result.spans);
        });
        observer.observe(item.editor, { childList: true, subtree: true, characterData: true });
      }
      item.timer = setIntervalFn(() => {
        if (active !== item) return;
        if (currentConversation() !== item.conversation ||
            readEditor(item.editor).text !== item.text) {
          invalidate(item);
        }
      }, 350);
      item.cleanup = [
        () => document.removeEventListener('input', onInput, true),
        () => document.removeEventListener('beforeinput', onInput, true),
        () => window?.removeEventListener?.('popstate', onNavigation),
        () => window?.removeEventListener?.('hashchange', onNavigation),
        () => window?.navigation?.removeEventListener?.('navigate', onNavigation),
        () => observer?.disconnect()
      ];
    }

    function ensureHighlightStyle() {
      if (document.getElementById?.(HIGHLIGHT_STYLE_ID)) return;
      const style = document.createElement('style');
      style.id = HIGHLIGHT_STYLE_ID;
      style.textContent =
        `::highlight(${HIGHLIGHT_NAME}) { background-color: #ffb3b3; color: #1a1b1e; text-decoration: underline wavy #b42318; }`;
      (document.head || document.documentElement).append(style);
    }

    function overlayHost() {
      const host = document.createElement('div');
      host.setAttribute('data-chat-protection-highlight', '');
      host.style.cssText =
        'position:fixed;pointer-events:none;z-index:2147483646;overflow:hidden;' +
        'border-radius:6px;';
      (document.body || document.documentElement).append(host);
      return host;
    }

    function drawRectangles(item, ranges) {
      const host = overlayHost();
      const draw = () => {
        while (host.firstChild) host.removeChild(host.firstChild);
        for (const range of ranges) {
          const rects = range.getClientRects?.() || [];
          for (const rect of rects) {
            if (!rect.width || !rect.height) continue;
            const mark = document.createElement('div');
            mark.style.cssText =
              `position:fixed;left:${rect.left}px;top:${rect.top}px;` +
              `width:${rect.width}px;height:${rect.height}px;` +
              'background:rgba(224,92,92,0.32);border-radius:3px;' +
              'box-shadow:inset 0 -2px 0 rgba(180,35,24,0.8);';
            host.append(mark);
          }
        }
      };
      draw();
      const onMove = () => draw();
      window?.addEventListener?.('scroll', onMove, true);
      window?.addEventListener?.('resize', onMove);
      highlightCleanup = () => {
        window?.removeEventListener?.('scroll', onMove, true);
        window?.removeEventListener?.('resize', onMove);
        host.remove();
      };
    }

    function drawTextareaOverlay(item, spans) {
      const editor = item.editor;
      const rect = editor.getBoundingClientRect?.();
      if (!rect || !rect.width || !rect.height) return;
      const style = window?.getComputedStyle?.(editor);
      if (!style) return;
      const host = overlayHost();
      host.style.left = `${rect.left}px`;
      host.style.top = `${rect.top}px`;
      host.style.width = `${rect.width}px`;
      host.style.height = `${rect.height}px`;

      const inner = document.createElement('div');
      inner.style.cssText =
        'position:absolute;left:0;top:0;box-sizing:border-box;' +
        `padding:${style.padding};border:${style.border};` +
        `font:${style.font};line-height:${style.lineHeight};` +
        `letter-spacing:${style.letterSpacing};` +
        'white-space:pre-wrap;overflow-wrap:break-word;color:transparent;' +
        'caret-color:transparent;pointer-events:none;';
      let cursor = 0;
      for (const span of spans) {
        if (span.start > cursor) inner.append(document.createTextNode(item.text.slice(cursor, span.start)));
        const mark = document.createElement('span');
        mark.textContent = item.text.slice(span.start, span.end);
        mark.style.cssText =
          'background:rgba(224,92,92,0.32);border-radius:3px;' +
          'box-shadow:inset 0 -2px 0 rgba(180,35,24,0.8);color:transparent;';
        inner.append(mark);
        cursor = span.end;
      }
      if (cursor < item.text.length) inner.append(document.createTextNode(item.text.slice(cursor)));
      host.append(inner);

      const position = () => {
        const next = editor.getBoundingClientRect?.();
        if (!next) return;
        host.style.left = `${next.left}px`;
        host.style.top = `${next.top}px`;
        host.style.width = `${next.width}px`;
        host.style.height = `${next.height}px`;
        inner.style.top = `${-editor.scrollTop}px`;
        inner.style.left = `${-editor.scrollLeft}px`;
      };
      position();
      editor.addEventListener('scroll', position);
      window?.addEventListener?.('scroll', position, true);
      window?.addEventListener?.('resize', position);
      highlightCleanup = () => {
        editor.removeEventListener('scroll', position);
        window?.removeEventListener?.('scroll', position, true);
        window?.removeEventListener?.('resize', position);
        host.remove();
      };
    }

    function applyHighlights(item, spans) {
      clearHighlights();
      if (!spans.length) return;
      if (item.kind === 'text') {
        drawTextareaOverlay(item, spans);
        return;
      }
      if (item.kind !== 'contenteditable') return;
      const ranges = rangesForSpans(document, item.segments, spans);
      if (!ranges.length) return;
      if (window?.CSS?.highlights && typeof window.Highlight === 'function') {
        ensureHighlightStyle();
        const highlight = new window.Highlight(...ranges);
        window.CSS.highlights.set(HIGHLIGHT_NAME, highlight);
        return;
      }
      drawRectangles(item, ranges);
    }

    function buildCard(item, state, titleText, bodyText, actions) {
      clearCard();
      cardHost = document.createElement('div');
      cardHost.setAttribute('data-chat-protection-card', '');
      cardHost.style.cssText =
        'position:fixed;right:16px;bottom:16px;left:auto;top:auto;z-index:2147483647;display:block;' +
        'max-width:min(360px,calc(100vw - 32px));font:13px/1.4 "Segoe UI",system-ui,sans-serif;';
      if (typeof cardHost.attachShadow === 'function') {
        cardRoot = cardHost.attachShadow({ mode: 'open' });
        const style = document.createElement('style');
        style.textContent = CARD_STYLE;
        cardRoot.append(style);
      } else {
        cardRoot = document.createElement('div');
      }
      const card = document.createElement('div');
      card.className = 'chat-protection-card';
      card.setAttribute('data-state', state);
      card.setAttribute('role', 'dialog');
      card.setAttribute('aria-modal', 'false');
      card.setAttribute('aria-live', 'polite');

      const head = document.createElement('div');
      head.className = 'chat-protection-head';
      const icon = document.createElement('span');
      icon.className = 'chat-protection-icon';
      icon.setAttribute('aria-hidden', 'true');
      if (state === 'changes') icon.textContent = '!';
      else if (state === 'error' || state === 'warning') icon.textContent = '!';
      const body = document.createElement('div');
      body.className = 'chat-protection-body';
      const title = document.createElement('div');
      title.className = 'chat-protection-title';
      title.textContent = titleText;
      const text = document.createElement('div');
      text.className = 'chat-protection-text';
      text.textContent = bodyText;
      body.append(title, text);
      head.append(icon, body);
      card.append(head);

      if (actions?.length) {
        const row = document.createElement('div');
        row.className = 'chat-protection-actions';
        for (const action of actions) {
          const button = document.createElement('button');
          button.type = 'button';
          button.textContent = action.label;
          if (action.secondary) button.className = 'secondary';
          button.addEventListener('click', action.onClick);
          row.append(button);
        }
        card.append(row);
      }
      cardRoot.append(card);
      (document.body || document.documentElement).append(cardHost);
      cardCleanup = [];
      cardDescription = text;
      const buttons = card.querySelectorAll?.('button');
      const focusTarget = buttons?.[buttons.length - 1];
      focusTarget?.focus?.();
    }

    function renderReviewing(item) {
      buildCard(item, 'reviewing', 'Revisando mensaje…', 'Analizando el borrador antes de enviarlo.');
    }

    function renderChanges(item) {
      const evaluation = item.result;
      const title = evaluation.count === 1
        ? 'Se protegerá 1 dato personal'
        : `Se protegerán ${evaluation.count} datos personales`;
      const warning = evaluation.warnings.length
        ? ' La revisión incluyó advertencias; revisa el resaltado antes de enviar.'
        : ' Revisa el resaltado. El texto original se mantiene hasta que confirmes.';
      buildCard(item, 'changes', title, `Se sustituirán los datos marcados.${warning}`, [
        { label: 'Enviar versión protegida', onClick: () => confirmSend(item) },
        { label: 'Volver a editar', secondary: true, onClick: () => cancelEdit(item) }
      ]);
      describeEditor(item.editor);
    }

    function renderWarning(item, message) {
      buildCard(item, 'warning', 'No se pudo confirmar la protección',
        message || 'La revisión devolvió advertencias. Reintenta o vuelve a editar.', [
          { label: 'Reintentar revisión', onClick: () => retry(item) },
          { label: 'Volver a editar', secondary: true, onClick: () => cancelEdit(item) }
        ]);
      describeEditor(item.editor);
    }

    function renderError(item, message) {
      buildCard(item, 'error', 'No se pudo revisar el mensaje',
        message || 'Conserva el borrador y vuelve a intentarlo.', [
          { label: 'Reintentar revisión', onClick: () => retry(item) },
          { label: 'Volver a editar', secondary: true, onClick: () => cancelEdit(item) }
        ]);
      describeEditor(item.editor);
    }

    function showBlocked(message, editor) {
      const item = { editor: editor || document.activeElement || document.body };
      buildCard(item, 'warning', 'Espera un momento', message);
      blockedTimer = setTimeoutFn(() => {
        blockedTimer = null;
        clearCard();
      }, 4000);
    }

    async function runReview(item) {
      if (active !== item || item.cancelled) return;
      item.result = null;
      item.error = null;
      renderReviewing(item);
      try {
        const response = await api.runtime.sendMessage({
          type: 'PROTEGER_TEXTO',
          text: item.text
        });
        if (!isCurrent(item)) {
          if (active === item) invalidate(item);
          return;
        }
        if (!response?.ok) {
          throw new Error(response?.error || 'No se pudo revisar el mensaje.');
        }
        const evaluation = evaluateProtection(item.text, response.protection);
        if (!isCurrent(item)) {
          if (active === item) invalidate(item);
          return;
        }
        if (evaluation.kind === 'clean') {
          resolveItem(item, { status: 'send', text: item.text });
          return;
        }
        item.result = evaluation;
        if (evaluation.kind === 'changes') {
          renderChanges(item);
          applyHighlights(item, evaluation.spans);
        } else {
          renderWarning(item);
        }
      } catch (error) {
        if (!isCurrent(item)) {
          if (active === item) invalidate(item);
          return;
        }
        clearHighlights();
        item.error = error?.message || 'No se pudo revisar el mensaje.';
        renderError(item, item.error);
      }
    }

    function authorize({ editor, text, conversation }) {
      if (!enabled) return Promise.resolve({ status: 'send', text });
      if (active) return Promise.resolve({ status: 'busy' });
      if (typeof text !== 'string' || !text.trim()) {
        return Promise.resolve({ status: 'cancelled' });
      }
      if (getAttachmentState() === 'processing') {
        return Promise.resolve({ status: 'cancelled' });
      }
      const snapshot = readEditor(editor);
      if (snapshot.kind === 'unknown') {
        showBlocked('No se pudo leer este editor. Vuelve a intentarlo.', editor);
        return Promise.resolve({ status: 'cancelled' });
      }
      const item = {
        id: ++sequence,
        editor,
        kind: snapshot.kind,
        segments: snapshot.segments,
        text: snapshot.text,
        conversation: conversation || currentConversation(),
        result: null,
        error: null,
        cancelled: false,
        resolving: false,
        resolve: null,
        cleanup: [],
        timer: null
      };
      active = item;
      const promise = new Promise(resolve => { item.resolve = resolve; });
      attachInvalidation(item);
      runReview(item);
      return promise;
    }

    function cancelEdit(item) {
      if (!item || active !== item || item.resolving) return;
      item.editor.focus?.();
      resolveItem(item, { status: 'cancelled' });
    }

    function retry(item) {
      if (!item || active !== item || item.resolving) return;
      if (!isCurrent(item)) {
        invalidate(item);
        return;
      }
      clearHighlights();
      restoreDescription(item.editor);
      renderReviewing(item);
      runReview(item);
    }

    function confirmSend(item) {
      if (!item || active !== item || item.resolving) return;
      item.resolving = true;
      if (!isCurrent(item)) {
        invalidate(item);
        return;
      }
      const protectedText = item.result?.result?.protected_text;
      if (typeof protectedText !== 'string') {
        item.resolving = false;
        renderError(item, 'La revisión no devolvió texto protegido.');
        return;
      }
      clearHighlights();
      restoreDescription(item.editor);
      clearCard();
      updatingEditor = true;
      const updated = setEditorText(document, item.editor, item.kind, protectedText);
      updatingEditor = false;
      if (!updated ||
          readEditor(item.editor).text !== protectedText ||
          currentConversation() !== item.conversation) {
        setEditorText(document, item.editor, item.kind, item.text);
        item.resolving = false;
        renderError(item, 'No se pudo actualizar el editor. El borrador se conservó.');
        return;
      }
      resolveItem(item, { status: 'send', text: protectedText, protected: true });
    }

    return {
      start,
      authorize,
      setEnabled,
      readText: editor => readEditor(editor).text,
      get enabled() { return enabled; },
      get active() { return active; }
    };
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      createChatProtection,
      evaluateProtection,
      protectedSpans,
      codePointOffsets,
      readEditor,
      setEditorText
    };
    return;
  }

  const protection = createChatProtection({
    document,
    window,
    api: typeof browser !== 'undefined' ? browser : chrome,
    getAttachmentState: () => root.attachmentStatus?.state || null
  });
  root.chatProtection = protection;
  protection.start();
})(typeof globalThis !== 'undefined' ? globalThis : this);
