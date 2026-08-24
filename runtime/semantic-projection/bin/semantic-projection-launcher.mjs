#!/usr/bin/env node

import { spawn } from 'node:child_process';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

const tunnelOnlyCredentialKeys = [
  'CONTROL_PLANE_API_KEY',
  'OPENAI_API_KEY',
  'OPENAI_ADMIN_KEY'
];
const EXPECTED_SEMANTIC_TOOLS = Object.freeze([
  'procedure_run',
  'web_interact',
  'web_observe',
  'web_open',
  'workspace_read',
  'workspace_write'
]);

for (const key of tunnelOnlyCredentialKeys) {
  delete process.env[key];
}

if (process.argv.includes('--verify-credential-scrub')) {
  for (const key of tunnelOnlyCredentialKeys) {
    if (Object.prototype.hasOwnProperty.call(process.env, key)) {
      console.error(`semantic launcher failed to scrub ${key}`);
      process.exit(1);
    }
  }
  console.log('SEMANTIC_TUNNEL_CREDENTIAL_SCRUB=PASS');
  process.exit(0);
}

const LEGACY_TOOL_ALIASES = new Map([
  ['semantic-projection_1mcp_workspace_read', 'workspace_read'],
  ['semantic-projection_1mcp_workspace_write', 'workspace_write'],
  ['semantic-projection_1mcp_web_open', 'web_open'],
  ['semantic-projection_1mcp_web_observe', 'web_observe'],
  ['semantic-projection_1mcp_web_interact', 'web_interact'],
  ['semantic-projection_1mcp_procedure_run', 'procedure_run'],
  ['procedure-qualification-projection_1mcp_workspace_read', 'workspace_read'],
  ['procedure-qualification-projection_1mcp_workspace_write', 'workspace_write'],
  ['procedure-qualification-projection_1mcp_web_open', 'web_open'],
  ['procedure-qualification-projection_1mcp_web_observe', 'web_observe'],
  ['procedure-qualification-projection_1mcp_web_interact', 'web_interact'],
  ['procedure-qualification-projection_1mcp_procedure_run', 'procedure_run']
]);

function rewriteLegacyToolCall(line) {
  if (!line.trim()) return line;
  try {
    const message = JSON.parse(line);
    if (
      message?.method === 'tools/call' &&
      typeof message?.params?.name === 'string' &&
      LEGACY_TOOL_ALIASES.has(message.params.name)
    ) {
      message.params.name = LEGACY_TOOL_ALIASES.get(message.params.name);
      return JSON.stringify(message);
    }
  } catch {
    // Preserve any non-JSON protocol/debug line byte-for-byte apart from the
    // newline framing handled by the caller. The semantic child remains the
    // authority for protocol validation.
  }
  return line;
}

function childEnvironment(source) {
  const env = {};
  for (const [key, value] of Object.entries(source ?? {})) {
    if (typeof value === 'string') env[key] = value;
  }
  return env;
}

async function assertExpectedSemanticInventory(entry) {
  const client = new Client({
    name: 'chat-semantic-inventory-guard',
    version: '1.0.0'
  });
  const transport = new StdioClientTransport({
    command: process.execPath,
    args: [entry],
    env: childEnvironment(process.env)
  });

  try {
    await client.connect(transport);
    const inventory = await client.listTools();
    const names = inventory.tools.map(tool => tool.name).sort();
    if (
      names.length !== EXPECTED_SEMANTIC_TOOLS.length ||
      names.some((name, index) => name !== EXPECTED_SEMANTIC_TOOLS[index])
    ) {
      throw new Error(
        `expected exactly: ${EXPECTED_SEMANTIC_TOOLS.join(', ')}; actual: ${names.join(', ')}`
      );
    }
    return names;
  } finally {
    await client.close().catch(() => {});
  }
}

const launcherDir = path.dirname(fileURLToPath(import.meta.url));
const semanticEntry = path.join(launcherDir, 'semantic-control-plane-projection.mjs');
const inventoryTestIndex = process.argv.indexOf('--verify-inventory-entry');
if (inventoryTestIndex >= 0) {
  const candidate = process.argv[inventoryTestIndex + 1];
  if (!candidate) {
    console.error('semantic launcher --verify-inventory-entry requires one entry path');
    process.exit(2);
  }
  try {
    const names = await assertExpectedSemanticInventory(path.resolve(candidate));
    console.log(`SEMANTIC_LIVE_INVENTORY_GUARD=PASS;TOOLS=${names.join(',')}`);
    process.exit(0);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error(`semantic launcher live inventory preflight failed: ${message}`);
    process.exit(1);
  }
}

try {
  await assertExpectedSemanticInventory(semanticEntry);
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`semantic launcher live inventory preflight failed: ${message}`);
  process.exit(1);
}

const child = spawn(process.execPath, [semanticEntry], {
  env: process.env,
  stdio: ['pipe', 'pipe', 'pipe'],
  windowsHide: true
});

child.stdout.pipe(process.stdout);
child.stderr.pipe(process.stderr);

let inputBuffer = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => {
  inputBuffer += chunk;
  while (true) {
    const newlineIndex = inputBuffer.indexOf('\n');
    if (newlineIndex < 0) break;
    let line = inputBuffer.slice(0, newlineIndex);
    inputBuffer = inputBuffer.slice(newlineIndex + 1);
    if (line.endsWith('\r')) line = line.slice(0, -1);
    const outgoing = `${rewriteLegacyToolCall(line)}\n`;
    if (!child.stdin.write(outgoing)) {
      process.stdin.pause();
      child.stdin.once('drain', () => process.stdin.resume());
    }
  }
});

process.stdin.on('end', () => {
  if (inputBuffer.length > 0) {
    child.stdin.write(rewriteLegacyToolCall(inputBuffer));
    inputBuffer = '';
  }
  child.stdin.end();
});

function forwardSignal(signal) {
  if (!child.killed) {
    try { child.kill(signal); } catch {}
  }
}

process.on('SIGINT', () => forwardSignal('SIGINT'));
process.on('SIGTERM', () => forwardSignal('SIGTERM'));

child.on('error', error => {
  console.error(`semantic launcher child process failed: ${error.message}`);
  process.exitCode = 1;
});

child.on('exit', (code, signal) => {
  if (signal) {
    process.exitCode = 1;
    return;
  }
  process.exitCode = code ?? 1;
});
