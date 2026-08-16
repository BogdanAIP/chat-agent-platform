import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import process from 'node:process';

import { Client, StreamableHTTPClientTransport } from '@modelcontextprotocol/client';

const mcpUrl = process.env.DIRECT_TUNNEL_MCP_URL;
const workspaceInput = process.env.DIRECT_TUNNEL_WORKSPACE;

if (!mcpUrl) throw new Error('DIRECT_TUNNEL_MCP_URL is required.');
if (!workspaceInput) throw new Error('DIRECT_TUNNEL_WORKSPACE is required.');

const workspace = path.resolve(workspaceInput);
const workspaceStat = fs.statSync(workspace, { throwIfNoEntry: false });
if (!workspaceStat?.isDirectory()) {
  throw new Error(`DIRECT_TUNNEL_WORKSPACE must be an existing directory: ${workspace}`);
}

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

function accessibilityRefOnMatchingLine(result, needle, label) {
  const text = textOf(result);
  for (const line of text.split(/\r?\n/)) {
    if (!line.includes(needle)) continue;
    const match = line.match(/\[ref=([^\]\s]+)\]/) ?? line.match(/\bref=([A-Za-z0-9_-]+)\b/);
    if (match) return match[1];
  }
  assert.fail(`${label} did not return a matching accessibility ref for ${JSON.stringify(needle)}:\n${text}`);
}

async function startFixtureServer() {
  const server = http.createServer((_request, response) => {
    response.setHeader('Content-Type', 'text/html; charset=utf-8');
    response.end(`<!doctype html>
      <html>
        <head><title>Direct Semantic Tunnel Test</title></head>
        <body>
          <h1>Direct Semantic Tunnel Test</h1>
          <button id="continue" onclick="document.getElementById('status').textContent='DIRECT_TUNNEL_BROWSER_DONE'">Continue direct tunnel test</button>
          <p id="status">waiting</p>
        </body>
      </html>`);
  });

  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });

  const address = server.address();
  assert(address && typeof address === 'object');
  return { server, baseUrl: `http://127.0.0.1:${address.port}` };
}

async function closeHttpServer(server) {
  await new Promise((resolve, reject) => {
    server.close(error => (error ? reject(error) : resolve()));
  });
}

const inputPath = path.join(workspace, 'direct-input.txt');
const outputPath = path.join(workspace, 'direct-output.txt');
fs.writeFileSync(inputPath, 'DIRECT_SEMANTIC_INPUT', 'utf8');
fs.rmSync(outputPath, { force: true });

const fixture = await startFixtureServer();
const client = new Client(
  { name: 'direct-semantic-tunnel-acceptance', version: '1.0.0' },
  { versionNegotiation: { mode: 'auto' } }
);
const transport = new StreamableHTTPClientTransport(new URL(mcpUrl));
const startedAt = performance.now();

try {
  await client.connect(transport);
  const connectMs = Math.round(performance.now() - startedAt);

  assert.equal(
    client.getProtocolEra(),
    'modern',
    'direct tunnel path must negotiate the modern MCP era through server/discover'
  );

  const inventory = await client.listTools();
  const names = inventory.tools.map(tool => tool.name).sort();
  assert.deepEqual(names, expectedTools, `unexpected direct-tunnel tool surface: ${names.join(', ')}`);

  for (const forbidden of [
    'tool_invoke',
    'tool_schema',
    'mcp_enable',
    'read_text_file',
    'write_file',
    'browser_navigate',
    'browser_click'
  ]) {
    assert(!names.includes(forbidden), `raw/generic tool leaked through direct tunnel: ${forbidden}`);
  }

  const read = await client.callTool({
    name: 'workspace_read',
    arguments: { operation: 'read_text', path: 'direct-input.txt' }
  });
  assert.equal(read.isError, undefined, textOf(read));
  assert(textOf(read).includes('DIRECT_SEMANTIC_INPUT'), textOf(read));

  const write = await client.callTool({
    name: 'workspace_write',
    arguments: { path: 'direct-output.txt', content: 'DIRECT_SEMANTIC_WRITE_OK' }
  });
  assert.equal(write.isError, undefined, textOf(write));
  assert.equal(fs.readFileSync(outputPath, 'utf8'), 'DIRECT_SEMANTIC_WRITE_OK');

  const traversal = await client.callTool({
    name: 'workspace_read',
    arguments: { operation: 'read_text', path: '../outside.txt' }
  });
  assert.equal(traversal.isError, true, 'direct tunnel must preserve workspace traversal rejection');

  const open = await client.callTool({
    name: 'web_open',
    arguments: { url: `${fixture.baseUrl}/` }
  });
  assert.equal(open.isError, undefined, textOf(open));

  const findButton = await client.callTool({
    name: 'web_observe',
    arguments: { operation: 'find', text: 'Continue direct tunnel test' }
  });
  assert.equal(findButton.isError, undefined, textOf(findButton));
  const buttonRef = accessibilityRefOnMatchingLine(
    findButton,
    'Continue direct tunnel test',
    'direct tunnel button search'
  );

  const click = await client.callTool({
    name: 'web_interact',
    arguments: {
      operation: 'click',
      target: buttonRef,
      element: 'Continue direct tunnel test button'
    }
  });
  assert.equal(click.isError, undefined, textOf(click));

  const findDone = await client.callTool({
    name: 'web_observe',
    arguments: { operation: 'find', text: 'DIRECT_TUNNEL_BROWSER_DONE' }
  });
  assert.equal(findDone.isError, undefined, textOf(findDone));
  assert(textOf(findDone).includes('DIRECT_TUNNEL_BROWSER_DONE'), textOf(findDone));

  console.log('DIRECT_SEMANTIC_PROTOCOL_ERA=modern');
  console.log('DIRECT_SEMANTIC_TOOL_COUNT=5');
  console.log('DIRECT_SEMANTIC_FILESYSTEM=PASS');
  console.log('DIRECT_SEMANTIC_BROWSER=PASS');
  console.log('DIRECT_SEMANTIC_NEGATIVE_CASES=PASS');
  console.log(`DIRECT_SEMANTIC_CONNECT_MS=${connectMs}`);
  console.log('DIRECT_SEMANTIC_TUNNEL_ACCEPTANCE=PASS');
} finally {
  await client.close().catch(() => {});
  await closeHttpServer(fixture.server).catch(() => {});
}
