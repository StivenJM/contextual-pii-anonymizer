const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const script = fs.readFileSync(
  path.join(__dirname, '../extension/research-content.js'),
  'utf8'
);
const settle = () => new Promise(resolve => setImmediate(resolve));

function harness() {
  const listeners = {};
  const sent = [];
  const notices = { success: 0, disposed: 0, incidents: [] };
  const windowListeners = {};
  const context = {
    document: {
      body: { append() {} },
      documentElement: {},
      querySelectorAll: () => [],
      querySelector: () => null,
      createElement: () => ({ style: {}, setAttribute() {}, append() {}, addEventListener() {} })
    },
    location: { pathname: '/', hostname: 'chatgpt.com' },
    window: { addEventListener(type, listener) { windowListeners[type] = listener; } },
    MutationObserver: class { observe() {} disconnect() {} },
    crypto: { randomUUID: () => `uuid-${Math.random().toString(16).slice(2)}` },
    setTimeout,
    clearTimeout,
    TextEncoder,
    console,
    createResearchNotice: () => ({
      showSuccess() { notices.success += 1; return true; },
      showIncident(incident) { notices.incidents.push(incident); return true; },
      dispose() { notices.disposed += 1; },
      dismiss() {},
      element: null,
      mode: null
    }),
    chrome: {
      runtime: {
        onMessage: { addListener(listener) { listeners.message = listener; } },
        async sendMessage(message) {
          sent.push(message);
          if (message.type === 'RESEARCH_STATUS') return { ok: true, recording: false, paused: false };
          if (message.type === 'RESEARCH_INCIDENT') {
            return { ok: true, incident: { id: 'incident-1', code: message.code, message: 'El envío se bloqueó.' } };
          }
          return { ok: true };
        }
      }
    }
  };
  vm.runInNewContext(script, context);
  const prepared = new Promise(resolve => {
    listeners.message({ type: 'RESEARCH_PREPARE' }, {}, resolve);
  });
  return { listeners, sent, notices, prepared, windowListeners };
}

function send(listener, message, nonce) {
  return new Promise(resolve => listener({ ...message, documentNonce: nonce }, {}, resolve));
}

test('activation alone does not announce success before the controller confirms', async () => {
  const h = harness();
  const { documentNonce } = await h.prepared;
  await settle();
  const reply = await send(h.listeners.message, { type: 'RESEARCH_ACTIVATE' }, documentNonce);
  assert.equal(reply.activated, true);
  assert.equal(h.notices.success, 0);
});

test('one confirmation from the controller shows the success notice', async () => {
  const h = harness();
  const { documentNonce } = await h.prepared;
  await settle();
  await send(h.listeners.message, { type: 'RESEARCH_ACTIVATE' }, documentNonce);
  const reply = await send(h.listeners.message, { type: 'RESEARCH_CONFIRM' }, documentNonce);
  assert.equal(reply.shown, true);
  assert.equal(h.notices.success, 1);
});

test('a stale confirmation or another document never announces success', async () => {
  const h = harness();
  const { documentNonce } = await h.prepared;
  await settle();
  await send(h.listeners.message, { type: 'RESEARCH_ACTIVATE' }, documentNonce);
  h.listeners.message({ type: 'RESEARCH_CONFIRM', documentNonce: 'other-document' }, {}, () => {});
  await send(h.listeners.message, { type: 'RESEARCH_STOP' }, documentNonce);
  await send(h.listeners.message, { type: 'RESEARCH_CONFIRM' }, documentNonce);
  await settle();
  assert.equal(h.notices.success, 0);
});

test('stopping or discarding disposes the notice and its timers', async () => {
  const h = harness();
  const { documentNonce } = await h.prepared;
  await settle();
  await send(h.listeners.message, { type: 'RESEARCH_ACTIVATE' }, documentNonce);
  await send(h.listeners.message, { type: 'RESEARCH_STOP' });
  assert.equal(h.notices.disposed, 1);
});

test('a blocked send reports an incident instead of re-announcing the capture', async () => {
  const h = harness();
  const { documentNonce } = await h.prepared;
  await settle();
  await send(h.listeners.message, { type: 'RESEARCH_ACTIVATE' }, documentNonce);
  h.windowListeners.click({
    type: 'click',
    target: { closest: () => ({}) },
    preventDefault() {},
    stopImmediatePropagation() {}
  });
  await settle();
  await settle();
  assert.equal(h.notices.success, 0);
  assert.equal(h.notices.incidents.length, 1);
  assert.equal(h.notices.incidents[0].id, 'incident-1');
  assert.ok(h.sent.some(message => message.type === 'RESEARCH_INCIDENT' && message.code === 'send_blocked'));
});
