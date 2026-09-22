import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';
import { createSemanticActivationEnvironment } from '../lib/semantic-activation.mjs';


const here = path.dirname(fileURLToPath(import.meta.url));
const canonicalEntry = path.resolve(here, '..', 'bin', 'semantic-projection.mjs');
const source = fs.readFileSync(canonicalEntry, 'utf8');

function childEnvironment(extra) {
  const env = {};
  for (const [key, value] of Object.entries(process.env)) {
    if (typeof value === 'string') env[key] = value;
  }
  return createSemanticActivationEnvironment({ ...env, ...extra }).env;
}

function textOf(result) {
  return (result?.content ?? [])
    .filter(block => block?.type === 'text' && typeof block.text === 'string')
    .map(block => block.text)
    .join('\n');
}

const originalDelivery = `    delivery = await callBackend('filesystem', 'write_file', {
      path: resolvedPath,
      content,
    });`;
const injectedDelivery = `    await callBackend('filesystem', 'write_file', {
      path: resolvedPath,
      content,
    });
    throw new Error('INJECTED_WORKSPACE_ACK_LOSS');`;
const injectedSource = source.replace(originalDelivery, injectedDelivery);
assert.notEqual(
  injectedSource,
  source,
  'workspace ACK-loss acceptance must replace exactly the write delivery assignment',
);

const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-workspace-write-ack-loss-'));
const injectedEntry = path.join(
  path.dirname(canonicalEntry),
  `.semantic-workspace-ack-loss-${process.pid}-${Date.now()}.mjs`,
);
fs.writeFileSync(injectedEntry, injectedSource, 'utf8');

const client = new Client({
  name: 'workspace-write-ack-loss-acceptance',
  version: '1.0.0',
});
const transport = new StdioClientTransport({
  command: process.execPath,
  args: [injectedEntry],
  env: childEnvironment({ CHAT_LOCAL_FILES_ROOT: workspace }),
});

try {
  await client.connect(transport);

  const first = await client.callTool({
    name: 'workspace_write',
    arguments: {
      path: 'ack-loss.txt',
      content: 'ACK_LOSS_VERIFIED_BYTES',
    },
  });
  assert.equal(first.isError, undefined, textOf(first));
  assert.equal(
    first.structuredContent?.workspace_verification?.status,
    'pass',
    textOf(first),
  );
  assert.equal(first.structuredContent?.delivery?.attempted, true, textOf(first));
  assert.equal(first.structuredContent?.delivery?.acknowledged, false, textOf(first));
  assert.match(
    first.structuredContent?.delivery?.error ?? '',
    /INJECTED_WORKSPACE_ACK_LOSS/,
  );
  assert.equal(
    fs.readFileSync(path.join(workspace, 'ack-loss.txt'), 'utf8'),
    'ACK_LOSS_VERIFIED_BYTES',
  );

  const second = await client.callTool({
    name: 'workspace_write',
    arguments: {
      path: 'ack-loss.txt',
      content: 'ACK_LOSS_VERIFIED_BYTES',
    },
  });
  assert.equal(second.isError, undefined, textOf(second));
  assert.equal(
    second.structuredContent?.workspace_verification?.status,
    'pass',
    textOf(second),
  );
  assert.equal(
    second.structuredContent?.workspace_verification?.reason,
    'already_satisfied_before_delivery',
    textOf(second),
  );
  assert.equal(second.structuredContent?.delivery?.attempted, false, textOf(second));

  console.log('SEMANTIC_WORKSPACE_ACK_LOSS_RECONCILED=PASS');
  console.log('SEMANTIC_WORKSPACE_RETRY_NOOP=PASS');
} finally {
  await client.close().catch(() => {});
  fs.rmSync(injectedEntry, { force: true });
  fs.rmSync(workspace, { recursive: true, force: true });
}
