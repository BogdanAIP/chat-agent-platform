import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import {
  EXPECTED_SEMANTIC_TOOLS,
  assertExpectedSemanticInventory,
  prepareSemanticRuntimeDirectory,
  resolveSemanticRuntimeDirectory
} from '../bin/semantic-projection-launcher.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const canonicalEntry = path.resolve(here, '..', 'bin', 'semantic-control-plane-projection.mjs');
const privateFiveToolEntry = path.resolve(here, '..', 'bin', 'semantic-projection.mjs');
const launcherEntry = path.resolve(here, '..', 'bin', 'semantic-projection-launcher.mjs');
const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-inventory-guard-workspace-'));
const stateRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-inventory-guard-state-'));
const runtimeRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-semantic-runtime-root-'));

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

try {
  const names = await assertExpectedSemanticInventory({
    entry: canonicalEntry,
    env: childEnvironment()
  });
  assert.deepEqual(names, EXPECTED_SEMANTIC_TOOLS);

  await assert.rejects(
    () => assertExpectedSemanticInventory({
      entry: privateFiveToolEntry,
      env: childEnvironment()
    }),
    /expected exactly:/
  );

  const ownedRuntime = resolveSemanticRuntimeDirectory({
    env: { CHAT_SEMANTIC_RUNTIME_ROOT: runtimeRoot },
    pid: 4242
  });
  assert.equal(ownedRuntime, path.join(runtimeRoot, 'session-4242'));
  assert.equal(path.isAbsolute(ownedRuntime), true);
  assert.notEqual(ownedRuntime, process.cwd());

  const preparedRuntime = prepareSemanticRuntimeDirectory({
    env: { CHAT_SEMANTIC_RUNTIME_ROOT: runtimeRoot },
    pid: 4243
  });
  assert.equal(preparedRuntime, path.join(runtimeRoot, 'session-4243'));
  assert.equal(fs.statSync(preparedRuntime).isDirectory(), true);

  assert.throws(
    () => resolveSemanticRuntimeDirectory({
      env: { CHAT_SEMANTIC_RUNTIME_ROOT: 'relative-runtime-root' },
      pid: 4244
    }),
    /must be an absolute path/
  );

  const launcherSource = fs.readFileSync(launcherEntry, 'utf8');
  const chdirIndex = launcherSource.indexOf('process.chdir(runtimeCwd);');
  const inventoryIndex = launcherSource.indexOf('await assertExpectedSemanticInventory({', chdirIndex);
  const spawnIndex = launcherSource.indexOf('const child = spawn(', chdirIndex);
  assert.ok(chdirIndex >= 0, 'semantic launcher must switch to an owned runtime CWD');
  assert.ok(inventoryIndex > chdirIndex, 'runtime CWD must be owned before live inventory preflight spawns children');
  assert.ok(spawnIndex > inventoryIndex, 'runtime CWD ownership must precede the long-lived semantic child');

  console.log('SEMANTIC_LIVE_INVENTORY_GUARD_CANONICAL=PASS');
  console.log('SEMANTIC_LIVE_INVENTORY_GUARD_REJECTS_FIVE_TOOL=PASS');
  console.log('SEMANTIC_RUNTIME_CWD_OWNERSHIP=PASS');
} finally {
  fs.rmSync(workspace, { recursive: true, force: true });
  fs.rmSync(stateRoot, { recursive: true, force: true });
  fs.rmSync(runtimeRoot, { recursive: true, force: true });
}
