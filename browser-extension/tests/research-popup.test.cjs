const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const directory = path.join(__dirname, '../extension');
const html = fs.readFileSync(path.join(directory, 'popup.html'), 'utf8');
const script = fs.readFileSync(path.join(directory, 'research-popup.js'), 'utf8');
const settle = () => new Promise(resolve => setImmediate(resolve));

async function popup(overrides = {}) {
  const elements = new Map([...html.matchAll(/id="([^"]+)"/g)].map(([, id]) => [id, {
    value: '', checked: false, disabled: false, textContent: '', dataset: {}, listeners: {},
    addEventListener(type, listener) { this.listeners[type] = listener; },
    select() { this.selected = true; }
  }]));
  let state = { phase: 'idle', count: 2, receipt_id: '', capture_status: '',
    api_origin: 'http://127.0.0.1:8000', enrollment_only: false, ...overrides };
  const calls = [], copied = [], dialogs = [];
  let clipboardFails = false;
  let runtimeFails = false;
  let startError = null;
  vm.runInNewContext(script, {
    document: { getElementById: id => elements.get(id) },
    chrome: { runtime: { sendMessage: async message => {
      if (runtimeFails) throw new Error('synthetic runtime connection failure');
      calls.push(structuredClone(message));
      if (message.type === 'RESEARCH_START' && startError) return { ok: false, error: startError };
      return message.type === 'RESEARCH_STATUS' ? { ok: true, ...state } : { ok: true };
    } } },
    navigator: { clipboard: { writeText: async value => {
      if (clipboardFails) throw new Error('synthetic clipboard failure');
      copied.push(value);
    } } },
    confirm: text => { dialogs.push(text); return true; }
  });
  await settle();
  return { elements, calls, copied, dialogs,
    failClipboard() { clipboardFails = true; },
    failRuntime() { runtimeFails = true; },
    failStart(message) { startError = message; },
    setState(value) { state = { ...state, ...value }; } };
}

test('research card labels and separate consent remain Spanish', () => {
  const panel = html.match(/<section[^>]*research-panel[\s\S]*?<\/section>/)[0];
  for (const text of ['Captura para investigación (solo texto)', 'Protocolo',
    'Iniciar en esta pestaña', 'Finalizar y guardar / reintentar',
    'Descartar / retirar sesión', 'Copiar identificador',
    'no protege ni desidentifica', 'entrenamiento del modelo',
    'no arranca ni detiene Docker']) {
    assert.ok(panel.includes(text), `Missing Spanish UI: ${text}`);
  }
  for (const id of ['researchConsent', 'researchTraining']) {
    const input = panel.match(new RegExp(`<input[^>]*id="${id}"[^>]*>`))[0];
    assert.ok(!input.includes('checked'), 'Consent must not become preselected');
  }
});

test('Spanish display labels do not replace protocol phase values or enrollment logic', async () => {
  for (const [phase, label] of Object.entries({ idle: 'Sin captura', starting: 'Iniciando',
    recording: 'Grabando', paused: 'En pausa', pending: 'Pendiente de guardar o reintentar' })) {
    const p = await popup({ phase });
    assert.ok(p.elements.get('researchStatus').textContent.startsWith(label));
    assert.equal(p.elements.get('researchKeyLabel').textContent, 'Clave local del investigador');
    assert.equal(p.elements.get('researchStart').disabled, phase !== 'idle');
  }
  const campus = await popup({ enrollment_only: true });
  assert.equal(campus.elements.get('researchKeyLabel').textContent, 'Código de participación del estudio');
  const withdrawing = await popup({ phase: 'withdrawing' });
  assert.match(withdrawing.elements.get('researchStatus').textContent, /retiro en la API está pendiente/);
});

test('saved receipt, interruption, clipboard fallback and withdrawal dialog stay Spanish', async () => {
  const receipt = 'r'.repeat(32);
  const p = await popup({ receipt_id: receipt, capture_status: 'interrupted' });
  assert.equal(p.elements.get('researchReceipt').value, receipt);
  assert.match(p.elements.get('researchStatus').textContent, /INTERRUMPIDA/);
  await p.elements.get('researchCopy').listeners.click();
  assert.deepEqual(p.copied, [receipt]);
  assert.match(p.elements.get('researchStatus').textContent, /Identificador copiado/);
  p.failClipboard();
  await p.elements.get('researchCopy').listeners.click();
  assert.equal(p.elements.get('researchReceipt').selected, true);
  assert.match(p.elements.get('researchStatus').textContent, /cópialo manualmente/);
  p.elements.get('researchDiscard').listeners.click();
  await settle();
  assert.match(p.dialogs[0], /¿Quieres descartar/);
  assert.match(p.dialogs[0], /no elimina.*Google Forms/);
  assert.ok(p.calls.some(call => call.type === 'RESEARCH_DISCARD'));
});

test('browser messaging failure uses a Spanish recovery message without exposing native text', async () => {
  const p = await popup({ phase: 'recording' });
  p.failRuntime();
  await p.elements.get('researchSetTask').listeners.click();
  assert.match(p.elements.get('researchStatus').textContent, /No se pudo comunicar con la extensión/);
  assert.ok(!p.elements.get('researchStatus').textContent.includes('synthetic runtime'));
});

test('failed start preserves setup inputs and exposes feedback next to the start action', async () => {
  const p = await popup();
  p.elements.get('researchKey').value = 'synthetic-local-key';
  p.elements.get('researchProtocol').value = 'research-v1';
  p.elements.get('researchConsent').checked = true;
  p.elements.get('researchTraining').checked = false;
  p.failStart('Esta conversación ya tiene mensajes. Abre una conversación nueva y vacía para iniciar la captura.');
  await p.elements.get('researchStart').listeners.click();
  assert.equal(p.elements.get('researchKey').value, 'synthetic-local-key');
  assert.equal(p.elements.get('researchProtocol').value, 'research-v1');
  assert.equal(p.elements.get('researchConsent').checked, true);
  assert.equal(p.elements.get('researchTraining').checked, false);
  assert.match(p.elements.get('researchStatus').textContent, /conversación nueva y vacía/);
  assert.equal(p.elements.get('researchStatus').dataset.kind, 'error');
  assert.ok(html.indexOf('id="researchStatus"') < html.indexOf('id="researchStart"'));
});

test('successful start still clears the operator key rather than persisting it', async () => {
  const p = await popup();
  p.elements.get('researchKey').value = 'synthetic-local-key';
  p.elements.get('researchConsent').checked = true;
  await p.elements.get('researchStart').listeners.click();
  assert.equal(p.elements.get('researchKey').value, '');
  assert.equal(p.calls.find(call => call.type === 'RESEARCH_START').key, 'synthetic-local-key');
});
