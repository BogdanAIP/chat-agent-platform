import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

import {
  BROWSERSKILL_IDENTITY,
  BROWSERSKILL_MODEL_TOOL_ACTIONS,
  BROWSERSKILL_PROTOCOL_METHODS,
  BROWSERSKILL_RUNTIME_STATUS,
  assertBrowserSkillRuntimeIdentity,
  validateBrowserSkillManifest,
} from '../lib/browserskill-capability-manifest.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const fixture = JSON.parse(
  await readFile(path.join(here, 'fixtures', 'browserskill-v0.3.1-inventory.json'), 'utf8'),
);

assert.equal(validateBrowserSkillManifest(), true);

assert.deepEqual(BROWSERSKILL_IDENTITY, {
  version: '0.3.1',
  protocolVersion: '1.3',
  sourceCommit: 'da6bf4eed2dd7256567e152df8c903c87f6598c3',
  cliTag: 'cli-v0.3.1',
  extensionTag: 'ext-v0.3.1',
});

assert.equal(fixture.source_commit, BROWSERSKILL_IDENTITY.sourceCommit);
assert.equal(fixture.protocol_version, BROWSERSKILL_IDENTITY.protocolVersion);

const manifestMethods = Object.keys(BROWSERSKILL_PROTOCOL_METHODS).sort();
const upstreamMethods = [...fixture.protocol_methods].sort();

assert.deepEqual(
  manifestMethods,
  upstreamMethods,
  'Every pinned BrowserSkill protocol method must have exactly one CAP classification',
);

assert.deepEqual(
  BROWSERSKILL_MODEL_TOOL_ACTIONS,
  fixture.model_facing_tools,
  'Every pinned BrowserSkill model-facing grouped action must stay represented',
);

for (const method of upstreamMethods) {
  const classification = BROWSERSKILL_PROTOCOL_METHODS[method];
  assert.equal(typeof classification, 'string');
  assert.ok(classification.length > 0, `missing classification for ${method}`);
}

assert.equal(
  Object.entries(BROWSERSKILL_PROTOCOL_METHODS).filter(
    ([, classification]) => classification === 'CROSS_CAPABILITY_GRANT_REQUIRED',
  ).length,
  2,
  'BrowserSkill upload/download must remain explicit cross-capability consequences',
);

for (const method of ['tool.evaluate', 'tool.debug', 'tool.record_start', 'audit.request']) {
  assert.equal(
    BROWSERSKILL_PROTOCOL_METHODS[method],
    'NEW_CONSEQUENCE_CONTRACT_REQUIRED',
    `${method} must remain visible but fail closed behind a truthful CAP consequence contract`,
  );
}

assert.equal(
  BROWSERSKILL_PROTOCOL_METHODS['tool.request_help'],
  'HUMAN_ASSIST',
);


const groupedKeys = Object.entries(BROWSERSKILL_MODEL_TOOL_ACTIONS)
  .flatMap(([tool, actions]) => actions.map(action => `${tool}:${action}`))
  .sort();
const statusGroupedKeys = Object.keys(BROWSERSKILL_RUNTIME_STATUS)
  .filter(key => !key.startsWith('extended:'))
  .sort();
assert.deepEqual(
  statusGroupedKeys,
  groupedKeys,
  'Every pinned grouped BrowserSkill action must have one explicit runtime status',
);
assert.equal(BROWSERSKILL_RUNTIME_STATUS['browser_page:navigate'], 'PUBLIC_CURRENT');
assert.equal(
  BROWSERSKILL_RUNTIME_STATUS['browser_tabs:borrow'],
  'MAPPED_PENDING_PUBLIC_CONTRACT',
);
assert.equal(
  BROWSERSKILL_RUNTIME_STATUS['extended:upload'],
  'MAPPED_CROSS_CAPABILITY_GRANT_REQUIRED',
);
assert.equal(
  BROWSERSKILL_RUNTIME_STATUS['extended:evaluate'],
  'MAPPED_BLOCKED_NEW_CONSEQUENCE_CONTRACT',
);

assert.equal(
  assertBrowserSkillRuntimeIdentity({ version: '0.3.1', protocolVersion: '1.3' }),
  true,
);

assert.throws(
  () => assertBrowserSkillRuntimeIdentity({ version: '0.3.2', protocolVersion: '1.3' }),
  /unsupported BrowserSkill version/,
);

assert.throws(
  () => assertBrowserSkillRuntimeIdentity({ version: '0.3.1', protocolVersion: '1.4' }),
  /unsupported BrowserSkill protocol/,
);

console.log('BROWSERSKILL_PINNED_INVENTORY_EXHAUSTIVE=PASS');
console.log('BROWSERSKILL_MODEL_TOOL_ACTIONS_EXHAUSTIVE=PASS');
console.log('BROWSERSKILL_RUNTIME_IDENTITY_FAIL_CLOSED=PASS');
console.log('BROWSERSKILL_HIGH_CONSEQUENCE_CAPABILITIES_EXPLICIT=PASS');
console.log('BROWSERSKILL_RUNTIME_STATUS_EXHAUSTIVE=PASS');
