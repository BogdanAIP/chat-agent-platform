import { createRequire } from 'node:module';
import path from 'node:path';
import process from 'node:process';

import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

import { semanticProviderEnvironment } from './semantic-activation.mjs';


const require = createRequire(import.meta.url);
const FILESYSTEM_ENTRY = require.resolve('@modelcontextprotocol/server-filesystem/dist/index.js');
const PLAYWRIGHT_MANIFEST = require.resolve('@playwright/mcp/package.json');
const PLAYWRIGHT_ENTRY = path.join(path.dirname(PLAYWRIGHT_MANIFEST), 'cli.js');

const PLAYWRIGHT_DEFENSE_BLOCKED_ORIGINS = [
  'http://169.254.169.254:*',
  'https://169.254.169.254:*',
  'http://metadata.google.internal:*',
  'https://metadata.google.internal:*',
].join(';');

const REQUIRED_FILESYSTEM_TOOLS = new Set([
  'list_allowed_directories',
  'read_text_file',
  'search_files',
  'write_file',
]);

const REQUIRED_BROWSER_TOOLS = new Set([
  'browser_navigate',
  'browser_find',
  'browser_snapshot',
  'browser_click',
  'browser_type',
  'browser_take_screenshot',
  'browser_mouse_click_xy',
]);


function normalizeBackendResult(result) {
  const normalized = { content: Array.isArray(result?.content) ? result.content : [] };
  if (result?.isError) normalized.isError = true;
  if (result?.structuredContent !== undefined) normalized.structuredContent = result.structuredContent;
  return normalized;
}

function localNodeCommand(entryPoint, extraArgs = []) {
  return { command: process.execPath, args: [entryPoint, ...extraArgs] };
}

async function connectBackend({ label, spec, requiredTools, version }) {
  const client = new Client({ name: `chat-semantic-projection-${label}`, version });
  const transport = new StdioClientTransport({
    ...spec,
    env: semanticProviderEnvironment(),
  });
  try {
    await client.connect(transport);
    const inventory = await client.listTools();
    const names = new Set(inventory.tools.map(tool => tool.name));
    const missing = [...requiredTools].filter(name => !names.has(name));
    if (missing.length > 0) {
      throw new Error(`${label} backend is missing required tools: ${missing.join(', ')}`);
    }
    return { client, transport };
  } catch (error) {
    try { await client.close(); } catch {}
    throw error;
  }
}

export function createSemanticProviderBindings({ workspaceRoot, version }) {
  if (typeof workspaceRoot !== 'string' || workspaceRoot.length === 0) {
    throw new TypeError('workspaceRoot must be a non-empty string');
  }
  if (typeof version !== 'string' || version.length === 0) {
    throw new TypeError('version must be a non-empty string');
  }

  let filesystemPromise = null;
  let browserPromise = null;

  function getFilesystem() {
    if (filesystemPromise === null) {
      filesystemPromise = connectBackend({
        label: 'filesystem',
        spec: localNodeCommand(FILESYSTEM_ENTRY, [workspaceRoot]),
        requiredTools: REQUIRED_FILESYSTEM_TOOLS,
        version,
      }).catch(error => {
        filesystemPromise = null;
        throw error;
      });
    }
    return filesystemPromise;
  }

  function getBrowser() {
    if (browserPromise === null) {
      browserPromise = connectBackend({
        label: 'playwright',
        spec: localNodeCommand(PLAYWRIGHT_ENTRY, [
          '--headless',
          '--browser',
          'chrome',
          '--isolated',
          '--image-responses',
          'allow',
          '--blocked-origins',
          PLAYWRIGHT_DEFENSE_BLOCKED_ORIGINS,
          '--block-service-workers',
          '--codegen',
          'none',
          '--caps',
          'vision',
          '--timeout-action',
          '15000',
        ]),
        requiredTools: REQUIRED_BROWSER_TOOLS,
        version,
      }).catch(error => {
        browserPromise = null;
        throw error;
      });
    }
    return browserPromise;
  }

  async function call(getter, requiredTools, label, toolName, args) {
    if (!requiredTools.has(toolName)) {
      throw new Error(`Projection refused non-allowlisted downstream tool: ${label}.${toolName}`);
    }
    const { client } = await getter();
    return normalizeBackendResult(await client.callTool({ name: toolName, arguments: args }));
  }

  return Object.freeze({
    callFilesystem(toolName, args) {
      return call(getFilesystem, REQUIRED_FILESYSTEM_TOOLS, 'filesystem', toolName, args);
    },
    callBrowser(toolName, args) {
      return call(getBrowser, REQUIRED_BROWSER_TOOLS, 'playwright', toolName, args);
    },
    async browserClient() {
      const { client } = await getBrowser();
      return client;
    },
    async close() {
      const pending = [filesystemPromise, browserPromise].filter(value => value !== null);
      filesystemPromise = null;
      browserPromise = null;
      const settled = await Promise.allSettled(pending);
      const closes = [];
      for (const entry of settled) {
        if (entry.status === 'fulfilled') closes.push(entry.value.client.close());
      }
      await Promise.allSettled(closes);
    },
  });
}
