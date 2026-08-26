#!/usr/bin/env node

import fs from 'node:fs';
import { createRequire } from 'node:module';
import net from 'node:net';
import path from 'node:path';
import process from 'node:process';

import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';
import { McpServer } from '@modelcontextprotocol/server';
import { serveStdio } from '@modelcontextprotocol/server/stdio';
import * as z from 'zod/v4';

import {
  parsePlaywrightSnapshotResult,
  verifyPlaywrightInteraction,
  verifyPlaywrightNavigation,
} from '../lib/browser-verification-bridge.mjs';
import { createSemanticVisionClickRouter } from '../lib/semantic-vision-click-router.mjs';

const VERSION = '0.1.0';
const require = createRequire(import.meta.url);
const FILESYSTEM_ENTRY = require.resolve('@modelcontextprotocol/server-filesystem/dist/index.js');
const PLAYWRIGHT_MANIFEST = require.resolve('@playwright/mcp/package.json');
const PLAYWRIGHT_ENTRY = path.join(path.dirname(PLAYWRIGHT_MANIFEST), 'cli.js');
const PLAYWRIGHT_DEFENSE_BLOCKED_ORIGINS = [
  'http://169.254.169.254:*',
  'https://169.254.169.254:*',
  'http://metadata.google.internal:*',
  'https://metadata.google.internal:*'
].join(';');
const REQUIRED_FILESYSTEM_TOOLS = new Set([
  'list_allowed_directories', 'read_text_file', 'search_files', 'write_file'
]);
const REQUIRED_PLAYWRIGHT_TOOLS = new Set([
  'browser_navigate', 'browser_find', 'browser_snapshot', 'browser_click', 'browser_type',
  'browser_take_screenshot', 'browser_mouse_click_xy'
]);

const workspaceRootInput = process.env.CHAT_LOCAL_FILES_ROOT;
if (!workspaceRootInput) throw new Error('CHAT_LOCAL_FILES_ROOT is required for semantic projection.');
const workspaceRoot = path.resolve(workspaceRootInput);
const workspaceStat = fs.statSync(workspaceRoot, { throwIfNoEntry: false });
if (!workspaceStat?.isDirectory()) {
  throw new Error(`CHAT_LOCAL_FILES_ROOT must be an existing directory: ${workspaceRoot}`);
}

const backendPromises = new Map();
let semanticVisionRouter = null;
let semanticVisionClient = null;
let shuttingDown = false;

function localNodeCommand(entryPoint, extraArgs = []) {
  return { command: process.execPath, args: [entryPoint, ...extraArgs] };
}

function resolveWorkspacePath(relativePath) {
  if (typeof relativePath !== 'string' || relativePath.length === 0) {
    throw new Error('A non-empty relative workspace path is required.');
  }
  if (path.isAbsolute(relativePath) || path.win32.isAbsolute(relativePath) || path.posix.isAbsolute(relativePath)) {
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
  if (result?.structuredContent !== undefined) normalized.structuredContent = result.structuredContent;
  return normalized;
}

function toolError(message) {
  return { content: [{ type: 'text', text: message }], isError: true };
}

function visualOutcomeResult(outcome) {
  if (outcome?.status === 'acted' && outcome.source === 'semantic' && outcome.backendResult) {
    return normalizeBackendResult(outcome.backendResult);
  }
  if (outcome?.status === 'acted' && outcome.source === 'vision') {
    return {
      content: [{ type: 'text', text: 'web_interact click completed through the reviewed same-session visual fallback after a proven semantic miss.' }]
    };
  }
  const reason = typeof outcome?.reason === 'string' && outcome.reason ? outcome.reason : 'unknown-escalation-result';
  if (outcome?.status === 'abstain') {
    return {
      content: [{ type: 'text', text: `web_interact abstained with no action: ${reason}` }]
    };
  }
  return toolError(`web_interact performed no action because of an error: ${reason}`);
}

function normalizeNavigationHostname(hostname) {
  let normalized = String(hostname ?? '').trim().toLowerCase();
  if (normalized.startsWith('[') && normalized.endsWith(']')) normalized = normalized.slice(1, -1);
  while (normalized.endsWith('.')) normalized = normalized.slice(0, -1);
  return normalized;
}

function classifyDirectNavigationHost(hostname) {
  const host = normalizeNavigationHostname(hostname);
  if (!host) return { allowed: false, scope: 'empty-host' };
  if (host === 'localhost' || host.endsWith('.localhost')) return { allowed: true, scope: 'loopback' };
  if (host === 'metadata.google.internal') return { allowed: false, scope: 'metadata-hostname' };

  const ipVersion = net.isIP(host);
  if (ipVersion === 4) {
    const octets = host.split('.').map(value => Number.parseInt(value, 10));
    const [a, b, c] = octets;
    if (a === 127) return { allowed: true, scope: 'loopback' };
    const blocked =
      a === 0 || a === 10 ||
      (a === 100 && b >= 64 && b <= 127) ||
      (a === 169 && b === 254) ||
      (a === 172 && b >= 16 && b <= 31) ||
      (a === 192 && b === 0 && c === 0) ||
      (a === 192 && b === 0 && c === 2) ||
      (a === 192 && b === 88 && c === 99) ||
      (a === 192 && b === 168) ||
      (a === 198 && (b === 18 || b === 19)) ||
      (a === 198 && b === 51 && c === 100) ||
      (a === 203 && b === 0 && c === 113) || a >= 224;
    return blocked
      ? { allowed: false, scope: a === 169 && b === 254 ? 'link-local-or-metadata-ip' : 'non-public-ip' }
      : { allowed: true, scope: 'public-ip' };
  }
  if (ipVersion === 6) {
    if (host === '::1') return { allowed: true, scope: 'loopback' };
    const blocked = host === '::' || host.startsWith('::ffff:') || /^f[cd]/.test(host) || /^fe[89ab]/.test(host) || /^ff/.test(host) || /^2001:db8(?::|$)/.test(host);
    return blocked ? { allowed: false, scope: 'non-public-ip' } : { allowed: true, scope: 'public-ip' };
  }
  return { allowed: true, scope: 'hostname' };
}

function normalizeExpectedBrowserUrl(value) {
  const parsed = new URL(value);
  if (!['http:', 'https:'].includes(parsed.protocol)) {
    throw new Error('web_interact expected.url accepts only HTTP or HTTPS URLs.');
  }
  if (parsed.username || parsed.password) {
    throw new Error('web_interact expected.url rejects embedded credentials.');
  }
  const policy = classifyDirectNavigationHost(parsed.hostname);
  if (!policy.allowed) {
    throw new Error(`web_interact expected.url rejects direct ${policy.scope} destinations by default: ${parsed.hostname}.`);
  }
  return parsed.href;
}

function normalizeInteractionExpected(args) {
  const explicit = args.expected;
  if (explicit === undefined) {
    if (args.operation === 'type' && args.submit !== true) {
      if (!args.target) throw new Error('web_interact type requires target.');
      if (args.text === undefined) throw new Error('web_interact type requires text.');
      if (args.target.length > 512) {
        throw new Error('web_interact type target is too long to bind as a verified control-ref.');
      }
      if (args.text.length > 4096) {
        throw new Error('web_interact type text exceeds the auto-verifiable control value limit; provide an explicit bounded expected result.');
      }
      return { control: { control_id: args.target, value: args.text } };
    }
    throw new Error('web_interact click and type+submit require an explicit expected postcondition before any action is delivered.');
  }

  const normalized = {};
  if (explicit.url !== undefined) normalized.url = normalizeExpectedBrowserUrl(explicit.url);
  if (explicit.control !== undefined) {
    const control = explicit.control;
    const controlId = control.target ?? args.target;
    if (!controlId) throw new Error('web_interact expected.control requires target or an action target.');
    if (controlId.length > 512) throw new Error('web_interact expected.control target exceeds 512 characters.');
    const stateFields = ['value', 'checked', 'selected', 'enabled'].filter(field => control[field] !== undefined);
    if (control.present === undefined && stateFields.length === 0) {
      throw new Error('web_interact expected.control requires present or one state field.');
    }
    if (control.present === false && stateFields.length > 0) {
      throw new Error('web_interact expected.control cannot combine present=false with state fields.');
    }
    normalized.control = { control_id: controlId };
    if (control.present !== undefined) normalized.control.present = control.present;
    for (const field of stateFields) normalized.control[field] = control[field];
  }
  if (Object.keys(normalized).length === 0) {
    throw new Error('web_interact expected requires url and/or control postcondition.');
  }
  return normalized;
}

async function createBackend(kind) {
  let spec;
  let requiredTools;
  if (kind === 'filesystem') {
    spec = localNodeCommand(FILESYSTEM_ENTRY, [workspaceRoot]);
    requiredTools = REQUIRED_FILESYSTEM_TOOLS;
  } else if (kind === 'playwright') {
    spec = localNodeCommand(PLAYWRIGHT_ENTRY, [
      '--headless', '--browser', 'chrome', '--isolated', '--image-responses', 'allow',
      '--blocked-origins', PLAYWRIGHT_DEFENSE_BLOCKED_ORIGINS,
      '--block-service-workers', '--codegen', 'none', '--caps', 'vision', '--timeout-action', '15000'
    ]);
    requiredTools = REQUIRED_PLAYWRIGHT_TOOLS;
  } else {
    throw new Error(`Unknown backend kind: ${kind}`);
  }

  const client = new Client({ name: `chat-semantic-projection-${kind}`, version: VERSION });
  const transport = new StdioClientTransport(spec);
  try {
    await client.connect(transport);
    const inventory = await client.listTools();
    const names = new Set(inventory.tools.map(tool => tool.name));
    const missing = [...requiredTools].filter(name => !names.has(name));
    if (missing.length > 0) throw new Error(`${kind} backend is missing required tools: ${missing.join(', ')}`);
    return { client, transport };
  } catch (error) {
    try { await client.close(); } catch {}
    throw error;
  }
}

async function getBackend(kind) {
  if (!backendPromises.has(kind)) {
    const pending = createBackend(kind).catch(error => { backendPromises.delete(kind); throw error; });
    backendPromises.set(kind, pending);
  }
  return backendPromises.get(kind);
}

async function callBackend(kind, toolName, args) {
  const required = kind === 'filesystem' ? REQUIRED_FILESYSTEM_TOOLS : REQUIRED_PLAYWRIGHT_TOOLS;
  if (!required.has(toolName)) throw new Error(`Projection refused non-allowlisted downstream tool: ${kind}.${toolName}`);
  const { client } = await getBackend(kind);
  return normalizeBackendResult(await client.callTool({ name: toolName, arguments: args }));
}

async function captureBrowserObservation() {
  const snapshot = await callBackend('playwright', 'browser_snapshot', {});
  return parsePlaywrightSnapshotResult(snapshot);
}

function browserVerifiedResult(delivery, verification, operationName) {
  const result = normalizeBackendResult(delivery);
  const status = verification?.status ?? 'unknown';
  const reason = verification?.verification?.reason ?? 'browser_verification_missing_reason';
  result.content = [
    ...result.content,
    {
      type: 'text',
      text: `${operationName} final-state verification=${status}; reason=${reason}`,
    },
  ];
  result.structuredContent = {
    ...(delivery?.structuredContent !== undefined ? { backend: delivery.structuredContent } : {}),
    browser_verification: verification,
  };
  if (status !== 'pass') result.isError = true;
  return result;
}

function browserDeliveredButUnverifiedResult(delivery, operationName, error) {
  const result = normalizeBackendResult(delivery);
  const reason = error instanceof Error ? error.message : String(error);
  result.content = [
    ...result.content,
    {
      type: 'text',
      text: `${operationName} action was delivered, but fresh final-state verification could not complete: ${reason}`,
    },
  ];
  result.structuredContent = {
    ...(delivery?.structuredContent !== undefined ? { backend: delivery.structuredContent } : {}),
    browser_verification: { status: 'unknown', reason: 'verification_runtime_unavailable' },
  };
  result.isError = true;
  return result;
}

async function getSemanticVisionRouter() {
  const { client } = await getBackend('playwright');
  if (!semanticVisionRouter || semanticVisionClient !== client) {
    semanticVisionRouter?.clear();
    semanticVisionClient = client;
    semanticVisionRouter = createSemanticVisionClickRouter({ client });
  }
  return semanticVisionRouter;
}

async function closeBackends() {
  semanticVisionRouter?.clear();
  semanticVisionRouter = null;
  semanticVisionClient = null;
  const pending = [...backendPromises.values()];
  backendPromises.clear();
  const settled = await Promise.allSettled(pending);
  const closes = [];
  for (const entry of settled) if (entry.status === 'fulfilled') closes.push(entry.value.client.close());
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

const relativePathSchema = z.string().min(1).max(2048).describe('Path relative to the configured workspace root. Absolute paths and parent traversal are rejected.');

const visualFallbackSchema = z.object({
  instruction: z.string().min(1).max(4096).describe('Concrete visual instruction for one text-labeled control.'),
  targetText: z.string().min(1).max(2048).describe('Visible text used for both exact accessibility preflight and reviewed visual grounding.'),
  semanticName: z.string().min(1).max(1024).optional().describe('Compatibility alias only. If supplied, it must normalize exactly to targetText and cannot force a different semantic preflight.')
}).strict();

const interactionExpectedControlSchema = z.object({
  target: z.string().min(1).max(512).optional().describe('Control ref whose fresh post-action state must be verified. Defaults to the action target when available.'),
  present: z.boolean().optional(),
  value: z.string().max(4096).optional(),
  checked: z.boolean().optional(),
  selected: z.boolean().optional(),
  enabled: z.boolean().optional(),
}).strict();

const interactionExpectedSchema = z.object({
  url: z.string().url().max(4096).optional().describe('Exact final HTTP/HTTPS URL expected after the interaction.'),
  control: interactionExpectedControlSchema.optional(),
}).strict();

const server = new McpServer(
  { name: 'chat-semantic-projection', version: VERSION },
  {
    instructions:
      'This server exposes a small fixed semantic projection. It cannot invoke arbitrary downstream tools. Workspace paths are relative to one configured root. Browser actions use an isolated headless Playwright session. web_open is accepted only after a fresh independent browser_snapshot proves the exact canonical final URL and document state. web_interact mutations are accepted only after fresh post-action verification of a bounded declared result; type without submit may infer the typed control value, while click and type+submit require an explicit expected result before delivery. For click only, a reviewed text-labeled visual fallback may run internally after a fresh accessibility snapshot proves zero exact targetText candidates. One exact candidate is clicked semantically; a unique enabled button may also be selected when all same-name alternatives are disabled. Unresolved ambiguity and semantic action errors fail closed without vision.'
  }
);

server.registerTool('workspace_read', {
  title: 'Read Workspace',
  description: 'Read-only workspace operations. operation=roots lists allowed roots; read_text reads one text file; search finds matching paths under a workspace subdirectory. No arbitrary backend/tool selection is available.',
  inputSchema: z.object({
    operation: z.enum(['roots', 'read_text', 'search']), path: relativePathSchema.optional(),
    head: z.number().int().positive().max(100000).optional(), tail: z.number().int().positive().max(100000).optional(),
    pattern: z.string().min(1).max(512).optional(), excludePatterns: z.array(z.string().max(512)).max(64).optional()
  }).strict(),
  annotations: { readOnlyHint: true, idempotentHint: true, openWorldHint: false }
}, async args => {
  try {
    if (args.operation === 'roots') return await callBackend('filesystem', 'list_allowed_directories', {});
    if (args.operation === 'read_text') {
      if (!args.path) return toolError('workspace_read read_text requires path.');
      if (args.head && args.tail) return toolError('Use head or tail, not both.');
      const downstream = { path: resolveWorkspacePath(args.path) };
      if (args.head !== undefined) downstream.head = args.head;
      if (args.tail !== undefined) downstream.tail = args.tail;
      return await callBackend('filesystem', 'read_text_file', downstream);
    }
    if (!args.pattern) return toolError('workspace_read search requires pattern.');
    const downstream = { path: resolveWorkspacePath(args.path ?? '.'), pattern: args.pattern };
    if (args.excludePatterns !== undefined) downstream.excludePatterns = args.excludePatterns;
    return await callBackend('filesystem', 'search_files', downstream);
  } catch (error) { return toolError(`workspace_read failed: ${error instanceof Error ? error.message : String(error)}`); }
});

server.registerTool('workspace_write', {
  title: 'Write Workspace Text',
  description: 'Create or overwrite one UTF-8 text file inside the configured workspace root. The path must be relative; arbitrary filesystem tools are not available.',
  inputSchema: z.object({ path: relativePathSchema, content: z.string().max(4_000_000) }).strict(),
  annotations: { readOnlyHint: false, destructiveHint: true, idempotentHint: true, openWorldHint: false }
}, async ({ path: relativePath, content }) => {
  try { return await callBackend('filesystem', 'write_file', { path: resolveWorkspacePath(relativePath), content }); }
  catch (error) { return toolError(`workspace_write failed: ${error instanceof Error ? error.message : String(error)}`); }
});

server.registerTool('web_open', {
  title: 'Open Web Page',
  description: 'Navigate the isolated headless browser to one HTTP or HTTPS URL. File, javascript, data, credential-bearing and direct non-public IP destinations are rejected. Loopback URLs remain allowed for reviewed local workflows. Success requires fresh post-navigation verification of the exact canonical final URL and document snapshot.',
  inputSchema: z.object({ url: z.string().url().max(4096) }).strict(),
  annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false, openWorldHint: true }
}, async ({ url }) => {
  let delivery = null;
  try {
    const parsed = new URL(url);
    if (!['http:', 'https:'].includes(parsed.protocol)) return toolError('web_open accepts only HTTP or HTTPS URLs.');
    if (parsed.username || parsed.password) return toolError('web_open rejects URLs containing embedded credentials.');
    const networkPolicy = classifyDirectNavigationHost(parsed.hostname);
    if (!networkPolicy.allowed) {
      return toolError(`web_open rejects direct ${networkPolicy.scope} destinations by default: ${parsed.hostname}. Loopback remains allowed; broader private-network access requires a separately reviewed capability.`);
    }

    const before = await captureBrowserObservation();
    delivery = await callBackend('playwright', 'browser_navigate', { url: parsed.href });
    if (delivery.isError) return delivery;

    try {
      const after = await captureBrowserObservation();
      const verification = await verifyPlaywrightNavigation({
        before,
        after,
        expectedUrl: parsed.href,
      });
      return browserVerifiedResult(delivery, verification, 'web_open');
    } catch (error) {
      return browserDeliveredButUnverifiedResult(delivery, 'web_open', error);
    }
  } catch (error) {
    if (delivery && !delivery.isError) return browserDeliveredButUnverifiedResult(delivery, 'web_open', error);
    return toolError(`web_open failed: ${error instanceof Error ? error.message : String(error)}`);
  }
});

server.registerTool('web_observe', {
  title: 'Observe Web Page',
  description: 'Read-only browser observation. operation=find searches the current accessibility snapshot by plain text or regex. operation=snapshot captures the current accessibility snapshot, optionally for one target. Screenshots remain internal to the reviewed click fallback and are never exposed as a public observation operation.',
  inputSchema: z.object({
    operation: z.enum(['find', 'snapshot']), text: z.string().min(1).max(2048).optional(),
    regex: z.string().min(1).max(2048).optional(), target: z.string().min(1).max(4096).optional()
  }).strict(),
  annotations: { readOnlyHint: true, idempotentHint: true, openWorldHint: true }
}, async args => {
  try {
    if (args.operation === 'find') {
      if (Boolean(args.text) === Boolean(args.regex)) return toolError('web_observe find requires exactly one of text or regex.');
      return await callBackend('playwright', 'browser_find', args.text ? { text: args.text } : { regex: args.regex });
    }
    const downstream = {};
    if (args.target !== undefined) downstream.target = args.target;
    return await callBackend('playwright', 'browser_snapshot', downstream);
  } catch (error) { return toolError(`web_observe failed: ${error instanceof Error ? error.message : String(error)}`); }
});

server.registerTool('web_interact', {
  title: 'Interact With Web Page',
  description: 'Interact with the isolated browser using click or type, with fresh before/after verification of a bounded observable postcondition. type without submit may infer the target control value; click and type+submit require expected={url and/or control state} before delivery. click may optionally use the existing reviewed text-labeled visual fallback. Generic page-change heuristics, arbitrary JavaScript, file upload, direct network inspection and backend/tool selection are not accepted.',
  inputSchema: z.object({
    operation: z.enum(['click', 'type']), target: z.string().min(1).max(4096).optional(),
    element: z.string().min(1).max(1024).optional(), doubleClick: z.boolean().optional(),
    text: z.string().max(200000).optional(), submit: z.boolean().optional(), slowly: z.boolean().optional(),
    visualFallback: visualFallbackSchema.optional(), expected: interactionExpectedSchema.optional()
  }).strict(),
  annotations: { readOnlyHint: false, destructiveHint: true, idempotentHint: false, openWorldHint: true }
}, async args => {
  let delivery = null;
  try {
    if (args.operation === 'click') {
      if (args.text !== undefined || args.submit !== undefined || args.slowly !== undefined) return toolError('web_interact click does not accept type-only arguments.');
      if (args.visualFallback !== undefined && args.doubleClick !== undefined) {
        return toolError('web_interact visualFallback supports only one left single click; doubleClick is not accepted.');
      }
      if (args.visualFallback === undefined && !args.target) {
        return toolError('web_interact click requires target unless visualFallback is provided.');
      }
    } else {
      if (args.visualFallback !== undefined) return toolError('web_interact type does not accept visualFallback.');
      if (!args.target) return toolError('web_interact type requires target.');
      if (args.text === undefined) return toolError('web_interact type requires text.');
      if (args.doubleClick !== undefined) return toolError('web_interact type does not accept doubleClick.');
    }

    let expected;
    try {
      expected = normalizeInteractionExpected(args);
    } catch (error) {
      return toolError(`web_interact refused action before delivery: ${error instanceof Error ? error.message : String(error)}`);
    }

    const before = await captureBrowserObservation();

    if (args.operation === 'click') {
      if (args.visualFallback !== undefined) {
        const router = await getSemanticVisionRouter();
        const outcome = await router.click({
          target: args.target ?? null,
          element: args.element ?? null,
          visualFallback: args.visualFallback,
        });
        if (outcome?.status !== 'acted') return visualOutcomeResult(outcome);
        delivery = visualOutcomeResult(outcome);
      } else {
        const downstream = { target: args.target };
        if (args.element !== undefined) downstream.element = args.element;
        if (args.doubleClick !== undefined) downstream.doubleClick = args.doubleClick;
        delivery = await callBackend('playwright', 'browser_click', downstream);
      }
    } else {
      const downstream = { target: args.target, text: args.text };
      if (args.element !== undefined) downstream.element = args.element;
      if (args.submit !== undefined) downstream.submit = args.submit;
      if (args.slowly !== undefined) downstream.slowly = args.slowly;
      delivery = await callBackend('playwright', 'browser_type', downstream);
    }

    if (delivery?.isError) return delivery;

    try {
      const after = await captureBrowserObservation();
      const verification = await verifyPlaywrightInteraction({ before, after, expected });
      return browserVerifiedResult(delivery, verification, `web_interact ${args.operation}`);
    } catch (error) {
      return browserDeliveredButUnverifiedResult(delivery, `web_interact ${args.operation}`, error);
    }
  } catch (error) {
    if (delivery && !delivery.isError) {
      return browserDeliveredButUnverifiedResult(delivery, `web_interact ${args.operation}`, error);
    }
    return toolError(`web_interact failed: ${error instanceof Error ? error.message : String(error)}`);
  }
});

void serveStdio(() => server);