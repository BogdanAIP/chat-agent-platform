#!/usr/bin/env node

import fs from 'node:fs';
import net from 'node:net';
import path from 'node:path';
import process from 'node:process';

import { McpServer } from '@modelcontextprotocol/server';
import { serveStdio } from '@modelcontextprotocol/server/stdio';
import * as z from 'zod/v4';

import {
  parsePlaywrightSnapshotResult,
  verifyPlaywrightInteraction,
  verifyPlaywrightNavigation,
} from '../lib/browser-verification-bridge.mjs';
import { authorizeSemanticBrowserMutation } from '../lib/browser-authorization-bridge.mjs';
import { createFilesystemSemanticProvider } from '../lib/filesystem-semantic-provider.mjs';
import { createPlaywrightBrowserSemanticProvider } from '../lib/playwright-browser-semantic-provider.mjs';
import { createSemanticVisionClickRouter } from '../lib/semantic-vision-click-router.mjs';
import {
  requireSemanticActivation,
  semanticProviderEnvironment,
} from '../lib/semantic-activation.mjs';
import {
  prepareSemanticWorkspaceWrite,
  semanticWorkspaceWriteIdentity,
  verifySemanticWorkspaceWrite,
} from '../lib/workspace-write-bridge.mjs';

const VERSION = '0.1.0';

const semanticActivation = requireSemanticActivation();

const workspaceRootInput = process.env.CHAT_LOCAL_FILES_ROOT;
if (!workspaceRootInput) throw new Error('CHAT_LOCAL_FILES_ROOT is required for semantic projection.');
const workspaceRoot = path.resolve(workspaceRootInput);
const workspaceStat = fs.statSync(workspaceRoot, { throwIfNoEntry: false });
if (!workspaceStat?.isDirectory()) {
  throw new Error(`CHAT_LOCAL_FILES_ROOT must be an existing directory: ${workspaceRoot}`);
}

const filesystemProvider = createFilesystemSemanticProvider({ workspaceRoot });
const browserProvider = createPlaywrightBrowserSemanticProvider();
let semanticVisionRouter = null;
let shuttingDown = false;

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

function assessInteractionExpectedBefore(before, expected) {
  let mismatch = false;
  let unknown = false;

  if (before?.settled !== true || before?.complete !== true || before?.ambiguous === true) {
    unknown = true;
  }

  if (expected.url !== undefined) {
    try {
      const observedUrl = normalizeExpectedBrowserUrl(before.url);
      if (observedUrl !== expected.url) mismatch = true;
    } catch {
      unknown = true;
    }
  }

  if (expected.control !== undefined) {
    const expectedControl = expected.control;
    const matches = Array.isArray(before?.controls)
      ? before.controls.filter(control => control?.control_id === expectedControl.control_id)
      : [];
    if (matches.length > 1) {
      unknown = true;
    } else {
      const observed = matches[0] ?? null;
      if (expectedControl.present === false) {
        if (observed !== null) mismatch = true;
      } else if (observed === null) {
        mismatch = true;
      } else {
        const fields = ['value', 'checked', 'selected', 'enabled'];
        for (const field of fields) {
          if (expectedControl[field] === undefined) continue;
          if (observed[field] === null || observed[field] === undefined) {
            unknown = true;
          } else if (observed[field] !== expectedControl[field]) {
            mismatch = true;
          }
        }
      }
    }
  }

  if (mismatch) return { status: 'delta_required', reason: 'expected_not_yet_satisfied' };
  if (unknown) return { status: 'unknown', reason: 'expected_before_state_not_fully_observable' };
  return { status: 'already_satisfied', reason: 'expected_already_satisfied' };
}

async function captureBrowserObservation() {
  const snapshot = await browserProvider.snapshot();
  return parsePlaywrightSnapshotResult(snapshot);
}

function browserMutationVerifiedResult({
  delivery,
  deliveryError,
  deliveryAttempted,
  verification,
  operationName,
  authorization,
}) {
  const result = delivery === null ? { content: [] } : normalizeBackendResult(delivery);
  const status = verification?.status ?? 'unknown';
  const reason = verification?.verification?.reason ?? 'browser_verification_missing_reason';
  const acknowledged = (
    deliveryAttempted === true &&
    deliveryError === null &&
    delivery !== null &&
    !delivery.isError
  );
  result.content = [
    ...result.content,
    {
      type: 'text',
      text: `${operationName} final-state verification=${status}; reason=${reason}; delivery_acknowledged=${acknowledged}`,
    },
  ];
  result.structuredContent = {
    ...(delivery?.structuredContent !== undefined ? { backend: delivery.structuredContent } : {}),
    browser_authorization: authorization,
    delivery: {
      attempted: deliveryAttempted === true,
      acknowledged,
      ...(deliveryError === null ? {} : {
        error: deliveryError instanceof Error ? deliveryError.message : String(deliveryError),
      }),
    },
    browser_verification: verification,
  };
  if (status === 'pass') {
    delete result.isError;
  } else {
    result.isError = true;
  }
  return result;
}

function browserMutationUnverifiedResult({
  delivery,
  deliveryError,
  deliveryAttempted,
  operationName,
  authorization,
  error,
}) {
  const result = delivery === null ? { content: [] } : normalizeBackendResult(delivery);
  const reason = error instanceof Error ? error.message : String(error);
  const acknowledged = (
    deliveryAttempted === true &&
    deliveryError === null &&
    delivery !== null &&
    !delivery.isError
  );
  result.content = [
    ...result.content,
    {
      type: 'text',
      text: `${operationName} action was attempted, but fresh final-state verification could not complete: ${reason}`,
    },
  ];
  result.structuredContent = {
    ...(delivery?.structuredContent !== undefined ? { backend: delivery.structuredContent } : {}),
    browser_authorization: authorization,
    delivery: {
      attempted: deliveryAttempted === true,
      acknowledged,
      ...(deliveryError === null ? {} : {
        error: deliveryError instanceof Error ? deliveryError.message : String(deliveryError),
      }),
    },
    browser_verification: { status: 'unknown', reason: 'verification_runtime_unavailable' },
  };
  result.isError = true;
  return result;
}

function browserAlreadySatisfiedResult({ operationName, authorization }) {
  return {
    content: [{
      type: 'text',
      text: `${operationName} performed no physical action because fresh pre-state already satisfies the requested final state.`,
    }],
    structuredContent: {
      browser_authorization: authorization,
      delivery: { attempted: false, acknowledged: false },
      browser_verification: {
        status: 'pass',
        reason: 'already_satisfied_before_delivery',
        observation_fingerprint: authorization?.before_fingerprint ?? null,
      },
    },
  };
}

async function getSemanticVisionRouter() {
  if (!semanticVisionRouter) {
    semanticVisionRouter = createSemanticVisionClickRouter({ browser: browserProvider });
  }
  return semanticVisionRouter;
}

async function closeProviders() {
  semanticVisionRouter?.clear();
  semanticVisionRouter = null;
  await Promise.allSettled([
    filesystemProvider.close(),
    browserProvider.close(),
  ]);
}

async function shutdown(code = 0) {
  if (shuttingDown) return;
  shuttingDown = true;
  await closeProviders();
  process.exit(code);
}

process.on('SIGINT', () => void shutdown(0));
process.on('SIGTERM', () => void shutdown(0));
process.stdin.on('end', () => void closeProviders());
process.stdin.on('close', () => void closeProviders());

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
      'This server exposes a small fixed semantic projection. It cannot invoke arbitrary downstream tools. Workspace paths are relative to one configured root. Browser actions use an isolated headless Playwright session. web_open is accepted only after a fresh independent browser_snapshot proves the exact canonical final URL and document state. web_interact mutations are accepted only after fresh post-action verification of a bounded declared result; type without submit may infer the typed control value, while click and type+submit require an explicit expected result before delivery. A web_interact action is also refused before delivery when the declared expected result is already satisfied or cannot be safely distinguished from the fresh pre-action state. For click only, a reviewed text-labeled visual fallback may run internally after a fresh accessibility snapshot proves zero exact targetText candidates. One exact candidate is clicked semantically; a unique enabled button may also be selected when all same-name alternatives are disabled. Unresolved ambiguity and semantic action errors fail closed without vision.'
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
    if (args.operation === 'roots') return await filesystemProvider.roots();
    if (args.operation === 'read_text') {
      if (!args.path) return toolError('workspace_read read_text requires path.');
      if (args.head && args.tail) return toolError('Use head or tail, not both.');
      const downstream = { path: resolveWorkspacePath(args.path) };
      if (args.head !== undefined) downstream.head = args.head;
      if (args.tail !== undefined) downstream.tail = args.tail;
      return await filesystemProvider.readText(downstream);
    }
    if (!args.pattern) return toolError('workspace_read search requires pattern.');
    const downstream = { path: resolveWorkspacePath(args.path ?? '.'), pattern: args.pattern };
    if (args.excludePatterns !== undefined) downstream.excludePatterns = args.excludePatterns;
    return await filesystemProvider.search(downstream);
  } catch (error) { return toolError(`workspace_read failed: ${error instanceof Error ? error.message : String(error)}`); }
});

server.registerTool('workspace_write', {
  title: 'Write Workspace Text',
  description: 'Create or overwrite one UTF-8 text file inside the configured workspace root. The request is authorized against the active semantic scope and success requires fresh exact-byte verification. The path must be relative; arbitrary filesystem tools are not available.',
  inputSchema: z.object({ path: relativePathSchema, content: z.string().max(4_000_000) }).strict(),
  annotations: { readOnlyHint: false, destructiveHint: true, idempotentHint: true, openWorldHint: false }
}, async ({ path: relativePath, content }) => {
  let prepared;
  let identity;
  let resolvedPath;
  try {
    resolvedPath = resolveWorkspacePath(relativePath);
    identity = semanticWorkspaceWriteIdentity(content);
    prepared = await prepareSemanticWorkspaceWrite({
      activationRef: semanticActivation.activationRef,
      workspaceRoot,
      relativePath,
      ...identity,
    });
  } catch (error) {
    return toolError(`workspace_write refused before delivery: ${error instanceof Error ? error.message : String(error)}`);
  }

  if (prepared?.status !== 'authorized') {
    return toolError(`workspace_write refused before delivery: authorization=${prepared?.status ?? 'unknown'} reason=${prepared?.reason ?? 'missing'}`);
  }

  if (prepared.already_satisfied === true) {
    return {
      content: [{
        type: 'text',
        text: 'workspace_write performed no physical write because fresh pre-state already matches the requested UTF-8 bytes.',
      }],
      structuredContent: {
        delivery: { attempted: false, acknowledged: false },
        workspace_verification: {
          status: 'pass',
          reason: 'already_satisfied_before_delivery',
          authorization: prepared.authorization,
          observation: prepared.before,
        },
      },
    };
  }

  let delivery = null;
  let deliveryError = null;
  try {
    delivery = await filesystemProvider.writeText({
      path: resolvedPath,
      content,
    });
  } catch (error) {
    deliveryError = error;
  }

  let verified;
  try {
    verified = await verifySemanticWorkspaceWrite({
      activationRef: semanticActivation.activationRef,
      workspaceRoot,
      relativePath,
      ...identity,
      before: prepared.before,
    });
  } catch (error) {
    const result = delivery === null ? { content: [] } : normalizeBackendResult(delivery);
    const reason = error instanceof Error ? error.message : String(error);
    result.content = [
      ...result.content,
      {
        type: 'text',
        text: `workspace_write delivery was attempted, but fresh exact-byte verification could not complete: ${reason}`,
      },
    ];
    result.structuredContent = {
      ...(delivery?.structuredContent !== undefined ? { backend: delivery.structuredContent } : {}),
      delivery: {
        attempted: true,
        acknowledged: delivery !== null && !delivery.isError,
        ...(deliveryError === null ? {} : {
          error: deliveryError instanceof Error ? deliveryError.message : String(deliveryError),
        }),
      },
      workspace_verification: {
        status: 'unknown',
        reason: 'verification_runtime_unavailable',
        authorization: prepared.authorization,
      },
    };
    result.isError = true;
    return result;
  }

  const result = delivery === null ? { content: [] } : normalizeBackendResult(delivery);
  const deliveryAcknowledged = delivery !== null && !delivery.isError;
  result.content = [
    ...result.content,
    {
      type: 'text',
      text: `workspace_write final-state verification=${verified.status}; reason=${verified.reason}; delivery_acknowledged=${deliveryAcknowledged}`,
    },
  ];
  result.structuredContent = {
    ...(delivery?.structuredContent !== undefined ? { backend: delivery.structuredContent } : {}),
    delivery: {
      attempted: true,
      acknowledged: deliveryAcknowledged,
      ...(deliveryError === null ? {} : {
        error: deliveryError instanceof Error ? deliveryError.message : String(deliveryError),
      }),
    },
    workspace_verification: verified,
  };
  if (verified.status === 'pass') {
    delete result.isError;
  } else {
    result.isError = true;
  }
  return result;
});

server.registerTool('web_open', {
  title: 'Open Web Page',
  description: 'Navigate the isolated headless browser to one HTTP or HTTPS URL. File, javascript, data, credential-bearing and direct non-public IP destinations are rejected. Loopback URLs remain allowed for reviewed local workflows. The exact navigation is authorized against the active semantic scope and success requires fresh post-navigation verification of the exact canonical final URL and document snapshot.',
  inputSchema: z.object({ url: z.string().url().max(4096) }).strict(),
  annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false, openWorldHint: true }
}, async ({ url }) => {
  let before = null;
  let authorization = null;
  let delivery = null;
  let deliveryError = null;
  let deliveryAttempted = false;
  let parsed;
  let networkPolicy;

  try {
    parsed = new URL(url);
    if (!['http:', 'https:'].includes(parsed.protocol)) return toolError('web_open accepts only HTTP or HTTPS URLs.');
    if (parsed.username || parsed.password) return toolError('web_open rejects URLs containing embedded credentials.');
    networkPolicy = classifyDirectNavigationHost(parsed.hostname);
    if (!networkPolicy.allowed) {
      return toolError(`web_open rejects direct ${networkPolicy.scope} destinations by default: ${parsed.hostname}. Loopback remains allowed; broader private-network access requires a separately reviewed capability.`);
    }

    before = await captureBrowserObservation();
    authorization = await authorizeSemanticBrowserMutation({
      activationRef: semanticActivation.activationRef,
      browserPolicyRef: semanticActivation.browserPolicyRef,
      actionRef: 'browser.navigate',
      before,
      resource: {
        url: parsed.href,
        network_scope: networkPolicy.scope,
      },
    });
    if (authorization?.status !== 'authorized') {
      return toolError(`web_open refused before delivery: authorization=${authorization?.status ?? 'unknown'} reason=${authorization?.reason ?? 'missing'}`);
    }

    if (before?.settled === true && before?.complete === true && before?.ambiguous !== true) {
      try {
        if (normalizeExpectedBrowserUrl(before.url) === parsed.href) {
          return browserAlreadySatisfiedResult({
            operationName: 'web_open',
            authorization,
          });
        }
      } catch {
        // about:blank or a non-admitted current URL is simply not already satisfied.
      }
    }
  } catch (error) {
    return toolError(`web_open refused before delivery: ${error instanceof Error ? error.message : String(error)}`);
  }

  deliveryAttempted = true;
  try {
    delivery = await browserProvider.navigate(parsed.href);
  } catch (error) {
    deliveryError = error;
  }

  try {
    const after = await captureBrowserObservation();
    const verification = await verifyPlaywrightNavigation({
      before,
      after,
      expectedUrl: parsed.href,
    });
    return browserMutationVerifiedResult({
      delivery,
      deliveryError,
      deliveryAttempted,
      verification,
      operationName: 'web_open',
      authorization,
    });
  } catch (error) {
    return browserMutationUnverifiedResult({
      delivery,
      deliveryError,
      deliveryAttempted,
      operationName: 'web_open',
      authorization,
      error,
    });
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
      return await browserProvider.find(args.text ? { text: args.text } : { regex: args.regex });
    }
    const downstream = {};
    if (args.target !== undefined) downstream.target = args.target;
    return await browserProvider.snapshot(downstream);
  } catch (error) { return toolError(`web_observe failed: ${error instanceof Error ? error.message : String(error)}`); }
});

server.registerTool('web_interact', {
  title: 'Interact With Web Page',
  description: 'Interact with the isolated browser using click or type, with exact active-scope authorization and fresh before/after verification of a bounded observable postcondition. type without submit may infer the target control value; click and type+submit require expected={url and/or control state} before delivery. The action is refused when expected is already satisfied or cannot be safely distinguished from the fresh pre-action state. click may optionally use the existing reviewed text-labeled visual fallback. Generic page-change heuristics, arbitrary JavaScript, file upload, direct network inspection and backend/tool selection are not accepted.',
  inputSchema: z.object({
    operation: z.enum(['click', 'type']), target: z.string().min(1).max(4096).optional(),
    element: z.string().min(1).max(1024).optional(), doubleClick: z.boolean().optional(),
    text: z.string().max(200000).optional(), submit: z.boolean().optional(), slowly: z.boolean().optional(),
    visualFallback: visualFallbackSchema.optional(), expected: interactionExpectedSchema.optional()
  }).strict(),
  annotations: { readOnlyHint: false, destructiveHint: true, idempotentHint: false, openWorldHint: true }
}, async args => {
  let before = null;
  let expected = null;
  let authorization = null;
  let delivery = null;
  let deliveryError = null;
  let deliveryAttempted = false;

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

    try {
      expected = normalizeInteractionExpected(args);
    } catch (error) {
      return toolError(`web_interact refused action before delivery: ${error instanceof Error ? error.message : String(error)}`);
    }

    before = await captureBrowserObservation();
    const preflight = assessInteractionExpectedBefore(before, expected);
    if (preflight.status === 'already_satisfied') {
      return toolError('web_interact refused action before delivery: expected postcondition is already satisfied by the fresh pre-action observation.');
    }
    if (preflight.status !== 'delta_required') {
      return toolError('web_interact refused action before delivery: expected postcondition cannot be safely distinguished from the fresh pre-action observation.');
    }

    authorization = await authorizeSemanticBrowserMutation({
      activationRef: semanticActivation.activationRef,
      browserPolicyRef: semanticActivation.browserPolicyRef,
      actionRef: args.operation === 'click' ? 'browser.click' : 'browser.type',
      before,
      resource: {
        operation: args.operation,
        target: args.target ?? null,
        element: args.element ?? null,
        double_click: args.doubleClick ?? null,
        text: args.text ?? null,
        submit: args.submit ?? null,
        slowly: args.slowly ?? null,
        visual_fallback: args.visualFallback === undefined ? null : args.visualFallback,
        expected,
      },
    });
    if (authorization?.status !== 'authorized') {
      return toolError(`web_interact refused action before delivery: authorization=${authorization?.status ?? 'unknown'} reason=${authorization?.reason ?? 'missing'}`);
    }
  } catch (error) {
    return toolError(`web_interact refused action before delivery: ${error instanceof Error ? error.message : String(error)}`);
  }

  if (args.operation === 'click' && args.visualFallback !== undefined) {
    let outcome;
    try {
      const router = await getSemanticVisionRouter();
      outcome = await router.click({
        target: args.target ?? null,
        element: args.element ?? null,
        visualFallback: args.visualFallback,
      });
    } catch (error) {
      return toolError(`web_interact failed before a proven delivery attempt: ${error instanceof Error ? error.message : String(error)}`);
    }

    deliveryAttempted = outcome?.deliveryAttempted === true;
    if (!deliveryAttempted) {
      return visualOutcomeResult(outcome);
    }
    delivery = visualOutcomeResult(outcome);
    if (outcome?.deliveryError !== undefined) {
      deliveryError = new Error(String(outcome.deliveryError));
    }
  } else {
    deliveryAttempted = true;
    try {
      if (args.operation === 'click') {
        const downstream = { target: args.target };
        if (args.element !== undefined) downstream.element = args.element;
        if (args.doubleClick !== undefined) downstream.doubleClick = args.doubleClick;
        delivery = await browserProvider.click(downstream);
      } else {
        const downstream = { target: args.target, text: args.text };
        if (args.element !== undefined) downstream.element = args.element;
        if (args.submit !== undefined) downstream.submit = args.submit;
        if (args.slowly !== undefined) downstream.slowly = args.slowly;
        delivery = await browserProvider.type(downstream);
      }
    } catch (error) {
      deliveryError = error;
    }
  }

  try {
    const after = await captureBrowserObservation();
    const verification = await verifyPlaywrightInteraction({ before, after, expected });
    return browserMutationVerifiedResult({
      delivery,
      deliveryError,
      deliveryAttempted,
      verification,
      operationName: `web_interact ${args.operation}`,
      authorization,
    });
  } catch (error) {
    return browserMutationUnverifiedResult({
      delivery,
      deliveryError,
      deliveryAttempted,
      operationName: `web_interact ${args.operation}`,
      authorization,
      error,
    });
  }
});

void serveStdio(() => server);