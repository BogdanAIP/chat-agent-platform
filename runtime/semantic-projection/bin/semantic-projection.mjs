#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';
import { McpServer } from '@modelcontextprotocol/server';
import { serveStdio } from '@modelcontextprotocol/server/stdio';
import * as z from 'zod/v4';

const VERSION = '0.1.0';
const FILESYSTEM_PACKAGE = '@modelcontextprotocol/server-filesystem@2026.7.10';
const PLAYWRIGHT_PACKAGE = '@playwright/mcp@0.0.78';
const REQUIRED_FILESYSTEM_TOOLS = new Set([
  'list_allowed_directories',
  'read_text_file',
  'search_files',
  'write_file'
]);
const REQUIRED_PLAYWRIGHT_TOOLS = new Set([
  'browser_navigate',
  'browser_find',
  'browser_snapshot',
  'browser_click',
  'browser_type'
]);

const workspaceRootInput = process.env.CHAT_LOCAL_FILES_ROOT;
if (!workspaceRootInput) {
  throw new Error('CHAT_LOCAL_FILES_ROOT is required for semantic projection.');
}

const workspaceRoot = path.resolve(workspaceRootInput);
const workspaceStat = fs.statSync(workspaceRoot, { throwIfNoEntry: false });
if (!workspaceStat?.isDirectory()) {
  throw new Error(`CHAT_LOCAL_FILES_ROOT must be an existing directory: ${workspaceRoot}`);
}

const backendPromises = new Map();
let shuttingDown = false;

function localNpxCommand(packageName, extraArgs = []) {
  if (process.platform === 'win32') {
    return {
      command: 'cmd',
      args: ['/c', 'npx', '-y', packageName, ...extraArgs]
    };
  }
  return {
    command: 'npx',
    args: ['-y', packageName, ...extraArgs]
  };
}

function resolveWorkspacePath(relativePath) {
  if (typeof relativePath !== 'string' || relativePath.length === 0) {
    throw new Error('A non-empty relative workspace path is required.');
  }
  if (
    path.isAbsolute(relativePath) ||
    path.win32.isAbsolute(relativePath) ||
    path.posix.isAbsolute(relativePath)
  ) {
    throw new Error('Absolute paths are not accepted; use a path relative to the configured workspace root.');
  }

  const resolved = path.resolve(workspaceRoot, relativePath);
  const relative = path.relative(workspaceRoot, resolved);
  if (relative === '..' || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) {
    throw new Error('Workspace path escapes the configured root.');
  }
  return resolved;
}

function normalizeBackendResult(result) {
  const normalized = { content: Array.isArray(result?.content) ? result.content : [] };
  if (result?.isError) normalized.isError = true;
  if (result?.structuredContent !== undefined) {
    normalized.structuredContent = result.structuredContent;
  }
  return normalized;
}

function toolError(message) {
  return {
    content: [{ type: 'text', text: message }],
    isError: true
  };
}

async function createBackend(kind) {
  let spec;
  let requiredTools;

  if (kind === 'filesystem') {
    spec = localNpxCommand(FILESYSTEM_PACKAGE, [workspaceRoot]);
    requiredTools = REQUIRED_FILESYSTEM_TOOLS;
  } else if (kind === 'playwright') {
    spec = localNpxCommand(PLAYWRIGHT_PACKAGE, [
      '--headless',
      '--browser',
      'chrome',
      '--isolated',
      '--image-responses',
      'omit',
      '--block-service-workers',
      '--codegen',
      'none'
    ]);
    requiredTools = REQUIRED_PLAYWRIGHT_TOOLS;
  } else {
    throw new Error(`Unknown backend kind: ${kind}`);
  }

  const client = new Client({
    name: `chat-semantic-projection-${kind}`,
    version: VERSION
  });
  const transport = new StdioClientTransport(spec);

  try {
    await client.connect(transport);
    const inventory = await client.listTools();
    const names = new Set(inventory.tools.map(tool => tool.name));
    const missing = [...requiredTools].filter(name => !names.has(name));
    if (missing.length > 0) {
      throw new Error(`${kind} backend is missing required tools: ${missing.join(', ')}`);
    }
    return { client, transport };
  } catch (error) {
    try {
      await client.close();
    } catch {
      // Preserve the original connection/inventory error.
    }
    throw error;
  }
}

async function getBackend(kind) {
  if (!backendPromises.has(kind)) {
    const pending = createBackend(kind).catch(error => {
      backendPromises.delete(kind);
      throw error;
    });
    backendPromises.set(kind, pending);
  }
  return backendPromises.get(kind);
}

async function callBackend(kind, toolName, args) {
  const required = kind === 'filesystem' ? REQUIRED_FILESYSTEM_TOOLS : REQUIRED_PLAYWRIGHT_TOOLS;
  if (!required.has(toolName)) {
    throw new Error(`Projection refused non-allowlisted downstream tool: ${kind}.${toolName}`);
  }
  const { client } = await getBackend(kind);
  const result = await client.callTool({ name: toolName, arguments: args });
  return normalizeBackendResult(result);
}

async function closeBackends() {
  const pending = [...backendPromises.values()];
  backendPromises.clear();
  const settled = await Promise.allSettled(pending);
  const closes = [];
  for (const entry of settled) {
    if (entry.status === 'fulfilled') {
      closes.push(entry.value.client.close());
    }
  }
  await Promise.allSettled(closes);
}

async function shutdown(code = 0) {
  if (shuttingDown) return;
  shuttingDown = true;
  await closeBackends();
  process.exit(code);
}

process.on('SIGINT', () => void shutdown(0));
process.on('SIGTERM', () => void shutdown(0));
process.stdin.on('end', () => void closeBackends());
process.stdin.on('close', () => void closeBackends());

const relativePathSchema = z
  .string()
  .min(1)
  .max(2048)
  .describe('Path relative to the configured workspace root. Absolute paths and parent traversal are rejected.');

const server = new McpServer(
  { name: 'chat-semantic-projection', version: VERSION },
  {
    instructions:
      'This server exposes a small fixed semantic projection. It cannot invoke arbitrary downstream tools. Workspace paths are relative to one configured root. Browser actions use an isolated headless Playwright session.'
  }
);

server.registerTool(
  'workspace_read',
  {
    title: 'Read Workspace',
    description:
      'Read-only workspace operations. operation=roots lists allowed roots; read_text reads one text file; search finds matching paths under a workspace subdirectory. No arbitrary backend/tool selection is available.',
    inputSchema: z
      .object({
        operation: z.enum(['roots', 'read_text', 'search']),
        path: relativePathSchema.optional(),
        head: z.number().int().positive().max(100000).optional(),
        tail: z.number().int().positive().max(100000).optional(),
        pattern: z.string().min(1).max(512).optional(),
        excludePatterns: z.array(z.string().max(512)).max(64).optional()
      })
      .strict(),
    annotations: {
      readOnlyHint: true,
      idempotentHint: true,
      openWorldHint: false
    }
  },
  async args => {
    try {
      if (args.operation === 'roots') {
        return await callBackend('filesystem', 'list_allowed_directories', {});
      }
      if (args.operation === 'read_text') {
        if (!args.path) return toolError('workspace_read read_text requires path.');
        if (args.head && args.tail) return toolError('Use head or tail, not both.');
        const downstream = { path: resolveWorkspacePath(args.path) };
        if (args.head !== undefined) downstream.head = args.head;
        if (args.tail !== undefined) downstream.tail = args.tail;
        return await callBackend('filesystem', 'read_text_file', downstream);
      }
      if (!args.pattern) return toolError('workspace_read search requires pattern.');
      const searchPath = resolveWorkspacePath(args.path ?? '.');
      const downstream = { path: searchPath, pattern: args.pattern };
      if (args.excludePatterns !== undefined) downstream.excludePatterns = args.excludePatterns;
      return await callBackend('filesystem', 'search_files', downstream);
    } catch (error) {
      return toolError(`workspace_read failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
);

server.registerTool(
  'workspace_write',
  {
    title: 'Write Workspace Text',
    description:
      'Create or overwrite one UTF-8 text file inside the configured workspace root. The path must be relative; arbitrary filesystem tools are not available.',
    inputSchema: z
      .object({
        path: relativePathSchema,
        content: z.string().max(4_000_000)
      })
      .strict(),
    annotations: {
      readOnlyHint: false,
      destructiveHint: true,
      idempotentHint: true,
      openWorldHint: false
    }
  },
  async ({ path: relativePath, content }) => {
    try {
      return await callBackend('filesystem', 'write_file', {
        path: resolveWorkspacePath(relativePath),
        content
      });
    } catch (error) {
      return toolError(`workspace_write failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
);

server.registerTool(
  'web_open',
  {
    title: 'Open Web Page',
    description:
      'Navigate the isolated headless browser to one HTTP or HTTPS URL. File, javascript, data and credential-bearing URLs are rejected.',
    inputSchema: z.object({ url: z.string().url().max(4096) }).strict(),
    annotations: {
      readOnlyHint: false,
      destructiveHint: false,
      idempotentHint: false,
      openWorldHint: true
    }
  },
  async ({ url }) => {
    try {
      const parsed = new URL(url);
      if (!['http:', 'https:'].includes(parsed.protocol)) {
        return toolError('web_open accepts only HTTP or HTTPS URLs.');
      }
      if (parsed.username || parsed.password) {
        return toolError('web_open rejects URLs containing embedded credentials.');
      }
      return await callBackend('playwright', 'browser_navigate', { url: parsed.href });
    } catch (error) {
      return toolError(`web_open failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
);

server.registerTool(
  'web_observe',
  {
    title: 'Observe Web Page',
    description:
      'Read-only browser observation. operation=find searches the current accessibility snapshot by plain text or regex. operation=snapshot captures the accessibility snapshot, optionally for one target. No screenshots, network bodies or arbitrary code are exposed.',
    inputSchema: z
      .object({
        operation: z.enum(['find', 'snapshot']),
        text: z.string().min(1).max(2048).optional(),
        regex: z.string().min(1).max(2048).optional(),
        target: z.string().min(1).max(4096).optional(),
        depth: z.number().int().positive().max(100).optional(),
        boxes: z.boolean().optional()
      })
      .strict(),
    annotations: {
      readOnlyHint: true,
      idempotentHint: true,
      openWorldHint: true
    }
  },
  async args => {
    try {
      if (args.operation === 'find') {
        if (Boolean(args.text) === Boolean(args.regex)) {
          return toolError('web_observe find requires exactly one of text or regex.');
        }
        return await callBackend('playwright', 'browser_find', args.text ? { text: args.text } : { regex: args.regex });
      }
      const downstream = {};
      if (args.target !== undefined) downstream.target = args.target;
      if (args.depth !== undefined) downstream.depth = args.depth;
      if (args.boxes !== undefined) downstream.boxes = args.boxes;
      return await callBackend('playwright', 'browser_snapshot', downstream);
    } catch (error) {
      return toolError(`web_observe failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
);

server.registerTool(
  'web_interact',
  {
    title: 'Interact With Web Page',
    description:
      'Interact with the isolated browser using a closed operation set: click one target or type text into one target. No arbitrary Playwright/JavaScript, file upload, direct network inspection or backend/tool selection is available.',
    inputSchema: z
      .object({
        operation: z.enum(['click', 'type']),
        target: z.string().min(1).max(4096),
        element: z.string().min(1).max(1024).optional(),
        doubleClick: z.boolean().optional(),
        text: z.string().max(200000).optional(),
        submit: z.boolean().optional(),
        slowly: z.boolean().optional()
      })
      .strict(),
    annotations: {
      readOnlyHint: false,
      destructiveHint: true,
      idempotentHint: false,
      openWorldHint: true
    }
  },
  async args => {
    try {
      if (args.operation === 'click') {
        if (args.text !== undefined || args.submit !== undefined || args.slowly !== undefined) {
          return toolError('web_interact click does not accept type-only arguments.');
        }
        const downstream = { target: args.target };
        if (args.element !== undefined) downstream.element = args.element;
        if (args.doubleClick !== undefined) downstream.doubleClick = args.doubleClick;
        return await callBackend('playwright', 'browser_click', downstream);
      }
      if (args.text === undefined) return toolError('web_interact type requires text.');
      if (args.doubleClick !== undefined) return toolError('web_interact type does not accept doubleClick.');
      const downstream = { target: args.target, text: args.text };
      if (args.element !== undefined) downstream.element = args.element;
      if (args.submit !== undefined) downstream.submit = args.submit;
      if (args.slowly !== undefined) downstream.slowly = args.slowly;
      return await callBackend('playwright', 'browser_type', downstream);
    } catch (error) {
      return toolError(`web_interact failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
);

void serveStdio(() => server).catch(async error => {
  console.error(`semantic projection failed: ${error instanceof Error ? error.stack ?? error.message : String(error)}`);
  await closeBackends();
  process.exitCode = 1;
});
