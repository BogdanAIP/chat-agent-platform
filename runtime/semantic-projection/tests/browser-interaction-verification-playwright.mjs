import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';
import { parsePlaywrightSnapshotResult } from '../lib/browser-verification-bridge.mjs';


const here = path.dirname(fileURLToPath(import.meta.url));
const entry = path.resolve(here, '..', 'bin', 'semantic-projection.mjs');

function textOf(result) {
  return (result?.content ?? [])
    .filter(block => block?.type === 'text' && typeof block.text === 'string')
    .map(block => block.text)
    .join('\n');
}

function childEnvironment(extra) {
  const env = {};
  for (const [key, value] of Object.entries(process.env)) {
    if (typeof value === 'string') env[key] = value;
  }
  return { ...env, ...extra };
}

async function startFixtureServer() {
  const html = `<!doctype html>
<html>
<head><meta charset="utf-8"><title>Interaction verification fixture</title></head>
<body>
  <label for="name">Name</label>
  <input id="name" type="text" value="OLD">

  <label for="agree">Agree</label>
  <input id="agree" type="checkbox">

  <button id="remove" type="button" onclick="this.remove(); document.getElementById('status').textContent='REMOVED_OK'">Remove me</button>
  <button id="unsafe" type="button" onclick="document.getElementById('status').textContent='NO_EXPECTED_CLICKED'">Needs expectation</button>
  <p id="status">SAFE</p>
</body>
</html>`;
  const server = http.createServer((_request, response) => {
    response.setHeader('Content-Type', 'text/html; charset=utf-8');
    response.end(html);
  });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  const address = server.address();
  assert(address && typeof address === 'object');
  return { server, url: `http://127.0.0.1:${address.port}/` };
}

async function observe(client) {
  const result = await client.callTool({
    name: 'web_observe',
    arguments: { operation: 'snapshot' },
  });
  assert.equal(result?.isError, undefined, textOf(result));
  return { result, parsed: parsePlaywrightSnapshotResult(result) };
}

function controlByName(parsed, name) {
  const matches = parsed.controls.filter(control => control.name === name);
  assert.equal(matches.length, 1, `expected one control named ${name}, got ${matches.length}`);
  return matches[0];
}

function assertVerifiedPass(result, label) {
  assert.equal(result?.isError, undefined, `${label}: ${textOf(result)}`);
  assert.equal(result?.structuredContent?.browser_verification?.status, 'pass', `${label}: ${textOf(result)}`);
}

const fixture = await startFixtureServer();
const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-browser-interaction-workspace-'));
const client = new Client({ name: 'browser-interaction-verification-playwright', version: '1.0.0' });
const transport = new StdioClientTransport({
  command: process.execPath,
  args: [entry],
  env: childEnvironment({ CHAT_LOCAL_FILES_ROOT: workspace }),
});

try {
  await client.connect(transport);
  const inventory = await client.listTools();
  const interact = inventory.tools.find(tool => tool.name === 'web_interact');
  assert(interact, 'web_interact missing');
  assert(interact.inputSchema?.properties?.expected, 'web_interact expected postcondition schema missing');

  const opened = await client.callTool({ name: 'web_open', arguments: { url: fixture.url } });
  assertVerifiedPass(opened, 'web_open');

  // Type without submit derives value==text as the bounded expected result.
  let snapshot = await observe(client);
  let nameInput = controlByName(snapshot.parsed, 'Name');
  const typed = await client.callTool({
    name: 'web_interact',
    arguments: { operation: 'type', target: nameInput.control_id, element: 'Name', text: 'HELLO' },
  });
  assertVerifiedPass(typed, 'type auto-value');
  snapshot = await observe(client);
  nameInput = controlByName(snapshot.parsed, 'Name');
  assert.equal(nameInput.value, 'HELLO');
  console.log('BROWSER_INTERACTION_TYPE_VERIFY=PASS');

  // A declared checkbox state is verified against a fresh after observation.
  let agree = controlByName(snapshot.parsed, 'Agree');
  const checked = await client.callTool({
    name: 'web_interact',
    arguments: {
      operation: 'click',
      target: agree.control_id,
      element: 'Agree',
      expected: { control: { target: agree.control_id, checked: true } },
    },
  });
  assertVerifiedPass(checked, 'checkbox click');
  snapshot = await observe(client);
  agree = controlByName(snapshot.parsed, 'Agree');
  assert.equal(agree.checked, true);
  console.log('BROWSER_INTERACTION_CHECKED_VERIFY=PASS');

  // A click may prove a concrete structural effect such as disappearance.
  const remove = controlByName(snapshot.parsed, 'Remove me');
  const removed = await client.callTool({
    name: 'web_interact',
    arguments: {
      operation: 'click',
      target: remove.control_id,
      element: 'Remove me',
      expected: { control: { target: remove.control_id, present: false } },
    },
  });
  assertVerifiedPass(removed, 'remove click');
  snapshot = await observe(client);
  assert.equal(snapshot.parsed.controls.some(control => control.name === 'Remove me'), false);
  assert(textOf(snapshot.result).includes('REMOVED_OK'), textOf(snapshot.result));
  console.log('BROWSER_INTERACTION_ABSENCE_VERIFY=PASS');

  // Generic click without a declared result must be refused before delivery.
  const unsafe = controlByName(snapshot.parsed, 'Needs expectation');
  const refused = await client.callTool({
    name: 'web_interact',
    arguments: { operation: 'click', target: unsafe.control_id, element: 'Needs expectation' },
  });
  assert.equal(refused?.isError, true, textOf(refused));
  assert(textOf(refused).includes('refused action before delivery'), textOf(refused));
  snapshot = await observe(client);
  assert(!textOf(snapshot.result).includes('NO_EXPECTED_CLICKED'), textOf(snapshot.result));
  console.log('BROWSER_INTERACTION_MISSING_EXPECTED_ZERO_ACTION=PASS');

  // type+submit also needs an explicit outcome and must not type before refusal.
  nameInput = controlByName(snapshot.parsed, 'Name');
  const refusedSubmit = await client.callTool({
    name: 'web_interact',
    arguments: {
      operation: 'type', target: nameInput.control_id, element: 'Name',
      text: 'MUST_NOT_APPEAR', submit: true,
    },
  });
  assert.equal(refusedSubmit?.isError, true, textOf(refusedSubmit));
  assert(textOf(refusedSubmit).includes('refused action before delivery'), textOf(refusedSubmit));
  snapshot = await observe(client);
  nameInput = controlByName(snapshot.parsed, 'Name');
  assert.equal(nameInput.value, 'HELLO');
  console.log('BROWSER_INTERACTION_SUBMIT_MISSING_EXPECTED_ZERO_ACTION=PASS');

  // Delivery and verification are separate: deliberately request the wrong
  // postcondition. The checkbox toggles, but the tool must report verification
  // failure rather than success.
  agree = controlByName(snapshot.parsed, 'Agree');
  assert.equal(agree.checked, true);
  const mismatch = await client.callTool({
    name: 'web_interact',
    arguments: {
      operation: 'click',
      target: agree.control_id,
      element: 'Agree',
      expected: { control: { target: agree.control_id, checked: true } },
    },
  });
  assert.equal(mismatch?.isError, true, textOf(mismatch));
  assert.equal(mismatch?.structuredContent?.browser_verification?.status, 'fail', textOf(mismatch));
  snapshot = await observe(client);
  agree = controlByName(snapshot.parsed, 'Agree');
  assert.equal(agree.checked, false);
  console.log('BROWSER_INTERACTION_DELIVERY_NOT_SUCCESS=PASS');

  console.log('BROWSER_INTERACTION_VERIFICATION_PLAYWRIGHT=PASS');
} finally {
  await client.close().catch(() => {});
  fs.rmSync(workspace, { recursive: true, force: true });
  await new Promise(resolve => fixture.server.close(() => resolve()));
}
