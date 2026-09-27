import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

import {
  BROWSERSKILL_IDENTITY,
} from '../lib/browserskill-capability-manifest.mjs';
import {
  createBskJsonRunner,
} from '../lib/browserskill-cli-provider.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const semanticRoot = path.resolve(here, '..');
const repoRoot = path.resolve(semanticRoot, '..', '..');
const entry = path.join(semanticRoot, 'bin', 'semantic-projection-launcher.mjs');

const resultPath = process.env.CAP_BROWSERSKILL_L3_RESULT_PATH
  ? path.resolve(process.env.CAP_BROWSERSKILL_L3_RESULT_PATH)
  : null;
const bskPath = process.env.CAP_BROWSERSKILL_BSK_PATH || 'bsk';

function textOf(result) {
  return (result?.content ?? [])
    .filter(block => block?.type === 'text' && typeof block.text === 'string')
    .map(block => block.text)
    .join('\n');
}

function payloadOf(result) {
  if (result?.structuredContent !== undefined) return result.structuredContent;
  const text = textOf(result).trim();
  if (!text) return null;
  try { return JSON.parse(text); } catch { return null; }
}

function refOnMatchingLine(result, needle) {
  for (const line of textOf(result).split(/\r?\n/)) {
    if (!line.includes(needle)) continue;
    const match =
      line.match(/\[ref=([^\]\s]+)\]/) ??
      line.match(/\bref=([A-Za-z0-9_-]+)\b/) ??
      line.match(/(@cap(?:g)?-[A-Za-z0-9-]+)/);
    if (match) return match[1];
  }
  assert.fail(`missing CAP Browser ref for ${JSON.stringify(needle)}:\n${textOf(result)}`);
}

function stringEnvironment(source) {
  const env = {};
  for (const [key, value] of Object.entries(source ?? {})) {
    if (typeof value === 'string') env[key] = value;
  }
  return env;
}

function gitHead() {
  try {
    return execFileSync('git', ['rev-parse', 'HEAD'], {
      cwd: repoRoot,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
    }).trim();
  } catch {
    return null;
  }
}

function sessionIds(value) {
  if (!Array.isArray(value)) return [];
  return value
    .map(item => item?.session_id)
    .filter(item => typeof item === 'string' && item.length > 0)
    .sort();
}

function hashIdentity(value) {
  // Do not persist the stable BrowserSkill instance id in acceptance artifacts.
  return createHash('sha256').update(String(value), 'utf8').digest('hex').slice(0, 24);
}

async function fixtureServer() {
  const html = `<!doctype html>
<html>
<head><meta charset="utf-8"><title>CAP BrowserSkill L3</title></head>
<body>
  <label for="name">Name</label>
  <input id="name" aria-label="Name" value="" />

  <label for="status">Status</label>
  <input id="status" aria-label="Status" value="WAITING" readonly />

  <button id="go" onclick="
    const count = document.getElementById('count');
    const next = Number(count.dataset.n) + 1;
    count.dataset.n = String(next);
    count.textContent = 'Count: ' + next;
    document.getElementById('status').value = 'CLICKED';
  ">Go</button>
  <span id="count" data-n="0">Count: 0</span>
</body>
</html>`;

  const server = http.createServer((_request, response) => {
    response.setHeader('Content-Type', 'text/html; charset=utf-8');
    response.setHeader('Cache-Control', 'no-store');
    response.end(html);
  });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  const address = server.address();
  assert(address && typeof address === 'object');
  return {
    server,
    url: `http://127.0.0.1:${address.port}/`,
  };
}

async function closeServer(server) {
  await new Promise((resolve, reject) => {
    server.close(error => error ? reject(error) : resolve());
  });
}

function writeResult(payload) {
  const encoded = `${JSON.stringify(payload, null, 2)}\n`;
  if (resultPath) {
    fs.mkdirSync(path.dirname(resultPath), { recursive: true });
    fs.writeFileSync(resultPath, encoded, 'utf8');
  }
  process.stdout.write(encoded);
}

async function waitForSessionGone(runBsk, sessionId, timeoutMs = 15_000) {
  const deadline = Date.now() + timeoutMs;
  let last = null;
  while (Date.now() < deadline) {
    try {
      last = sessionIds(await runBsk(['session', 'list']));
      if (!last.includes(sessionId)) {
        return { clean: true, sessions: last };
      }
    } catch {}
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  return { clean: false, sessions: last };
}

async function selectBrowser(runBsk) {
  const status = await runBsk(['status']);
  assert.equal(
    status?.daemon_version,
    BROWSERSKILL_IDENTITY.version,
    'physical L3 requires the reviewed BrowserSkill daemon version',
  );
  assert.equal(
    status?.protocol_version,
    BROWSERSKILL_IDENTITY.protocolVersion,
    'physical L3 requires the reviewed BrowserSkill protocol version',
  );
  assert.deepEqual(
    status?.version_skew_browsers ?? [],
    [],
    'physical L3 refuses BrowserSkill browser/daemon version skew',
  );

  const browsers = await runBsk(['browsers']);
  assert(Array.isArray(browsers), 'bsk browsers --json must return an array');
  const compatible = browsers.filter(browser => (
    browser?.extension_version === BROWSERSKILL_IDENTITY.version &&
    browser?.extension_protocol_version === BROWSERSKILL_IDENTITY.protocolVersion
  ));
  assert.equal(
    compatible.length,
    1,
    `physical L3 requires exactly one reviewed compatible connected browser; found ${compatible.length}`,
  );
  return compatible[0];
}

async function run() {
  assert.equal(process.platform, 'win32', 'BrowserSkill physical L3 is qualified on target Windows');

  const runBsk = createBskJsonRunner({ bskPath });
  const selected = await selectBrowser(runBsk);
  const baselineSessions = sessionIds(await runBsk(['session', 'list']));

  const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'cap-browserskill-l3-workspace-'));
  const stateRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'cap-browserskill-l3-state-'));
  const fixture = await fixtureServer();

  const client = new Client({
    name: 'cap-browserskill-physical-l3',
    version: '1.0.0',
  });
  const transport = new StdioClientTransport({
    command: process.execPath,
    args: [entry],
    env: stringEnvironment({
      ...process.env,
      CHAT_LOCAL_FILES_ROOT: workspace,
      CAP_BROWSER_PROVIDER: 'browserskill',
      CAP_BROWSERSKILL_BROWSER: selected.instance_id,
      CAP_BROWSERSKILL_BSK_PATH: bskPath,
      CAP_BROWSERSKILL_STATE_ROOT: stateRoot,
    }),
  });

  let physicalSessionId = null;

  const evidence = {
    schema_version: 1,
    git_head: gitHead(),
    browser_provider: 'browserskill',
    browserskill_version: BROWSERSKILL_IDENTITY.version,
    browserskill_protocol: BROWSERSKILL_IDENTITY.protocolVersion,
    browser_instance_hint: hashIdentity(selected.instance_id),
    public_tool_count: null,
    web_open_pass: false,
    type_pass: false,
    click_pass: false,
    duplicate_type_blocked: false,
    duplicate_click_blocked: false,
    click_count_after_repeat: null,
    provider_session_detected: false,
    cleanup_clean: false,
    fatal_error: null,
  };

  try {
    await client.connect(transport);

    const inventory = await client.listTools();
    const names = inventory.tools.map(tool => tool.name).sort();
    assert.deepEqual(names, [
      'procedure_run',
      'web_interact',
      'web_observe',
      'web_open',
      'workspace_read',
      'workspace_write',
    ]);
    evidence.public_tool_count = names.length;

    const opened = await client.callTool({
      name: 'web_open',
      arguments: { url: fixture.url },
    });
    assert.equal(opened.isError, undefined, textOf(opened));
    assert.equal(payloadOf(opened)?.browser_verification?.status, 'pass', textOf(opened));
    assert.equal(payloadOf(opened)?.delivery?.attempted, true, textOf(opened));
    evidence.web_open_pass = true;

    const activeAfterOpen = sessionIds(await runBsk(['session', 'list']));
    const newSessions = activeAfterOpen.filter(id => !baselineSessions.includes(id));
    assert.equal(
      newSessions.length,
      1,
      `physical L3 expected exactly one CAP-created BrowserSkill session; found ${newSessions.length}`,
    );
    physicalSessionId = newSessions[0];
    evidence.provider_session_detected = true;

    const nameFound = await client.callTool({
      name: 'web_observe',
      arguments: { operation: 'find', regex: 'textbox "Name"' },
    });
    const nameRef = refOnMatchingLine(nameFound, 'textbox "Name"');
    assert.match(nameRef, /^@cap(?:g)?-/);

    const typed = await client.callTool({
      name: 'web_interact',
      arguments: {
        operation: 'type',
        target: nameRef,
        text: 'CAP_BROWSERSKILL_L3',
      },
    });
    assert.equal(typed.isError, undefined, textOf(typed));
    assert.equal(payloadOf(typed)?.browser_verification?.status, 'pass', textOf(typed));
    assert.equal(payloadOf(typed)?.delivery?.attempted, true, textOf(typed));
    evidence.type_pass = true;

    const duplicateType = await client.callTool({
      name: 'web_interact',
      arguments: {
        operation: 'type',
        target: nameRef,
        text: 'CAP_BROWSERSKILL_L3',
      },
    });
    assert.equal(duplicateType.isError, true, textOf(duplicateType));
    assert.match(textOf(duplicateType), /already satisfied/i);
    evidence.duplicate_type_blocked = true;

    const goFound = await client.callTool({
      name: 'web_observe',
      arguments: { operation: 'find', text: 'button "Go"' },
    });
    const statusFound = await client.callTool({
      name: 'web_observe',
      arguments: { operation: 'find', regex: 'textbox "Status"' },
    });
    const goRef = refOnMatchingLine(goFound, 'button "Go"');
    const statusRef = refOnMatchingLine(statusFound, 'textbox "Status"');

    const clicked = await client.callTool({
      name: 'web_interact',
      arguments: {
        operation: 'click',
        target: goRef,
        expected: {
          control: {
            target: statusRef,
            value: 'CLICKED',
          },
        },
      },
    });
    assert.equal(clicked.isError, undefined, textOf(clicked));
    assert.equal(payloadOf(clicked)?.browser_verification?.status, 'pass', textOf(clicked));
    assert.equal(payloadOf(clicked)?.delivery?.attempted, true, textOf(clicked));
    evidence.click_pass = true;

    const duplicateClick = await client.callTool({
      name: 'web_interact',
      arguments: {
        operation: 'click',
        target: goRef,
        expected: {
          control: {
            target: statusRef,
            value: 'CLICKED',
          },
        },
      },
    });
    assert.equal(duplicateClick.isError, true, textOf(duplicateClick));
    assert.match(textOf(duplicateClick), /already satisfied/i);
    evidence.duplicate_click_blocked = true;

    const countOne = await client.callTool({
      name: 'web_observe',
      arguments: { operation: 'find', text: 'Count: 1' },
    });
    assert.match(textOf(countOne), /Count: 1/);
    const countTwo = await client.callTool({
      name: 'web_observe',
      arguments: { operation: 'find', text: 'Count: 2' },
    });
    assert.doesNotMatch(textOf(countTwo), /Count: 2/);
    evidence.click_count_after_repeat = 1;

    const repeatedOpen = await client.callTool({
      name: 'web_open',
      arguments: { url: fixture.url },
    });
    assert.equal(repeatedOpen.isError, undefined, textOf(repeatedOpen));
    assert.equal(payloadOf(repeatedOpen)?.delivery?.attempted, false, textOf(repeatedOpen));
    assert.equal(
      payloadOf(repeatedOpen)?.browser_verification?.reason,
      'already_satisfied_before_delivery',
      textOf(repeatedOpen),
    );
  } finally {
    await client.close().catch(() => {});
    await closeServer(fixture.server).catch(() => {});

    if (physicalSessionId !== null) {
      const cleanup = await waitForSessionGone(runBsk, physicalSessionId);
      evidence.cleanup_clean = cleanup.clean;
    } else {
      const current = sessionIds(await runBsk(['session', 'list']));
      evidence.cleanup_clean = current.every(id => baselineSessions.includes(id));
    }

    fs.rmSync(workspace, { recursive: true, force: true });
    fs.rmSync(stateRoot, { recursive: true, force: true });
  }

  assert.equal(evidence.cleanup_clean, true, 'BrowserSkill physical L3 leaked a provider session');
  writeResult({
    ...evidence,
    acceptance_pass: (
      evidence.public_tool_count === 6 &&
      evidence.web_open_pass &&
      evidence.provider_session_detected &&
      evidence.type_pass &&
      evidence.click_pass &&
      evidence.duplicate_type_blocked &&
      evidence.duplicate_click_blocked &&
      evidence.click_count_after_repeat === 1 &&
      evidence.cleanup_clean
    ),
  });
}

try {
  await run();
} catch (error) {
  writeResult({
    schema_version: 1,
    git_head: gitHead(),
    browser_provider: 'browserskill',
    browserskill_version: BROWSERSKILL_IDENTITY.version,
    browserskill_protocol: BROWSERSKILL_IDENTITY.protocolVersion,
    acceptance_pass: false,
    fatal_error: error instanceof Error ? error.message : String(error),
  });
  process.exitCode = 1;
}
