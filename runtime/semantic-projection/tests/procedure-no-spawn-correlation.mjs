import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

const here = path.dirname(fileURLToPath(import.meta.url));
const controlPlaneEntry = path.resolve(here, '..', 'bin', 'semantic-control-plane-projection.mjs');

function childEnvironment(extra) {
  const env = {};
  for (const [key, value] of Object.entries(process.env)) {
    if (typeof value === 'string') env[key] = value;
  }
  return { ...env, ...extra };
}

function textOf(result) {
  return (result.content ?? [])
    .filter(block => block.type === 'text')
    .map(block => block.text)
    .join('\n');
}

const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-no-spawn-workspace-'));
const stateRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-no-spawn-state-'));
const missingPython = path.join(
  os.tmpdir(),
  `chat-definitely-missing-python-${process.pid}-${Date.now()}`,
);
const injectedEntry = path.join(
  path.dirname(controlPlaneEntry),
  `.semantic-control-plane-no-spawn-${process.pid}-${Date.now()}.mjs`,
);
fs.rmSync(missingPython, { force: true });

const source = fs.readFileSync(controlPlaneEntry, 'utf8');
const freshPythonBinding = "if (request?.procedure !== WINDOWS_CASE_PROCEDURE) return 'python';";
const injectedSource = source.replace(
  freshPythonBinding,
  `if (request?.procedure !== WINDOWS_CASE_PROCEDURE) return ${JSON.stringify(missingPython)};`,
);
assert.notEqual(
  injectedSource,
  source,
  'no-spawn acceptance must replace exactly the private fresh-workspace Python binding',
);
fs.writeFileSync(injectedEntry, injectedSource, 'utf8');

const client = new Client({ name: 'procedure-no-spawn-correlation-acceptance', version: '1.0.0' });
const transport = new StdioClientTransport({
  command: process.execPath,
  args: [injectedEntry],
  env: childEnvironment({
    CHAT_LOCAL_FILES_ROOT: workspace,
    CHAT_PROCEDURE_STATE_ROOT: stateRoot,
  }),
});

try {
  await client.connect(transport);

  const fresh = await client.callTool({
    name: 'procedure_run',
    arguments: {
      procedure: 'verified_workspace_artifact_v1',
      artifact_name: 'no-spawn-fresh.txt',
      content: 'NO_SPAWN_FRESH',
    },
  });
  assert.equal(fresh.isError, true, textOf(fresh));
  const freshPayload = fresh.structuredContent ?? JSON.parse(textOf(fresh));
  assert.equal(freshPayload.status, 'error');
  assert.match(freshPayload.reason, /^control_plane_child_error:/);
  assert.equal(
    Object.prototype.hasOwnProperty.call(freshPayload, 'resume_task_id'),
    false,
    'fresh no-spawn failure must not advertise a generated resumable task id',
  );
  assert.equal(
    fs.readdirSync(stateRoot).filter(name => name.endsWith('.json')).length,
    0,
    'no child process means no durable procedure checkpoint can exist',
  );

  const knownTaskId = 'd'.repeat(32);
  const resumed = await client.callTool({
    name: 'procedure_run',
    arguments: {
      procedure: 'verified_workspace_artifact_v1',
      artifact_name: 'no-spawn-resume.txt',
      content: 'NO_SPAWN_RESUME',
      resume_task_id: knownTaskId,
    },
  });
  assert.equal(resumed.isError, true, textOf(resumed));
  const resumedPayload = resumed.structuredContent ?? JSON.parse(textOf(resumed));
  assert.equal(resumedPayload.status, 'error');
  assert.match(resumedPayload.reason, /^control_plane_child_error:/);
  assert.equal(
    resumedPayload.resume_task_id,
    knownTaskId,
    'resume no-spawn failure must preserve the caller-known correlation id',
  );

  console.log('SEMANTIC_PUBLIC_FRESH_NO_SPAWN_CORRELATION=PASS');
  console.log('SEMANTIC_PUBLIC_RESUME_NO_SPAWN_CORRELATION=PASS');
} finally {
  try { await client.close(); } catch {}
  fs.rmSync(workspace, { recursive: true, force: true });
  fs.rmSync(stateRoot, { recursive: true, force: true });
  fs.rmSync(injectedEntry, { force: true });
}
