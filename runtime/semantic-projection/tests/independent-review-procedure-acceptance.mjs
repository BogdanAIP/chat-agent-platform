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
const BASE_SHA = '1'.repeat(40);
const HEAD_SHA = '2'.repeat(40);
const REVIEW_IDENTITY = {
  repository: 'BogdanAIP/chat-agent-platform',
  pr_number: 141,
  base_sha: BASE_SHA,
  head_sha: HEAD_SHA,
  review_skill: 'code-review',
  review_skill_version: '1.1'
};

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

function variantsOf(schema) {
  if (Array.isArray(schema?.anyOf)) return schema.anyOf;
  if (Array.isArray(schema?.oneOf)) return schema.oneOf;
  return [schema];
}

function procedureLiteral(schema) {
  const procedure = schema?.properties?.procedure;
  if (typeof procedure?.const === 'string') return procedure.const;
  if (Array.isArray(procedure?.enum) && procedure.enum.length === 1) return procedure.enum[0];
  return null;
}

const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-review-procedure-workspace-'));
const stateRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-review-procedure-state-'));
const client = new Client({ name: 'independent-review-procedure-acceptance', version: '1.0.0' });
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
  assert.equal(inventory.tools.length, 6, 'review procedure wiring must not add a seventh public tool');
  const procedure = inventory.tools.find(tool => tool.name === 'procedure_run');
  assert(procedure, 'procedure_run missing');

  const variants = variantsOf(procedure.inputSchema);
  assert.equal(variants.length, 5, 'procedure_run must expose exactly five registered procedure schemas');
  const byProcedure = new Map(variants.map(variant => [procedureLiteral(variant), variant]));
  assert.deepEqual(
    [...byProcedure.keys()].sort(),
    [
      'launch_independent_review_v1',
      'reconcile_independent_review_result_v1',
      'submit_independent_review_result_v1',
      'verified_workspace_artifact_v1',
      'windows_case_update_v1'
    ],
  );

  const launchSchema = byProcedure.get('launch_independent_review_v1');
  const submitSchema = byProcedure.get('submit_independent_review_result_v1');
  const reconcileSchema = byProcedure.get('reconcile_independent_review_result_v1');
  assert(launchSchema && submitSchema && reconcileSchema, 'independent review procedure schemas missing');
  assert.equal(launchSchema.additionalProperties, false);
  assert.equal(submitSchema.additionalProperties, false);
  assert.equal(reconcileSchema.additionalProperties, false);
  assert.deepEqual(
    Object.keys(launchSchema.properties ?? {}).sort(),
    ['base_sha', 'head_sha', 'pr_number', 'procedure', 'repository', 'review_skill', 'review_skill_version'],
  );
  assert.deepEqual(
    Object.keys(submitSchema.properties ?? {}).sort(),
    ['procedure', 'result', 'review_run_id'],
  );
  assert.deepEqual(
    Object.keys(reconcileSchema.properties ?? {}).sort(),
    [
      'base_sha',
      'head_sha',
      'manual_result',
      'pr_number',
      'procedure',
      'repository',
      'review_skill',
      'review_skill_version'
    ],
  );
  for (const schema of [launchSchema, submitSchema, reconcileSchema]) {
    const properties = schema.properties ?? {};
    for (const forbidden of [
      'url', 'prompt', 'command', 'path', 'python', 'backend', 'tool', 'args',
      'server', 'github_token', 'github_app', 'github_action'
    ]) {
      assert.equal(
        Object.prototype.hasOwnProperty.call(properties, forbidden),
        false,
        `forbidden reviewer authority leaked into ${procedureLiteral(schema)}: ${forbidden}`,
      );
    }
  }

  const launch = await client.callTool({
    name: 'procedure_run',
    arguments: { procedure: 'launch_independent_review_v1', ...REVIEW_IDENTITY }
  });
  assert.equal(launch.isError, undefined, textOf(launch));
  const launchPayload = launch.structuredContent ?? JSON.parse(textOf(launch));
  assert.equal(launchPayload.status, 'abstained');
  assert.equal(launchPayload.escalation_reason, 'reviewer_authority_unqualified');
  assert.equal(launchPayload.dispatch_state, 'prepared');
  assert.equal(launchPayload.result_state, 'open');
  assert.equal(launchPayload.automatic_launch_performed, false);
  assert.equal(launchPayload.automatic_submission_open, false);
  assert.equal(Object.prototype.hasOwnProperty.call(launchPayload, 'review_run_id'), false);

  const reconcile = await client.callTool({
    name: 'procedure_run',
    arguments: { procedure: 'reconcile_independent_review_result_v1', ...REVIEW_IDENTITY }
  });
  assert.equal(reconcile.isError, undefined, textOf(reconcile));
  const reconcilePayload = reconcile.structuredContent ?? JSON.parse(textOf(reconcile));
  assert.equal(reconcilePayload.status, 'pending');
  assert.equal(reconcilePayload.dispatch_state, 'prepared');
  assert.equal(reconcilePayload.result_state, 'open');
  assert.equal(reconcilePayload.automatic_submission_open, false);

  const invalid = await client.callTool({
    name: 'procedure_run',
    arguments: {
      procedure: 'launch_independent_review_v1',
      ...REVIEW_IDENTITY,
      url: 'https://chatgpt.com/'
    }
  });
  assert.equal(invalid.isError, true, 'strict schema must reject arbitrary launch URL');
} finally {
  try { await client.close(); } catch {}
  fs.rmSync(workspace, { recursive: true, force: true });
  fs.rmSync(stateRoot, { recursive: true, force: true });
}
