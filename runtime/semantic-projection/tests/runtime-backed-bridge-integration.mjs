import assert from 'node:assert/strict';
import http from 'node:http';
import path from 'node:path';
import process from 'node:process';
import { createRequire } from 'node:module';

import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

import { createRuntimeBackedBridgeGrounder } from '../lib/runtime-backed-bridge-grounder.mjs';
import { SameSessionVisualGroundingBridge } from '../lib/visual-grounding-bridge.mjs';

const require = createRequire(import.meta.url);
const playwrightManifest = require.resolve('@playwright/mcp/package.json');
const playwrightEntry = path.join(path.dirname(playwrightManifest), 'cli.js');

function textOf(result) {
  return (result?.content ?? [])
    .filter(block => block?.type === 'text' && typeof block.text === 'string')
    .map(block => block.text)
    .join('\n');
}

function refOnMatchingLine(result, needle) {
  const text = textOf(result);
  for (const line of text.split(/\r?\n/)) {
    if (!line.includes(needle)) continue;
    const match = line.match(/\[ref=([^\]\s]+)\]/) ?? line.match(/\bref=([A-Za-z0-9_-]+)\b/);
    if (match) return match[1];
  }
  assert.fail(`Could not resolve a Playwright ref for ${JSON.stringify(needle)}:\n${text}`);
}

async function clickSemantic(client, label) {
  const found = await client.callTool({ name: 'browser_find', arguments: { text: label } });
  assert.equal(found.isError, undefined, textOf(found));
  const ref = refOnMatchingLine(found, label);
  const clicked = await client.callTool({
    name: 'browser_click',
    arguments: { target: ref, element: `${label} button` }
  });
  assert.equal(clicked.isError, undefined, textOf(clicked));
}

async function startFixtureServer() {
  const server = http.createServer((_request, response) => {
    response.setHeader('Content-Type', 'text/html; charset=utf-8');
    response.end(`<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<title>Runtime-backed Bridge Integration</title>
<style>
  html, body { margin: 0; width: 100%; min-height: 800px; background: #f6f7f8; font-family: Arial, sans-serif; }
  #visual-target { position: absolute; left: 120px; top: 160px; width: 80px; height: 50px; background: #d32f2f; }
  #shift { position: absolute; right: 24px; top: 24px; padding: 8px 16px; }
  #status { position: absolute; left: 24px; top: 300px; font-size: 20px; }
</style>
</head>
<body>
  <div id="visual-target"></div>
  <button id="shift" type="button">Shift layout</button>
  <p id="status">WAITING</p>
<script>
  const target = document.getElementById('visual-target');
  const status = document.getElementById('status');
  target.addEventListener('click', () => { status.textContent = 'RUNTIME_BRIDGE_CLICKED'; });
  document.getElementById('shift').addEventListener('click', () => {
    target.style.left = '360px';
    status.textContent = 'SHIFTED_DURING_GROUNDING';
  });
</script>
</body>
</html>`);
  });

  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  const address = server.address();
  assert(address && typeof address === 'object');
  return { server, baseUrl: `http://127.0.0.1:${address.port}/` };
}

async function closeHttpServer(server) {
  await new Promise((resolve, reject) => server.close(error => (error ? reject(error) : resolve())));
}

function childEnvironment() {
  const env = {};
  for (const [key, value] of Object.entries(process.env)) {
    if (typeof value === 'string') env[key] = value;
  }
  return env;
}

async function openBase(client, fixture) {
  const result = await client.callTool({ name: 'browser_navigate', arguments: { url: fixture.baseUrl } });
  assert.equal(result.isError, undefined, textOf(result));
}

async function snapshotText(client) {
  const snapshot = await client.callTool({ name: 'browser_snapshot', arguments: {} });
  assert.equal(snapshot.isError, undefined, textOf(snapshot));
  return textOf(snapshot);
}

const fixture = await startFixtureServer();
const client = new Client({ name: 'runtime-backed-bridge-integration', version: '1.0.0' });
const transport = new StdioClientTransport({
  command: process.execPath,
  args: [
    playwrightEntry,
    '--headless',
    '--browser',
    'chrome',
    '--isolated',
    '--image-responses',
    'allow',
    '--block-service-workers',
    '--codegen',
    'none',
    '--caps',
    'vision',
    '--timeout-action',
    '15000'
  ],
  env: childEnvironment()
});

try {
  await client.connect(transport);

  let runnerCalls = 0;
  const fakeRuntimeBackedRunner = {
    async ground(request) {
      runnerCalls += 1;
      assert(Buffer.isBuffer(request.imageBytes));
      assert.equal(request.mimeType, 'image/png');
      assert.equal(request.coordinateSpace, 'css_viewport');
      assert(request.width >= 400);
      assert(request.height >= 350);
      assert.equal(request.kind, 'icon_only');
      assert.equal(request.targetText, null);
      assert.equal(Object.prototype.hasOwnProperty.call(request, 'port'), false);
      assert.equal(Object.prototype.hasOwnProperty.call(request, 'modelPath'), false);

      if (request.instruction === 'locate missing visual target') {
        return { status: 'abstain', reason: 'fake-runtime-target-absent' };
      }
      if (request.instruction === 'simulate runtime failure') {
        throw new Error('fake-runtime-unavailable');
      }
      if (request.instruction === 'locate target while page changes') {
        await clickSemantic(client, 'Shift layout');
      } else {
        assert.equal(request.instruction, 'locate red visual target');
      }
      return {
        status: 'resolved',
        reason: 'fake-runtime-resolved',
        bbox: { x1: 120, y1: 160, x2: 200, y2: 210 },
        point: { x: 160, y: 185 }
      };
    }
  };

  const bridge = new SameSessionVisualGroundingBridge({
    client,
    ttlMs: 15_000,
    grounder: createRuntimeBackedBridgeGrounder(fakeRuntimeBackedRunner)
  });

  const structured = (instruction) => ({
    target: 'red visual target',
    instruction,
    kind: 'icon_only',
    targetText: null
  });

  // Happy path: structured internal target reaches the runtime-backed adapter,
  // remains fresh, then commits exactly one same-session coordinate action.
  await openBase(client, fixture);
  const prepared = await bridge.prepare(structured('locate red visual target'));
  assert.equal(prepared.status, 'resolved', JSON.stringify(prepared));
  const committed = await bridge.commitClick(prepared.token);
  assert.equal(committed.status, 'acted', JSON.stringify(committed));
  const positiveText = await snapshotText(client);
  assert(positiveText.includes('RUNTIME_BRIDGE_CLICKED'), positiveText);
  console.log('RUNTIME_BRIDGE_INTEGRATION_RESOLVED_CLICK=PASS');

  // Grounder ABSTAIN never creates an actionable token or a click.
  await openBase(client, fixture);
  const missing = await bridge.prepare(structured('locate missing visual target'));
  assert.equal(missing.status, 'abstain', JSON.stringify(missing));
  assert.equal(missing.reason, 'fake-runtime-target-absent');
  const missingText = await snapshotText(client);
  assert(missingText.includes('WAITING'), missingText);
  assert(!missingText.includes('RUNTIME_BRIDGE_CLICKED'), missingText);
  console.log('RUNTIME_BRIDGE_INTEGRATION_ABSTAIN_NO_ACTION=PASS');

  // Runtime/provider error is converted by the bridge to a non-authorizing error.
  await openBase(client, fixture);
  const failed = await bridge.prepare(structured('simulate runtime failure'));
  assert.equal(failed.status, 'error', JSON.stringify(failed));
  assert(failed.reason.includes('grounder-error:fake-runtime-unavailable'), failed.reason);
  const failedText = await snapshotText(client);
  assert(failedText.includes('WAITING'), failedText);
  assert(!failedText.includes('RUNTIME_BRIDGE_CLICKED'), failedText);
  console.log('RUNTIME_BRIDGE_INTEGRATION_RUNTIME_ERROR_NO_ACTION=PASS');

  // If the page changes while the runtime-backed grounder is computing, the
  // returned coordinate is still non-authorizing at commit time.
  await openBase(client, fixture);
  const stalePrepared = await bridge.prepare(structured('locate target while page changes'));
  assert.equal(stalePrepared.status, 'resolved', JSON.stringify(stalePrepared));
  const staleCommit = await bridge.commitClick(stalePrepared.token);
  assert.equal(staleCommit.status, 'abstain', JSON.stringify(staleCommit));
  assert.equal(staleCommit.reason, 'stale-visual-capture');
  const staleText = await snapshotText(client);
  assert(staleText.includes('SHIFTED_DURING_GROUNDING'), staleText);
  assert(!staleText.includes('RUNTIME_BRIDGE_CLICKED'), staleText);
  console.log('RUNTIME_BRIDGE_INTEGRATION_STALE_DURING_GROUNDING=PASS');

  await assert.rejects(
    bridge.prepare({
      ...structured('locate red visual target'),
      port: 9999
    }),
    /unsupported field: port/
  );
  console.log('RUNTIME_BRIDGE_INTEGRATION_STRUCTURED_TARGET_STRICT=PASS');

  assert.equal(runnerCalls, 4);
  console.log('RUNTIME_BRIDGE_INTEGRATION=PASS');
} finally {
  await client.close().catch(() => {});
  await closeHttpServer(fixture.server).catch(() => {});
}
