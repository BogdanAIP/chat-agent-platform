import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

const here = path.dirname(fileURLToPath(import.meta.url));
const entry = path.resolve(here, '..', 'bin', 'semantic-projection-launcher.mjs');
const controlPlaneEntry = path.resolve(here, '..', 'bin', 'semantic-control-plane-projection.mjs');
const expectedTools = [
  'procedure_run',
  'web_interact',
  'web_observe',
  'web_open',
  'workspace_read',
  'workspace_write'
];

function childEnvironment(extra) {
  const env = {};
  for (const [key, value] of Object.entries(process.env)) if (typeof value === 'string') env[key] = value;
  return { ...env, ...extra };
}

function textOf(result) {
  return (result.content ?? []).filter(block => block.type === 'text').map(block => block.text).join('\n');
}

function closedSchemaVariants(schema) {
  const variants = Array.isArray(schema?.anyOf)
    ? schema.anyOf
    : Array.isArray(schema?.oneOf)
      ? schema.oneOf
      : [schema];
  assert.equal(variants.length, 2, 'procedure_run must expose exactly two registered closed procedure schemas');
  return variants;
}

function procedureLiteral(schema) {
  const procedure = schema?.properties?.procedure;
  if (typeof procedure?.const === 'string') return procedure.const;
  if (Array.isArray(procedure?.enum) && procedure.enum.length === 1) return procedure.enum[0];
  return null;
}

const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-six-tool-workspace-'));
const stateRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-six-tool-state-'));
const client = new Client({ name: 'six-tool-semantic-acceptance', version: '1.0.0' });
const transport = new StdioClientTransport({
  command: process.execPath,
  args: [entry],
  env: childEnvironment({
    CHAT_LOCAL_FILES_ROOT: workspace,
    CHAT_PROCEDURE_STATE_ROOT: stateRoot
  })
});

try {
  await client.connect(transport);
  const inventory = await client.listTools();
  const names = inventory.tools.map(tool => tool.name).sort();
  assert.deepEqual(names, expectedTools, `public semantic surface must be exactly six tools: ${names.join(', ')}`);

  const byName = new Map(inventory.tools.map(tool => [tool.name, tool]));
  assert.equal(byName.get('workspace_read')?.annotations?.readOnlyHint, true);
  assert.equal(byName.get('workspace_write')?.annotations?.destructiveHint, true);
  assert.equal(byName.get('web_observe')?.annotations?.readOnlyHint, true);
  assert.equal(byName.get('web_interact')?.annotations?.openWorldHint, true);

  const interact = byName.get('web_interact');
  assert(interact, 'web_interact missing from canonical semantic surface');
  const interactProperties = interact.inputSchema?.properties ?? {};
  assert(interactProperties.expected, 'web_interact must expose bounded expected postconditions');
  for (const forbidden of ['javascript', 'script', 'selector', 'code', 'command', 'backend', 'tool']) {
    assert.equal(
      Object.prototype.hasOwnProperty.call(interactProperties, forbidden),
      false,
      `forbidden generic Browser authority leaked into web_interact: ${forbidden}`,
    );
  }
  const expectedProperties = interactProperties.expected?.properties ?? {};
  assert.deepEqual(Object.keys(expectedProperties).sort(), ['control', 'url']);
  const expectedControlProperties = expectedProperties.control?.properties ?? {};
  assert.deepEqual(
    Object.keys(expectedControlProperties).sort(),
    ['checked', 'enabled', 'present', 'selected', 'target', 'value'],
  );

  const procedure = byName.get('procedure_run');
  assert(procedure, 'procedure_run missing from canonical semantic surface');
  assert.equal(procedure.annotations?.readOnlyHint, false);
  assert.equal(procedure.annotations?.destructiveHint, true);
  assert.equal(procedure.annotations?.openWorldHint, false);

  const variants = closedSchemaVariants(procedure.inputSchema);
  const byProcedure = new Map(variants.map(variant => [procedureLiteral(variant), variant]));
  assert.deepEqual(
    [...byProcedure.keys()].sort(),
    ['verified_workspace_artifact_v1', 'windows_case_update_v1'],
    'procedure_run registry literals drifted',
  );

  const workspaceProcedure = byProcedure.get('verified_workspace_artifact_v1');
  const windowsProcedure = byProcedure.get('windows_case_update_v1');
  assert(workspaceProcedure, 'verified_workspace_artifact_v1 schema missing');
  assert(windowsProcedure, 'windows_case_update_v1 schema missing');
  assert.equal(workspaceProcedure.additionalProperties, false);
  assert.equal(windowsProcedure.additionalProperties, false);
  assert.deepEqual(
    Object.keys(workspaceProcedure.properties ?? {}).sort(),
    ['artifact_name', 'content', 'procedure', 'resume_task_id'],
  );
  assert.deepEqual(
    Object.keys(windowsProcedure.properties ?? {}).sort(),
    ['case_id', 'note', 'procedure', 'status'],
  );
  for (const variant of variants) {
    const properties = variant.properties ?? {};
    for (const forbidden of ['path', 'command', 'python', 'backend', 'tool', 'args', 'pid', 'hwnd', 'server']) {
      assert.equal(
        Object.prototype.hasOwnProperty.call(properties, forbidden),
        false,
        `forbidden procedure authority leaked into ${procedureLiteral(variant)}: ${forbidden}`,
      );
    }
  }

  fs.writeFileSync(path.join(workspace, 'input.txt'), 'SIX_TOOL_READ_OK', 'utf8');
  const read = await client.callTool({
    name: 'workspace_read',
    arguments: { operation: 'read_text', path: 'input.txt' }
  });
  assert.equal(read.isError, undefined, textOf(read));
  assert(textOf(read).includes('SIX_TOOL_READ_OK'), textOf(read));

  const write = await client.callTool({
    name: 'workspace_write',
    arguments: { path: 'notes.txt', content: 'SIX_TOOL_WRITE_OK' }
  });
  assert.equal(write.isError, undefined, textOf(write));
  assert.equal(fs.readFileSync(path.join(workspace, 'notes.txt'), 'utf8'), 'SIX_TOOL_WRITE_OK');

  const run = await client.callTool({
    name: 'procedure_run',
    arguments: {
      procedure: 'verified_workspace_artifact_v1',
      artifact_name: 'six-tool-result.txt',
      content: 'SIX_TOOL_PROCEDURE_OK'
    }
  });
  assert.equal(run.isError, undefined, textOf(run));
  const payload = run.structuredContent ?? JSON.parse(textOf(run));
  assert.equal(payload.status, 'completed', textOf(run));
  assert.equal(payload.action_count, 3, textOf(run));
  assert.equal(payload.procedure_id, 'verified_workspace_artifact_v1', textOf(run));
  assert.match(payload.task_id, /^[0-9a-f]{32}$/);
  assert.equal(
    JSON.parse(fs.readFileSync(path.join(stateRoot, `${payload.task_id}.json`), 'utf8')).task_id,
    payload.task_id,
    'public procedure result must expose the exact durable task correlation id',
  );

  const relative = '.chat-agent-platform/stage26-3a/six-tool-result.txt';
  assert.equal(fs.readFileSync(path.join(workspace, relative), 'utf8'), 'SIX_TOOL_PROCEDURE_OK');

  const independentRead = await client.callTool({
    name: 'workspace_read',
    arguments: { operation: 'read_text', path: relative }
  });
  assert.equal(independentRead.isError, undefined, textOf(independentRead));
  assert(textOf(independentRead).includes('SIX_TOOL_PROCEDURE_OK'), textOf(independentRead));

  const resumed = await client.callTool({
    name: 'procedure_run',
    arguments: {
      procedure: 'verified_workspace_artifact_v1',
      artifact_name: 'six-tool-result.txt',
      content: 'SIX_TOOL_PROCEDURE_OK',
      resume_task_id: payload.task_id
    }
  });
  assert.equal(resumed.isError, undefined, textOf(resumed));
  const resumedPayload = resumed.structuredContent ?? JSON.parse(textOf(resumed));
  assert.equal(resumedPayload.status, 'completed');
  assert.equal(resumedPayload.resumed, true);
  assert.equal(resumedPayload.action_count, 3);
  assert.equal(resumedPayload.task_id, payload.task_id);

  const conflictName = 'protected-existing.txt';
  const protectedDir = path.join(workspace, '.chat-agent-platform', 'stage26-3a');
  fs.mkdirSync(protectedDir, { recursive: true });
  fs.writeFileSync(path.join(protectedDir, conflictName), 'DO_NOT_OVERWRITE', 'utf8');
  const abstain = await client.callTool({
    name: 'procedure_run',
    arguments: {
      procedure: 'verified_workspace_artifact_v1',
      artifact_name: conflictName,
      content: 'MUST_NOT_REPLACE_EXISTING'
    }
  });
  assert.equal(abstain.isError, undefined, textOf(abstain));
  const abstainPayload = abstain.structuredContent ?? JSON.parse(textOf(abstain));
  assert.equal(abstainPayload.status, 'abstained', textOf(abstain));
  assert.equal(abstainPayload.escalation_reason, 'target_already_exists');
  assert.equal(fs.readFileSync(path.join(protectedDir, conflictName), 'utf8'), 'DO_NOT_OVERWRITE');

  // controlPlaneEnvironment cannot be forced to fail through the public MCP
  // route without also preventing the inner semantic server from starting.
  // Lock the narrow pre-spawn correlation invariant structurally here while the
  // surrounding public tests continue to execute procedureFailure behavior.
  const controlPlaneSource = fs.readFileSync(controlPlaneEntry, 'utf8');
  assert(
    controlPlaneSource.includes(
      'const resumableCorrelationTaskId = assignedTaskId === null ? correlationTaskId : null;'
    ),
    'fresh pre-spawn setup failures must drop generated non-durable resume ids',
  );
  assert(
    controlPlaneSource.includes(
      'procedureFailure(`control_plane_setup:${reason}`, resumableCorrelationTaskId)'
    ),
    'setup failure must use the durable/resume-aware correlation selection',
  );

  // Force the outer semantic projection's Python child to terminate without a
  // JSON result and without creating durable procedure state. This exercises
  // the public procedure_run failure receipt: a generated id must not become a
  // resumable id merely because spawn succeeded.
  const failureWorkspace = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-procedure-failure-workspace-'));
  const failureState = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-procedure-failure-state-'));
  const fakeBin = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-fake-python-'));
  const fakePython = path.join(fakeBin, process.platform === 'win32' ? 'python.exe' : 'python');
  fs.copyFileSync(process.execPath, fakePython);
  if (process.platform !== 'win32') fs.chmodSync(fakePython, 0o755);
  const fakePath = `${fakeBin}${path.delimiter}${process.env.PATH ?? process.env.Path ?? ''}`;
  const failureClient = new Client({ name: 'procedure-failure-correlation-acceptance', version: '1.0.0' });
  const failureTransport = new StdioClientTransport({
    command: process.execPath,
    args: [entry],
    env: childEnvironment({
      CHAT_LOCAL_FILES_ROOT: failureWorkspace,
      CHAT_PROCEDURE_STATE_ROOT: failureState,
      PATH: fakePath,
      Path: fakePath
    })
  });
  try {
    await failureClient.connect(failureTransport);
    const failed = await failureClient.callTool({
      name: 'procedure_run',
      arguments: {
        procedure: 'verified_workspace_artifact_v1',
        artifact_name: 'crash-receipt.txt',
        content: 'CRASH_RECEIPT'
      }
    });
    assert.equal(failed.isError, true, textOf(failed));
    const failedPayload = failed.structuredContent ?? JSON.parse(textOf(failed));
    assert.equal(failedPayload.status, 'error');
    assert.match(failedPayload.reason, /^invalid_control_plane_response:/);
    assert.equal(
      Object.prototype.hasOwnProperty.call(failedPayload, 'resume_task_id'),
      false,
      'fresh child crash without durable state must not advertise a resumable task id',
    );
    assert.equal(
      Object.prototype.hasOwnProperty.call(failedPayload, 'action_count'),
      false,
      'parent crash receipt must not invent procedure progress it cannot observe',
    );
    assert.equal(fs.readdirSync(failureState).filter(name => name.endsWith('.json')).length, 0);
  } finally {
    try { await failureClient.close(); } catch {}
    fs.rmSync(failureWorkspace, { recursive: true, force: true });
    fs.rmSync(failureState, { recursive: true, force: true });
    fs.rmSync(fakeBin, { recursive: true, force: true });
  }

  // Reproduce a valid child error after durable state can already exist. The
  // temporary entrypoint stays inside the installed package directory so it
  // uses the same MCP dependencies and semantic base, while only its private
  // controlPlaneCli constant points at an injected child. That child persists
  // the parent-assigned id and then emits syntactically valid status=error JSON.
  // The public parent must preserve the same id as resume_task_id.
  const validErrorWorkspace = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-valid-error-workspace-'));
  const validErrorState = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-valid-error-state-'));
  const validErrorCli = path.join(os.tmpdir(), `chat-valid-error-cli-${process.pid}-${Date.now()}.py`);
  const validErrorEntry = path.join(
    path.dirname(controlPlaneEntry),
    `.semantic-control-plane-valid-error-${process.pid}-${Date.now()}.mjs`,
  );
  fs.writeFileSync(
    validErrorCli,
    [
      'import json, os',
      'from pathlib import Path',
      'task_id = os.environ["CHAT_PROCEDURE_ASSIGNED_TASK_ID"]',
      'state_root = Path(os.environ["CHAT_PROCEDURE_STATE_ROOT"])',
      'state_root.mkdir(parents=True, exist_ok=True)',
      'checkpoint = {"schema_version": 2, "task_id": task_id, "status": "running", "action_count": 0}',
      '(state_root / f"{task_id}.json").write_text(json.dumps(checkpoint), encoding="utf-8")',
      'print(json.dumps({"schema_version": 1, "status": "error", "reason": "runtime_unavailable:InjectedValidChildError", "action_count": 0}))',
      'raise SystemExit(2)',
      ''
    ].join('\n'),
    'utf8',
  );
  const controlPlaneCliBinding = "const controlPlaneCli = path.join(repoRoot, 'runtime', 'control_plane', 'cli.py');";
  const injectedControlPlaneSource = controlPlaneSource.replace(
    controlPlaneCliBinding,
    `const controlPlaneCli = ${JSON.stringify(validErrorCli)};`,
  );
  assert.notEqual(
    injectedControlPlaneSource,
    controlPlaneSource,
    'valid-error acceptance must replace exactly the private controlPlaneCli binding',
  );
  fs.writeFileSync(validErrorEntry, injectedControlPlaneSource, 'utf8');
  const validErrorClient = new Client({ name: 'procedure-valid-error-correlation-acceptance', version: '1.0.0' });
  const validErrorTransport = new StdioClientTransport({
    command: process.execPath,
    args: [validErrorEntry],
    env: childEnvironment({
      CHAT_LOCAL_FILES_ROOT: validErrorWorkspace,
      CHAT_PROCEDURE_STATE_ROOT: validErrorState
    })
  });
  try {
    await validErrorClient.connect(validErrorTransport);
    const failed = await validErrorClient.callTool({
      name: 'procedure_run',
      arguments: {
        procedure: 'verified_workspace_artifact_v1',
        artifact_name: 'valid-error-receipt.txt',
        content: 'VALID_ERROR_RECEIPT'
      }
    });
    assert.equal(failed.isError, true, textOf(failed));
    const failedPayload = failed.structuredContent ?? JSON.parse(textOf(failed));
    assert.equal(failedPayload.status, 'error');
    assert.equal(failedPayload.reason, 'runtime_unavailable:InjectedValidChildError');
    assert.match(failedPayload.resume_task_id, /^[0-9a-f]{32}$/);
    const durableFiles = fs.readdirSync(validErrorState).filter(name => name.endsWith('.json'));
    assert.deepEqual(
      durableFiles,
      [`${failedPayload.resume_task_id}.json`],
      'valid child error must expose the exact parent-owned durable correlation id',
    );
    const durable = JSON.parse(
      fs.readFileSync(path.join(validErrorState, durableFiles[0]), 'utf8'),
    );
    assert.equal(durable.task_id, failedPayload.resume_task_id);
    assert.equal(durable.status, 'running');
    assert.equal(durable.action_count, 0);
  } finally {
    try { await validErrorClient.close(); } catch {}
    fs.rmSync(validErrorWorkspace, { recursive: true, force: true });
    fs.rmSync(validErrorState, { recursive: true, force: true });
    fs.rmSync(validErrorCli, { force: true });
    fs.rmSync(validErrorEntry, { force: true });
  }

  console.log('SEMANTIC_PUBLIC_TOOL_COUNT=6');
  console.log('SEMANTIC_PUBLIC_WEB_INTERACT_EXPECTED=PASS');
  console.log('SEMANTIC_PUBLIC_PROCEDURE_REGISTRY=PASS');
  console.log('SEMANTIC_PUBLIC_PROCEDURE_RUN=PASS');
  console.log('SEMANTIC_PUBLIC_INDEPENDENT_READ=PASS');
  console.log('SEMANTIC_PUBLIC_RESUME=PASS');
  console.log('SEMANTIC_PUBLIC_SETUP_FAILURE_CORRELATION=PASS');
  console.log('SEMANTIC_PUBLIC_CRASH_CORRELATION_RECEIPT=PASS');
  console.log('SEMANTIC_PUBLIC_VALID_CHILD_ERROR_CORRELATION=PASS');
  console.log('SEMANTIC_PUBLIC_ABSTAIN_NO_OVERWRITE=PASS');
  console.log('SEMANTIC_PUBLIC_SIX_TOOL_ACCEPTANCE=PASS');
} finally {
  try { await client.close(); } catch {}
  fs.rmSync(workspace, { recursive: true, force: true });
  fs.rmSync(stateRoot, { recursive: true, force: true });
}
