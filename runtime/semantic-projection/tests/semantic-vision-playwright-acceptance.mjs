import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import process from 'node:process';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';
import { SemanticVisionClickRouter, exactAccessibilityCandidates } from '../lib/semantic-vision-click-router.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const semanticRoot = path.resolve(here, '..');
const repoRoot = path.resolve(semanticRoot, '..', '..');
const fixturePath = path.join(repoRoot, 'tests', 'fixtures', 'stage25_2_semantic_vision_fixture.html');
const require = createRequire(import.meta.url);
const playwrightManifest = require.resolve('@playwright/mcp/package.json');
const playwrightEntry = path.join(path.dirname(playwrightManifest), 'cli.js');

function textOf(result) {
  return (result?.content ?? []).filter(block => block?.type === 'text' && typeof block.text === 'string').map(block => block.text).join('\n');
}

async function startFixtureServer() {
  const html = fs.readFileSync(fixturePath, 'utf8');
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

async function navigate(client, url) {
  const result = await client.callTool({ name: 'browser_navigate', arguments: { url } });
  assert.equal(result?.isError, undefined, textOf(result));
}

async function snapshot(client) {
  const result = await client.callTool({ name: 'browser_snapshot', arguments: {} });
  assert.equal(result?.isError, undefined, textOf(result));
  return result;
}

async function assertMarker(client, expected) {
  const current = textOf(await snapshot(client));
  assert(current.includes(expected), `expected marker ${expected} in snapshot:\n${current}`);
}

const fixture = await startFixtureServer();
const client = new Client({ name: 'stage25-2-semantic-vision-playwright', version: '1.0.0' });
const transport = new StdioClientTransport({
  command: process.execPath,
  args: [
    playwrightEntry,
    '--headless', '--browser', 'chrome', '--isolated',
    '--image-responses', 'allow', '--block-service-workers', '--codegen', 'none',
    '--caps', 'vision', '--viewport-size', '1280x720',
    '--timeout-action', '15000', '--timeout-navigation', '30000'
  ],
  env: { ...process.env }
});

try {
  await client.connect(transport);
  const inventory = await client.listTools();
  const names = new Set(inventory.tools.map(tool => tool.name));
  for (const required of ['browser_navigate','browser_snapshot','browser_click','browser_take_screenshot','browser_mouse_click_xy']) {
    assert(names.has(required), `missing Playwright MCP tool ${required}`);
  }

  await navigate(client, fixture.url);
  const initial = await snapshot(client);
  assert.equal(exactAccessibilityCandidates(initial, 'Save').length, 1);
  assert.equal(exactAccessibilityCandidates(initial, 'Launch').length, 0);
  assert.equal(exactAccessibilityCandidates(initial, 'Delete').length, 2);
  const sendCandidates = exactAccessibilityCandidates(initial, 'Send');
  assert.equal(sendCandidates.length, 2);
  assert.equal(sendCandidates.filter(candidate => candidate.disabled).length, 1);
  console.log('SEMANTIC_VISION_REAL_SNAPSHOT_CLASSIFICATION=PASS');

  let grounderCalls = 0;
  const router = new SemanticVisionClickRouter({
    client,
    grounder: async request => {
      grounderCalls += 1;
      assert.equal(request.kind, 'labeled_button');
      assert.equal(request.targetText, 'Launch');
      assert.equal(request.width, 1280);
      assert.equal(request.height, 720);
      return {
        status: 'resolved', reason: 'fixture-grounder', point: { x: 600, y: 330 },
        bbox: { x1: 500, y1: 300, x2: 700, y2: 360 }
      };
    }
  });

  await navigate(client, fixture.url);
  const semantic = await router.click({
    target: 'stale-ref-not-used',
    visualFallback: { targetText: 'Save', instruction: 'click the Save button' }
  });
  assert.equal(semantic.status, 'acted');
  assert.equal(semantic.source, 'semantic');
  assert.equal(grounderCalls, 0);
  await assertMarker(client, 'CLICKED:semantic-save');
  console.log('SEMANTIC_VISION_REAL_SEMANTIC_FIRST=PASS');

  await navigate(client, fixture.url);
  const state = await router.click({
    visualFallback: { targetText: 'Send', instruction: 'click the enabled Send button' }
  });
  assert.equal(state.status, 'acted');
  assert.equal(state.source, 'semantic');
  assert.equal(state.reason, 'semantic-unique-enabled-button-state');
  assert.equal(grounderCalls, 0);
  await assertMarker(client, 'CLICKED:send-enabled');
  console.log('SEMANTIC_VISION_REAL_STATE_DISAMBIGUATION=PASS');

  await navigate(client, fixture.url);
  const visual = await router.click({
    visualFallback: { targetText: 'Launch', instruction: 'click the visible Launch control' }
  });
  assert.equal(visual.status, 'acted');
  assert.equal(visual.source, 'vision');
  assert.equal(grounderCalls, 1);
  await assertMarker(client, 'CLICKED:visual-launch');
  console.log('SEMANTIC_VISION_REAL_SAME_SESSION_FALLBACK=PASS');

  await navigate(client, fixture.url);
  const ambiguousCallsBefore = grounderCalls;
  const ambiguous = await router.click({
    visualFallback: { targetText: 'Delete', instruction: 'click Delete' }
  });
  assert.equal(ambiguous.status, 'abstain');
  assert.equal(ambiguous.reason, 'semantic-ambiguity-visual-escalation-not-promoted');
  assert.equal(grounderCalls, ambiguousCallsBefore);
  const ambiguousSnapshot = textOf(await snapshot(client));
  assert(!ambiguousSnapshot.includes('CLICKED:delete-a'));
  assert(!ambiguousSnapshot.includes('CLICKED:delete-b'));
  console.log('SEMANTIC_VISION_REAL_AMBIGUITY_NO_ACTION=PASS');

  console.log('SEMANTIC_VISION_PLAYWRIGHT_ACCEPTANCE=PASS');
} finally {
  await client.close().catch(() => {});
  await new Promise(resolve => fixture.server.close(() => resolve()));
}
