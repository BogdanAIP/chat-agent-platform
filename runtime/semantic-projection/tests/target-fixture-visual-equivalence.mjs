import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import process from 'node:process';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

import { parseScreenshotResult } from '../lib/visual-grounding-bridge.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, '..', '..', '..');
const original = fs.readFileSync(path.join(repoRoot, 'tests', 'fixtures', 'stage25_grounding_fixture.html'), 'utf8');
const target = fs.readFileSync(path.join(repoRoot, 'tests', 'fixtures', 'stage25_1_runtime_grounding_fixture.html'), 'utf8');
const require = createRequire(import.meta.url);
const playwrightManifest = require.resolve('@playwright/mcp/package.json');
const playwrightEntry = path.join(path.dirname(playwrightManifest), 'cli.js');

function childEnvironment() {
  const env = {};
  for (const [key, value] of Object.entries(process.env)) {
    if (typeof value === 'string') env[key] = value;
  }
  return env;
}

async function startServer() {
  const server = http.createServer((request, response) => {
    response.setHeader('Content-Type', 'text/html; charset=utf-8');
    response.end(request.url === '/target' ? target : original);
  });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  const address = server.address();
  assert(address && typeof address === 'object');
  return { server, baseUrl: `http://127.0.0.1:${address.port}` };
}

async function closeServer(server) {
  await new Promise((resolve, reject) => server.close(error => (error ? reject(error) : resolve())));
}

async function screenshot(client, url) {
  const opened = await client.callTool({ name: 'browser_navigate', arguments: { url } });
  assert.equal(opened?.isError, undefined);
  const shot = await client.callTool({
    name: 'browser_take_screenshot',
    arguments: { type: 'png', fullPage: false, scale: 'css' }
  });
  return parseScreenshotResult(shot);
}

const fixture = await startServer();
const client = new Client({ name: 'stage25-1-fixture-equivalence', version: '1.0.0' });
const transport = new StdioClientTransport({
  command: process.execPath,
  args: [
    playwrightEntry,
    '--headless',
    '--browser',
    'chrome',
    '--isolated',
    '--image-responses',
    'allow',
    '--block-service-workers',
    '--codegen',
    'none',
    '--caps',
    'vision',
    '--viewport-size',
    '1280x720',
    '--timeout-action',
    '15000'
  ],
  env: childEnvironment()
});

try {
  await client.connect(transport);
  const originalShot = await screenshot(client, `${fixture.baseUrl}/original`);
  const targetShot = await screenshot(client, `${fixture.baseUrl}/target`);

  assert.deepEqual(
    { width: originalShot.width, height: originalShot.height },
    { width: 1280, height: 720 }
  );
  assert.deepEqual(
    { width: targetShot.width, height: targetShot.height },
    { width: 1280, height: 720 }
  );
  assert.equal(
    targetShot.sha256,
    originalShot.sha256,
    `Stage 25.1 telemetry fixture changed pre-click pixels: original=${originalShot.sha256} target=${targetShot.sha256}`
  );

  console.log(`STAGE25_1_FIXTURE_PIXEL_SHA256=${targetShot.sha256}`);
  console.log('STAGE25_1_FIXTURE_VISUAL_EQUIVALENCE=PASS');
} finally {
  await client.close().catch(() => {});
  await closeServer(fixture.server).catch(() => {});
}
