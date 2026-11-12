const { test } = require('node:test');
const assert = require('node:assert/strict');
const {
  createResearchNotice,
  SUCCESS_TITLE,
  SUCCESS_DESCRIPTION
} = require('../extension/research-notice.js');

function node(tag = 'div') {
  const element = {
    tagName: tag,
    className: '',
    textContent: '',
    type: '',
    style: { cssText: '' },
    attributes: {},
    children: [],
    parent: null,
    listeners: {},
    removed: false,
    append(...items) {
      for (const item of items) {
        item.parent = element;
        element.children.push(item);
      }
    },
    remove() {
      element.removed = true;
      if (element.parent) {
        element.parent.children = element.parent.children.filter(child => child !== element);
        element.parent = null;
      }
    },
    setAttribute(name, value) { element.attributes[name] = String(value); },
    getAttribute(name) { return element.attributes[name]; },
    addEventListener(type, listener) { element.listeners[type] = listener; },
    contains(candidate) {
      if (candidate === element) return true;
      return element.children.some(child => child.contains?.(candidate));
    },
    attachShadow() {
      element.shadowRoot = node('shadow-root');
      return element.shadowRoot;
    }
  };
  return element;
}

function fakeDocument() {
  const body = node('body');
  return {
    body,
    documentElement: body,
    createElement: tag => node(tag)
  };
}

function fakeClock() {
  let now = 0;
  let sequence = 0;
  const tasks = [];
  return {
    now: () => now,
    setTimeout(fn, ms) {
      const id = ++sequence;
      tasks.push({ id, at: now + ms, fn, done: false });
      return id;
    },
    clearTimeout(id) {
      const task = tasks.find(item => item.id === id);
      if (task) task.done = true;
    },
    advance(ms) {
      now += ms;
      for (const task of [...tasks]) {
        if (!task.done && task.at <= now) {
          task.done = true;
          task.fn();
        }
      }
    }
  };
}

function walk(element, predicate, found = []) {
  if (predicate(element)) found.push(element);
  for (const child of element.children || []) walk(child, predicate, found);
  return found;
}

function create() {
  const document = fakeDocument();
  const clock = fakeClock();
  const notice = createResearchNotice(document, {
    setTimeout: clock.setTimeout,
    clearTimeout: clock.clearTimeout,
    now: clock.now,
    duration: 6000
  });
  const host = () => document.body.children.find(child => child.getAttribute('data-research-notice'));
  const title = () => {
    const element = host();
    if (!element) return '';
    return walk(element.shadowRoot || element, item => item.className === 'research-notice-title')[0]?.textContent || '';
  };
  const closeButton = () => {
    const element = host();
    if (!element) return null;
    return walk(element.shadowRoot || element, item => item.getAttribute('aria-label') === 'Cerrar aviso')[0] || null;
  };
  return { notice, document, clock, host, title, closeButton };
}

test('a confirmed activation shows one dismissible success notice with the requested copy', () => {
  const { notice, host, title, closeButton } = create();
  assert.equal(notice.showSuccess(), true);
  assert.equal(title(), SUCCESS_TITLE);
  assert.equal(SUCCESS_DESCRIPTION, 'Consulta el estado y finaliza la sesión desde el icono de la extensión.');
  assert.equal(closeButton()?.textContent, '×');
  assert.equal(closeButton()?.getAttribute('aria-label'), 'Cerrar aviso');
  assert.ok(host());
});

test('the success notice dismisses itself after about six seconds', () => {
  const { notice, clock, host } = create();
  notice.showSuccess();
  clock.advance(5900);
  assert.ok(host());
  clock.advance(200);
  assert.equal(host(), undefined);
});

test('the auto-dismiss timer pauses while hovered or focused and resumes afterwards', () => {
  const { notice, clock, host } = create();
  notice.showSuccess();
  clock.advance(3000);
  host().listeners.pointerenter();
  clock.advance(60000);
  assert.ok(host(), 'hover must suspend the countdown');

  host().listeners.pointerleave();
  clock.advance(2999);
  assert.ok(host());
  clock.advance(2);
  assert.equal(host(), undefined);

  notice.showSuccess();
  clock.advance(1000);
  host().listeners.focusin();
  clock.advance(60000);
  assert.ok(host(), 'focus inside must suspend the countdown');
  host().listeners.focusout({ relatedTarget: null });
  clock.advance(5001);
  assert.equal(host(), undefined);
});

test('closing with the button removes the notice completely with no replacement control', () => {
  const { notice, document, closeButton } = create();
  notice.showSuccess();
  closeButton().listeners.click();
  assert.equal(document.body.children.length, 0);
  assert.equal(notice.element, null);
});

test('blocking incidents stay until closed and are announced as alerts', () => {
  const { notice, clock, host } = create();
  notice.showIncident({ id: 'incident-1', text: 'El envío se bloqueó.' });
  const element = host();
  assert.equal(element.getAttribute('data-research-notice'), 'incident');
  const noticeElement = walk(element.shadowRoot, item => item.className === 'research-notice')[0];
  assert.equal(noticeElement.getAttribute('role'), 'alert');
  clock.advance(120000);
  assert.ok(host(), 'incidents must not auto-dismiss');
});

test('a closed incident does not reappear for every retry, but a distinct incident does', () => {
  const { notice, closeButton, host } = create();
  notice.showIncident({ id: 'send-1', text: 'Bloqueado.' });
  closeButton().listeners.click();
  assert.equal(notice.showIncident({ id: 'send-1', text: 'Bloqueado otra vez.' }), false);
  assert.equal(host(), undefined);
  assert.equal(notice.showIncident({ id: 'send-2', text: 'Otro problema.' }), true);
  assert.ok(host());
});

test('an active incident is never replaced by the success confirmation', () => {
  const { notice, host, title } = create();
  notice.showIncident({ id: 'send-1', text: 'Bloqueado.' });
  assert.equal(notice.showSuccess(), false);
  assert.equal(notice.mode, 'incident');
  assert.notEqual(title(), SUCCESS_TITLE);
  assert.ok(host());
});

test('dispose clears the notice, the timers and the incident memory', () => {
  const { notice, clock, document, closeButton } = create();
  notice.showIncident({ id: 'send-1', text: 'Bloqueado.' });
  notice.dispose();
  assert.equal(document.body.children.length, 0);
  clock.advance(120000);
  assert.equal(document.body.children.length, 0);
  assert.equal(notice.showIncident({ id: 'send-1', text: 'Bloqueado.' }), true);
  assert.ok(closeButton());
});
