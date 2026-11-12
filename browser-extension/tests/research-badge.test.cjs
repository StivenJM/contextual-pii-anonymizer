const { test } = require('node:test');
const assert = require('node:assert/strict');
const { badgeForState, createBadgeSync, describeView } =
  require('../extension/research-background.js');

const session = (phase, tabId = 7) => ({
  session: { phase, tabId, events: [] }
});

function fakeApi() {
  const calls = [];
  const action = {};
  for (const method of ['setBadgeText', 'setBadgeBackgroundColor', 'setTitle']) {
    action[method] = async details => calls.push({ method, ...details });
  }
  return {
    calls,
    api: { action, tabs: { query: async () => [{ id: 3 }, { id: 9 }] } }
  };
}

test('badge text follows the persisted phase and stays empty when nothing is pending', () => {
  assert.equal(badgeForState({}).text, '');
  assert.equal(badgeForState({ receipt: { receipt_id: 'r'.repeat(32) } }).text, '');
  assert.equal(badgeForState(session('starting')).text, '…');
  assert.equal(badgeForState(session('recording')).text, 'REC');
  assert.equal(badgeForState(session('paused')).text, '!');
  assert.equal(badgeForState(session('pending')).text, 'PEND');
  assert.equal(badgeForState({ withdrawing: true }).text, '!');
});

test('REC belongs to the captured tab and never claims another tab is recording', () => {
  const badge = badgeForState(session('recording', 42));
  assert.equal(badge.tabId, 42);
  assert.equal(badge.text, 'REC');
  assert.match(badge.title, /Captura activa/);

  const sync = createBadgeSync;
  assert.equal(typeof sync, 'function');
});

test('a blocking incident outranks a healthy capture and keeps attention visible', () => {
  const badge = badgeForState({
    ...session('recording', 42),
    incident: { id: 'incident-1', code: 'send_blocked' }
  });
  assert.equal(badge.text, '!');
  assert.equal(badge.tabId, null);
  assert.match(badge.title, /necesita atención/);
});

test('pending and withdrawal stay global so they survive switching or closing the tab', () => {
  for (const phase of ['pending', 'withdrawing']) {
    const badge = badgeForState(session(phase, 42));
    assert.equal(badge.tabId, null, phase);
    assert.notEqual(badge.text, '', phase);
  }
});

test('titles describe the state with words instead of relying on colour', () => {
  for (const badge of [
    badgeForState({}),
    badgeForState(session('starting')),
    badgeForState(session('recording')),
    badgeForState(session('paused')),
    badgeForState(session('pending'))
  ]) {
    assert.ok(badge.title.length > 8);
    assert.equal(/^#[0-9a-f]{6}$/.test(badge.color), true);
  }
});

test('sync keeps a per-tab REC label, then clears it when the phase changes', async () => {
  const { api, calls } = fakeApi();
  const sync = createBadgeSync(api);
  await sync(session('recording', 42));
  assert.deepEqual(
    calls.filter(call => call.method === 'setBadgeText' && call.tabId === 42).at(-1),
    { method: 'setBadgeText', tabId: 42, text: 'REC' }
  );
  assert.deepEqual(
    calls.filter(call => call.method === 'setBadgeText' && call.tabId === undefined).at(-1),
    { method: 'setBadgeText', text: '' }
  );

  calls.length = 0;
  await sync(session('pending', 42));
  assert.deepEqual(calls[0], { method: 'setBadgeText', tabId: 42, text: '' });
  assert.deepEqual(
    calls.filter(call => call.method === 'setBadgeText' && call.tabId === undefined).at(-1),
    { method: 'setBadgeText', text: 'PEND' }
  );
});

test('sync clears labels left on chat tabs by a previous service-worker lifetime', async () => {
  const { api, calls } = fakeApi();
  const sync = createBadgeSync(api);
  await sync({});
  const cleared = calls.filter(call => call.method === 'setBadgeText' && call.tabId !== undefined);
  assert.deepEqual(cleared.map(call => call.tabId), [3, 9]);
  assert.ok(cleared.every(call => call.text === ''));
});

test('describeView maps the persisted session to a single popup state', () => {
  assert.equal(describeView({}), 'idle');
  assert.equal(describeView({ receipt: { receipt_id: 'x' } }), 'saved');
  assert.equal(describeView({ withdrawing: true }), 'withdrawing');
  assert.equal(describeView(session('starting')), 'starting');
  assert.equal(describeView(session('recording')), 'recording');
  assert.equal(describeView(session('paused')), 'interrupted');
  assert.equal(describeView(session('pending')), 'pending');
});
