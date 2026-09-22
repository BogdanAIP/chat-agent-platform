import assert from 'node:assert/strict';

import { authorizeSemanticBrowserMutation } from '../lib/browser-authorization-bridge.mjs';
import {
  SEMANTIC_BROWSER_POLICY_REF,
  createSemanticActivationEnvironment,
} from '../lib/semantic-activation.mjs';


const activation = createSemanticActivationEnvironment(process.env, {
  randomBytesFn: () => Buffer.alloc(16, 0x11),
});

const before = {
  url: 'https://example.com/',
  complete: true,
  settled: true,
  ambiguous: false,
  controls: [],
};

for (const [label, text] of [
  ['cyrillic', 'я'.repeat(190_000)],
  ['non-bmp', '😀'.repeat(95_000)],
  ['escaped-controls', '\0'.repeat(200_000)],
]) {
  const result = await authorizeSemanticBrowserMutation({
    activationRef: activation.activationRef,
    browserPolicyRef: SEMANTIC_BROWSER_POLICY_REF,
    actionRef: 'browser.type',
    before,
    resource: {
      operation: 'type',
      target: 'e1',
      element: null,
      double_click: null,
      text,
      submit: true,
      slowly: false,
      visual_fallback: null,
      expected: { url: 'https://example.com/done' },
    },
  });
  assert.equal(result.status, 'authorized', label);
  assert.equal(result.action_ref, 'browser.type', label);
  assert.match(result.resource_scope_ref, /^semantic-browser-resource:[0-9a-f]{64}$/, label);
}

console.log('SEMANTIC_BROWSER_AUTHORIZATION_UNICODE_BOUNDARY=PASS');
