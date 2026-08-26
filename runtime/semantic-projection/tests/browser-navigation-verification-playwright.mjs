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

function textOf(result) {
  return (result.content ?? []).filter(block => block.type === 'text').map(block => block.text).join('\n');
}

function childEnvironment(extra) {
  const env = {};
  for (const [key, value] of Object.entries(process.env)) if (typeof value === 'string') env[key] = value;
  return { ...env, ...extra };
}

async function fixtureServer() {
  const server = http.createServer((request, response) => {
    if (request.url === '/redirect') {
      response.statusCode = 302;
      response.setHeader('Location', '/final');
      response.end();
      return;
    }
    response.setHeader('Content-Type', 'text/html; charset=utf-8');
    if (request.url === '/final') {
      response.end('<!doctype html><html><head><title>Redirect Final</title></head><body><h1>REDIRECT_FINAL</h1></body></html>');
      return;
    }
    response.end('<!doctype html><html><head><title>Verified Exact</title></head><body><h1>EXACT_NAVIGATION_OK</h1></body></html>');
  });
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
  const address = server.address();
  assert(address && typeof address === 'object');
  return { server, baseUrl: `http://127.0.0.1:${address.port}` };
}

async function closeServer(server) {
  await new Promise((resolve, reject) => server.close(error => (error ? reject(error) : resolve())));
}

const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-browser-navigation-verification-'));
const fixture = await fixtureServer();
const client = new Client({ name: 'browser-navigation-verification', version: '1.0.0' });
const transport = new StdioClientTransport({
  command: process.execPath,
  args: [projectionEntry],
  env: childEnvironment({ CHAT_LOCAL_FILES_ROOT: workspace }),
});

try {
  await client.connect(transport);

  const exact = await client.callTool({
    name: 'web_open',
    arguments: { url: `${fixture.baseUrl}/exact` },
  });
  assert.equal(exact.isError, undefined, textOf(exact));
  assert.equal(exact.structuredContent?.browser_verification?.status, 'pass');
  assert.equal(exact.structuredContent?.browser_verification?.verification?.status, 'pass');
  assert(textOf(exact).includes('web_open final-state verification=pass'), textOf(exact));

  const exactSnapshot = await client.callTool({ name: 'web_observe', arguments: { operation: 'snapshot' } });
  assert.equal(exactSnapshot.isError, undefined, textOf(exactSnapshot));
  assert(textOf(exactSnapshot).includes(`Page URL: ${fixture.baseUrl}/exact`), textOf(exactSnapshot));
  assert(textOf(exactSnapshot).includes('EXACT_NAVIGATION_OK'), textOf(exactSnapshot));

  const redirected = await client.callTool({
    name: 'web_open',
    arguments: { url: `${fixture.baseUrl}/redirect` },
  });
  assert.equal(redirected.isError, true, 'redirect must not be silently promoted before redirect policy is reviewed');
  assert.equal(redirected.structuredContent?.browser_verification?.status, 'fail');
  assert.equal(redirected.structuredContent?.browser_verification?.verification?.reason, 'expected_effect_failed');
  assert(textOf(redirected).includes('web_open final-state verification=fail'), textOf(redirected));

  const redirectSnapshot = await client.callTool({ name: 'web_observe', arguments: { operation: 'snapshot' } });
  assert.equal(redirectSnapshot.isError, undefined, textOf(redirectSnapshot));
  assert(textOf(redirectSnapshot).includes(`Page URL: ${fixture.baseUrl}/final`), textOf(redirectSnapshot));
  assert(textOf(redirectSnapshot).includes('REDIRECT_FINAL'), textOf(redirectSnapshot));

  console.log('BROWSER_NAVIGATION_KERNEL_INTEGRATION=PASS');
} finally {
  await client.close().catch(() => {});
  await closeServer(fixture.server).catch(() => {});
  fs.rmSync(workspace, { recursive: true, force: true });
}
