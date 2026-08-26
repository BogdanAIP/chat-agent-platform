import assert from 'node:assert/strict';

import {
  parsePlaywrightSnapshotResult,
  verifyPlaywrightNavigation,
} from '../lib/browser-verification-bridge.mjs';


function result(text) {
  return { content: [{ type: 'text', text }] };
}

// Exact current @playwright/mcp 0.0.78 shape: empty titles are omitted.
const before = parsePlaywrightSnapshotResult(result(`### Page
- Page URL: about:blank

### Snapshot
\`\`\`yaml

\`\`\``));
assert.equal(before.url, 'about:blank');
assert.equal(before.title, '');
assert.equal(before.snapshot_text, '');
assert.deepEqual(before.controls, []);
assert.equal(before.complete, true);
assert.equal(before.settled, true);

const after = parsePlaywrightSnapshotResult(result(`### Page
- Page URL: https://example.com/
- Page Title: Example

### Snapshot
\`\`\`yaml
- heading "Example" [level=1]
- button "Save" [ref=e1]
- textbox "Semantic input" [ref=e2]: HELLO
- checkbox "Remember" [checked] [ref=e3]
\`\`\``));
assert.equal(after.url, 'https://example.com/');
assert.equal(after.title, 'Example');
assert.equal(after.controls.length, 3);
assert.deepEqual(after.controls.find(control => control.control_id === 'e1'), {
  control_id: 'e1', role: 'button', name: 'Save', enabled: true,
  checked: null, selected: null, visible: true, value: null,
});
assert.equal(after.controls.find(control => control.control_id === 'e2')?.value, 'HELLO');
assert.equal(after.controls.find(control => control.control_id === 'e3')?.checked, true);

// Preserve bounded compatibility with the older inline Page Snapshot shape.
const legacyInline = parsePlaywrightSnapshotResult(result(`### Page state
- Page URL: https://legacy.example/
- Page Title: Legacy
- Page Snapshot:
\`\`\`yaml
- button "Legacy" [ref=l1]
\`\`\``));
assert.equal(legacyInline.url, 'https://legacy.example/');
assert.equal(legacyInline.title, 'Legacy');
assert.equal(legacyInline.controls[0]?.control_id, 'l1');

const verified = await verifyPlaywrightNavigation({
  before,
  after,
  expectedUrl: 'https://EXAMPLE.com:443',
});
assert.equal(verified.status, 'pass');
assert.equal(verified.verification.status, 'pass');
assert.equal(verified.expected_url, 'https://example.com/');

const redirectMismatch = await verifyPlaywrightNavigation({
  before,
  after: { ...after, url: 'https://example.com/final' },
  expectedUrl: 'https://example.com/redirect',
});
assert.equal(redirectMismatch.status, 'fail');

assert.throws(
  () => parsePlaywrightSnapshotResult(result('### Snapshot\n```yaml\n- heading Missing page\n```')),
  /missing Page URL/,
);

console.log('BROWSER_VERIFICATION_BRIDGE=PASS');
