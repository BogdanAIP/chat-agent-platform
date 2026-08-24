import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const launcher = path.resolve(here, '..', 'bin', 'semantic-projection-launcher.mjs');
const source = fs.readFileSync(launcher, 'utf8');

const deleteIndex = source.indexOf('delete process.env[key]');
const semanticEntryIndex = source.indexOf("path.join(launcherDir, 'semantic-control-plane-projection.mjs')");
const spawnIndex = source.indexOf('spawn(process.execPath, [semanticEntry]');
assert(deleteIndex >= 0, 'launcher must delete tunnel-only credentials');
assert(semanticEntryIndex > deleteIndex, 'six-tool semantic entry must be resolved after credential scrub');
assert(spawnIndex > semanticEntryIndex, 'credential scrub and fixed semantic entry resolution must happen before child spawn');
assert(source.includes("'CONTROL_PLANE_API_KEY'"));
assert(source.includes("'OPENAI_API_KEY'"));
assert(source.includes("'OPENAI_ADMIN_KEY'"));

for (const legacyName of [
  'semantic-projection_1mcp_workspace_read',
  'semantic-projection_1mcp_workspace_write',
  'semantic-projection_1mcp_web_open',
  'semantic-projection_1mcp_web_observe',
  'semantic-projection_1mcp_web_interact',
  'semantic-projection_1mcp_procedure_run'
]) {
  assert(source.includes(`'${legacyName}'`), `missing reviewed frozen-action alias: ${legacyName}`);
}

const sentinel = 'STAGE26_3A_SECRET_MUST_NOT_REACH_SEMANTIC_CORE';
const child = spawnSync(
  process.execPath,
  [launcher, '--verify-credential-scrub'],
  {
    cwd: path.dirname(launcher),
    env: {
      ...process.env,
      CONTROL_PLANE_API_KEY: sentinel,
      OPENAI_API_KEY: sentinel,
      OPENAI_ADMIN_KEY: sentinel,
      CHAT_LOCAL_FILES_ROOT: process.cwd()
    },
    encoding: 'utf8',
    windowsHide: true
  }
);

assert.equal(child.status, 0, `secure launcher verification failed:\n${child.stderr}`);
assert(child.stdout.includes('SEMANTIC_TUNNEL_CREDENTIAL_SCRUB=PASS'), child.stdout);
assert(!child.stdout.includes(sentinel), 'credential value leaked to launcher stdout');
assert(!child.stderr.includes(sentinel), 'credential value leaked to launcher stderr');

console.log('SEMANTIC_TUNNEL_PARENT_ENV_SENTINEL=INJECTED');
console.log('SEMANTIC_TUNNEL_CREDENTIAL_SCRUB_ORDER=PASS');
console.log('SEMANTIC_TUNNEL_CREDENTIAL_SCRUB=PASS');
