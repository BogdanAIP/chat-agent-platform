import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

const here = path.dirname(fileURLToPath(import.meta.url));
const entry = path.resolve(here, '..', 'bin', 'procedure-qualification-projection.mjs');
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

const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-procedure-workspace-'));
const stateRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-procedure-state-'));
const client = new Client({ name: 'procedure-qualification-acceptance', version: '1.0.0' });
const transport = new StdioClientTransport({
  command: process.execPath,
  args: [entry],
  env: childEnvironment({
    CHAT_LOCAL_FILES_ROOT: workspace,
    CHAT_PROCEDURE_STATE_ROOT: stateRoot,
    CHAT_PROCEDURE_ALLOW_CANDIDATE: 'stage26-3a-qualification'
  })
});

try {
  await client.connect(transport);
  const inventory = await client.listTools();
  const names = inventory.tools.map(tool => tool.name).sort();
  assert.deepEqual(names, expectedTools, `unexpected qualification tools: ${names.join(', ')}`);

  const byName = new Map(inventory.tools.map(tool => [tool.name, tool]));
  const procedure = byName.get('procedure_run');
  assert(procedure, 'procedure_run missing');
  assert.equal(procedure.annotations?.readOnlyHint, false);
  assert.equal(procedure.annotations?.destructiveHint, true);
  assert.equal(procedure.annotations?.openWorldHint, false);
  const properties = procedure.inputSchema?.properties ?? {};
  assert.deepEqual(Object.keys(properties).sort(), ['artifact_name', 'content', 'procedure', 'resume_task_id']);
  for (const forbidden of ['path', 'command', 'python', 'backend', 'tool', 'args']) {
    assert.equal(Object.prototype.hasOwnProperty.call(properties, forbidden), false, `forbidden procedure selector leaked: ${forbidden}`);
  }

  const run = await client.callTool({
    name: 'procedure_run',
    arguments: {
      procedure: 'verified_workspace_artifact_v1',
      artifact_name: 'qualification.txt',
      content: 'PROCEDURE_RUN_MCP_OK'
    }
  });
  assert.equal(run.isError, undefined, textOf(run));
  const payload = run.structuredContent ?? JSON.parse(textOf(run));
  assert.equal(payload.status, 'completed', textOf(run));
  assert.equal(payload.action_count, 3, textOf(run));
  assert.equal(payload.procedure_id, 'verified_workspace_artifact_v1', textOf(run));

  const relative = '.chat-agent-platform/stage26-3a/qualification.txt';
  assert.equal(fs.readFileSync(path.join(workspace, relative), 'utf8'), 'PROCEDURE_RUN_MCP_OK');

  const independentRead = await client.callTool({
    name: 'workspace_read',
    arguments: { operation: 'read_text', path: relative }
  });
  assert.equal(independentRead.isError, undefined, textOf(independentRead));
  assert(textOf(independentRead).includes('PROCEDURE_RUN_MCP_OK'), textOf(independentRead));

  const taskId = payload.task_id;
  assert.match(taskId, /^[0-9a-f]{32}$/);
  const resumed = await client.callTool({
    name: 'procedure_run',
    arguments: {
      procedure: 'verified_workspace_artifact_v1',
      artifact_name: 'qualification.txt',
      content: 'PROCEDURE_RUN_MCP_OK',
      resume_task_id: taskId
    }
  });
  assert.equal(resumed.isError, undefined, textOf(resumed));
  const resumedPayload = resumed.structuredContent ?? JSON.parse(textOf(resumed));
  assert.equal(resumedPayload.status, 'completed');
  assert.equal(resumedPayload.resumed, true);
  assert.equal(resumedPayload.action_count, 3);

  console.log('PROCEDURE_QUALIFICATION_TOOL_SURFACE=PASS');
  console.log('PROCEDURE_QUALIFICATION_MCP_RUN=PASS');
  console.log('PROCEDURE_QUALIFICATION_INDEPENDENT_READ=PASS');
  console.log('PROCEDURE_QUALIFICATION_RESUME=PASS');
} finally {
  try { await client.close(); } catch {}
  fs.rmSync(workspace, { recursive: true, force: true });
  fs.rmSync(stateRoot, { recursive: true, force: true });
}
