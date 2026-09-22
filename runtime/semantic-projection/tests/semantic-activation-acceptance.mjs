import assert from 'node:assert/strict';

import {
  SEMANTIC_ACTIVATION_ENV_KEYS,
  SEMANTIC_ACTIVATION_VERSION,
  SEMANTIC_BROWSER_POLICY_REF,
  createSemanticActivationEnvironment,
  requireSemanticActivation,
  semanticProviderEnvironment,
} from '../lib/semantic-activation.mjs';


const hostile = {
  CHAT_SEMANTIC_ACTIVATION_REF: 'f'.repeat(32),
  CHAT_SEMANTIC_ACTIVATION_VERSION: 'hostile-version',
  CHAT_SEMANTIC_BROWSER_POLICY_REF: 'hostile-policy',
  CHAT_LOCAL_FILES_ROOT: 'hostile-workspace-marker',
  PATH: process.env.PATH ?? '',
};

const first = createSemanticActivationEnvironment(hostile, {
  randomBytesFn: () => Buffer.alloc(16, 0x01),
});
const second = createSemanticActivationEnvironment(hostile, {
  randomBytesFn: () => Buffer.alloc(16, 0x02),
});

assert.equal(first.activationRef, '01'.repeat(16));
assert.equal(second.activationRef, '02'.repeat(16));
assert.notEqual(first.activationRef, hostile.CHAT_SEMANTIC_ACTIVATION_REF);
assert.notEqual(first.activationRef, second.activationRef);
assert.equal(first.env.CHAT_SEMANTIC_ACTIVATION_VERSION, SEMANTIC_ACTIVATION_VERSION);
assert.equal(first.env.CHAT_SEMANTIC_BROWSER_POLICY_REF, SEMANTIC_BROWSER_POLICY_REF);

const required = requireSemanticActivation(first.env);
assert.equal(required.activationRef, first.activationRef);
assert.equal(required.activationVersion, SEMANTIC_ACTIVATION_VERSION);
assert.equal(required.browserPolicyRef, SEMANTIC_BROWSER_POLICY_REF);

assert.throws(
  () => requireSemanticActivation({}),
  /requires a launcher-owned activation_ref/,
);
assert.throws(
  () => requireSemanticActivation({
    ...first.env,
    CHAT_SEMANTIC_ACTIVATION_VERSION: 'wrong',
  }),
  /activation version mismatch/,
);

const providerEnv = semanticProviderEnvironment(first.env);
for (const key of SEMANTIC_ACTIVATION_ENV_KEYS) {
  assert.equal(
    Object.prototype.hasOwnProperty.call(providerEnv, key),
    false,
    `provider environment leaked semantic activation key ${key}`,
  );
}
assert.equal(
  Object.prototype.hasOwnProperty.call(providerEnv, 'CHAT_LOCAL_FILES_ROOT'),
  false,
  'provider environment must receive filesystem root through bounded process args, not ambient CAP scope',
);

console.log('SEMANTIC_ACTIVATION_INHERITED_OVERRIDE=PASS');
console.log('SEMANTIC_ACTIVATION_PER_LIFETIME_IDENTITY=PASS');
console.log('SEMANTIC_PROVIDER_ACTIVATION_SCRUB=PASS');
