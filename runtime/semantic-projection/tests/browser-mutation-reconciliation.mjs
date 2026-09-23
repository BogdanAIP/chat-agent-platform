import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';
import { createSemanticActivationEnvironment } from '../lib/semantic-activation.mjs';


const here = path.dirname(fileURLToPath(import.meta.url));
const canonicalEntry = path.resolve(here, '..', 'bin', 'semantic-projection.mjs');
const source = fs.readFileSync(canonicalEntry, 'utf8').replaceAll('\r\n', '\n');

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

function refOnMatchingLine(result, needle) {
  for (const line of textOf(result).split(/\r?\n/)) {
    if (!line.includes(needle)) continue;
    const match = line.match(/\[ref=([^\]\s]+)\]/) ?? line.match(/\bref=([A-Za-z0-9_-]+)\b/);
    if (match) return match[1];
  }
  assert.fail(`missing accessibility ref for ${JSON.stringify(needle)}:\n${textOf(result)}`);
}

async function fixtureServer() {
  const server = http.createServer((_request, response) => {
    response.setHeader('Content-Type', 'text/html; charset=utf-8');
    response.end(`<!doctype html>
<html><body>
  <button id="go" onclick="document.getElementById('status').value='CLICKED'">Go</button>
  <label for="status">Status</label>
  <input id="status" aria-label="Status" value="WAITING" readonly />
  <label for="name">Name</label>
  <input id="name" aria-label="Name" value="" />
</body></html>`);
  });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  const address = server.address();
  assert(address && typeof address === 'object');
  return { server, url: `http://127.0.0.1:${address.port}/` };
}

async function closeServer(server) {
  await new Promise((resolve, reject) => server.close(error => error ? reject(error) : resolve()));
}

async function withInjectedProjection({ needle, replacement, scenario }) {
  const injected = source.replace(needle, replacement);
  assert.notEqual(injected, source, 'browser ACK-loss test failed to inject delivery failure');
  const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-browser-ack-loss-workspace-'));
  const entry = path.join(
    path.dirname(canonicalEntry),
    `.semantic-browser-ack-loss-${process.pid}-${Date.now()}-${Math.random().toString(16).slice(2)}.mjs`,
  );
  fs.writeFileSync(entry, injected, 'utf8');

  const client = new Client({ name: 'browser-ack-loss-acceptance', version: '1.0.0' });
  const transport = new StdioClientTransport({
    command: process.execPath,
    args: [entry],
    env: childEnvironment({ CHAT_LOCAL_FILES_ROOT: workspace }),
  });

  try {
    await client.connect(transport);
    await scenario(client);
  } finally {
    await client.close().catch(() => {});
    fs.rmSync(entry, { force: true });
    fs.rmSync(workspace, { recursive: true, force: true });
  }
}

const fixture = await fixtureServer();
try {
  await withInjectedProjection({
    needle: `    delivery = await providers.callBrowser('browser_navigate', { url: parsed.href });`,
    replacement: `    await providers.callBrowser('browser_navigate', { url: parsed.href });
    throw new Error('INJECTED_NAVIGATION_ACK_LOSS');`,
    scenario: async client => {
      const opened = await client.callTool({
        name: 'web_open',
        arguments: { url: fixture.url },
      });
      assert.equal(opened.isError, undefined, textOf(opened));
      assert.equal(opened.structuredContent?.browser_authorization?.status, 'authorized', textOf(opened));
      assert.equal(opened.structuredContent?.browser_verification?.status, 'pass', textOf(opened));
      assert.equal(opened.structuredContent?.delivery?.attempted, true, textOf(opened));
      assert.equal(opened.structuredContent?.delivery?.acknowledged, false, textOf(opened));
      assert.match(opened.structuredContent?.delivery?.error ?? '', /INJECTED_NAVIGATION_ACK_LOSS/);

      const repeat = await client.callTool({
        name: 'web_open',
        arguments: { url: fixture.url },
      });
      assert.equal(repeat.isError, undefined, textOf(repeat));
      assert.equal(repeat.structuredContent?.delivery?.attempted, false, textOf(repeat));
      assert.equal(
        repeat.structuredContent?.browser_verification?.reason,
        'already_satisfied_before_delivery',
        textOf(repeat),
      );
    },
  });

  await withInjectedProjection({
    needle: `        delivery = await providers.callBrowser('browser_click', downstream);`,
    replacement: `        await providers.callBrowser('browser_click', downstream);
        throw new Error('INJECTED_CLICK_ACK_LOSS');`,
    scenario: async client => {
      const opened = await client.callTool({ name: 'web_open', arguments: { url: fixture.url } });
      assert.equal(opened.isError, undefined, textOf(opened));

      const button = await client.callTool({ name: 'web_observe', arguments: { operation: 'find', text: 'Go' } });
      const status = await client.callTool({ name: 'web_observe', arguments: { operation: 'find', regex: 'textbox "Status"' } });
      const buttonRef = refOnMatchingLine(button, 'button "Go"');
      const statusRef = refOnMatchingLine(status, 'textbox "Status"');

      const clicked = await client.callTool({
        name: 'web_interact',
        arguments: {
          operation: 'click',
          target: buttonRef,
          expected: { control: { target: statusRef, value: 'CLICKED' } },
        },
      });
      assert.equal(clicked.isError, undefined, textOf(clicked));
      assert.equal(clicked.structuredContent?.browser_authorization?.status, 'authorized', textOf(clicked));
      assert.equal(clicked.structuredContent?.browser_verification?.status, 'pass', textOf(clicked));
      assert.equal(clicked.structuredContent?.delivery?.attempted, true, textOf(clicked));
      assert.equal(clicked.structuredContent?.delivery?.acknowledged, false, textOf(clicked));
      assert.match(clicked.structuredContent?.delivery?.error ?? '', /INJECTED_CLICK_ACK_LOSS/);

      const repeat = await client.callTool({
        name: 'web_interact',
        arguments: {
          operation: 'click',
          target: buttonRef,
          expected: { control: { target: statusRef, value: 'CLICKED' } },
        },
      });
      assert.equal(repeat.isError, true, 'already-satisfied interaction must not click twice');
      assert.match(textOf(repeat), /already satisfied/);
    },
  });

  await withInjectedProjection({
    needle: `        delivery = await providers.callBrowser('browser_type', downstream);`,
    replacement: `        await providers.callBrowser('browser_type', downstream);
        throw new Error('INJECTED_TYPE_ACK_LOSS');`,
    scenario: async client => {
      const opened = await client.callTool({ name: 'web_open', arguments: { url: fixture.url } });
      assert.equal(opened.isError, undefined, textOf(opened));

      const input = await client.callTool({ name: 'web_observe', arguments: { operation: 'find', regex: 'textbox "Name"' } });
      const inputRef = refOnMatchingLine(input, 'textbox "Name"');

      const typed = await client.callTool({
        name: 'web_interact',
        arguments: {
          operation: 'type',
          target: inputRef,
          text: 'TYPE_ACK_VERIFIED',
        },
      });
      assert.equal(typed.isError, undefined, textOf(typed));
      assert.equal(typed.structuredContent?.browser_authorization?.status, 'authorized', textOf(typed));
      assert.equal(typed.structuredContent?.browser_verification?.status, 'pass', textOf(typed));
      assert.equal(typed.structuredContent?.delivery?.attempted, true, textOf(typed));
      assert.equal(typed.structuredContent?.delivery?.acknowledged, false, textOf(typed));
      assert.match(typed.structuredContent?.delivery?.error ?? '', /INJECTED_TYPE_ACK_LOSS/);

      const repeat = await client.callTool({
        name: 'web_interact',
        arguments: {
          operation: 'type',
          target: inputRef,
          text: 'TYPE_ACK_VERIFIED',
        },
      });
      assert.equal(repeat.isError, true, 'already-satisfied type must not be delivered twice');
      assert.match(textOf(repeat), /already satisfied/);
    },
  });

  console.log('SEMANTIC_BROWSER_NAV_ACK_LOSS_RECONCILED=PASS');
  console.log('SEMANTIC_BROWSER_CLICK_ACK_LOSS_RECONCILED=PASS');
  console.log('SEMANTIC_BROWSER_TYPE_ACK_LOSS_RECONCILED=PASS');
  console.log('SEMANTIC_BROWSER_REPEAT_NO_BLIND_RETRY=PASS');
} finally {
  await closeServer(fixture.server).catch(() => {});
}
