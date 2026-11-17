const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

function loadBackground(state) {
  const noop = { addListener() {} };
  const context = vm.createContext({
    chrome: {
      runtime: { onInstalled: noop, onMessage: noop },
      storage: { local: { get: async defaults => ({ ...defaults, ...state }) }, onChanged: noop }
    }
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../extension/background.js'), 'utf8'), context);
  return context;
}

function background(state) {
  const context = loadBackground(state);
  return id => vm.runInContext(`obtenerEstado(${id})`, context);
}

function chatProtection(state) {
  const context = loadBackground(state);
  return id => vm.runInContext(`obtenerChatProtection(${id})`, context);
}

test('research pauses attachment protection only on its selected tab', async () => {
  const getState = background({ activo: true, researchState: { session: { tabId: 7, phase: 'recording' } } });
  assert.equal(await getState(7), false);
  assert.equal(await getState(8), true);
});

test('ordinary protection resumes during pending upload and withdrawal, but not paused capture', async () => {
  for (const phase of ['starting', 'pending', 'withdrawing']) {
    assert.equal(await background({ activo: true, researchState: { session: { tabId: 7, phase } } })(7), true);
  }
  assert.equal(await background({ activo: true, researchState: { session: { tabId: 7, phase: 'paused' } } })(7), false);
});

test('ordinary enabled and disabled preferences keep their previous behavior', async () => {
  assert.equal(await background({ activo: true })(7), true);
  assert.equal(await background({ activo: false })(7), false);
});

test('research capture pauses chat protection only on its selected tab', async () => {
  for (const phase of ['recording', 'paused']) {
    const getChat = chatProtection({
      chatProtection: true,
      researchState: { session: { tabId: 7, phase } }
    });
    assert.equal(await getChat(7), false, phase);
    assert.equal(await getChat(8), true, phase);
  }
});

test('chat protection resumes outside an active capture and stays independent', async () => {
  for (const phase of ['starting', 'pending', 'withdrawing']) {
    assert.equal(await chatProtection({
      chatProtection: true,
      researchState: { session: { tabId: 7, phase } }
    })(7), true, phase);
  }
  assert.equal(await chatProtection({ chatProtection: false })(7), false);
});
