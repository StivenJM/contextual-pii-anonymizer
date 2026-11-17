const { test } = require('node:test');
const assert = require('node:assert/strict');
const {
  codePointOffsets,
  protectedSpans,
  evaluateProtection,
  readEditor,
  setEditorText
} = require('../extension/chat-protection.js');

function textNode(value) {
  return { nodeType: 3, nodeValue: value };
}

function element(tagName, childNodes = []) {
  return {
    nodeType: 1,
    tagName,
    childNodes,
    isContentEditable: true,
    getAttribute: name => name === 'contenteditable' ? 'true' : null
  };
}

function protection(overrides = {}) {
  return {
    original_text: 'hola',
    protected_text: 'hola',
    detections: [],
    operations: [],
    mapping_gaps: [],
    warnings: [],
    ...overrides
  };
}

test('converts Python code-point offsets to JS UTF-16 offsets without shifting emojis', () => {
  const text = 'a😀b';
  assert.deepEqual(codePointOffsets(text), [0, 1, 3, 4]);
  assert.deepEqual(
    protectedSpans(text, [{
      action: 'MASK', start: 1, end: 2, original_text: '😀',
      replacement: '****', mapping_gap: false
    }]),
    [{ start: 1, end: 3 }]
  );
  assert.deepEqual(
    protectedSpans(text, [{
      action: 'MASK', start: 2, end: 3, original_text: 'b',
      replacement: '*', mapping_gap: false
    }]),
    [{ start: 3, end: 4 }]
  );
});

test('counts changed operations, includes mapping gaps and merges overlaps', () => {
  const text = 'hola ana@example.com y 1234567890';
  const emailStart = text.indexOf('ana@example.com');
  const phoneStart = text.indexOf('1234567890');
  const spans = protectedSpans(text, [
    { action: 'KEEP', start: 0, end: 4, original_text: 'hola', replacement: 'hola', mapping_gap: false },
    { action: 'REPLACE_WITH_LABEL', start: emailStart, end: emailStart + 15, original_text: 'ana@example.com', replacement: '<EMAIL>', mapping_gap: false },
    { action: 'MASK', start: emailStart + 4, end: emailStart + 15, original_text: 'example.com', replacement: '***********', mapping_gap: false },
    { action: 'MASK', start: phoneStart, end: phoneStart + 10, original_text: '1234567890', replacement: '**********', mapping_gap: true }
  ]);
  assert.equal(spans.length, 2);
  assert.equal(spans[0].start, emailStart);
  assert.equal(spans[0].end, emailStart + 15);
  assert.equal(spans[1].start, phoneStart);
});

test('classifies clean, changed, warning and inconsistent responses', () => {
  assert.equal(evaluateProtection('hola', protection()).kind, 'clean');

  const changed = evaluateProtection('hola ana@example.com', protection({
    original_text: 'hola ana@example.com',
    protected_text: 'hola <EMAIL>',
    operations: [{
      action: 'REPLACE_WITH_LABEL', start: 5, end: 20,
      original_text: 'ana@example.com', replacement: '<EMAIL>', mapping_gap: false
    }]
  }));
  assert.equal(changed.kind, 'changes');
  assert.equal(changed.count, 1);

  const warned = evaluateProtection('hola', protection({ warnings: ['warning'] }));
  assert.equal(warned.kind, 'warning');

  assert.throws(() => evaluateProtection('hola', protection({
    protected_text: 'otro'
  })), /sin operaciones/);
  assert.throws(() => evaluateProtection('hola', protection({
    original_text: 'distinto'
  })), /no corresponde/);
  assert.throws(() => evaluateProtection('hola', protection({
    operations: [{
      action: 'MASK', start: 0, end: 4, original_text: 'hola',
      replacement: '****', mapping_gap: false
    }]
  })), /no devolvió texto protegido/);
  assert.throws(() => evaluateProtection('hola', protection({
    protected_text: '****',
    operations: [{
      action: 'MASK', start: 0, end: 99, original_text: 'hola',
      replacement: '****', mapping_gap: false
    }]
  })), /operaciones inconsistentes/);
});

test('reads textarea values and preserves contenteditable block line breaks', () => {
  assert.deepEqual(readEditor({ value: 'linea', tagName: 'TEXTAREA' }), {
    kind: 'text', text: 'linea', segments: []
  });

  const editor = element('DIV', [
    element('P', [textNode('primera')]),
    element('P', [textNode('segunda')]),
    element('DIV', [textNode('tercera'), element('BR')])
  ]);
  const snapshot = readEditor(editor);
  assert.equal(snapshot.kind, 'contenteditable');
  assert.equal(snapshot.text, 'primera\nsegunda\ntercera');
  assert.equal(snapshot.segments.length, 3);
});

test('updates a textarea through its native value setter and announces input', () => {
  let value = '';
  const prototype = {};
  Object.defineProperty(prototype, 'value', {
    get() { return value; },
    set(next) { value = next; }
  });
  const editor = Object.create(prototype);
  editor.tagName = 'TEXTAREA';
  let input = 0;
  editor.dispatchEvent = event => { if (event.type === 'input') input += 1; };
  const document = { defaultView: { Event: class Event { constructor(type) { this.type = type; } } } };

  assert.equal(setEditorText(document, editor, 'text', 'texto protegido'), true);
  assert.equal(editor.value, 'texto protegido');
  assert.equal(input, 1);
});
