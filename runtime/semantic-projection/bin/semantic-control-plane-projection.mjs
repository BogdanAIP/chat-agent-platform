#!/usr/bin/env node

import { spawn } from 'node:child_process';
import { randomBytes } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';
import { McpServer } from '@modelcontextprotocol/server';
import { serveStdio } from '@modelcontextprotocol/server/stdio';
import * as z from 'zod/v4';

const TUNNEL_ONLY_CREDENTIAL_KEYS = [
  'CONTROL_PLANE_API_KEY',
  'OPENAI_API_KEY',
  'OPENAI_ADMIN_KEY'
];
for (const key of TUNNEL_ONLY_CREDENTIAL_KEYS) delete process.env[key];

const VERSION = '0.2.0';
const here = path.dirname(fileURLToPath(import.meta.url));
const semanticEntry = path.join(here, 'semantic-projection.mjs');
const repoRoot = path.resolve(here, '..', '..', '..');
const controlPlaneCli = path.join(repoRoot, 'runtime', 'control_plane', 'cli.py');
const WORKSPACE_ARTIFACT_PROCEDURE = 'verified_workspace_artifact_v1';
const WINDOWS_CASE_PROCEDURE = 'windows_case_update_v1';
const REVIEW_LAUNCH_PROCEDURE = 'launch_independent_review_v1';
const REVIEW_SUBMIT_PROCEDURE = 'submit_independent_review_result_v1';
const REVIEW_RECONCILE_PROCEDURE = 'reconcile_independent_review_result_v1';
const TASK_ID_RE = /^[0-9a-f]{32}$/;
const REVIEW_RUN_ID_RE = /^[0-9a-f]{64}$/;
const REVIEW_SHA_RE = /^[0-9a-f]{40}$/;
const REVIEW_REPOSITORY_RE = /^[A-Za-z0-9_.-]{1,100}\/[A-Za-z0-9_.-]{1,100}$/;
const REVIEW_SKILL_VERSION_RE = /^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$/;
const MAX_REVIEW_RESULT_BYTES = 256_000;
const INTERNAL_SEMANTIC_TOOLS = new Set([
  'workspace_read',
  'workspace_write',
  'web_open',
  'web_observe',
  'web_interact'
]);
const PUBLIC_TOOLS = new Set([...INTERNAL_SEMANTIC_TOOLS, 'procedure_run']);
// REVIEW_RESULT_V1 is bounded by decoded UTF-8 bytes. JSON transport can expand
// ASCII controls to six-byte \u00XX escapes, so keep the parent response bound
// coherent with the child request/state bound rather than silently truncating a
// result that the review validator itself accepts.
const MAX_PROCEDURE_RESPONSE_BYTES = MAX_REVIEW_RESULT_BYTES * 6 + 65_536;
const SAFE_CHILD_ENV_ALLOWLIST = new Set([
  'PATH', 'Path', 'PATHEXT',
  'SystemRoot', 'SYSTEMROOT', 'WINDIR', 'COMSPEC',
  'TEMP', 'TMP', 'TMPDIR',
  'LOCALAPPDATA', 'HOME', 'USERPROFILE',
  'PROGRAMFILES', 'ProgramFiles', 'PROGRAMFILES(X86)',
  'LANG', 'LC_ALL', 'PYTHONUTF8', 'PYTHONIOENCODING',
  'CHAT_LOCAL_FILES_ROOT',
  'CHAT_PROCEDURE_STATE_ROOT',
  'PLAYWRIGHT_MCP_OUTPUT_DIR'
]);

function toolError(message) {
  return { content: [{ type: 'text', text: message }], isError: true };
}

function procedureFailure(reason, correlationTaskId = null) {
  const payload = {
    schema_version: 1,
    status: 'error',
    reason,
    ...(correlationTaskId === null ? {} : { resume_task_id: correlationTaskId })
  };
  return {
    content: [{ type: 'text', text: JSON.stringify(payload) }],
    structuredContent: payload,
    isError: true
  };
}

function prepareProcedureCorrelation(request) {
  if (request?.procedure !== WORKSPACE_ARTIFACT_PROCEDURE) {
    return { correlationTaskId: null, assignedTaskId: null };
  }
  const resumeTaskId = typeof request?.resume_task_id === 'string'
    ? request.resume_task_id
    : null;
  if (resumeTaskId !== null) {
    if (!TASK_ID_RE.test(resumeTaskId)) {
      throw new Error('resume_task_id must be a 32-character lowercase hex task id');
    }
    return { correlationTaskId: resumeTaskId, assignedTaskId: null };
  }
  const assignedTaskId = randomBytes(16).toString('hex');
  return { correlationTaskId: assignedTaskId, assignedTaskId };
}

function resumableProcedureCorrelation(env, correlationTaskId, assignedTaskId) {
  if (correlationTaskId === null) return null;
  // A caller-supplied resume id is already known independently of this child
  // launch. A newly generated id becomes resumable only after the exact regular
  // checkpoint file is durably visible in the configured state root.
  if (assignedTaskId === null) return correlationTaskId;
  const stateRoot = env?.CHAT_PROCEDURE_STATE_ROOT;
  if (typeof stateRoot !== 'string' || !stateRoot) return null;
  const checkpoint = path.join(stateRoot, `${assignedTaskId}.json`);
  try {
    return fs.lstatSync(checkpoint).isFile() ? correlationTaskId : null;
  } catch {
    return null;
  }
}

function normalizeResult(result) {
  const normalized = { content: Array.isArray(result?.content) ? result.content : [] };
  if (result?.isError) normalized.isError = true;
  if (result?.structuredContent !== undefined) normalized.structuredContent = result.structuredContent;
  return normalized;
}

function safeChildEnvironment() {
  const env = {};
  for (const name of SAFE_CHILD_ENV_ALLOWLIST) {
    const value = process.env[name];
    if (typeof value === 'string') env[name] = value;
  }
  return env;
}

function controlPlaneEnvironment(request) {
  const env = safeChildEnvironment();
  const workspace = env.CHAT_LOCAL_FILES_ROOT;
  if (!workspace) throw new Error('CHAT_LOCAL_FILES_ROOT is required for procedure_run.');

  if (!env.CHAT_PROCEDURE_STATE_ROOT) {
    env.CHAT_PROCEDURE_STATE_ROOT = env.LOCALAPPDATA
      ? path.join(env.LOCALAPPDATA, 'ChatAgentPlatform', 'state', 'procedure-runtime')
      : path.join(workspace, '.chat-agent-platform', 'procedure-state');
  }

  // Admission is selected only from the registered procedure id. The caller
  // cannot supply an admission token, executable, path, backend or command.
  env.CHAT_PROCEDURE_ALLOW_CANDIDATE = request?.procedure === WINDOWS_CASE_PROCEDURE
    ? 'stage26-3b-windows-l3'
    : 'stage26-3a-qualification';
  return env;
}

function controlPlanePython(request, env) {
  if (request?.procedure !== WINDOWS_CASE_PROCEDURE) return 'python';
  if (!env.LOCALAPPDATA) {
    throw new Error('LOCALAPPDATA is required for the registered Windows procedure.');
  }
  const python = path.join(
    env.LOCALAPPDATA,
    'ChatAgentPlatform',
    'stage26',
    'hot-runtime-env',
    'venv',
    'Scripts',
    'python.exe'
  );
  if (!fs.existsSync(python)) {
    throw new Error('accepted Stage 26 Windows runtime environment is not installed.');
  }
  return python;
}

function procedureTimeoutMs(request) {
  return request?.procedure === WINDOWS_CASE_PROCEDURE ? 90_000 : 30_000;
}

const semanticClient = new Client({
  name: 'chat-semantic-control-plane-base-client',
  version: VERSION
});
const semanticTransport = new StdioClientTransport({
  command: process.execPath,
  args: [semanticEntry],
  env: safeChildEnvironment()
});

await semanticClient.connect(semanticTransport);
const inventory = await semanticClient.listTools();
const semanticNames = new Set(inventory.tools.map(tool => tool.name));
const missing = [...INTERNAL_SEMANTIC_TOOLS].filter(name => !semanticNames.has(name));
const unexpected = [...semanticNames].filter(name => !INTERNAL_SEMANTIC_TOOLS.has(name));
if (missing.length || unexpected.length) {
  await semanticClient.close();
  throw new Error(
    `six-tool semantic surface requires the reviewed internal semantic base; missing=${missing.join(',') || 'none'} unexpected=${unexpected.join(',') || 'none'}`
  );
}

async function callSemantic(name, args) {
  if (!INTERNAL_SEMANTIC_TOOLS.has(name)) {
    throw new Error(`refused non-allowlisted semantic tool: ${name}`);
  }
  return normalizeResult(await semanticClient.callTool({ name, arguments: args }));
}

function runProcedure(request) {
  return new Promise((resolve) => {
    let correlation;
    try {
      correlation = prepareProcedureCorrelation(request);
    } catch (error) {
      resolve(toolError(`procedure_run failed: ${error instanceof Error ? error.message : String(error)}`));
      return;
    }
    const { correlationTaskId, assignedTaskId } = correlation;

    let env;
    let python;
    try {
      env = controlPlaneEnvironment(request);
      // This private child-only variable is set after the inherited environment
      // allowlist is built, so a caller/process environment cannot select a new
      // task id. Only this reviewed parent generates it for a new workspace run.
      if (assignedTaskId !== null) env.CHAT_PROCEDURE_ASSIGNED_TASK_ID = assignedTaskId;
      python = controlPlanePython(request, env);
    } catch (error) {
      const reason = error instanceof Error ? error.message : String(error);
      const resumableCorrelationTaskId = assignedTaskId === null ? correlationTaskId : null;
      resolve(
        correlationTaskId === null
          ? toolError(`procedure_run failed: ${reason}`)
          : procedureFailure(`control_plane_setup:${reason}`, resumableCorrelationTaskId)
      );
      return;
    }

    const child = spawn(python, [controlPlaneCli], {
      cwd: repoRoot,
      env,
      stdio: ['pipe', 'pipe', 'ignore'],
      windowsHide: true
    });

    let stdout = Buffer.alloc(0);
    let settled = false;
    const finish = (result) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve(result);
    };
    const fail = (reason) => {
      const resumableCorrelationTaskId = resumableProcedureCorrelation(
        env,
        correlationTaskId,
        assignedTaskId,
      );
      finish(
        correlationTaskId === null
          ? toolError(`procedure_run failed: ${reason}`)
          : procedureFailure(reason, resumableCorrelationTaskId)
      );
    };

    const timer = setTimeout(() => {
      try { child.kill(); } catch {}
      fail('control_plane_timeout');
    }, procedureTimeoutMs(request));

    child.stdout.on('data', chunk => {
      stdout = Buffer.concat([stdout, Buffer.from(chunk)]);
      if (stdout.length > MAX_PROCEDURE_RESPONSE_BYTES) {
        try { child.kill(); } catch {}
        fail('response_too_large');
      }
    });
    child.on('error', error => fail(`control_plane_child_error:${error.name}`));
    child.on('close', (code, signal) => {
      if (settled) return;
      try {
        const parsed = JSON.parse(stdout.toString('utf8'));
        let correlated = parsed;
        if (parsed?.status === 'error' && correlationTaskId !== null) {
          const resumableCorrelationTaskId = resumableProcedureCorrelation(
            env,
            correlationTaskId,
            assignedTaskId,
          );
          correlated = { ...parsed };
          delete correlated.resume_task_id;
          if (resumableCorrelationTaskId !== null) {
            correlated.resume_task_id = resumableCorrelationTaskId;
          }
        }
        finish({
          content: [{ type: 'text', text: JSON.stringify(correlated) }],
          structuredContent: correlated,
          ...(correlated?.status === 'error' ? { isError: true } : {})
        });
      } catch {
        const termination = signal
          ? `signal_${signal}`
          : Number.isInteger(code)
            ? `exit_${code}`
            : 'unknown_exit';
        fail(`invalid_control_plane_response:${termination}`);
      }
    });

    child.stdin.end(JSON.stringify(request));
  });
}

const relativePathSchema = z.string().min(1).max(2048);
const visualFallbackSchema = z.object({
  instruction: z.string().min(1).max(4096),
  targetText: z.string().min(1).max(2048),
  semanticName: z.string().min(1).max(1024).optional()
}).strict();
const interactionExpectedControlSchema = z.object({
  target: z.string().min(1).max(512).optional(),
  present: z.boolean().optional(),
  value: z.string().max(4096).optional(),
  checked: z.boolean().optional(),
  selected: z.boolean().optional(),
  enabled: z.boolean().optional(),
}).strict();
const interactionExpectedSchema = z.object({
  url: z.string().url().max(4096).optional(),
  control: interactionExpectedControlSchema.optional(),
}).strict();
const reviewResultTextSchema = z.string().min(1).refine(
  value => Buffer.byteLength(value, 'utf8') <= MAX_REVIEW_RESULT_BYTES,
  { message: 'review result exceeds the accepted UTF-8 byte bound' }
);
const reviewIdentityShape = {
  repository: z.string().regex(REVIEW_REPOSITORY_RE),
  pr_number: z.number().int().positive().max(2_147_483_647),
  base_sha: z.string().regex(REVIEW_SHA_RE),
  head_sha: z.string().regex(REVIEW_SHA_RE),
  review_skill: z.literal('code-review'),
  review_skill_version: z.string().regex(REVIEW_SKILL_VERSION_RE)
};
const workspaceArtifactProcedureSchema = z.object({
  procedure: z.literal('verified_workspace_artifact_v1'),
  artifact_name: z.string().regex(/^[A-Za-z0-9][A-Za-z0-9._-]{0,62}\.txt$/),
  content: z.string().max(4096),
  resume_task_id: z.string().regex(/^[0-9a-f]{32}$/).optional()
}).strict();
const windowsCaseProcedureSchema = z.object({
  procedure: z.literal(WINDOWS_CASE_PROCEDURE),
  case_id: z.string().regex(/^CASE-[A-F0-9]{8}-[0-9]{4}$/),
  note: z.string().min(1).max(512),
  status: z.enum(['Approved', 'Needs Review'])
}).strict();
const reviewLaunchProcedureSchema = z.object({
  procedure: z.literal(REVIEW_LAUNCH_PROCEDURE),
  ...reviewIdentityShape
}).strict();
const reviewSubmitProcedureSchema = z.object({
  procedure: z.literal(REVIEW_SUBMIT_PROCEDURE),
  review_run_id: z.string().regex(REVIEW_RUN_ID_RE),
  result: reviewResultTextSchema
}).strict();
const reviewReconcileProcedureSchema = z.object({
  procedure: z.literal(REVIEW_RECONCILE_PROCEDURE),
  ...reviewIdentityShape,
  manual_result: reviewResultTextSchema.optional()
}).strict();

const server = new McpServer(
  { name: 'chat-semantic-control-plane', version: VERSION },
  {
    instructions:
      'Canonical Chat Agent Platform semantic surface. It always exposes exactly six reviewed tools: workspace_read, workspace_write, web_open, web_observe, web_interact and procedure_run. Browser mutations require fresh final-state verification. procedure_run admits only registered bounded procedures. The independent-review procedures accept only exact review identity, private run capability/result submission, or exact reconciliation/manual-result fields; launch remains fail-closed before browser dispatch until reviewer authority qualification and Send claiming are separately installed and accepted. No shell, arbitrary Python, URL/prompt launcher, backend selector, generic dispatch or arbitrary filesystem path is exposed.'
  }
);

server.registerTool('workspace_read', {
  title: 'Read Workspace',
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
  title: 'Write Workspace Text',
  description: 'Accepted semantic bounded workspace text write surface.',
  inputSchema: z.object({ path: relativePathSchema, content: z.string().max(4_000_000) }).strict(),
  annotations: { readOnlyHint: false, destructiveHint: true, idempotentHint: true, openWorldHint: false }
}, args => callSemantic('workspace_write', args));

server.registerTool('web_open', {
  title: 'Open Web Page',
  description: 'Accepted isolated semantic web navigation surface.',
  inputSchema: z.object({ url: z.string().url().max(4096) }).strict(),
  annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false, openWorldHint: true }
}, args => callSemantic('web_open', args));

server.registerTool('web_observe', {
  title: 'Observe Web Page',
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
  title: 'Interact With Web Page',
  description: 'Accepted semantic click/type surface with fresh bounded postcondition verification. click and type+submit require expected={url and/or control state}; type without submit may infer value==text. No arbitrary selector, JavaScript or backend dispatch is exposed.',
  inputSchema: z.object({
    operation: z.enum(['click', 'type']),
    target: z.string().min(1).max(4096).optional(),
    element: z.string().min(1).max(1024).optional(),
    doubleClick: z.boolean().optional(),
    text: z.string().max(200000).optional(),
    submit: z.boolean().optional(),
    slowly: z.boolean().optional(),
    visualFallback: visualFallbackSchema.optional(),
    expected: interactionExpectedSchema.optional()
  }).strict(),
  annotations: { readOnlyHint: false, destructiveHint: true, idempotentHint: false, openWorldHint: true }
}, args => callSemantic('web_interact', args));

server.registerTool('procedure_run', {
  title: 'Run Verified Procedure',
  description:
    'Run one registered bounded local procedure. Registered ids are verified_workspace_artifact_v1, windows_case_update_v1, launch_independent_review_v1, submit_independent_review_result_v1 and reconcile_independent_review_result_v1. Reviewer launch accepts only exact review identity and currently ABSTAINS before browser dispatch while reviewer authority is unqualified; it never returns review_run_id. Submit accepts only the private review_run_id plus REVIEW_RESULT_V1 text. Reconcile accepts exact review identity plus optional fresh manual REVIEW_RESULT_V1. No PID, HWND, URL, prompt, path, command, Python, backend, GitHub credential or generic tool selector is accepted.',
  inputSchema: z.union([
    workspaceArtifactProcedureSchema,
    windowsCaseProcedureSchema,
    reviewLaunchProcedureSchema,
    reviewSubmitProcedureSchema,
    reviewReconcileProcedureSchema
  ]),
  annotations: { readOnlyHint: false, destructiveHint: true, idempotentHint: false, openWorldHint: false }
}, args => runProcedure(args));

if (PUBLIC_TOOLS.size !== 6) throw new Error('canonical semantic tool inventory must contain exactly six tools');

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

void serveStdio(() => server);
