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
  const server = http.createServer((request, response) => {
    response.setHeader('Content-Type', 'text/html; charset=utf-8');

    if (request.url?.startsWith('/replacement')) {
      response.end(`<!doctype html>
<html>
<head><meta charset="utf-8" /><title>Replacement Page</title></head>
<body style="margin:0;background:#ddeeff;font-family:Arial,sans-serif">
  <h1>REPLACEMENT_PAGE</h1>
  <p>The original visual target is not present on this page.</p>
</body>
</html>`);
      return;
    }

    response.end(`<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<title>Stage 25.1 Same Session Fixture</title>
<style>
  html, body { margin: 0; width: 100%; min-height: 1400px; background: #f4f5f7; font-family: Arial, sans-serif; }
  #visual-target { position: absolute; left: 120px; top: 160px; width: 80px; height: 50px; background: #d32f2f; }
  .control { position: absolute; right: 24px; padding: 8px 16px; }
  #shift { top: 24px; }
  #scroll { top: 70px; }
  #overlay { top: 116px; }
  #status { position: absolute; left: 24px; top: 300px; font-size: 20px; }
  #lower-marker { position: absolute; left: 24px; top: 720px; font-size: 20px; }
  .blocking-overlay { position: fixed; left: 90px; top: 130px; width: 150px; height: 120px; background: rgba(20,20,20,.92); color: white; z-index: 99; }
</style>
</head>
<body>
  <div id="visual-target"></div>
  <button class="control" id="shift" type="button">Shift layout</button>
  <button class="control" id="scroll" type="button">Scroll viewport</button>
  <button class="control" id="overlay" type="button">Show overlay</button>
  <p id="status">WAITING</p>
  <p id="lower-marker">LOWER_CONTENT</p>
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
  document.getElementById('scroll').addEventListener('click', () => {
    status.textContent = 'SCROLLED';
    window.scrollTo(0, 220);
  });
  document.getElementById('overlay').addEventListener('click', () => {
    const blocker = document.createElement('div');
    blocker.className = 'blocking-overlay';
    blocker.textContent = 'OVERLAY_BLOCKING_TARGET';
    document.body.appendChild(blocker);
    status.textContent = 'OVERLAY_SHOWN';
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
  const open = await client.callTool({ name: 'browser_navigate', arguments: { url: fixture.baseUrl } });
  assert.equal(open.isError, undefined, textOf(open));
}

async function assertNoVisualClick(client, expectedMarker) {
  const snapshot = await client.callTool({ name: 'browser_snapshot', arguments: {} });
  const text = textOf(snapshot);
  if (expectedMarker) assert(text.includes(expectedMarker), text);
  assert(!text.includes('VISUAL_CLICKED'), text);
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
      if (request.target === 'ambiguous repeated visual target') {
        return { status: 'abstain', reason: 'fixture-target-ambiguous' };
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

  // Positive: unchanged screenshot in the same Playwright session authorizes exactly one click.
  await openBase(client, fixture);
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

  // Prepared targets are one-shot; replay cannot cause a second click.
  const replay = await bridge.commitClick(prepared.token);
  assert.equal(replay.status, 'abstain');
  assert.equal(replay.reason, 'unknown-or-consumed-visual-target');
  const afterReplay = await client.callTool({ name: 'browser_snapshot', arguments: {} });
  assert(textOf(afterReplay).includes('VISUAL_CLICKED_1'), textOf(afterReplay));
  assert(!textOf(afterReplay).includes('VISUAL_CLICKED_2'), textOf(afterReplay));
  console.log('VISION_BRIDGE_REPLAY_GUARD=PASS');

  // Layout shift invalidates the exact prepared frame.
  await openBase(client, fixture);
  const layoutPrepared = await bridge.prepare('red visual target');
  assert.equal(layoutPrepared.status, 'resolved');
  await clickSemantic(client, 'Shift layout');
  const layoutCommit = await bridge.commitClick(layoutPrepared.token);
  assert.equal(layoutCommit.status, 'abstain', JSON.stringify(layoutCommit));
  assert.equal(layoutCommit.reason, 'stale-visual-capture');
  assert.notEqual(layoutCommit.preparedSha256, layoutCommit.currentSha256);
  await assertNoVisualClick(client, 'SHIFTED');
  console.log('VISION_BRIDGE_LAYOUT_SHIFT_ABSTAIN=PASS');

  // Scroll changes CSS viewport contents and invalidates the prepared visual target.
  await openBase(client, fixture);
  const scrollPrepared = await bridge.prepare('red visual target');
  assert.equal(scrollPrepared.status, 'resolved');
  await clickSemantic(client, 'Scroll viewport');
  const scrollCommit = await bridge.commitClick(scrollPrepared.token);
  assert.equal(scrollCommit.status, 'abstain', JSON.stringify(scrollCommit));
  assert.equal(scrollCommit.reason, 'stale-visual-capture');
  assert.notEqual(scrollCommit.preparedSha256, scrollCommit.currentSha256);
  await assertNoVisualClick(client, 'SCROLLED');
  console.log('VISION_BRIDGE_SCROLL_ABSTAIN=PASS');

  // A newly introduced overlay invalidates the prepared target before it can be clicked.
  await openBase(client, fixture);
  const overlayPrepared = await bridge.prepare('red visual target');
  assert.equal(overlayPrepared.status, 'resolved');
  await clickSemantic(client, 'Show overlay');
  const overlayCommit = await bridge.commitClick(overlayPrepared.token);
  assert.equal(overlayCommit.status, 'abstain', JSON.stringify(overlayCommit));
  assert.equal(overlayCommit.reason, 'stale-visual-capture');
  assert.notEqual(overlayCommit.preparedSha256, overlayCommit.currentSha256);
  await assertNoVisualClick(client, 'OVERLAY_SHOWN');
  console.log('VISION_BRIDGE_OVERLAY_ABSTAIN=PASS');

  // Navigation/page replacement cannot reuse a target prepared on the previous page.
  await openBase(client, fixture);
  const navigationPrepared = await bridge.prepare('red visual target');
  assert.equal(navigationPrepared.status, 'resolved');
  const replacement = await client.callTool({
    name: 'browser_navigate',
    arguments: { url: `${fixture.baseUrl}replacement` }
  });
  assert.equal(replacement.isError, undefined, textOf(replacement));
  const navigationCommit = await bridge.commitClick(navigationPrepared.token);
  assert.equal(navigationCommit.status, 'abstain', JSON.stringify(navigationCommit));
  assert.equal(navigationCommit.reason, 'stale-visual-capture');
  assert.notEqual(navigationCommit.preparedSha256, navigationCommit.currentSha256);
  await assertNoVisualClick(client, 'REPLACEMENT_PAGE');
  console.log('VISION_BRIDGE_NAVIGATION_ABSTAIN=PASS');

  // Grounder uncertainty never produces an actionable token.
  await openBase(client, fixture);
  const missing = await bridge.prepare('missing visual target');
  assert.equal(missing.status, 'abstain');
  assert.equal(missing.reason, 'fixture-target-absent');
  await assertNoVisualClick(client, 'WAITING');
  console.log('VISION_BRIDGE_GROUNDER_ABSTAIN=PASS');

  const ambiguous = await bridge.prepare('ambiguous repeated visual target');
  assert.equal(ambiguous.status, 'abstain');
  assert.equal(ambiguous.reason, 'fixture-target-ambiguous');
  await assertNoVisualClick(client, 'WAITING');
  console.log('VISION_BRIDGE_AMBIGUOUS_ABSTAIN=PASS');

  assert.equal(grounderCalls, 7);
  console.log('VISION_BRIDGE_ADVERSARIAL_STALE_STATE=PASS');
  console.log('VISION_BRIDGE_ACCEPTANCE=PASS');
} finally {
  await client.close().catch(() => {});
  await closeHttpServer(fixture.server).catch(() => {});
}
