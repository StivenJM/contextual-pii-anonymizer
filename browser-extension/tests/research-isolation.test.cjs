const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

function background(state) {
  const noop = { addListener() {} };
  const context = vm.createContext({
    chrome: {
      runtime: { onInstalled: noop, onMessage: noop },
      storage: { local: { get: async defaults => ({ ...defaults, ...state }) }, onChanged: noop }
    }
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../extension/background.js'), 'utf8'), context);
  return id => vm.runInContext(`obtenerEstado(${id})`, context);
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
