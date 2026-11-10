const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const directory = path.join(__dirname, '../extension');
const html = fs.readFileSync(path.join(directory, 'popup.html'), 'utf8');
const script = fs.readFileSync(path.join(directory, 'popup.js'), 'utf8');
const settle = () => new Promise(resolve => setImmediate(resolve));

async function popup(stored = { activo: true }) {
  const elements = new Map([...html.matchAll(/id="([^"]+)"/g)].map(([, id]) => [id, {
    checked: false, textContent: '', classList: {
      values: new Set(),
      toggle(name, enabled) { enabled ? this.values.add(name) : this.values.delete(name); }
    },
    listeners: {},
    addEventListener(type, listener) { this.listeners[type] = listener; }
  }]));
  const writes = [];
  const chrome = { storage: { local: {
    get: (defaults, callback) => callback({ ...defaults, ...stored }),
    set: values => { writes.push(values); Object.assign(stored, values); }
  } } };
  vm.runInNewContext(script, {
    document: { getElementById: id => elements.get(id) },
    chrome
  });
  await settle();
  return { elements, writes };
}

test('attachment protection state names its scope instead of implying whole-extension state', async () => {
  const p = await popup();
  assert.equal(p.elements.get('estadoTexto').textContent, 'Activada');
  assert.ok(html.includes('Protección de adjuntos'));
  assert.match(p.elements.get('estadoAlcance').textContent, /No anonimiza el texto/);
  assert.match(html, /localhost:5000/);
  assert.match(html, /127\.0\.0\.1:8000/);
});

test('disabling protection explains the bypass without touching research state', async () => {
  const p = await popup();
  p.elements.get('toggleActivo').checked = false;
  p.elements.get('toggleActivo').listeners.change();
  await settle();

  assert.equal(p.elements.get('estadoTexto').textContent, 'Desactivada');
  assert.match(p.elements.get('estadoAlcance').textContent, /sin convertir ni proteger/);
  assert.match(p.elements.get('estadoAlcance').textContent, /Docker/);
  assert.equal(p.writes.length, 1);
  assert.deepEqual(Object.keys(p.writes[0]), ['activo']);
  assert.equal(p.writes[0].activo, false);
});
