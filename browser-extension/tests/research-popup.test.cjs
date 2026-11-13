const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const directory = path.join(__dirname, '../extension');
const html = fs.readFileSync(path.join(directory, 'popup.html'), 'utf8');
const script = fs.readFileSync(path.join(directory, 'research-popup.js'), 'utf8');
const { describe } = require('../extension/research-popup.js');
const settle = () => new Promise(resolve => setImmediate(resolve));

const receipt = 'r'.repeat(32);

async function popup(overrides = {}) {
  const elements = new Map([...html.matchAll(/id="([^"]+)"/g)].map(([, id]) => [id, {
    value: '', checked: false, disabled: false, hidden: false, textContent: '',
    listeners: {}, attributes: {},
    addEventListener(type, listener) { this.listeners[type] = listener; },
    setAttribute(name, value) { this.attributes[name] = value; },
    select() { this.selected = true; }
  }]));
  let state = {
    view: 'idle', phase: 'idle', count: 0, receipt_id: '', provider: '',
    task: 'unassigned', paused_reason: '', enrollment_only: false, last_error: '',
    tab: null, incident: null, ...overrides
  };
  const calls = [];
  const copied = [];
  const dialogs = [];
  let clipboardFails = false;
  let runtimeFails = false;
  let startError = null;
  let held = null;
  vm.runInNewContext(script, {
    document: { getElementById: id => elements.get(id) },
    chrome: {
      runtime: { sendMessage: async message => {
        if (runtimeFails) throw new Error('synthetic runtime connection failure');
        calls.push(JSON.parse(JSON.stringify(message)));
        if (held && held.type === message.type) await held.promise;
        if (message.type === 'RESEARCH_START' && startError) return { ok: false, error: startError };
        return message.type === 'RESEARCH_STATUS' ? { ok: true, ...state } : { ok: true };
      } },
      storage: { onChanged: { addListener() {} } }
    },
    navigator: { clipboard: { writeText: async value => {
      if (clipboardFails) throw new Error('synthetic clipboard failure');
      copied.push(value);
    } } },
    confirm: text => { dialogs.push(text); return true; }
  });
  await settle();
  return {
    elements, calls, copied, dialogs,
    failClipboard() { clipboardFails = true; },
    failRuntime() { runtimeFails = true; },
    failStart(message) { startError = message; },
    hold(type) {
      let release;
      const promise = new Promise(resolve => { release = resolve; });
      held = { type, promise };
      return () => { held = null; release(); };
    }
  };
}

test('the capture card keeps the requested consent copy separate and unchecked', () => {
  const panel = html.match(/<section[^>]*research-panel[\s\S]*?<\/section>/)[0];
  for (const text of [
    'Captura de chats',
    'Puedes abrir esta ventana desde el menú de extensiones y fijar su icono a la barra del navegador.',
    'Declaro estar informado y autorizo recopilar mis textos sin anonimizar.',
    'Autorizo utilizar mi sesión para entrenar modelos de IA.',
    'Iniciar en esta pestaña',
    'Finalizar y guardar',
    'Reintentar guardado',
    'Reintentar retiro',
    'Retirar sesión guardada',
    'Ir a la pestaña de captura'
  ]) {
    assert.ok(panel.includes(text), `Missing Spanish UI: ${text}`);
  }
  for (const id of ['researchConsent', 'researchTraining']) {
    const input = panel.match(new RegExp(`<input[^>]*id="${id}"[^>]*>`))[0];
    assert.ok(!input.includes('checked'), 'Consent must not become preselected');
  }
});

test('describe maps every persisted view to one visible section and label', () => {
  const cases = {
    idle: ['Sin captura', 'setup'],
    starting: ['Iniciando la captura', 'starting'],
    recording: ['Captura activa', 'active'],
    interrupted: ['Captura interrumpida', 'interrupted'],
    pending: ['Pendiente de guardar', 'pending'],
    saved: ['Sesión guardada', 'saved'],
    withdrawing: ['Retiro pendiente', 'withdrawing']
  };
  for (const [view, [label, section]] of Object.entries(cases)) {
    const model = describe({ view });
    assert.equal(model.label, label);
    const visible = Object.entries(model.sections).filter(([, shown]) => shown).map(([key]) => key);
    assert.deepEqual(visible, [section], view);
  }
});

test('starting inputs are only offered while a new session can start', () => {
  assert.equal(describe({ view: 'idle' }).canStart, true);
  assert.equal(describe({ view: 'saved', receipt_id: receipt }).canStart, true);
  for (const view of ['starting', 'recording', 'interrupted', 'pending', 'withdrawing']) {
    assert.equal(describe({ view }).canStart, false, view);
  }
});

test('capture scope distinguishes this tab, another tab and a closed tab', () => {
  const here = describe({ view: 'recording', tab: { id: 7, exists: true, active: true } });
  assert.equal(here.scope, 'Esta pestaña');
  assert.equal(here.canGoToTab, false);
  assert.equal(here.scopeNotice, '');

  const other = describe({ view: 'recording', tab: { id: 7, exists: true, active: false } });
  assert.equal(other.scope, 'Otra pestaña');
  assert.equal(other.canGoToTab, true);
  assert.match(other.scopeNotice, /otra pestaña/);

  const closed = describe({ view: 'recording', tab: { id: 7, exists: false, active: false } });
  assert.equal(closed.canGoToTab, false);
  assert.equal(closed.tabMissing, true);
  assert.match(closed.scopeNotice, /ya no existe/);
});

test('interruption, pending and withdrawal explain a known reason without inventing success', () => {
  const interrupted = describe({ view: 'interrupted', paused_reason: 'tab_closed' });
  assert.match(interrupted.interruptReason, /pestaña de la captura se cerró/);
  const routed = describe({ view: 'interrupted', paused_reason: 'conversation_changed', paused_from: '/', paused_to: '/c/abc' });
  assert.match(routed.interruptReason, /\/ → \/c\/abc/);
  assert.equal(describe({ view: 'pending' }).label.includes('guardar'), true);
  assert.match(describe({ view: 'pending', last_error: 'La API respondió con el código 503.' }).pendingReason, /503/);
  assert.match(describe({ view: 'withdrawing', last_error: 'offline' }).withdrawalReason, /offline/);
});

test('enrollment and researcher labels stay distinct', () => {
  assert.equal(describe({ view: 'idle' }).keyLabel, 'Clave local del investigador');
  assert.equal(describe({ view: 'idle', enrollment_only: true }).keyLabel, 'Código de participación del estudio');
});

test('failed start keeps the setup inputs editable and shows feedback next to the action', async () => {
  const p = await popup();
  p.elements.get('researchKey').value = 'synthetic-local-key';
  p.elements.get('researchProtocol').value = 'research-v1';
  p.elements.get('researchConsent').checked = true;
  p.failStart('Esta conversación ya tiene mensajes. Abre una conversación nueva y vacía para iniciar la captura.');
  await p.elements.get('researchStart').listeners.click();
  await settle();
  assert.equal(p.elements.get('researchKey').value, 'synthetic-local-key');
  assert.equal(p.elements.get('researchProtocol').value, 'research-v1');
  assert.equal(p.elements.get('researchConsent').checked, true);
  assert.equal(p.elements.get('researchStartError').hidden, false);
  assert.match(p.elements.get('researchStartError').textContent, /conversación nueva y vacía/);
  assert.equal(p.elements.get('researchStart').disabled, false);
});

test('a start that is already in flight cannot be sent twice', async () => {
  const p = await popup();
  p.elements.get('researchKey').value = 'synthetic-local-key';
  p.elements.get('researchConsent').checked = true;
  const release = p.hold('RESEARCH_START');
  const first = p.elements.get('researchStart').listeners.click();
  await settle();
  assert.equal(p.elements.get('researchStart').disabled, true);
  await p.elements.get('researchStart').listeners.click();
  await settle();
  assert.equal(p.calls.filter(call => call.type === 'RESEARCH_START').length, 1);
  release();
  await first;
  await settle();
  assert.equal(p.elements.get('researchStart').disabled, false);
});

test('successful start clears the operator key instead of persisting it', async () => {
  const p = await popup();
  p.elements.get('researchKey').value = 'synthetic-local-key';
  p.elements.get('researchConsent').checked = true;
  await p.elements.get('researchStart').listeners.click();
  await settle();
  assert.equal(p.elements.get('researchKey').value, '');
  assert.equal(p.calls.find(call => call.type === 'RESEARCH_START').key, 'synthetic-local-key');
});

test('browser messaging failure shows a local Spanish explanation', async () => {
  const p = await popup({ view: 'recording' });
  p.failRuntime();
  await p.elements.get('researchSetTask').listeners.click();
  await settle();
  assert.match(p.elements.get('researchActionError').textContent, /No se pudo comunicar con la extensión/);
  assert.ok(!p.elements.get('researchActionError').textContent.includes('synthetic runtime'));
});

test('a failed clipboard copy selects the identifier and explains the manual path', async () => {
  const p = await popup({ view: 'saved', receipt_id: receipt });
  assert.equal(p.elements.get('researchReceipt').value, receipt);
  p.failClipboard();
  await p.elements.get('researchCopy').listeners.click();
  await settle();
  assert.equal(p.elements.get('researchReceipt').selected, true);
  assert.match(p.elements.get('researchCopyError').textContent, /cópialo manualmente/);
});

test('a confirmed receipt is copied without touching the research state', async () => {
  const p = await popup({ view: 'saved', receipt_id: receipt });
  await p.elements.get('researchCopy').listeners.click();
  await settle();
  assert.deepEqual(p.copied, [receipt]);
  assert.equal(p.calls.filter(call => call.type === 'RESEARCH_STATUS').length >= 1, true);
});

test('destructive actions ask for confirmation and keep the documented warning', async () => {
  const p = await popup({ view: 'pending' });
  p.elements.get('researchDiscardPending').listeners.click();
  await settle();
  assert.match(p.dialogs[0], /¿Quieres descartar/);
  assert.match(p.dialogs[0], /no elimina.*Google Forms/);
  assert.ok(p.calls.some(call => call.type === 'RESEARCH_DISCARD'));
});

test('retrying a pending save sends the existing finish operation once', async () => {
  const p = await popup({ view: 'pending', last_error: 'La API respondió con el código 503.' });
  assert.match(p.elements.get('researchPendingReason').textContent, /503/);
  const release = p.hold('RESEARCH_FINISH');
  const first = p.elements.get('researchRetrySave').listeners.click();
  await settle();
  await p.elements.get('researchRetrySave').listeners.click();
  await settle();
  assert.equal(p.calls.filter(call => call.type === 'RESEARCH_FINISH').length, 1);
  release();
  await first;
  await settle();
});
