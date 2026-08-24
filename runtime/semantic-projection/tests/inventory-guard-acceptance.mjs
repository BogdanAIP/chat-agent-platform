import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import {
  EXPECTED_SEMANTIC_TOOLS,
  assertExpectedSemanticInventory
} from '../lib/semantic-inventory-guard.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
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

  console.log('SEMANTIC_LIVE_INVENTORY_GUARD_CANONICAL=PASS');
  console.log('SEMANTIC_LIVE_INVENTORY_GUARD_REJECTS_FIVE_TOOL=PASS');
} finally {
  fs.rmSync(workspace, { recursive: true, force: true });
  fs.rmSync(stateRoot, { recursive: true, force: true });
}
