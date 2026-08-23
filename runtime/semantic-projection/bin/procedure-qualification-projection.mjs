#!/usr/bin/env node

import { spawn } from 'node:child_process';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';
import { McpServer } from '@modelcontextprotocol/server';
import { serveStdio } from '@modelcontextprotocol/server/stdio';
import * as z from 'zod/v4';

const VERSION = '0.1.0';
const here = path.dirname(fileURLToPath(import.meta.url));
const semanticLauncher = path.join(here, 'semantic-projection-launcher.mjs');
const repoRoot = path.resolve(here, '..', '..', '..');
const controlPlaneCli = path.join(repoRoot, 'runtime', 'control_plane', 'cli.py');
const REQUIRED_SEMANTIC_TOOLS = new Set([
  'workspace_read',
  'workspace_write',
  'web_open',
  'web_observe',
  'web_interact'
]);
const MAX_PROCEDURE_RESPONSE_BYTES = 1_000_000;
const PROCEDURE_TIMEOUT_MS = 30_000;

function toolError(message) {
  return { content: [{ type: 'text', text: message }], isError: true };
}

function normalizeResult(result) {
  const normalized = { content: Array.isArray(result?.content) ? result.content : [] };
  if (result?.isError) normalized.isError = true;
  if (result?.structuredContent !== undefined) normalized.structuredContent = result.structuredContent;
  return normalized;
}

const semanticClient = new Client({
  name: 'chat-procedure-qualification-semantic-client',
  version: VERSION
});
const semanticTransport = new StdioClientTransport({
  command: process.execPath,
  args: [semanticLauncher]
});

await semanticClient.connect(semanticTransport);
const inventory = await semanticClient.listTools();
const semanticNames = new Set(inventory.tools.map(tool => tool.name));
const missing = [...REQUIRED_SEMANTIC_TOOLS].filter(name => !semanticNames.has(name));
const unexpected = [...semanticNames].filter(name => !REQUIRED_SEMANTIC_TOOLS.has(name));
if (missing.length || unexpected.length) {
  await semanticClient.close();
  throw new Error(
    `qualification projection requires the exact five-tool semantic surface; missing=${missing.join(',') || 'none'} unexpected=${unexpected.join(',') || 'none'}`
  );
}

async function callSemantic(name, args) {
  if (!REQUIRED_SEMANTIC_TOOLS.has(name)) {
    throw new Error(`refused non-allowlisted semantic tool: ${name}`);
  }
  return normalizeResult(await semanticClient.callTool({ name, arguments: args }));
}

function runProcedure(request) {
  return new Promise((resolve) => {
    const child = spawn('python', [controlPlaneCli], {
      cwd: repoRoot,
      env: process.env,
      stdio: ['pipe', 'pipe', 'pipe'],
      windowsHide: true
    });

    let stdout = Buffer.alloc(0);
    let stderr = Buffer.alloc(0);
    let settled = false;
    const finish = (result) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve(result);
    };

    const timer = setTimeout(() => {
      try { child.kill(); } catch {}
      finish(toolError('procedure_run failed: control_plane_timeout'));
    }, PROCEDURE_TIMEOUT_MS);

    child.stdout.on('data', chunk => {
      stdout = Buffer.concat([stdout, Buffer.from(chunk)]);
      if (stdout.length > MAX_PROCEDURE_RESPONSE_BYTES) {
        try { child.kill(); } catch {}
        finish(toolError('procedure_run failed: response_too_large'));
      }
    });
    child.stderr.on('data', chunk => {
      if (stderr.length < 64_000) stderr = Buffer.concat([stderr, Buffer.from(chunk)]);
    });
    child.on('error', error => finish(toolError(`procedure_run failed: ${error.name}`)));
    child.on('close', () => {
      if (settled) return;
      try {
        const parsed = JSON.parse(stdout.toString('utf8'));
        const text = JSON.stringify(parsed);
        finish({
          content: [{ type: 'text', text }],
          structuredContent: parsed,
          ...(parsed?.status === 'error' ? { isError: true } : {})
        });
      } catch {
        const diagnostic = stderr.toString('utf8').trim();
        finish(toolError(`procedure_run failed: invalid_control_plane_response${diagnostic ? ` (${diagnostic.slice(0, 240)})` : ''}`));
      }
    });

    child.stdin.end(JSON.stringify(request));
  });
}

const relativePathSchema = z.string().min(1).max(2048);
const server = new McpServer(
  { name: 'chat-procedure-qualification-projection', version: VERSION },
  {
    instructions:
      'Qualification-only Stage 26.3A projection. It preserves the accepted five semantic tools and adds exactly one typed procedure_run surface for the fixed candidate verified_workspace_artifact_v1 Control Plane. It exposes no shell, arbitrary Python, backend selector, generic tool dispatch, or arbitrary filesystem path.'
  }
);

server.registerTool('workspace_read', {
  description: 'Accepted semantic workspace read/search surface.',
  inputSchema: z.object({
    operation: z.enum(['roots', 'read_text', 'search']),
    path: relativePathSchema.optional(),
    head: z.number().int().positive().max(100000).optional(),
    tail: z.number().int().positive().max(100000).optional(),
    pattern: z.string().min(1).max(512).optional(),
    excludePatterns: z.array(z.string().max(512)).max(64).optional()
  }).strict(),
  annotations: { readOnlyHint: true, idempotentHint: true, openWorldHint: false }
}, args => callSemantic('workspace_read', args));

server.registerTool('workspace_write', {
  description: 'Accepted semantic bounded workspace text write surface.',
  inputSchema: z.object({
    path: relativePathSchema,
    content: z.string().max(4_000_000)
  }).strict(),
  annotations: { readOnlyHint: false, destructiveHint: true, idempotentHint: true, openWorldHint: false }
}, args => callSemantic('workspace_write', args));

server.registerTool('web_open', {
  description: 'Accepted isolated semantic web navigation surface.',
  inputSchema: z.object({ url: z.string().url().max(4096) }).strict(),
  annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false, openWorldHint: true }
}, args => callSemantic('web_open', args));

server.registerTool('web_observe', {
  description: 'Accepted read-only semantic browser observation surface.',
  inputSchema: z.object({
    operation: z.enum(['find', 'snapshot']),
    text: z.string().min(1).max(2048).optional(),
    regex: z.string().min(1).max(2048).optional(),
    target: z.string().min(1).max(4096).optional()
  }).strict(),
  annotations: { readOnlyHint: true, idempotentHint: true, openWorldHint: true }
}, args => callSemantic('web_observe', args));

server.registerTool('web_interact', {
  description: 'Accepted semantic click/type surface with existing reviewed guards.',
  inputSchema: z.object({
    operation: z.enum(['click', 'type']),
    ref: z.string().min(1).max(2048).optional(),
    text: z.string().max(200000).optional(),
    element: z.string().min(1).max(2048).optional(),
    visualFallback: z.object({
      instruction: z.string().min(1).max(4096),
      targetText: z.string().min(1).max(2048),
      semanticName: z.string().min(1).max(1024).optional()
    }).strict().optional()
  }).strict(),
  annotations: { readOnlyHint: false, destructiveHint: true, idempotentHint: false, openWorldHint: true }
}, args => callSemantic('web_interact', args));

server.registerTool('procedure_run', {
  title: 'Run Verified Candidate Procedure',
  description:
    'Qualification-only Stage 26.3A typed procedure execution. The only admitted procedure is verified_workspace_artifact_v1. It accepts a leaf .txt artifact name, bounded UTF-8 content, and optional resume_task_id. No path, command, Python, backend, or generic tool selector is accepted.',
  inputSchema: z.object({
    procedure: z.literal('verified_workspace_artifact_v1'),
    artifact_name: z.string().min(1).max(72),
    content: z.string().max(1_000_000),
    resume_task_id: z.string().regex(/^[0-9a-f]{32}$/).optional()
  }).strict(),
  annotations: { readOnlyHint: false, destructiveHint: true, idempotentHint: false, openWorldHint: false }
}, args => runProcedure(args));

let closing = false;
async function close() {
  if (closing) return;
  closing = true;
  try { await semanticClient.close(); } catch {}
}
process.on('SIGINT', () => void close().finally(() => process.exit(0)));
process.on('SIGTERM', () => void close().finally(() => process.exit(0)));
process.stdin.on('end', () => void close());
process.stdin.on('close', () => void close());

await serveStdio(server);
