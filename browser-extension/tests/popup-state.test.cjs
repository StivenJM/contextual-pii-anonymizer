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
    checked: false, textContent: '', hidden: false, classList: {
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

test('the attachment toggle names its own scope instead of implying whole-extension state', async () => {
  const p = await popup();
  assert.equal(p.elements.get('estadoTexto').textContent, 'Activada');
  assert.ok(html.includes('Protección de adjuntos'));
  assert.ok(html.includes('Anonimiza tus mensajes y archivos antes de enviarlos al chat.'));
  assert.match(html, /fijar su icono a la barra del navegador/);
});

test('disabling protection persists only the attachment preference', async () => {
  const p = await popup();
  p.elements.get('toggleActivo').checked = false;
  p.elements.get('toggleActivo').listeners.change();
  await settle();

  assert.equal(p.elements.get('estadoTexto').textContent, 'Desactivada');
  assert.equal(p.writes.length, 1);
  assert.deepEqual(Object.keys(p.writes[0]), ['activo']);
  assert.equal(p.writes[0].activo, false);
});
