import assert from 'node:assert/strict';

import {
  parsePlaywrightSnapshotResult,
  verifyPlaywrightInteraction,
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

// @playwright/mcp omits the value suffix for an observable empty value-state
// control. Normalize that omission to "" so pre-action verification can prove
// that typing a non-empty value would create a real delta.
const emptyValueState = parsePlaywrightSnapshotResult(result(`### Page
- Page URL: https://example.com/
- Page Title: Example

### Snapshot
\`\`\`yaml
- textbox "Empty input" [ref=v1]
- searchbox "Empty search" [ref=v2]
\`\`\``));
assert.equal(emptyValueState.controls.find(control => control.control_id === 'v1')?.value, '');
assert.equal(emptyValueState.controls.find(control => control.control_id === 'v2')?.value, '');

// @playwright/mcp omits positive-state markers when checkbox/option state is
// false. That omission is semantically meaningful only for roles that define
// those states; generic controls remain null rather than inferred false.
const roleStateDefaults = parsePlaywrightSnapshotResult(result(`### Page
- Page URL: https://example.com/
- Page Title: Example

### Snapshot
\`\`\`yaml
- checkbox "Off" [ref=c1]
- radio "Radio off" [ref=r1]
- option "Not selected" [ref=o1]
- button "Plain" [ref=b1]
\`\`\``));
assert.equal(roleStateDefaults.controls.find(control => control.control_id === 'c1')?.checked, false);
assert.equal(roleStateDefaults.controls.find(control => control.control_id === 'r1')?.checked, false);
assert.equal(roleStateDefaults.controls.find(control => control.control_id === 'o1')?.selected, false);
assert.equal(roleStateDefaults.controls.find(control => control.control_id === 'b1')?.checked, null);
assert.equal(roleStateDefaults.controls.find(control => control.control_id === 'b1')?.selected, null);

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

const interactionBefore = parsePlaywrightSnapshotResult(result(`### Page
- Page URL: https://example.com/
- Page Title: Example

### Snapshot
\`\`\`yaml
- textbox "Semantic input" [ref=e2]: OLD
- checkbox "Remember" [ref=e3]
\`\`\``));
assert.equal(interactionBefore.controls.find(control => control.control_id === 'e3')?.checked, false);
const interactionVerified = await verifyPlaywrightInteraction({
  before: interactionBefore,
  after,
  expected: {
    control: { control_id: 'e2', value: 'HELLO' },
  },
});
assert.equal(interactionVerified.status, 'pass');
assert.equal(interactionVerified.verification.status, 'pass');

const interactionMismatch = await verifyPlaywrightInteraction({
  before: interactionBefore,
  after,
  expected: {
    control: { control_id: 'e3', checked: false },
  },
});
assert.equal(interactionMismatch.status, 'fail');

await assert.rejects(
  () => verifyPlaywrightInteraction({
    before: interactionBefore,
    after,
    expected: { javascript: 'document.body.innerText' },
  }),
  /invalid_request|unsupported fields/,
);

assert.throws(
  () => parsePlaywrightSnapshotResult(result('### Snapshot\n```yaml\n- heading Missing page\n```')),
  /missing Page URL/,
);

console.log('BROWSER_VERIFICATION_BRIDGE=PASS');
