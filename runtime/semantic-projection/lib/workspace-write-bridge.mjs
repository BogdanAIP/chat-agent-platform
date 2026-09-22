import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { semanticProviderEnvironment } from './semantic-activation.mjs';


const MAX_GATE_RESPONSE_BYTES = 256_000;
const GATE_TIMEOUT_MS = 20_000;
const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, '..', '..', '..');
const gateCli = path.join(repoRoot, 'runtime', 'control_plane', 'semantic_workspace_write.py');

function contentIdentity(content) {
  if (typeof content !== 'string') {
    throw new TypeError('workspace write content must be a string');
  }
  const bytes = Buffer.from(content, 'utf8');
  return {
    contentSha256: createHash('sha256').update(bytes).digest('hex'),
    contentSize: bytes.length,
  };
}

function runGate(request) {
  return new Promise((resolve, reject) => {
    const child = spawn('python', [gateCli], {
      cwd: repoRoot,
      env: semanticProviderEnvironment(),
      stdio: ['pipe', 'pipe', 'ignore'],
      windowsHide: true,
    });

    let stdout = Buffer.alloc(0);
    let settled = false;
    const finish = (fn, value) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      fn(value);
    };
    const timer = setTimeout(() => {
      try { child.kill(); } catch {}
      finish(reject, new Error('semantic workspace gate timeout'));
    }, GATE_TIMEOUT_MS);

    child.stdout.on('data', chunk => {
      stdout = Buffer.concat([stdout, Buffer.from(chunk)]);
      if (stdout.length > MAX_GATE_RESPONSE_BYTES) {
        try { child.kill(); } catch {}
        finish(reject, new Error('semantic workspace gate response too large'));
      }
    });
    child.on('error', error => {
      finish(reject, new Error(`semantic workspace gate spawn failed: ${error.name}`));
    });
    child.on('close', () => {
      if (settled) return;
      try {
        const parsed = JSON.parse(stdout.toString('utf8'));
        if (!parsed || typeof parsed !== 'object') {
          finish(reject, new Error('semantic workspace gate returned invalid response'));
          return;
        }
        if (parsed.status === 'error') {
          finish(reject, new Error(parsed.reason || 'semantic workspace gate error'));
          return;
        }
        finish(resolve, parsed);
      } catch {
        finish(reject, new Error('semantic workspace gate returned invalid JSON'));
      }
    });
    child.stdin.end(JSON.stringify(request));
  });
}

function baseRequest({
  activationRef,
  workspaceRoot,
  relativePath,
  contentSha256,
  contentSize,
}) {
  return {
    activation_ref: activationRef,
    workspace_root: workspaceRoot,
    relative_path: relativePath,
    content_sha256: contentSha256,
    content_size: contentSize,
  };
}

export function semanticWorkspaceWriteIdentity(content) {
  return contentIdentity(content);
}

export async function prepareSemanticWorkspaceWrite({
  activationRef,
  workspaceRoot,
  relativePath,
  contentSha256,
  contentSize,
}) {
  return runGate({
    operation: 'prepare',
    ...baseRequest({
      activationRef,
      workspaceRoot,
      relativePath,
      contentSha256,
      contentSize,
    }),
  });
}

export async function verifySemanticWorkspaceWrite({
  activationRef,
  workspaceRoot,
  relativePath,
  contentSha256,
  contentSize,
  before,
}) {
  return runGate({
    operation: 'verify',
    ...baseRequest({
      activationRef,
      workspaceRoot,
      relativePath,
      contentSha256,
      contentSize,
    }),
    before,
  });
}
