import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import process from 'node:process';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

const here = path.dirname(fileURLToPath(import.meta.url));
const semanticRoot = path.resolve(here, '..');
const repoRoot = path.resolve(semanticRoot, '..', '..');
const fixturePath = path.join(repoRoot, 'tests', 'fixtures', 'stage25_2_semantic_vision_fixture.html');
const semanticEntry = path.join(semanticRoot, 'bin', 'semantic-projection-launcher.mjs');
const runtimeController = path.join(repoRoot, 'scripts', 'local-vision-runtime.ps1');
const resultPath = process.env.STAGE25_2_RESULT_PATH ? path.resolve(process.env.STAGE25_2_RESULT_PATH) : null;
const expectedTools = ['web_interact','web_observe','web_open','workspace_read','workspace_write'];

function progress(message) { process.stderr.write(`[stage25.2] ${message}\n`); }
function textOf(result) {
  return (result?.content ?? []).filter(block => block?.type === 'text' && typeof block.text === 'string').map(block => block.text).join('\n');
}
function elapsedMs(started) { return Number(process.hrtime.bigint() - started) / 1_000_000; }
function childEnvironment(extra = {}) {
  const env = {};
  for (const [key, value] of Object.entries(process.env)) if (typeof value === 'string') env[key] = value;
  return { ...env, ...extra };
}
function gitHead() {
  try { return execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repoRoot, encoding: 'utf8' }).trim(); }
  catch { return null; }
}
function runtimeStatus() {
  const command = process.platform === 'win32' ? 'pwsh.exe' : 'pwsh';
  const raw = execFileSync(command, [
    '-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass',
    '-File', runtimeController, '-Action', 'Status'
  ], { cwd: repoRoot, encoding: 'utf8', windowsHide: true });
  return JSON.parse(raw);
}
function writeResult(payload) {
  const encoded = `${JSON.stringify(payload, null, 2)}\n`;
  if (resultPath) {
    fs.mkdirSync(path.dirname(resultPath), { recursive: true });
    fs.writeFileSync(resultPath, encoded, 'utf8');
  }
  process.stdout.write(encoded);
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
async function closeServer(server) { await new Promise(resolve => server.close(() => resolve())); }
async function call(client, name, args) { return client.callTool({ name, arguments: args }); }
async function openFixture(client, url) {
  const result = await call(client, 'web_open', { url });
  if (result?.isError) throw new Error(`web_open failed: ${textOf(result)}`);
}
async function snapshotText(client) {
  const result = await call(client, 'web_observe', { operation: 'snapshot' });
  if (result?.isError) throw new Error(`web_observe snapshot failed: ${textOf(result)}`);
  return textOf(result);
}
function markers(text) { return [...new Set(text.match(/CLICKED:[A-Za-z0-9_-]+/g) ?? [])].sort(); }

const workspace = fs.mkdtempSync(path.join(process.env.TEMP ?? process.cwd(), 'stage25-2-public-'));
const fixture = await startFixtureServer();
const client = new Client({ name: 'stage25-2-real-f16-public-escalation', version: '1.0.0' });
const transport = new StdioClientTransport({
  command: process.execPath,
  args: [semanticEntry],
  env: childEnvironment({ CHAT_LOCAL_FILES_ROOT: workspace })
});

const rows = [];
try {
  progress('PUBLIC_SEMANTIC_CONNECT start');
  await client.connect(transport);
  progress('PUBLIC_SEMANTIC_CONNECT ready');
  const inventory = await client.listTools();
  const tools = inventory.tools.map(tool => tool.name).sort();
  assert.deepEqual(tools, expectedTools);
  const webInteract = inventory.tools.find(tool => tool.name === 'web_interact');
  assert(webInteract?.inputSchema?.properties?.visualFallback, 'public web_interact lacks visualFallback');

  const cases = [
    {
      id: 'semantic-unique',
      targetText: 'Save',
      instruction: 'click Save',
      expected: 'semantic_hit',
      expectedMarker: 'CLICKED:semantic-save',
      expectRuntime: false
    },
    {
      id: 'semantic-enabled-state',
      targetText: 'Send',
      instruction: 'click the enabled Send button',
      expected: 'semantic_hit',
      expectedMarker: 'CLICKED:send-enabled',
      expectRuntime: false
    },
    {
      id: 'semantic-ambiguity',
      targetText: 'Delete',
      instruction: 'click Delete',
      expected: 'abstain',
      expectedMarker: null,
      expectRuntime: false
    },
    {
      id: 'semantic-miss-visual-hit',
      targetText: 'Launch',
      instruction: 'click the visible Launch control',
      expected: 'visual_hit',
      expectedMarker: 'CLICKED:visual-launch',
      expectRuntime: true
    },
    {
      id: 'semantic-miss-absent',
      targetText: 'Export CSV',
      instruction: 'click Export CSV',
      expected: 'abstain',
      expectedMarker: null,
      expectRuntime: true
    }
  ];

  for (let index = 0; index < cases.length; index += 1) {
    const testCase = cases[index];
    progress(`CASE ${index + 1}/${cases.length} ${testCase.id} start`);
    await openFixture(client, fixture.url);
    const before = runtimeStatus();
    const started = process.hrtime.bigint();
    const result = await call(client, 'web_interact', {
      operation: 'click',
      visualFallback: { targetText: testCase.targetText, instruction: testCase.instruction }
    });
    const after = runtimeStatus();
    const pageText = await snapshotText(client);
    const actualMarkers = markers(pageText);
    const resultText = textOf(result);

    let classification = 'error';
    let falseClick = false;
    let error = false;
    if (testCase.expected === 'semantic_hit') {
      if (!result?.isError && actualMarkers.length === 1 && actualMarkers[0] === testCase.expectedMarker && !after.running) {
        classification = 'semantic_hit';
      } else {
        falseClick = actualMarkers.length > 0 && actualMarkers[0] !== testCase.expectedMarker;
        error = !falseClick;
      }
    } else if (testCase.expected === 'visual_hit') {
      if (!result?.isError && resultText.includes('reviewed same-session visual fallback') && actualMarkers.length === 1 && actualMarkers[0] === testCase.expectedMarker && after.running && after.ready) {
        classification = 'visual_hit';
      } else {
        falseClick = actualMarkers.length > 0 && actualMarkers[0] !== testCase.expectedMarker;
        error = !falseClick;
      }
    } else {
      if (!result?.isError && resultText.includes('abstained with no action') && actualMarkers.length === 0 && Boolean(after.running) === testCase.expectRuntime) {
        classification = 'correct_abstain';
      } else {
        falseClick = actualMarkers.length > 0;
        error = !falseClick;
      }
    }

    const row = {
      case_id: testCase.id,
      target_text: testCase.targetText,
      expected: testCase.expected,
      classification,
      result_is_error: Boolean(result?.isError),
      result_text: resultText,
      markers: actualMarkers,
      runtime_running_before: Boolean(before.running),
      runtime_running_after: Boolean(after.running),
      runtime_ready_after: Boolean(after.ready),
      false_click: falseClick,
      error,
      total_ms: elapsedMs(started)
    };
    rows.push(row);
    progress(`CASE ${index + 1}/${cases.length} ${testCase.id} done classification=${classification} runtime=${row.runtime_running_after} ms=${row.total_ms.toFixed(1)}`);
  }
} finally {
  progress('PUBLIC_SEMANTIC_CLOSE start');
  await client.close().catch(error => progress(`PUBLIC_SEMANTIC_CLOSE error=${error instanceof Error ? error.message : String(error)}`));
  progress('PUBLIC_SEMANTIC_CLOSE done');
  await closeServer(fixture.server).catch(() => {});
  fs.rmSync(workspace, { recursive: true, force: true });
}

const summary = {
  semantic_hits: rows.filter(row => row.classification === 'semantic_hit').length,
  visual_hits: rows.filter(row => row.classification === 'visual_hit').length,
  correct_abstains: rows.filter(row => row.classification === 'correct_abstain').length,
  false_clicks: rows.filter(row => row.false_click).length,
  errors: rows.filter(row => row.error).length,
  semantic_cases_started_vlm: rows.slice(0, 3).filter(row => row.runtime_running_after).length,
  acceptance_pass: false
};
summary.acceptance_pass =
  summary.semantic_hits === 2 &&
  summary.visual_hits === 1 &&
  summary.correct_abstains === 2 &&
  summary.false_clicks === 0 &&
  summary.errors === 0 &&
  summary.semantic_cases_started_vlm === 0;

const payload = {
  schema_version: 1,
  git_head: gitHead(),
  public_tools: expectedTools,
  runtime_profile: 'lfm25-vl-450m-f16',
  cases: rows,
  summary
};
writeResult(payload);
if (!summary.acceptance_pass) process.exitCode = 1;
