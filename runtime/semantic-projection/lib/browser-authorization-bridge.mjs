import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { semanticProviderEnvironment } from './semantic-activation.mjs';


const MAX_RESPONSE_BYTES = 256_000;
const TIMEOUT_MS = 15_000;
const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, '..', '..', '..');
const authorizerCli = path.join(
  repoRoot,
  'runtime',
  'control_plane',
  'semantic_browser_authorization.py',
);

function canonicalize(value) {
  if (
    value === null ||
    typeof value === 'string' ||
    typeof value === 'boolean' ||
    Number.isInteger(value)
  ) {
    return value;
  }
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value && typeof value === 'object') {
    const result = {};
    for (const key of Object.keys(value).sort()) {
      const item = value[key];
      if (item === undefined) continue;
      result[key] = canonicalize(item);
    }
    return result;
  }
  throw new Error('semantic browser authorization input must be plain JSON');
}

function canonicalBytes(value) {
  return Buffer.from(JSON.stringify(canonicalize(value)), 'utf8');
}

export function browserObservationFingerprint(observation) {
  if (!observation || typeof observation !== 'object' || Array.isArray(observation)) {
    throw new Error('browser observation must be one object');
  }
  return createHash('sha256').update(canonicalBytes(observation)).digest('hex');
}

function runAuthorizer(request) {
  return new Promise((resolve, reject) => {
    const child = spawn('python', [authorizerCli], {
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
      finish(reject, new Error('semantic browser authorizer timeout'));
    }, TIMEOUT_MS);

    child.stdout.on('data', chunk => {
      stdout = Buffer.concat([stdout, Buffer.from(chunk)]);
      if (stdout.length > MAX_RESPONSE_BYTES) {
        try { child.kill(); } catch {}
        finish(reject, new Error('semantic browser authorizer response too large'));
      }
    });
    child.on('error', error => {
      finish(
        reject,
        new Error(`semantic browser authorizer spawn failed: ${error.name}`),
      );
    });
    child.on('close', () => {
      if (settled) return;
      try {
        const parsed = JSON.parse(stdout.toString('utf8'));
        if (!parsed || typeof parsed !== 'object') {
          finish(reject, new Error('semantic browser authorizer returned invalid response'));
          return;
        }
        if (parsed.status === 'error') {
          finish(reject, new Error(parsed.reason || 'semantic browser authorizer error'));
          return;
        }
        finish(resolve, parsed);
      } catch {
        finish(reject, new Error('semantic browser authorizer returned invalid JSON'));
      }
    });
    child.stdin.end(JSON.stringify(request));
  });
}

export async function authorizeSemanticBrowserMutation({
  activationRef,
  browserPolicyRef,
  actionRef,
  before,
  resource,
}) {
  const beforeFingerprint = browserObservationFingerprint(before);
  return runAuthorizer({
    activation_ref: activationRef,
    browser_policy_ref: browserPolicyRef,
    action_ref: actionRef,
    before_fingerprint: beforeFingerprint,
    resource: canonicalize(resource),
  });
}
