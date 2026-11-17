const { test } = require('node:test');
const assert = require('node:assert/strict');
const {
  createAttachmentStatus,
  PROCESSING_TITLE,
  DONE_TITLE,
  ERROR_TITLE
} = require('../extension/attachment-status.js');

function node(tag = 'div') {
  const element = {
    tagName: tag,
    className: '',
    textContent: '',
    style: { cssText: '' },
    attributes: {},
    children: [],
    parent: null,
    listeners: {},
    append(...items) {
      for (const item of items) {
        item.parent = element;
        element.children.push(item);
      }
    },
    remove() {
      if (element.parent) {
        element.parent.children = element.parent.children.filter(child => child !== element);
        element.parent = null;
      }
    },
    setAttribute(name, value) { element.attributes[name] = String(value); },
    getAttribute(name) { return element.attributes[name]; },
    addEventListener(type, listener) { element.listeners[type] = listener; },
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

function byClass(root, name) {
  if (root.className === name) return root;
  for (const child of root.children) {
    const found = byClass(child, name);
    if (found) return found;
  }
  return null;
}

function setup(options = {}) {
  const document = fakeDocument();
  const clock = fakeClock();
  const status = createAttachmentStatus(document, {
    setTimeout: clock.setTimeout,
    clearTimeout: clock.clearTimeout,
    delay: 150,
    doneDuration: 2500,
    errorDuration: 8000,
    ...options
  });
  return { document, clock, status };
}

test('shows one non-blocking processing status after a short delay', () => {
  const { document, clock, status } = setup();

  status.start('informe.pdf');
  assert.equal(document.body.children.length, 0);
  assert.equal(status.state, 'processing');

  clock.advance(149);
  assert.equal(document.body.children.length, 0);
  clock.advance(1);

  const host = document.body.children[0];
  assert.equal(host.getAttribute('data-attachment-status'), 'processing');
  assert.match(host.style.cssText, /pointer-events:none/);

  const card = byClass(host.shadowRoot, 'attachment-status-card');
  assert.equal(card.getAttribute('data-state'), 'processing');
  assert.equal(card.getAttribute('role'), 'status');
  assert.equal(card.getAttribute('aria-live'), 'polite');
  assert.equal(card.getAttribute('aria-busy'), 'true');
  assert.equal(byClass(card, 'attachment-status-title').textContent, PROCESSING_TITLE);
  assert.match(byClass(card, 'attachment-status-text').textContent, /informe\.pdf/);
  assert.equal(byClass(card, 'attachment-status-icon').textContent, '');
  assert.match(host.shadowRoot.children[0].textContent, /attachment-status-spin/);
  assert.match(host.shadowRoot.children[0].textContent, /prefers-reduced-motion/);
  assert.equal(status.state, 'processing');
});

test('confirms completion, then dismisses without blocking the page', () => {
  const { document, clock, status } = setup();
  status.start('informe.pdf');
  clock.advance(150);

  status.done();
  const host = document.body.children[0];
  const card = byClass(host.shadowRoot, 'attachment-status-card');
  assert.equal(host.getAttribute('data-attachment-status'), 'done');
  assert.equal(card.getAttribute('data-state'), 'done');
  assert.equal(card.getAttribute('aria-busy'), 'false');
  assert.equal(byClass(card, 'attachment-status-title').textContent, DONE_TITLE);
  assert.equal(byClass(card, 'attachment-status-icon').textContent, '✓');
  assert.equal(status.state, 'done');

  clock.advance(2499);
  assert.equal(document.body.children.length, 1);
  clock.advance(1);
  assert.equal(document.body.children.length, 0);
  assert.equal(status.state, 'idle');
});

test('a failure is visible immediately and is announced as an alert', () => {
  const { document, clock, status } = setup();
  status.start('informe.pdf');
  status.fail('El archivo supera el límite de 20 MB.');

  const host = document.body.children[0];
  const card = byClass(host.shadowRoot, 'attachment-status-card');
  assert.equal(host.getAttribute('data-attachment-status'), 'error');
  assert.equal(card.getAttribute('data-state'), 'error');
  assert.equal(card.getAttribute('role'), 'alert');
  assert.equal(card.getAttribute('aria-live'), 'assertive');
  assert.equal(card.getAttribute('aria-busy'), 'false');
  assert.equal(byClass(card, 'attachment-status-title').textContent, ERROR_TITLE);
  assert.equal(byClass(card, 'attachment-status-icon').textContent, '!');
  assert.match(byClass(card, 'attachment-status-text').textContent, /20 MB/);

  clock.advance(7999);
  assert.equal(document.body.children.length, 1);
  clock.advance(1);
  assert.equal(document.body.children.length, 0);
});

test('a fast success never flashes unfinished loading UI', () => {
  const { document, clock, status } = setup();
  status.start('informe.pdf');
  status.done();
  clock.advance(1000);
  assert.equal(document.body.children.length, 0);
  assert.equal(status.state, 'idle');
});

test('starting another file replaces the previous status', () => {
  const { document, clock, status } = setup();
  status.start('primero.pdf');
  clock.advance(150);
  status.start('segundo.pdf');
  clock.advance(150);

  assert.equal(document.body.children.length, 1);
  const card = byClass(document.body.children[0].shadowRoot, 'attachment-status-card');
  assert.match(byClass(card, 'attachment-status-text').textContent, /segundo\.pdf/);
});

test('dispose removes the status and clears pending work', () => {
  const { document, clock, status } = setup();
  status.start('informe.pdf');
  clock.advance(150);
  status.dispose();
  clock.advance(10000);
  assert.equal(document.body.children.length, 0);
  assert.equal(status.state, 'idle');
  assert.equal(status.element, null);
});
