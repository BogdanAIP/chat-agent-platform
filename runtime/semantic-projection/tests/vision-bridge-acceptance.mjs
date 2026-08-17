import assert from 'node:assert/strict';
import http from 'node:http';
import path from 'node:path';
import process from 'node:process';
import { createRequire } from 'node:module';

import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

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

async function startFixtureServer() {
  const server = http.createServer((_request, response) => {
    response.setHeader('Content-Type', 'text/html; charset=utf-8');
    response.end(`<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<title>Stage 25.1 Same Session Fixture</title>
<style>
  html, body { margin: 0; width: 100%; height: 100%; background: #f4f5f7; font-family: Arial, sans-serif; }
  #visual-target { position: absolute; left: 120px; top: 160px; width: 80px; height: 50px; background: #d32f2f; }
  #shift { position: absolute; right: 24px; top: 24px; padding: 10px 18px; }
  #status { position: absolute; left: 24px; top: 300px; font-size: 20px; }
</style>
</head>
<body>
  <div id="visual-target"></div>
  <button id="shift" type="button">Shift layout</button>
  <p id="status">WAITING</p>
<script>
  let visualClicks = 0;
  const target = document.getElementById('visual-target');
  const status = document.getElementById('status');
  target.addEventListener('click', () => {
    visualClicks += 1;
    status.textContent = 'VISUAL_CLICKED_' + visualClicks;
  });
  document.getElementById('shift').addEventListener('click', () => {
    target.style.left = '360px';
    status.textContent = 'SHIFTED';
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

const fixture = await startFixtureServer();
const client = new Client({ name: 'stage25-1-vision-bridge-acceptance', version: '1.0.0' });
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

  const inventory = await client.listTools();
  const toolNames = new Set(inventory.tools.map(tool => tool.name));
  for (const required of [
    'browser_navigate',
    'browser_find',
    'browser_snapshot',
    'browser_click',
    'browser_take_screenshot',
    'browser_mouse_click_xy'
  ]) {
    assert(toolNames.has(required), `Playwright MCP 0.0.78 vision bridge is missing ${required}.`);
  }
  console.log('VISION_BRIDGE_PLAYWRIGHT_TOOLS=PASS');

  let grounderCalls = 0;
  const bridge = new SameSessionVisualGroundingBridge({
    client,
    ttlMs: 15_000,
    grounder: async request => {
      grounderCalls += 1;
      assert.equal(request.mimeType, 'image/png');
      assert.equal(request.coordinateSpace, 'css_viewport');
      assert(Buffer.isBuffer(request.imageBytes));
      assert(request.imageBytes.length > 100);
      assert(request.width >= 400);
      assert(request.height >= 350);
      if (request.target === 'missing visual target') {
        return { status: 'abstain', reason: 'fixture-target-absent' };
      }
      assert.equal(request.target, 'red visual target');
      return {
        status: 'resolved',
        reason: 'fixture-grounder',
        bbox: { x1: 120, y1: 160, x2: 200, y2: 210 },
        point: { x: 160, y: 185 }
      };
    }
  });

  const open = await client.callTool({ name: 'browser_navigate', arguments: { url: fixture.baseUrl } });
  assert.equal(open.isError, undefined, textOf(open));

  const prepared = await bridge.prepare('red visual target');
  assert.equal(prepared.status, 'resolved');
  assert.match(prepared.token, /^visual-target:/);
  assert.equal(prepared.coordinateSpace, 'css_viewport');
  assert.deepEqual(prepared.point, { x: 160, y: 185 });

  const committed = await bridge.commitClick(prepared.token);
  assert.equal(committed.status, 'acted', JSON.stringify(committed));
  const positive = await client.callTool({ name: 'browser_find', arguments: { text: 'VISUAL_CLICKED_1' } });
  assert.equal(positive.isError, undefined, textOf(positive));
  assert(textOf(positive).includes('VISUAL_CLICKED_1'), textOf(positive));
  console.log('VISION_BRIDGE_POSITIVE=PASS');

  const replay = await bridge.commitClick(prepared.token);
  assert.equal(replay.status, 'abstain');
  assert.equal(replay.reason, 'unknown-or-consumed-visual-target');
  const afterReplay = await client.callTool({ name: 'browser_snapshot', arguments: {} });
  assert(textOf(afterReplay).includes('VISUAL_CLICKED_1'), textOf(afterReplay));
  assert(!textOf(afterReplay).includes('VISUAL_CLICKED_2'), textOf(afterReplay));
  console.log('VISION_BRIDGE_REPLAY_GUARD=PASS');

  const reopen = await client.callTool({ name: 'browser_navigate', arguments: { url: fixture.baseUrl } });
  assert.equal(reopen.isError, undefined, textOf(reopen));

  const stalePrepared = await bridge.prepare('red visual target');
  assert.equal(stalePrepared.status, 'resolved');

  const findShift = await client.callTool({ name: 'browser_find', arguments: { text: 'Shift layout' } });
  assert.equal(findShift.isError, undefined, textOf(findShift));
  const shiftRef = refOnMatchingLine(findShift, 'Shift layout');
  const shift = await client.callTool({
    name: 'browser_click',
    arguments: { target: shiftRef, element: 'Shift layout button' }
  });
  assert.equal(shift.isError, undefined, textOf(shift));
  const shiftedBeforeCommit = await client.callTool({ name: 'browser_find', arguments: { text: 'SHIFTED' } });
  assert.equal(shiftedBeforeCommit.isError, undefined, textOf(shiftedBeforeCommit));

  const staleCommit = await bridge.commitClick(stalePrepared.token);
  assert.equal(staleCommit.status, 'abstain', JSON.stringify(staleCommit));
  assert.equal(staleCommit.reason, 'stale-visual-capture');
  assert.notEqual(staleCommit.preparedSha256, staleCommit.currentSha256);

  const staleSnapshot = await client.callTool({ name: 'browser_snapshot', arguments: {} });
  const staleText = textOf(staleSnapshot);
  assert(staleText.includes('SHIFTED'), staleText);
  assert(!staleText.includes('VISUAL_CLICKED'), staleText);
  console.log('VISION_BRIDGE_STALE_ABSTAIN=PASS');

  const missing = await bridge.prepare('missing visual target');
  assert.equal(missing.status, 'abstain');
  assert.equal(missing.reason, 'fixture-target-absent');
  assert.equal(grounderCalls, 3);
  console.log('VISION_BRIDGE_GROUNDER_ABSTAIN=PASS');

  console.log('VISION_BRIDGE_ACCEPTANCE=PASS');
} finally {
  await client.close().catch(() => {});
  await closeHttpServer(fixture.server).catch(() => {});
}
