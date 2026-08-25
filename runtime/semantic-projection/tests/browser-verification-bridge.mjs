import assert from 'node:assert/strict';

import {
  parsePlaywrightSnapshotResult,
  verifyPlaywrightNavigation,
} from '../lib/browser-verification-bridge.mjs';


function result(text) {
  return { content: [{ type: 'text', text }] };
}

const before = parsePlaywrightSnapshotResult(result(`### Page state
- Page URL: about:blank
- Page Title: 
- Page Snapshot:
\`\`\`yaml

\`\`\``));
assert.equal(before.url, 'about:blank');
assert.equal(before.title, '');
assert.equal(before.snapshot_text, '');
assert.deepEqual(before.controls, []);
assert.equal(before.complete, true);
assert.equal(before.settled, true);

const after = parsePlaywrightSnapshotResult(result(`### Page state
- Page URL: https://example.com/
- Page Title: Example
- Page Snapshot:
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
  () => parsePlaywrightSnapshotResult(result('### Page state\n- Page URL: https://example.com/')),
  /missing Page URL, Page Title or Page Snapshot/,
);

console.log('BROWSER_VERIFICATION_BRIDGE=PASS');
