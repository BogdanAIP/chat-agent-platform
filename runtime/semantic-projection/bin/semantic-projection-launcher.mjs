#!/usr/bin/env node

const tunnelOnlyCredentialKeys = [
  'CONTROL_PLANE_API_KEY',
  'OPENAI_API_KEY'
];

for (const key of tunnelOnlyCredentialKeys) {
  delete process.env[key];
}

if (process.argv.includes('--verify-credential-scrub')) {
  for (const key of tunnelOnlyCredentialKeys) {
    if (Object.prototype.hasOwnProperty.call(process.env, key)) {
      console.error(`semantic launcher failed to scrub ${key}`);
      process.exit(1);
    }
  }
  console.log('SEMANTIC_TUNNEL_CREDENTIAL_SCRUB=PASS');
  process.exit(0);
}

await import('./semantic-projection.mjs');
