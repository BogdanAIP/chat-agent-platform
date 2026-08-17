import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

if (process.platform !== 'win32') {
  throw new Error('Windows junction security acceptance must run on Windows.');
}

const here = path.dirname(fileURLToPath(import.meta.url));
const projectionEntry = path.resolve(here, '..', 'bin', 'semantic-projection.mjs');

function textOf(result) {
  return (result?.content ?? [])
    .filter(block => block?.type === 'text' && typeof block.text === 'string')
    .map(block => block.text)
    .join('\n');
}

function childEnvironment(extra) {
  const env = {};
  for (const [key, value] of Object.entries(process.env)) {
    if (typeof value === 'string') env[key] = value;
  }
  return { ...env, ...extra };
}

const root = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-stage25-1-junction-'));
const workspace = path.join(root, 'workspace');
const outside = path.join(root, 'outside');
const junction = path.join(workspace, 'outside-link');
const outsideSecret = path.join(outside, 'secret.txt');
const escapedWrite = path.join(outside, 'written-by-projection.txt');

fs.mkdirSync(workspace, { recursive: true });
fs.mkdirSync(outside, { recursive: true });
fs.writeFileSync(outsideSecret, 'OUTSIDE_JUNCTION_SECRET', 'utf8');
fs.symlinkSync(outside, junction, 'junction');

const client = new Client({ name: 'stage25-1-junction-security', version: '1.0.0' });
const transport = new StdioClientTransport({
  command: process.execPath,
  args: [projectionEntry],
  env: childEnvironment({ CHAT_LOCAL_FILES_ROOT: workspace })
});

try {
  await client.connect(transport);

  const read = await client.callTool({
    name: 'workspace_read',
    arguments: { operation: 'read_text', path: 'outside-link/secret.txt' }
  });
  assert.equal(read.isError, true, `junction read escaped workspace:\n${textOf(read)}`);
  assert(!textOf(read).includes('OUTSIDE_JUNCTION_SECRET'), textOf(read));
  console.log('WORKSPACE_JUNCTION_READ_BLOCKED=PASS');

  const write = await client.callTool({
    name: 'workspace_write',
    arguments: { path: 'outside-link/written-by-projection.txt', content: 'MUST_NOT_ESCAPE' }
  });
  assert.equal(write.isError, true, `junction write escaped workspace:\n${textOf(write)}`);
  assert.equal(fs.existsSync(escapedWrite), false, 'workspace_write created a file outside root through junction');
  console.log('WORKSPACE_JUNCTION_WRITE_BLOCKED=PASS');

  const normalWrite = await client.callTool({
    name: 'workspace_write',
    arguments: { path: 'inside.txt', content: 'INSIDE_OK' }
  });
  assert.equal(normalWrite.isError, undefined, textOf(normalWrite));
  assert.equal(fs.readFileSync(path.join(workspace, 'inside.txt'), 'utf8'), 'INSIDE_OK');
  console.log('WORKSPACE_NORMAL_WRITE_STILL_WORKS=PASS');

  console.log('WORKSPACE_JUNCTION_SECURITY=PASS');
} finally {
  await client.close().catch(() => {});
  fs.rmSync(root, { recursive: true, force: true });
}
