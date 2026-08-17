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
const importIndex = source.indexOf("await import('./semantic-projection.mjs')");
assert(deleteIndex >= 0, 'launcher must delete tunnel-only credentials');
assert(importIndex > deleteIndex, 'credential scrub must happen before semantic core import');
assert(source.includes("'CONTROL_PLANE_API_KEY'"));
assert(source.includes("'OPENAI_API_KEY'"));

const sentinel = 'STAGE25_1_SECRET_MUST_NOT_REACH_SEMANTIC_CORE';
const child = spawnSync(
  process.execPath,
  [launcher, '--verify-credential-scrub'],
  {
    cwd: path.dirname(launcher),
    env: {
      ...process.env,
      CONTROL_PLANE_API_KEY: sentinel,
      OPENAI_API_KEY: sentinel,
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
