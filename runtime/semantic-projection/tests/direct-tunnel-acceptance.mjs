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
  'procedure_run',
  'web_interact',
  'web_observe',
  'web_open',
  'workspace_read',
  'workspace_write'
];

const legacyTools = [
  'semantic-projection_1mcp_procedure_run',
  'semantic-projection_1mcp_web_interact',
  'semantic-projection_1mcp_web_observe',
  'semantic-projection_1mcp_web_open',
  'semantic-projection_1mcp_workspace_read',
  'semantic-projection_1mcp_workspace_write'
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
          <button id="continue" onclick="document.getElementById('status').value='DIRECT_TUNNEL_BROWSER_DONE'">Continue direct tunnel test</button>
          <label for="status">Direct tunnel status</label>
          <input id="status" aria-label="Direct tunnel status" value="waiting" readonly />
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
const legacyOutputPath = path.join(workspace, 'legacy-direct-output.txt');
fs.writeFileSync(inputPath, 'DIRECT_SEMANTIC_INPUT', 'utf8');
fs.rmSync(outputPath, { force: true });
fs.rmSync(legacyOutputPath, { force: true });

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
  const interactSchema = inventory.tools.find(tool => tool.name === 'web_interact')?.inputSchema;
  assert(interactSchema?.properties?.expected, 'direct tunnel must expose bounded web_interact expected postconditions');

  for (const forbidden of [
    'tool_invoke',
    'tool_schema',
    'mcp_enable',
    'read_text_file',
    'write_file',
    'browser_navigate',
    'browser_click',
    ...legacyTools
  ]) {
    assert(!names.includes(forbidden), `raw/generic/legacy tool leaked through direct tunnel: ${forbidden}`);
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
  assert.equal(open.structuredContent?.browser_verification?.status, 'pass', textOf(open));

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
  const findStatus = await client.callTool({
    name: 'web_observe',
    arguments: { operation: 'find', regex: 'textbox "Direct tunnel status"' }
  });
  assert.equal(findStatus.isError, undefined, textOf(findStatus));
  const statusRef = accessibilityRefOnMatchingLine(
    findStatus,
    'textbox "Direct tunnel status"',
    'direct tunnel status search'
  );

  const click = await client.callTool({
    name: 'web_interact',
    arguments: {
      operation: 'click',
      target: buttonRef,
      element: 'Continue direct tunnel test button',
      expected: { control: { target: statusRef, value: 'DIRECT_TUNNEL_BROWSER_DONE' } }
    }
  });
  assert.equal(click.isError, undefined, textOf(click));
  assert.equal(click.structuredContent?.browser_verification?.status, 'pass', textOf(click));

  const findDone = await client.callTool({
    name: 'web_observe',
    arguments: { operation: 'find', text: 'DIRECT_TUNNEL_BROWSER_DONE' }
  });
  assert.equal(findDone.isError, undefined, textOf(findDone));
  assert(textOf(findDone).includes('DIRECT_TUNNEL_BROWSER_DONE'), textOf(findDone));

  const procedure = await client.callTool({
    name: 'procedure_run',
    arguments: {
      procedure: 'verified_workspace_artifact_v1',
      artifact_name: 'direct-tunnel-result.txt',
      content: 'DIRECT_TUNNEL_PROCEDURE_OK'
    }
  });
  assert.equal(procedure.isError, undefined, textOf(procedure));
  const procedurePayload = procedure.structuredContent ?? JSON.parse(textOf(procedure));
  assert.equal(procedurePayload.status, 'completed', textOf(procedure));
  assert.equal(procedurePayload.action_count, 3, textOf(procedure));

  const procedurePath = '.chat-agent-platform/stage26-3a/direct-tunnel-result.txt';
  const procedureRead = await client.callTool({
    name: 'workspace_read',
    arguments: { operation: 'read_text', path: procedurePath }
  });
  assert.equal(procedureRead.isError, undefined, textOf(procedureRead));
  assert(textOf(procedureRead).includes('DIRECT_TUNNEL_PROCEDURE_OK'), textOf(procedureRead));

  // Frozen ChatGPT action snapshots from the old Stage 24 route used
  // server-qualified action IDs. The launcher accepts those aliases without
  // republishing them in tools/list. Compatibility aliases inherit the current
  // bounded arguments/verification semantics; they do not preserve unsafe old
  // click behavior after the canonical action contract is hardened.
  const legacyRead = await client.callTool({
    name: 'semantic-projection_1mcp_workspace_read',
    arguments: { operation: 'read_text', path: 'direct-input.txt' }
  });
  assert.equal(legacyRead.isError, undefined, textOf(legacyRead));
  assert(textOf(legacyRead).includes('DIRECT_SEMANTIC_INPUT'), textOf(legacyRead));

  const legacyWrite = await client.callTool({
    name: 'semantic-projection_1mcp_workspace_write',
    arguments: { path: 'legacy-direct-output.txt', content: 'LEGACY_SEMANTIC_WRITE_OK' }
  });
  assert.equal(legacyWrite.isError, undefined, textOf(legacyWrite));
  assert.equal(fs.readFileSync(legacyOutputPath, 'utf8'), 'LEGACY_SEMANTIC_WRITE_OK');

  const legacyOpen = await client.callTool({
    name: 'semantic-projection_1mcp_web_open',
    arguments: { url: `${fixture.baseUrl}/` }
  });
  assert.equal(legacyOpen.isError, undefined, textOf(legacyOpen));
  assert.equal(legacyOpen.structuredContent?.browser_verification?.status, 'pass', textOf(legacyOpen));

  const legacyFindButton = await client.callTool({
    name: 'semantic-projection_1mcp_web_observe',
    arguments: { operation: 'find', text: 'Continue direct tunnel test' }
  });
  assert.equal(legacyFindButton.isError, undefined, textOf(legacyFindButton));
  const legacyButtonRef = accessibilityRefOnMatchingLine(
    legacyFindButton,
    'Continue direct tunnel test',
    'legacy direct tunnel button search'
  );
  const legacyFindStatus = await client.callTool({
    name: 'semantic-projection_1mcp_web_observe',
    arguments: { operation: 'find', regex: 'textbox "Direct tunnel status"' }
  });
  assert.equal(legacyFindStatus.isError, undefined, textOf(legacyFindStatus));
  const legacyStatusRef = accessibilityRefOnMatchingLine(
    legacyFindStatus,
    'textbox "Direct tunnel status"',
    'legacy direct tunnel status search'
  );

  const legacyClick = await client.callTool({
    name: 'semantic-projection_1mcp_web_interact',
    arguments: {
      operation: 'click',
      target: legacyButtonRef,
      element: 'Continue direct tunnel test button',
      expected: { control: { target: legacyStatusRef, value: 'DIRECT_TUNNEL_BROWSER_DONE' } }
    }
  });
  assert.equal(legacyClick.isError, undefined, textOf(legacyClick));
  assert.equal(legacyClick.structuredContent?.browser_verification?.status, 'pass', textOf(legacyClick));

  const legacyFindDone = await client.callTool({
    name: 'semantic-projection_1mcp_web_observe',
    arguments: { operation: 'find', text: 'DIRECT_TUNNEL_BROWSER_DONE' }
  });
  assert.equal(legacyFindDone.isError, undefined, textOf(legacyFindDone));
  assert(textOf(legacyFindDone).includes('DIRECT_TUNNEL_BROWSER_DONE'), textOf(legacyFindDone));

  console.log('DIRECT_SEMANTIC_PROTOCOL_ERA=modern');
  console.log('DIRECT_SEMANTIC_TOOL_COUNT=6');
  console.log('DIRECT_SEMANTIC_FILESYSTEM=PASS');
  console.log('DIRECT_SEMANTIC_BROWSER=PASS');
  console.log('DIRECT_SEMANTIC_BROWSER_VERIFICATION=PASS');
  console.log('DIRECT_SEMANTIC_PROCEDURE=PASS');
  console.log('DIRECT_SEMANTIC_LEGACY_ACTION_COMPAT=PASS');
  console.log('DIRECT_SEMANTIC_NEGATIVE_CASES=PASS');
  console.log(`DIRECT_SEMANTIC_CONNECT_MS=${connectMs}`);
  console.log('DIRECT_SEMANTIC_TUNNEL_ACCEPTANCE=PASS');
} finally {
  await client.close().catch(() => {});
  await closeHttpServer(fixture.server).catch(() => {});
}
