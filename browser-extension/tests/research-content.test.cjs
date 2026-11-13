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
  const editor = { value: '', innerText: '', getClientRects: () => [1], contains: () => false };
  const sendButton = { getClientRects: () => [1], click() {}, closest: () => null };
  const location = { pathname: '/', hostname: 'chatgpt.com' };
  let userText = '';
  const RealDate = Date;
  let currentTime = RealDate.now();
  class TestDate extends RealDate {
    constructor(...args) {
      if (args.length) super(...args);
      else super(currentTime);
    }
    static now() { return currentTime; }
  }
  const context = {
    document: {
      body: { append() {} },
      documentElement: {},
      querySelectorAll: selector => {
        if (selector.includes('data-research-editor')) return [editor];
        if (selector.includes('data-research-send')) return [sendButton];
        if (selector.includes('data-message-author-role="user"')) {
          return userText ? [{ innerText: userText, getClientRects: () => [1] }] : [];
        }
        return [];
      },
      querySelector: () => null,
      createElement: () => ({ style: {}, setAttribute() {}, append() {}, addEventListener() {} })
    },
    location,
    Date: TestDate,
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
  const clickSend = () => {
    const text = editor.value;
    // The provider renders the submitted message in the transcript.
    userText = text;
    windowListeners.click({
      type: 'click',
      target: { closest: () => sendButton },
      preventDefault() {},
      stopImmediatePropagation() {}
    });
  };
  const clickStray = () => windowListeners.click({
    type: 'click',
    target: { closest: () => null },
    preventDefault() {},
    stopImmediatePropagation() {}
  });
  return {
    listeners, sent, notices, prepared, windowListeners, location, editor,
    button: sendButton, clickSend, clickStray,
    advance(ms) { currentTime += ms; },
    showUserMessage(text) { userText = text; },
    clearUserMessages() { userText = ''; }
  };
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
  h.button.disabled = true;
  h.clickSend();
  await settle();
  await settle();
  assert.equal(h.notices.success, 0);
  assert.equal(h.notices.incidents.length, 1);
  assert.equal(h.notices.incidents[0].id, 'incident-1');
  assert.ok(h.sent.some(message => message.type === 'RESEARCH_INCIDENT' && message.code === 'send_blocked'));
});

async function capturing(h) {
  const { documentNonce } = await h.prepared;
  await settle();
  await send(h.listeners.message, { type: 'RESEARCH_ACTIVATE' }, documentNonce);
  h.editor.value = 'Synthetic prompt';
  h.clickSend();
  await settle();
  await settle();
  assert.equal(h.sent.filter(message => message.type === 'RESEARCH_INTERRUPTED').length, 0);
}

test('the conversation URL assigned by the first send keeps the capture recording', async () => {
  const h = harness();
  await capturing(h);
  h.location.pathname = '/c/11111111-1111-1111-1111-111111111111';
  h.clickStray();
  await settle();
  assert.equal(h.sent.filter(message => message.type === 'RESEARCH_INTERRUPTED').length, 0);
  assert.equal(h.notices.incidents.length, 0);
});

test('the empty-chat route is accepted for every supported provider', async () => {
  for (const [hostname, from, to] of [
    ['chatgpt.com', '/', '/c/68f1a2b3-1111-2222-3333-444444444444'],
    ['chatgpt.com', '/', '/uc/68f1a2b3-1111-2222-3333-444444444444'],
    ['chatgpt.com', '/', '/g/abc12345/c/68f1a2b3-1111-2222-3333-444444444444'],
    ['claude.ai', '/new', '/chat/68f1a2b3-1111-2222-3333-444444444444'],
    ['claude.ai', '/', '/chat/68f1a2b3-1111-2222-3333-444444444444'],
    ['gemini.google.com', '/app', '/app/c_68f1a2b3c9d0'],
    ['gemini.google.com', '/', '/app/c_68f1a2b3c9d0']
  ]) {
    const h = harness();
    h.location.hostname = hostname;
    h.location.pathname = from;
    await capturing(h);
    h.location.pathname = to;
    h.clickStray();
    await settle();
    assert.equal(h.sent.filter(message => message.type === 'RESEARCH_INTERRUPTED').length, 0, `${hostname} ${from} -> ${to}`);
  }
});

test('a route change that replaces the transcript interrupts the capture', async () => {
  const h = harness();
  await capturing(h);
  h.location.pathname = '/c/11111111-1111-1111-1111-111111111111';
  h.clickStray();
  // A real switch renders another conversation, so our message is gone.
  h.showUserMessage('Un mensaje de otra conversación');
  h.location.pathname = '/c/22222222-2222-2222-2222-222222222222';
  h.clickStray();
  await settle();
  assert.equal(h.sent.filter(message => message.type === 'RESEARCH_INTERRUPTED').length, 1);
});

test('an unreadable provider transcript follows the URL instead of interrupting', async () => {
  const h = harness();
  await capturing(h);
  h.clearUserMessages();
  h.advance(60000);
  h.location.pathname = '/c/22222222-2222-2222-2222-222222222222';
  h.clickStray();
  await settle();
  assert.equal(h.sent.filter(message => message.type === 'RESEARCH_INTERRUPTED').length, 0);
});

test('returning to a new chat after capturing interrupts the capture', async () => {
  const h = harness();
  await capturing(h);
  h.location.pathname = '/c/11111111-1111-1111-1111-111111111111';
  h.clickStray();
  h.location.pathname = '/';
  h.clickStray();
  await settle();
  assert.equal(h.sent.filter(message => message.type === 'RESEARCH_INTERRUPTED').length, 1);
});

test('an identifier replacement keeps recording while our message stays visible', async () => {
  const h = harness();
  await capturing(h);
  h.location.pathname = '/c/11111111-1111-1111-1111-111111111111';
  h.clickStray();
  h.location.pathname = '/c/22222222-2222-2222-2222-222222222222';
  h.clickStray();
  await settle();
  assert.equal(h.sent.filter(message => message.type === 'RESEARCH_INTERRUPTED').length, 0);
  assert.equal(h.notices.incidents.length, 0);
});

test('moving to another conversation after the second message always interrupts', async () => {
  const h = harness();
  await capturing(h);
  h.location.pathname = '/uc/11111111-1111-1111-1111-111111111111';
  h.clickStray();
  h.editor.value = 'Second prompt';
  h.clickSend();
  await settle();
  h.showUserMessage('Un mensaje de otra conversación');
  h.location.pathname = '/c/99999999-9999-9999-9999-999999999999';
  h.clickStray();
  await settle();
  assert.equal(h.sent.filter(message => message.type === 'RESEARCH_INTERRUPTED').length, 1);
});

test('a new-chat route normalised before sending is not an interruption', async () => {
  const h = harness();
  const { documentNonce } = await h.prepared;
  await settle();
  await send(h.listeners.message, { type: 'RESEARCH_ACTIVATE' }, documentNonce);
  h.location.pathname = '/new';
  h.clickStray();
  await settle();
  assert.equal(h.sent.filter(message => message.type === 'RESEARCH_INTERRUPTED').length, 0);
});
