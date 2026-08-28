import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import {
  EXPECTED_SEMANTIC_TOOLS,
  assertExpectedSemanticInventory,
  prepareSemanticRuntimeEnvironment,
  resolveSemanticRuntimePaths
} from '../bin/semantic-projection-launcher.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const canonicalEntry = path.resolve(here, '..', 'bin', 'semantic-control-plane-projection.mjs');
const privateFiveToolEntry = path.resolve(here, '..', 'bin', 'semantic-projection.mjs');
const launcherEntry = path.resolve(here, '..', 'bin', 'semantic-projection-launcher.mjs');
const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-inventory-guard-workspace-'));
const stateRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-inventory-guard-state-'));
const runtimeRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-semantic-runtime-root-'));
const callerRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-semantic-caller-root-'));

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

function ownershipOptions(pid, extraEnv = {}) {
  const env = { ...extraEnv };
  if (process.platform === 'win32') {
    env.LOCALAPPDATA = runtimeRoot;
    return { env, platform: 'win32', pid };
  }
  return { env, platform: process.platform, pid, tempDir: runtimeRoot };
}

function isWithin(parent, child) {
  const relative = path.relative(path.resolve(parent), path.resolve(child));
  return relative === '' || (
    relative !== '..' &&
    !relative.startsWith(`..${path.sep}`) &&
    !path.isAbsolute(relative)
  );
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

  const expectedOwnedRoot = path.join(
    runtimeRoot,
    'ChatAgentPlatform',
    'logs',
    'semantic-runtime'
  );
  const owned = resolveSemanticRuntimePaths(ownershipOptions(4242));
  assert.equal(owned.runtimeDirectory, path.join(expectedOwnedRoot, 'session-4242'));
  assert.equal(
    owned.playwrightOutputDirectory,
    path.join(expectedOwnedRoot, 'session-4242', 'playwright-mcp')
  );
  assert.equal(path.isAbsolute(owned.runtimeDirectory), true);
  assert.notEqual(owned.runtimeDirectory, process.cwd());

  const hostileOutput = path.join(callerRoot, 'caller-selected-playwright-output');
  const prepared = prepareSemanticRuntimeEnvironment(
    ownershipOptions(4243, { PLAYWRIGHT_MCP_OUTPUT_DIR: hostileOutput })
  );
  assert.equal(prepared.runtimeDirectory, path.join(expectedOwnedRoot, 'session-4243'));
  assert.equal(fs.statSync(prepared.runtimeDirectory).isDirectory(), true);
  assert.equal(fs.statSync(prepared.playwrightOutputDirectory).isDirectory(), true);
  assert.equal(prepared.env.PLAYWRIGHT_MCP_OUTPUT_DIR, prepared.playwrightOutputDirectory);
  assert.notEqual(prepared.env.PLAYWRIGHT_MCP_OUTPUT_DIR, hostileOutput);
  assert.equal(fs.existsSync(hostileOutput), false);

  assert.throws(
    () => resolveSemanticRuntimePaths({
      env: {},
      platform: 'win32',
      pid: 4244,
      tempDir: runtimeRoot
    }),
    /LOCALAPPDATA must be an absolute path/
  );
  assert.throws(
    () => resolveSemanticRuntimePaths(ownershipOptions(0)),
    /positive process id/
  );

  const launcherSource = fs.readFileSync(launcherEntry, 'utf8');
  assert.equal(
    launcherSource.includes('CHAT_SEMANTIC_RUNTIME_ROOT'),
    false,
    'runtime ownership must not be caller-selectable through a launcher override'
  );
  assert.ok(
    launcherSource.includes('env.PLAYWRIGHT_MCP_OUTPUT_DIR = paths.playwrightOutputDirectory;'),
    'launcher must force an owned Playwright output path'
  );
  const chdirIndex = launcherSource.indexOf('process.chdir(runtime.runtimeDirectory);');
  const inventoryIndex = launcherSource.indexOf('await assertExpectedSemanticInventory({', chdirIndex);
  const spawnIndex = launcherSource.indexOf('const child = spawn(', chdirIndex);
  assert.ok(chdirIndex >= 0, 'semantic launcher must switch to an owned runtime CWD');
  assert.ok(inventoryIndex > chdirIndex, 'runtime CWD must be owned before live inventory preflight spawns children');
  assert.ok(spawnIndex > inventoryIndex, 'runtime CWD ownership must precede the long-lived semantic child');
  assert.ok(
    launcherSource.includes('cwd: runtime.runtimeDirectory'),
    'long-lived semantic child must also receive the controlled cwd explicitly'
  );

  const controlPlaneSource = fs.readFileSync(canonicalEntry, 'utf8');
  assert.ok(
    controlPlaneSource.includes("'PLAYWRIGHT_MCP_OUTPUT_DIR'"),
    'sanitized semantic child environment must forward the owned Playwright output path'
  );

  const verificationEnv = childEnvironment();
  verificationEnv.PLAYWRIGHT_MCP_OUTPUT_DIR = hostileOutput;
  if (process.platform === 'win32') {
    verificationEnv.LOCALAPPDATA = runtimeRoot;
  } else {
    verificationEnv.TEMP = runtimeRoot;
    verificationEnv.TMP = runtimeRoot;
    verificationEnv.TMPDIR = runtimeRoot;
  }
  const verification = spawnSync(
    process.execPath,
    [launcherEntry, '--verify-runtime-output-ownership'],
    {
      cwd: callerRoot,
      env: verificationEnv,
      encoding: 'utf8',
      windowsHide: true
    }
  );
  assert.equal(verification.status, 0, verification.stderr);
  const report = JSON.parse(verification.stdout.trim().split(/\r?\n/).at(-1));
  assert.equal(path.resolve(report.caller_cwd), path.resolve(callerRoot));
  assert.equal(report.playwright_output_dir, report.playwright_env_output_dir);
  assert.equal(isWithin(callerRoot, report.runtime_dir), false);
  assert.equal(isWithin(callerRoot, report.playwright_output_dir), false);
  assert.equal(path.resolve(report.playwright_output_dir), path.resolve(hostileOutput), false);
  assert.equal(fs.existsSync(path.join(callerRoot, '.playwright-mcp')), false);
  assert.equal(fs.existsSync(hostileOutput), false);

  console.log('SEMANTIC_LIVE_INVENTORY_GUARD_CANONICAL=PASS');
  console.log('SEMANTIC_LIVE_INVENTORY_GUARD_REJECTS_FIVE_TOOL=PASS');
  console.log('SEMANTIC_RUNTIME_CWD_OWNERSHIP=PASS');
  console.log('SEMANTIC_PLAYWRIGHT_OUTPUT_OWNERSHIP=PASS');
} finally {
  fs.rmSync(workspace, { recursive: true, force: true });
  fs.rmSync(stateRoot, { recursive: true, force: true });
  fs.rmSync(runtimeRoot, { recursive: true, force: true });
  fs.rmSync(callerRoot, { recursive: true, force: true });
}
