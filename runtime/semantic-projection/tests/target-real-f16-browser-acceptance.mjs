import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import process from 'node:process';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

import { createRuntimeBackedBridgeGrounder } from '../lib/runtime-backed-bridge-grounder.mjs';
import { RuntimeBackedVisualGrounder } from '../lib/runtime-backed-visual-grounder.mjs';
import { SameSessionVisualGroundingBridge } from '../lib/visual-grounding-bridge.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const semanticRoot = path.resolve(here, '..');
const repoRoot = path.resolve(semanticRoot, '..', '..');
const fixturePath = path.join(repoRoot, 'tests', 'fixtures', 'stage25_1_runtime_grounding_fixture.html');
const casesPath = path.join(repoRoot, 'tests', 'fixtures', 'stage25_grounding_cases.json');
const require = createRequire(import.meta.url);
const playwrightManifest = require.resolve('@playwright/mcp/package.json');
const playwrightEntry = path.join(path.dirname(playwrightManifest), 'cli.js');
const expectedHitKinds = new Set(['labeled_button', 'icon_only', 'visual_state']);
const resultPath = process.env.STAGE25_1_RESULT_PATH
  ? path.resolve(process.env.STAGE25_1_RESULT_PATH)
  : null;

function progress(message) {
  process.stderr.write(`[stage25.1] ${message}\n`);
}

function textOf(result) {
  return (result?.content ?? [])
    .filter(block => block?.type === 'text' && typeof block.text === 'string')
    .map(block => block.text)
    .join('\n');
}

function childEnvironment() {
  const env = {};
  for (const [key, value] of Object.entries(process.env)) {
    if (typeof value === 'string') env[key] = value;
  }
  return env;
}

async function startFixtureServer() {
  const fixtureHtml = fs.readFileSync(fixturePath, 'utf8');
  const server = http.createServer((_request, response) => {
    response.setHeader('Content-Type', 'text/html; charset=utf-8');
    response.end(fixtureHtml);
  });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  const address = server.address();
  assert(address && typeof address === 'object');
  return { server, url: `http://127.0.0.1:${address.port}/` };
}

async function closeHttpServer(server) {
  await new Promise((resolve, reject) => server.close(error => (error ? reject(error) : resolve())));
}

function elapsedMs(started) {
  return Number(process.hrtime.bigint() - started) / 1_000_000;
}

function clickedMarkers(snapshotText) {
  return [...new Set(snapshotText.match(/CLICKED:[A-Za-z0-9_-]+/g) ?? [])].sort();
}

async function currentMarkers(client) {
  const snapshot = await client.callTool({ name: 'browser_snapshot', arguments: {} });
  if (snapshot?.isError) throw new Error(`browser_snapshot failed: ${textOf(snapshot)}`);
  return clickedMarkers(textOf(snapshot));
}

async function openFixture(client, url) {
  const opened = await client.callTool({ name: 'browser_navigate', arguments: { url } });
  if (opened?.isError) throw new Error(`browser_navigate failed: ${textOf(opened)}`);
}

function gitHead() {
  try {
    return execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repoRoot, encoding: 'utf8' }).trim();
  } catch {
    return null;
  }
}

function writeResult(payload) {
  const encoded = `${JSON.stringify(payload, null, 2)}\n`;
  if (resultPath) {
    fs.mkdirSync(path.dirname(resultPath), { recursive: true });
    fs.writeFileSync(resultPath, encoded, 'utf8');
  }
  process.stdout.write(encoded);
}

async function run() {
  const parsedCases = JSON.parse(fs.readFileSync(casesPath, 'utf8'));
  assert.deepEqual(parsedCases.viewport, { width: 1280, height: 720 });
  assert.equal(parsedCases.cases.length, 6);

  const fixture = await startFixtureServer();
  const client = new Client({ name: 'stage25-1-real-f16-browser-acceptance', version: '1.0.0' });
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
      '--viewport-size',
      '1280x720',
      '--timeout-action',
      '15000',
      '--timeout-navigation',
      '30000'
    ],
    env: childEnvironment()
  });

  const rows = [];
  try {
    progress('PLAYWRIGHT_CONNECT start');
    await client.connect(transport);
    progress('PLAYWRIGHT_CONNECT ready');
    const inventory = await client.listTools();
    const tools = new Set(inventory.tools.map(tool => tool.name));
    for (const required of ['browser_navigate', 'browser_snapshot', 'browser_take_screenshot', 'browser_mouse_click_xy']) {
      assert(tools.has(required), `Playwright MCP is missing target-acceptance tool ${required}`);
    }

    const runner = new RuntimeBackedVisualGrounder();
    const bridge = new SameSessionVisualGroundingBridge({
      client,
      grounder: createRuntimeBackedBridgeGrounder(runner),
      ttlMs: 30_000
    });

    for (let index = 0; index < parsedCases.cases.length; index += 1) {
      const testCase = parsedCases.cases[index];
      progress(`CASE ${index + 1}/6 ${testCase.id} open`);
      await openFixture(client, fixture.url);
      const expectedHit = expectedHitKinds.has(testCase.kind);
      const row = {
        case_id: testCase.id,
        kind: testCase.kind,
        target_id: testCase.target_id,
        expected: expectedHit ? 'hit' : 'abstain',
        prepare_status: null,
        prepare_reason: null,
        commit_status: null,
        commit_reason: null,
        markers: [],
        classification: null,
        false_click: false,
        error: false,
        prepare_ms: null,
        total_ms: null
      };
      const totalStarted = process.hrtime.bigint();
      const prepareStarted = process.hrtime.bigint();

      let prepared;
      try {
        progress(`CASE ${index + 1}/6 ${testCase.id} grounding-start`);
        prepared = await bridge.prepare({
          target: testCase.id,
          instruction: testCase.instruction,
          kind: testCase.kind,
          targetText: testCase.target_text
        });
        row.prepare_ms = elapsedMs(prepareStarted);
        row.prepare_status = prepared.status;
        row.prepare_reason = prepared.reason ?? null;
        progress(`CASE ${index + 1}/6 ${testCase.id} grounding-done status=${prepared.status} reason=${row.prepare_reason ?? 'none'} ms=${row.prepare_ms.toFixed(1)}`);
      } catch (error) {
        row.prepare_ms = elapsedMs(prepareStarted);
        row.prepare_status = 'exception';
        row.prepare_reason = error instanceof Error ? error.message : String(error);
        row.classification = 'error';
        row.error = true;
        row.total_ms = elapsedMs(totalStarted);
        rows.push(row);
        progress(`CASE ${index + 1}/6 ${testCase.id} exception=${row.prepare_reason}`);
        continue;
      }

      if (prepared.status === 'resolved') {
        progress(`CASE ${index + 1}/6 ${testCase.id} freshness-click-start`);
        const committed = await bridge.commitClick(prepared.token);
        row.commit_status = committed.status;
        row.commit_reason = committed.reason ?? null;
        progress(`CASE ${index + 1}/6 ${testCase.id} freshness-click-done status=${row.commit_status} reason=${row.commit_reason ?? 'none'}`);
      }

      row.markers = await currentMarkers(client);
      const expectedMarker = testCase.target_id ? `CLICKED:${testCase.target_id}` : null;

      if (expectedHit) {
        if (
          prepared.status === 'resolved' &&
          row.commit_status === 'acted' &&
          expectedMarker &&
          row.markers.length === 1 &&
          row.markers[0] === expectedMarker
        ) {
          row.classification = 'hit';
        } else if (row.commit_status === 'acted') {
          row.classification = 'false_click';
          row.false_click = true;
        } else if (prepared.status === 'error') {
          row.classification = 'error';
          row.error = true;
        } else {
          row.classification = 'safe_miss';
        }
      } else {
        if (prepared.status === 'abstain' && row.markers.length === 0) {
          row.classification = 'correct_abstain';
        } else if (row.commit_status === 'acted') {
          row.classification = 'false_click';
          row.false_click = true;
        } else {
          row.classification = 'error';
          row.error = true;
        }
      }

      row.total_ms = elapsedMs(totalStarted);
      rows.push(row);
      progress(`CASE ${index + 1}/6 ${testCase.id} done classification=${row.classification} total_ms=${row.total_ms.toFixed(1)}`);
    }
  } finally {
    progress('PLAYWRIGHT_CLOSE start');
    await client.close().catch(error => progress(`PLAYWRIGHT_CLOSE error=${error instanceof Error ? error.message : String(error)}`));
    progress('PLAYWRIGHT_CLOSE done');
    await closeHttpServer(fixture.server).catch(() => {});
  }

  const summary = {
    expected_hits: rows.filter(row => row.expected === 'hit').length,
    hits: rows.filter(row => row.classification === 'hit').length,
    expected_abstains: rows.filter(row => row.expected === 'abstain').length,
    correct_abstains: rows.filter(row => row.classification === 'correct_abstain').length,
    safe_misses: rows.filter(row => row.classification === 'safe_miss').length,
    false_clicks: rows.filter(row => row.false_click).length,
    errors: rows.filter(row => row.error).length
  };
  summary.safety_pass = summary.false_clicks === 0;
  summary.acceptance_pass =
    summary.hits === summary.expected_hits &&
    summary.correct_abstains === summary.expected_abstains &&
    summary.safe_misses === 0 &&
    summary.false_clicks === 0 &&
    summary.errors === 0;

  const output = {
    schema_version: 1,
    git_head: gitHead(),
    fixture: path.basename(fixturePath),
    viewport: parsedCases.viewport,
    runtime_profile: 'lfm25-vl-450m-f16',
    cases: rows,
    summary
  };
  progress(`SUMMARY hits=${summary.hits}/${summary.expected_hits} abstains=${summary.correct_abstains}/${summary.expected_abstains} false_clicks=${summary.false_clicks} errors=${summary.errors}`);
  writeResult(output);
  return summary.acceptance_pass ? 0 : 1;
}

try {
  process.exitCode = await run();
} catch (error) {
  progress(`FATAL ${error instanceof Error ? error.message : String(error)}`);
  writeResult({
    schema_version: 1,
    git_head: gitHead(),
    fatal_error: error instanceof Error ? error.message : String(error),
    summary: {
      safety_pass: false,
      acceptance_pass: false,
      false_clicks: 0,
      errors: 1
    }
  });
  process.exitCode = 2;
}
