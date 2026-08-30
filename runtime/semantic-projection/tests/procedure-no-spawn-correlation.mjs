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
const projectionSource = fs.readFileSync(controlPlaneEntry, 'utf8');

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

async function callInjectedProjection({ source, workspace, stateRoot, artifactName, content }) {
  const injectedEntry = path.join(
    path.dirname(controlPlaneEntry),
    `.semantic-control-plane-correlation-${process.pid}-${Date.now()}-${Math.random().toString(16).slice(2)}.mjs`,
  );
  fs.writeFileSync(injectedEntry, source, 'utf8');
  const client = new Client({ name: 'procedure-correlation-acceptance', version: '1.0.0' });
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
    return await client.callTool({
      name: 'procedure_run',
      arguments: {
        procedure: 'verified_workspace_artifact_v1',
        artifact_name: artifactName,
        content,
      },
    });
  } finally {
    try { await client.close(); } catch {}
    fs.rmSync(injectedEntry, { force: true });
  }
}

async function callWithFakeSpawnedChild({ childSource, artifactName, content }) {
  const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-spawned-workspace-'));
  const stateRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-spawned-state-'));
  const fakeChild = path.join(
    os.tmpdir(),
    `chat-fake-control-plane-${process.pid}-${Date.now()}-${Math.random().toString(16).slice(2)}.mjs`,
  );
  fs.writeFileSync(fakeChild, childSource, 'utf8');

  const originalSpawn = 'const child = spawn(python, [controlPlaneCli], {';
  const injectedSpawn = `const child = spawn(process.execPath, [${JSON.stringify(fakeChild)}], {`;
  const source = projectionSource.replace(originalSpawn, injectedSpawn);
  assert.notEqual(
    source,
    projectionSource,
    'spawned correlation acceptance must replace exactly the private control-plane child command',
  );

  try {
    const result = await callInjectedProjection({
      source,
      workspace,
      stateRoot,
      artifactName,
      content,
    });
    return {
      result,
      stateNames: fs.readdirSync(stateRoot).sort(),
    };
  } finally {
    fs.rmSync(fakeChild, { force: true });
    fs.rmSync(workspace, { recursive: true, force: true });
    fs.rmSync(stateRoot, { recursive: true, force: true });
  }
}

const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-no-spawn-workspace-'));
const stateRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-no-spawn-state-'));
const missingPython = path.join(
  os.tmpdir(),
  `chat-definitely-missing-python-${process.pid}-${Date.now()}`,
);
fs.rmSync(missingPython, { force: true });

const freshPythonBinding = "if (request?.procedure !== WINDOWS_CASE_PROCEDURE) return 'python';";
const noSpawnSource = projectionSource.replace(
  freshPythonBinding,
  `if (request?.procedure !== WINDOWS_CASE_PROCEDURE) return ${JSON.stringify(missingPython)};`,
);
assert.notEqual(
  noSpawnSource,
  projectionSource,
  'no-spawn acceptance must replace exactly the private fresh-workspace Python binding',
);

try {
  const fresh = await callInjectedProjection({
    source: noSpawnSource,
    workspace,
    stateRoot,
    artifactName: 'no-spawn-fresh.txt',
    content: 'NO_SPAWN_FRESH',
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
  const injectedEntry = path.join(
    path.dirname(controlPlaneEntry),
    `.semantic-control-plane-known-resume-${process.pid}-${Date.now()}.mjs`,
  );
  fs.writeFileSync(injectedEntry, noSpawnSource, 'utf8');
  const client = new Client({ name: 'procedure-known-resume-correlation', version: '1.0.0' });
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
  } finally {
    try { await client.close(); } catch {}
    fs.rmSync(injectedEntry, { force: true });
  }

  console.log('SEMANTIC_PUBLIC_FRESH_NO_SPAWN_CORRELATION=PASS');
  console.log('SEMANTIC_PUBLIC_RESUME_NO_SPAWN_CORRELATION=PASS');
} finally {
  fs.rmSync(workspace, { recursive: true, force: true });
  fs.rmSync(stateRoot, { recursive: true, force: true });
}

const invalidNoState = await callWithFakeSpawnedChild({
  artifactName: 'spawned-invalid-no-state.txt',
  content: 'SPAWNED_INVALID_NO_STATE',
  childSource: `
process.stdin.resume();
process.stdin.on('end', () => {
  process.stdout.write('not-json');
});
`,
});
assert.equal(invalidNoState.result.isError, true, textOf(invalidNoState.result));
const invalidNoStatePayload = invalidNoState.result.structuredContent
  ?? JSON.parse(textOf(invalidNoState.result));
assert.equal(invalidNoStatePayload.status, 'error');
assert.match(invalidNoStatePayload.reason, /^invalid_control_plane_response:/);
assert.equal(
  Object.prototype.hasOwnProperty.call(invalidNoStatePayload, 'resume_task_id'),
  false,
  'a successfully spawned child without a checkpoint must not make a fresh id resumable',
);
assert.deepEqual(invalidNoState.stateNames, []);

const validErrorNoState = await callWithFakeSpawnedChild({
  artifactName: 'spawned-valid-no-state.txt',
  content: 'SPAWNED_VALID_NO_STATE',
  childSource: `
process.stdin.resume();
process.stdin.on('end', () => {
  process.stdout.write(JSON.stringify({
    schema_version: 1,
    status: 'error',
    reason: 'fake_initialization_error',
    action_count: 0,
    resume_task_id: '${'f'.repeat(32)}'
  }));
});
`,
});
assert.equal(validErrorNoState.result.isError, true, textOf(validErrorNoState.result));
const validErrorNoStatePayload = validErrorNoState.result.structuredContent
  ?? JSON.parse(textOf(validErrorNoState.result));
assert.equal(validErrorNoStatePayload.status, 'error');
assert.equal(validErrorNoStatePayload.reason, 'fake_initialization_error');
assert.equal(
  Object.prototype.hasOwnProperty.call(validErrorNoStatePayload, 'resume_task_id'),
  false,
  'valid child errors without a durable checkpoint must not retain or forge resume_task_id',
);
assert.deepEqual(validErrorNoState.stateNames, []);

const validErrorWithState = await callWithFakeSpawnedChild({
  artifactName: 'spawned-valid-with-state.txt',
  content: 'SPAWNED_VALID_WITH_STATE',
  childSource: `
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
process.stdin.resume();
process.stdin.on('end', () => {
  const taskId = process.env.CHAT_PROCEDURE_ASSIGNED_TASK_ID;
  const stateRoot = process.env.CHAT_PROCEDURE_STATE_ROOT;
  fs.mkdirSync(stateRoot, { recursive: true });
  fs.writeFileSync(path.join(stateRoot, taskId + '.json'), JSON.stringify({ task_id: taskId }));
  process.stdout.write(JSON.stringify({
    schema_version: 1,
    status: 'error',
    reason: 'fake_post_checkpoint_error',
    action_count: 0
  }));
});
`,
});
assert.equal(validErrorWithState.result.isError, true, textOf(validErrorWithState.result));
const validErrorWithStatePayload = validErrorWithState.result.structuredContent
  ?? JSON.parse(textOf(validErrorWithState.result));
assert.equal(validErrorWithStatePayload.status, 'error');
assert.equal(validErrorWithStatePayload.reason, 'fake_post_checkpoint_error');
assert.match(validErrorWithStatePayload.resume_task_id, /^[0-9a-f]{32}$/);
assert.deepEqual(validErrorWithState.stateNames, [`${validErrorWithStatePayload.resume_task_id}.json`]);

console.log('SEMANTIC_PUBLIC_SPAWNED_NO_STATE_CORRELATION=PASS');
console.log('SEMANTIC_PUBLIC_VALID_CHILD_ERROR_CORRELATION=PASS');
