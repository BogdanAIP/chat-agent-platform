import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { createSemanticProviderBindings } from '../lib/semantic-provider-bindings.mjs';


const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const projectionSource = fs.readFileSync(
  path.join(root, 'bin', 'semantic-projection.mjs'),
  'utf8',
);
const seamSource = fs.readFileSync(
  path.join(root, 'lib', 'semantic-provider-bindings.mjs'),
  'utf8',
);

assert.match(projectionSource, /createSemanticProviderBindings/);
for (const forbidden of [
  '@modelcontextprotocol/client',
  '@modelcontextprotocol/server-filesystem',
  '@playwright/mcp',
  'StdioClientTransport',
  'createRequire',
  'FILESYSTEM_ENTRY',
  'PLAYWRIGHT_ENTRY',
]) {
  assert.equal(
    projectionSource.includes(forbidden),
    false,
    `semantic projection still owns provider mechanic: ${forbidden}`,
  );
}

assert.match(seamSource, /@modelcontextprotocol\/server-filesystem/);
assert.match(seamSource, /@playwright\/mcp/);
assert.equal(seamSource.includes('CapabilityGrant'), false);
assert.equal(seamSource.includes('WorkingState'), false);
assert.equal(seamSource.includes('verify_expected_effect'), false);
assert.equal(seamSource.includes('PASS'), false);
assert.equal(seamSource.includes('DONE'), false);

assert.throws(
  () => createSemanticProviderBindings({ workspaceRoot: '', version: '0.1.0' }),
  /workspaceRoot/,
);
assert.throws(
  () => createSemanticProviderBindings({ workspaceRoot: root, version: '' }),
  /version/,
);

const providers = createSemanticProviderBindings({
  workspaceRoot: root,
  version: '0.1.0-test',
});
assert.equal(Object.isFrozen(providers), true);
assert.deepEqual(
  Object.keys(providers).sort(),
  ['browserClient', 'callBrowser', 'callFilesystem', 'close'].sort(),
);

await assert.rejects(
  providers.callFilesystem('browser_click', {}),
  /non-allowlisted downstream tool: filesystem\.browser_click/,
);
await assert.rejects(
  providers.callBrowser('write_file', {}),
  /non-allowlisted downstream tool: playwright\.write_file/,
);
await providers.close();

console.log('SEMANTIC_PROVIDER_SEAM_ACCEPTANCE=PASS');
