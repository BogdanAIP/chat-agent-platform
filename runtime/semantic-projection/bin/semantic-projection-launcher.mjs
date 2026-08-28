#!/usr/bin/env node

import { spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

const tunnelOnlyCredentialKeys = [
  'CONTROL_PLANE_API_KEY',
  'OPENAI_API_KEY',
  'OPENAI_ADMIN_KEY'
];

export const EXPECTED_SEMANTIC_TOOLS = Object.freeze([
  'procedure_run',
  'web_interact',
  'web_observe',
  'web_open',
  'workspace_read',
  'workspace_write'
]);

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

function stringEnvironment(source) {
  const env = {};
  for (const [key, value] of Object.entries(source ?? {})) {
    if (typeof value === 'string') env[key] = value;
  }
  return env;
}

export function resolveSemanticRuntimePaths({
  env = process.env,
  platform = process.platform,
  pid = process.pid,
  tempDir = os.tmpdir()
} = {}) {
  if (!Number.isInteger(pid) || pid <= 0) {
    throw new Error('semantic runtime output ownership requires a positive process id');
  }

  let platformRoot;
  if (platform === 'win32') {
    const localAppData = typeof env?.LOCALAPPDATA === 'string' ? env.LOCALAPPDATA.trim() : '';
    if (!localAppData || !path.isAbsolute(localAppData)) {
      throw new Error('LOCALAPPDATA must be an absolute path for semantic runtime output ownership on Windows');
    }
    platformRoot = path.join(localAppData, 'ChatAgentPlatform');
  } else {
    if (!path.isAbsolute(tempDir)) {
      throw new Error('system temporary directory must be absolute for semantic runtime output ownership');
    }
    platformRoot = path.join(tempDir, 'ChatAgentPlatform');
  }

  const runtimeDirectory = path.join(
    platformRoot,
    'logs',
    'semantic-runtime',
    `session-${pid}`
  );
  const playwrightOutputDirectory = path.join(runtimeDirectory, 'playwright-mcp');
  return { platformRoot, runtimeDirectory, playwrightOutputDirectory };
}

export function prepareSemanticRuntimeEnvironment(options = {}) {
  const paths = resolveSemanticRuntimePaths(options);
  fs.mkdirSync(paths.playwrightOutputDirectory, { recursive: true });
  const env = stringEnvironment(options.env ?? process.env);
  env.PLAYWRIGHT_MCP_OUTPUT_DIR = paths.playwrightOutputDirectory;
  return { ...paths, env };
}

export async function assertExpectedSemanticInventory({ entry, env = process.env }) {
  if (typeof entry !== 'string' || entry.length === 0) {
    throw new Error('semantic inventory guard requires one semantic entry path');
  }

  const [{ Client }, { StdioClientTransport }] = await Promise.all([
    import('@modelcontextprotocol/client'),
    import('@modelcontextprotocol/client/stdio')
  ]);
  const client = new Client({
    name: 'chat-semantic-inventory-guard',
    version: '1.0.0'
  });
  const transport = new StdioClientTransport({
    command: process.execPath,
    args: [entry],
    env: stringEnvironment(env)
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

async function main() {
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

  const callerCwd = path.resolve(process.cwd());
  const runtime = prepareSemanticRuntimeEnvironment({ env: process.env });

  if (process.argv.includes('--verify-runtime-output-ownership')) {
    console.log(JSON.stringify({
      caller_cwd: callerCwd,
      runtime_dir: runtime.runtimeDirectory,
      playwright_output_dir: runtime.playwrightOutputDirectory,
      playwright_env_output_dir: runtime.env.PLAYWRIGHT_MCP_OUTPUT_DIR
    }));
    process.exit(0);
  }

  process.chdir(runtime.runtimeDirectory);

  const launcherDir = path.dirname(fileURLToPath(import.meta.url));
  const semanticEntry = path.join(launcherDir, 'semantic-control-plane-projection.mjs');

  try {
    await assertExpectedSemanticInventory({
      entry: semanticEntry,
      env: runtime.env
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error(`semantic launcher live inventory preflight failed: ${message}`);
    process.exitCode = 1;
    return;
  }

  const child = spawn(process.execPath, [semanticEntry], {
    cwd: runtime.runtimeDirectory,
    env: runtime.env,
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
}

const launcherPath = path.resolve(fileURLToPath(import.meta.url));
const invokedPath = process.argv[1] ? path.resolve(process.argv[1]) : '';
if (invokedPath === launcherPath) {
  await main();
}
