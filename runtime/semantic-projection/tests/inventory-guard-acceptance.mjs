import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const launcher = path.resolve(here, '..', 'bin', 'semantic-projection-launcher.mjs');
const canonicalEntry = path.resolve(here, '..', 'bin', 'semantic-control-plane-projection.mjs');
const privateFiveToolEntry = path.resolve(here, '..', 'bin', 'semantic-projection.mjs');
const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-inventory-guard-workspace-'));
const stateRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-inventory-guard-state-'));

function childEnvironment() {
  const env = {};
  for (const [key, value] of Object.entries(process.env)) if (typeof value === 'string') env[key] = value;
  env.CHAT_LOCAL_FILES_ROOT = workspace;
  env.CHAT_PROCEDURE_STATE_ROOT = stateRoot;
  delete env.CONTROL_PLANE_API_KEY;
  delete env.OPENAI_API_KEY;
  delete env.OPENAI_ADMIN_KEY;
  return env;
}

function verify(entry) {
  return spawnSync(
    process.execPath,
    [launcher, '--verify-inventory-entry', entry],
    {
      env: childEnvironment(),
      encoding: 'utf8',
      timeout: 30_000,
      windowsHide: true
    }
  );
}

try {
  const canonical = verify(canonicalEntry);
  assert.equal(canonical.error, undefined, canonical.error?.message);
  assert.equal(canonical.status, 0, `canonical inventory guard failed:\n${canonical.stderr}`);
  assert.match(canonical.stdout, /SEMANTIC_LIVE_INVENTORY_GUARD=PASS/);
  assert.match(canonical.stdout, /procedure_run/);

  const privateFive = verify(privateFiveToolEntry);
  assert.equal(privateFive.error, undefined, privateFive.error?.message);
  assert.equal(privateFive.status, 1, `five-tool private base unexpectedly passed:\n${privateFive.stdout}`);
  assert.match(privateFive.stderr, /semantic launcher live inventory preflight failed/);
  assert.match(privateFive.stderr, /expected exactly:/);

  console.log('SEMANTIC_LIVE_INVENTORY_GUARD_CANONICAL=PASS');
  console.log('SEMANTIC_LIVE_INVENTORY_GUARD_REJECTS_FIVE_TOOL=PASS');
} finally {
  fs.rmSync(workspace, { recursive: true, force: true });
  fs.rmSync(stateRoot, { recursive: true, force: true });
}
