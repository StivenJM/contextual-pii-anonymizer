const { test } = require('node:test');
const assert = require('node:assert/strict');
const { createResearchController } = require('../extension/research-background.js');

function fixture() {
  let saved = {};
  let fail = false;
  let rejectReceiptWrite = false;
  let badReceipt = false;
  const calls = [];
  const seen = [];
  const options = {
    read: async () => structuredClone(saved),
    write: async value => {
      if (rejectReceiptWrite && value.session === null) throw new Error('synthetic storage quota');
      saved = structuredClone(value);
    },
    onChange: async value => { seen.push(structuredClone(value)); },
    request: async (path, options, apiOrigin) => {
      calls.push({ path, options, apiOrigin });
      if (fail) throw new Error('offline');
      if (options.method === 'DELETE') return {};
      if (path.endsWith('/complete')) return { receipt_id: badReceipt ? 'invalid' : 'r'.repeat(32), event_count: JSON.parse(options.body).events.length };
      return { session_id: JSON.parse(options.body).session_id };
    }
  };
  const controller = createResearchController(options);
  return { controller, calls, seen, state: () => saved,
    recreate: () => createResearchController(options),
    rejectReceiptWrite: value => { rejectReceiptWrite = value; },
    badReceipt: value => { badReceipt = value; },
    fail: value => { fail = value; } };
}

const start = async c => {
  await c.start({ tabId: 7, origin: 'https://chatgpt.com', documentNonce: 'document-1', provider: 'chatgpt', consent: true, trainingConsent: false, key: 'setup-key', protocol: 'research-v1' });
  await c.activate(7, 'document-1');
};
const event = (text = '  exact prompt\n') => ({ event_id: crypto.randomUUID(), role: 'user', text, captured_at: new Date().toISOString() });

test('campus enrollment and API origin remain bound through retry and withdrawal', async () => {
  const f = fixture();
  const apiOrigin = 'https://10.20.30.40';
  await f.controller.start({ tabId: 7, origin: 'https://chatgpt.com', documentNonce: 'document-1', provider: 'chatgpt', consent: true, key: 'enrollment-only', enrollmentOnly: true, apiOrigin, protocol: 'research-v1' });
  assert.deepEqual(f.calls[0].options.headers, { 'X-Research-Enrollment': 'enrollment-only' });
  assert.equal(f.state().session.apiOrigin, apiOrigin);
  assert.equal(f.calls[0].apiOrigin, apiOrigin);
  await f.controller.activate(7, 'document-1');
  await f.controller.append(7, 'document-1', event());
  await f.controller.freeze('complete');
  await f.recreate().upload();
  assert.equal(f.state().receipt.apiOrigin, apiOrigin);
  assert.equal(f.calls.at(-1).apiOrigin, apiOrigin);
  f.fail(true);
  await assert.rejects(f.controller.discard());
  assert.equal(f.state().receipt.apiOrigin, apiOrigin);
  f.fail(false);
  await f.controller.discard();
  assert.equal(f.calls.at(-1).apiOrigin, apiOrigin);
  assert.equal(f.state().receipt, null);
});

test('persists exact submissions before acknowledgement; serializes concurrent appends', async () => {
  const f = fixture();
  await start(f.controller);
  await Promise.all(Array.from({ length: 10 }, (_, n) => f.controller.append(7, 'document-1', event(`prompt ${n}`))));
  assert.equal(f.state().session.events.length, 10);
  assert.equal(f.calls.length, 1); // Only session authorization, no inference or per-prompt network.
  assert.equal(f.state().session.events[0].text, 'prompt 0');
});

test('rejects other tabs/documents and does not collect without consent', async () => {
  const f = fixture();
  await assert.rejects(f.controller.start({ consent: false }));
  await start(f.controller);
  await assert.rejects(f.controller.append(8, 'document-1', event()));
  await assert.rejects(f.controller.append(7, 'other-document', event()));
  assert.equal(f.state().session.events.length, 0);
});

test('freezes a stable batch, retains it on failure, retries and clears only after receipt', async () => {
  const f = fixture();
  await start(f.controller);
  await f.controller.append(7, 'document-1', event());
  await f.controller.freeze('complete');
  const original = structuredClone(f.state().session);
  f.fail(true);
  await assert.rejects(f.controller.upload());
  assert.deepEqual(f.state().session, original);
  await assert.rejects(f.controller.append(7, 'document-1', event()));
  f.fail(false);
  const receipt = await f.controller.upload();
  assert.equal(receipt.receipt_id, 'r'.repeat(32));
  assert.equal(f.state().session, null);
  assert.equal(f.state().receipt.receipt_id, receipt.receipt_id);
  assert.equal('events' in f.state().receipt, false);
  assert.equal(JSON.parse(f.calls.at(-1).options.body).events[0].text, '  exact prompt\n');
});

test('updates a streaming assistant turn without erasing repeated user messages', async () => {
  const f = fixture();
  await start(f.controller);
  const first = event('same');
  await f.controller.append(7, 'document-1', first);
  await f.controller.append(7, 'document-1', first); // Transport retry is idempotent.
  await f.controller.append(7, 'document-1', event('same'));
  const answer = { ...event('part'), role: 'assistant' };
  await f.controller.append(7, 'document-1', answer);
  await f.controller.append(7, 'document-1', { ...answer, text: 'complete' });
  assert.deepEqual(f.state().session.events.map(e => e.text), ['same', 'same', 'complete']);
});

test('rejects oversized data without changing the persisted snapshot', async () => {
  const f = fixture();
  await start(f.controller);
  const before = structuredClone(f.state());
  await assert.rejects(f.controller.append(7, 'document-1', event('x'.repeat(100001))));
  assert.deepEqual(f.state(), before);
});

test('cannot record until activation is acknowledged, and interrupted capture stays partial', async () => {
  const f = fixture();
  await f.controller.start({ tabId: 7, origin: 'https://chatgpt.com', documentNonce: 'document-1', provider: 'chatgpt', consent: true, key: 'setup-key', protocol: 'research-v1' });
  assert.equal(f.state().session.phase, 'starting');
  await assert.rejects(f.controller.append(7, 'document-1', event()));
  await f.controller.activate(7, 'document-1');
  await f.controller.append(7, 'document-1', event());
  await f.controller.pause(7, 'document-1');
  await assert.rejects(f.controller.append(7, 'document-1', event()));
  await f.controller.freeze('complete');
  assert.equal(f.state().session.batch.capture_status, 'interrupted');
});

test('restart and failed receipt persistence retain the frozen batch for retry', async () => {
  const f = fixture();
  await start(f.controller);
  await f.controller.append(7, 'document-1', event());
  await f.controller.freeze('complete');
  const original = structuredClone(f.state());
  const restarted = f.recreate();
  f.rejectReceiptWrite(true);
  await assert.rejects(restarted.upload());
  assert.deepEqual(f.state(), original);
  f.rejectReceiptWrite(false);
  assert.equal((await restarted.upload()).receipt_id, 'r'.repeat(32));
});

test('invalid acknowledgements never clear local text or display a saved receipt', async () => {
  const f = fixture();
  await start(f.controller);
  await f.controller.append(7, 'document-1', event());
  await f.controller.freeze('complete');
  const original = structuredClone(f.state());
  f.badReceipt(true);
  await assert.rejects(f.controller.upload());
  assert.deepEqual(f.state(), original);
});

test('discard deletes the capability-scoped record and restores idle state', async () => {
  const f = fixture();
  await start(f.controller);
  const id = f.state().session.id;
  await f.controller.discard();
  assert.equal(f.state().session, null);
  assert.equal(f.calls.at(-1).path, `/sessions/${id}`);
  assert.equal(f.calls.at(-1).options.method, 'DELETE');
});

test('offline withdrawal clears raw local text immediately but retains deletion capability', async () => {
  const f = fixture();
  await start(f.controller);
  await f.controller.append(7, 'document-1', event());
  await f.controller.freeze('complete');
  f.fail(true);
  await assert.rejects(f.controller.discard());
  assert.equal(f.state().withdrawing, true);
  assert.deepEqual(f.state().session.events, []);
  assert.equal('batch' in f.state().session, false);
  await assert.rejects(f.controller.freeze('complete'));
  await assert.rejects(f.controller.append(7, 'document-1', event()));
  f.fail(false);
  await f.controller.discard();
  assert.equal(f.state().session, null);
});

test('records one deduplicated incident per unresolved failure and rejects foreign senders', async () => {
  const f = fixture();
  await start(f.controller);
  const first = await f.controller.incident(7, 'document-1', 'send_blocked');
  const second = await f.controller.incident(7, 'document-1', 'send_blocked');
  assert.equal(second.incident.id, first.incident.id);
  assert.match(first.incident.message, /se bloque/);
  assert.equal(f.state().incident.id, first.incident.id);
  await assert.rejects(f.controller.incident(8, 'document-1', 'send_blocked'));
  await assert.rejects(f.controller.incident(7, 'other-document', 'send_blocked'));
  await assert.rejects(f.controller.incident(7, 'document-1', 'unknown_code'));
});

test('a successful send resolves the incident and a later failure gets a new identity', async () => {
  const f = fixture();
  await start(f.controller);
  const first = await f.controller.incident(7, 'document-1', 'send_blocked');
  await f.controller.append(7, 'document-1', event());
  assert.equal(f.state().incident, null);
  const second = await f.controller.incident(7, 'document-1', 'send_blocked');
  assert.notEqual(second.incident.id, first.incident.id);
});

test('an interruption keeps a discoverable reason and a closed tab pauses capture', async () => {
  const f = fixture();
  await start(f.controller);
  await f.controller.append(7, 'document-1', event());
  assert.deepEqual(await f.controller.interrupt('tab_closed', 99), { interrupted: false });
  assert.deepEqual(await f.controller.interrupt('tab_closed', 7), { interrupted: true });
  assert.equal(f.state().session.phase, 'paused');
  assert.equal(f.state().session.pausedReason, 'tab_closed');
  await f.controller.freeze('complete');
  assert.equal(f.state().session.batch.capture_status, 'interrupted');
});

test('a failed operation stays discoverable until a later success clears it', async () => {
  const f = fixture();
  await start(f.controller);
  await f.controller.append(7, 'document-1', event());
  await f.controller.freeze('complete');
  f.fail(true);
  await assert.rejects(f.controller.upload());
  await f.controller.fail('No se pudo conectar con la API de investigación.');
  assert.match(f.state().lastError, /No se pudo conectar/);
  f.fail(false);
  await f.controller.upload();
  assert.equal(f.state().lastError, null);
});

test('every persisted change notifies the indicator sync', async () => {
  const f = fixture();
  await start(f.controller);
  assert.equal(f.seen[0].session.phase, 'starting');
  assert.equal(f.seen.at(-1).session.phase, 'recording');
});
