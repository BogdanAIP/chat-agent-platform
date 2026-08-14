import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

const here = path.dirname(fileURLToPath(import.meta.url));
const projectionEntry = path.resolve(here, '..', 'bin', 'semantic-projection.mjs');
const expectedTools = [
  'web_interact',
  'web_observe',
  'web_open',
  'workspace_read',
  'workspace_write'
];

function textOf(result) {
  return (result.content ?? [])
    .filter(block => block.type === 'text')
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

async function startFixtureServer() {
  const server = http.createServer((request, response) => {
    response.setHeader('Content-Type', 'text/html; charset=utf-8');
    if (request.url === '/done') {
      response.end(`<!doctype html>
        <html><body>
          <h1>SEMANTIC_BROWSER_DONE</h1>
          <label for="semantic-input">Semantic input</label>
          <input id="semantic-input" aria-label="Semantic input" />
        </body></html>`);
      return;
    }
    response.end(`<!doctype html>
      <html><body>
        <h1>Semantic Projection Test</h1>
        <a id="continue" href="/done">Continue semantic test</a>
      </body></html>`);
  });

  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  const address = server.address();
  assert(address && typeof address === 'object');
  return {
    server,
    baseUrl: `http://127.0.0.1:${address.port}`
  };
}

async function closeHttpServer(server) {
  await new Promise((resolve, reject) => {
    server.close(error => (error ? reject(error) : resolve()));
  });
}

const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-semantic-projection-'));
const inputPath = path.join(workspace, 'input.txt');
const outputPath = path.join(workspace, 'output.txt');
fs.writeFileSync(inputPath, 'SEMANTIC_PROJECTION_INPUT', 'utf8');

const fixture = await startFixtureServer();
const client = new Client({ name: 'semantic-projection-acceptance', version: '1.0.0' });
const transport = new StdioClientTransport({
  command: process.execPath,
  args: [projectionEntry],
  env: childEnvironment({ CHAT_LOCAL_FILES_ROOT: workspace })
});

try {
  await client.connect(transport);

  const inventory = await client.listTools();
  const names = inventory.tools.map(tool => tool.name).sort();
  assert.deepEqual(names, expectedTools, `unexpected Chat-facing tools: ${names.join(', ')}`);
  for (const forbidden of ['tool_invoke', 'tool_schema', 'mcp_enable', 'read_text_file', 'write_file', 'browser_navigate', 'browser_click']) {
    assert(!names.includes(forbidden), `raw/generic tool leaked through projection: ${forbidden}`);
  }

  const byName = new Map(inventory.tools.map(tool => [tool.name, tool]));
  assert.equal(byName.get('workspace_read')?.annotations?.readOnlyHint, true);
  assert.equal(byName.get('workspace_write')?.annotations?.readOnlyHint, false);
  assert.equal(byName.get('workspace_write')?.annotations?.destructiveHint, true);
  assert.equal(byName.get('web_observe')?.annotations?.readOnlyHint, true);
  assert.equal(byName.get('web_interact')?.annotations?.readOnlyHint, false);
  assert.equal(byName.get('web_interact')?.annotations?.openWorldHint, true);

  const roots = await client.callTool({
    name: 'workspace_read',
    arguments: { operation: 'roots' }
  });
  assert.equal(roots.isError, undefined, textOf(roots));
  assert(textOf(roots).toLowerCase().includes(workspace.toLowerCase()), textOf(roots));

  const read = await client.callTool({
    name: 'workspace_read',
    arguments: { operation: 'read_text', path: 'input.txt' }
  });
  assert.equal(read.isError, undefined, textOf(read));
  assert(textOf(read).includes('SEMANTIC_PROJECTION_INPUT'), textOf(read));

  const search = await client.callTool({
    name: 'workspace_read',
    arguments: { operation: 'search', pattern: 'input.txt' }
  });
  assert.equal(search.isError, undefined, textOf(search));
  assert(textOf(search).toLowerCase().includes('input.txt'), textOf(search));

  const write = await client.callTool({
    name: 'workspace_write',
    arguments: { path: 'output.txt', content: 'SEMANTIC_PROJECTION_WRITE_OK' }
  });
  assert.equal(write.isError, undefined, textOf(write));
  assert.equal(fs.readFileSync(outputPath, 'utf8'), 'SEMANTIC_PROJECTION_WRITE_OK');

  const traversal = await client.callTool({
    name: 'workspace_read',
    arguments: { operation: 'read_text', path: '../outside.txt' }
  });
  assert.equal(traversal.isError, true, 'parent traversal must be rejected by projection');

  const absoluteWrite = await client.callTool({
    name: 'workspace_write',
    arguments: { path: path.resolve(workspace, 'absolute.txt'), content: 'NO' }
  });
  assert.equal(absoluteWrite.isError, true, 'absolute workspace path must be rejected by projection');

  const open = await client.callTool({
    name: 'web_open',
    arguments: { url: `${fixture.baseUrl}/` }
  });
  assert.equal(open.isError, undefined, textOf(open));

  const findLink = await client.callTool({
    name: 'web_observe',
    arguments: { operation: 'find', text: 'Continue semantic test' }
  });
  assert.equal(findLink.isError, undefined, textOf(findLink));
  assert(textOf(findLink).includes('Continue semantic test'), textOf(findLink));

  const click = await client.callTool({
    name: 'web_interact',
    arguments: {
      operation: 'click',
      target: '#continue',
      element: 'Continue semantic test link'
    }
  });
  assert.equal(click.isError, undefined, textOf(click));

  const findDone = await client.callTool({
    name: 'web_observe',
    arguments: { operation: 'find', text: 'SEMANTIC_BROWSER_DONE' }
  });
  assert.equal(findDone.isError, undefined, textOf(findDone));
  assert(textOf(findDone).includes('SEMANTIC_BROWSER_DONE'), textOf(findDone));

  const type = await client.callTool({
    name: 'web_interact',
    arguments: {
      operation: 'type',
      target: '#semantic-input',
      element: 'Semantic input',
      text: 'SEMANTIC_TYPED_OK'
    }
  });
  assert.equal(type.isError, undefined, textOf(type));

  const snapshot = await client.callTool({
    name: 'web_observe',
    arguments: { operation: 'snapshot', target: '#semantic-input' }
  });
  assert.equal(snapshot.isError, undefined, textOf(snapshot));
  assert(textOf(snapshot).includes('SEMANTIC_TYPED_OK'), textOf(snapshot));

  const fileUrl = await client.callTool({
    name: 'web_open',
    arguments: { url: `file://${inputPath.replaceAll('\\', '/')}` }
  });
  assert.equal(fileUrl.isError, true, 'non-http web_open URL must be rejected');

  const mixedInteraction = await client.callTool({
    name: 'web_interact',
    arguments: {
      operation: 'click',
      target: '#semantic-input',
      text: 'must-not-be-accepted-for-click'
    }
  });
  assert.equal(mixedInteraction.isError, true, 'click must reject type-only arguments');

  console.log('SEMANTIC_PROJECTION_TOOL_COUNT=5');
  console.log('SEMANTIC_PROJECTION_FILESYSTEM=PASS');
  console.log('SEMANTIC_PROJECTION_BROWSER=PASS');
  console.log('SEMANTIC_PROJECTION_NEGATIVE_CASES=PASS');
  console.log('SEMANTIC_PROJECTION_ACCEPTANCE=PASS');
} finally {
  await client.close().catch(() => {});
  await closeHttpServer(fixture.server).catch(() => {});
  fs.rmSync(workspace, { recursive: true, force: true });
}
