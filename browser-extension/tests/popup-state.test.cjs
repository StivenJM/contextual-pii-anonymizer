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
    checked: false, textContent: '', hidden: false, attributes: {}, classList: {
      values: new Set(),
      toggle(name, enabled) { enabled ? this.values.add(name) : this.values.delete(name); }
    },
    listeners: {},
    addEventListener(type, listener) { this.listeners[type] = listener; },
    setAttribute(name, value) { this.attributes[name] = String(value); }
  }]));
  const writes = [];
  const chrome = { storage: { local: {
    get: (defaults, callback) => callback({ ...defaults, ...stored }),
    set: values => { writes.push(values); Object.assign(stored, values); }
  } } };
  const context = {
    document: { getElementById: id => elements.get(id) },
    chrome
  };
  vm.runInNewContext(script, context);
  await settle();
  return { elements, writes, context };
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

test('active research capture disables and dims both protection sections', async () => {
  const p = await popup();
  p.context.protectionUi.setDisabledByCapture(true);
  assert.equal(p.elements.get('estadoTexto').textContent, 'Desactivada');
  assert.equal(p.elements.get('estadoChats').textContent, 'Desactivada');
  assert.equal(p.elements.get('toggleActivo').checked, false);
  assert.equal(p.elements.get('toggleChats').checked, false);
  assert.equal(p.elements.get('estadoTexto').classList.values.has('off'), true);
  assert.equal(p.elements.get('estadoChats').classList.values.has('off'), true);
  assert.equal(p.elements.get('attachmentProtectionCard').attributes['data-disabled'], 'true');
  assert.equal(p.elements.get('chatProtectionCard').attributes['data-disabled'], 'true');

  p.context.protectionUi.setDisabledByCapture(false);
  assert.equal(p.elements.get('estadoTexto').textContent, 'Activada');
  assert.equal(p.elements.get('estadoChats').textContent, 'Desactivada');
  assert.equal(p.elements.get('toggleActivo').checked, true);
  assert.equal(p.elements.get('attachmentProtectionCard').attributes['data-disabled'], 'false');
});

test('chat protection is independent, off by default, and persists its own preference', async () => {
  const p = await popup();
  assert.ok(html.includes('Protección de chats'));
  assert.ok(html.includes('Revisa y protege tus mensajes antes de enviarlos'));
  assert.equal(p.elements.get('toggleChats').checked, false);
  assert.equal(p.elements.get('estadoChats').textContent, 'Desactivada');

  p.elements.get('toggleChats').checked = true;
  p.elements.get('toggleChats').listeners.change();
  await settle();

  assert.equal(p.elements.get('estadoChats').textContent, 'Activada');
  assert.equal(p.elements.get('estadoTexto').textContent, 'Activada');
  assert.deepEqual(Object.keys(p.writes.at(-1)), ['chatProtection']);
  assert.equal(p.writes.at(-1).chatProtection, true);
});
