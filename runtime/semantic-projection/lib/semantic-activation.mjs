import { randomBytes } from 'node:crypto';

export const SEMANTIC_ACTIVATION_VERSION = 'semantic-activation-v1';
export const SEMANTIC_BROWSER_POLICY_REF = 'isolated-playwright-public-http-loopback-v1';
export const SEMANTIC_ACTIVATION_ENV_KEYS = Object.freeze([
  'CHAT_SEMANTIC_ACTIVATION_REF',
  'CHAT_SEMANTIC_ACTIVATION_VERSION',
  'CHAT_SEMANTIC_BROWSER_POLICY_REF'
]);

const SEMANTIC_ACTIVATION_REF_RE = /^[0-9a-f]{32}$/;
const SAFE_PROVIDER_ENV_ALLOWLIST = new Set([
  'PATH', 'Path', 'PATHEXT',
  'SystemRoot', 'SYSTEMROOT', 'WINDIR', 'COMSPEC',
  'TEMP', 'TMP', 'TMPDIR',
  'LOCALAPPDATA', 'HOME', 'USERPROFILE',
  'PROGRAMFILES', 'ProgramFiles', 'PROGRAMFILES(X86)',
  'LANG', 'LC_ALL', 'PYTHONUTF8', 'PYTHONIOENCODING',
  'PLAYWRIGHT_MCP_OUTPUT_DIR'
]);

function stringEnvironment(source) {
  const env = {};
  for (const [key, value] of Object.entries(source ?? {})) {
    if (typeof value === 'string') env[key] = value;
  }
  return env;
}

export function createSemanticActivationEnvironment(
  baseEnv,
  { randomBytesFn = randomBytes } = {},
) {
  if (typeof randomBytesFn !== 'function') {
    throw new TypeError('semantic activation randomBytesFn must be a function');
  }
  const env = stringEnvironment(baseEnv);
  for (const key of SEMANTIC_ACTIVATION_ENV_KEYS) delete env[key];

  const raw = randomBytesFn(16);
  if (!Buffer.isBuffer(raw) || raw.length !== 16) {
    throw new Error('semantic activation identity source must return exactly 16 bytes');
  }
  const activationRef = raw.toString('hex');
  env.CHAT_SEMANTIC_ACTIVATION_REF = activationRef;
  env.CHAT_SEMANTIC_ACTIVATION_VERSION = SEMANTIC_ACTIVATION_VERSION;
  env.CHAT_SEMANTIC_BROWSER_POLICY_REF = SEMANTIC_BROWSER_POLICY_REF;
  return {
    env,
    activationRef,
    activationVersion: SEMANTIC_ACTIVATION_VERSION,
    browserPolicyRef: SEMANTIC_BROWSER_POLICY_REF,
  };
}

export function requireSemanticActivation(env = process.env) {
  const activationRef = env.CHAT_SEMANTIC_ACTIVATION_REF;
  const activationVersion = env.CHAT_SEMANTIC_ACTIVATION_VERSION;
  const browserPolicyRef = env.CHAT_SEMANTIC_BROWSER_POLICY_REF;
  if (typeof activationRef !== 'string' || !SEMANTIC_ACTIVATION_REF_RE.test(activationRef)) {
    throw new Error('semantic mutation runtime requires a launcher-owned activation_ref');
  }
  if (activationVersion !== SEMANTIC_ACTIVATION_VERSION) {
    throw new Error('semantic mutation runtime activation version mismatch');
  }
  if (browserPolicyRef !== SEMANTIC_BROWSER_POLICY_REF) {
    throw new Error('semantic mutation runtime browser policy mismatch');
  }
  return Object.freeze({ activationRef, activationVersion, browserPolicyRef });
}

export function semanticProviderEnvironment(env = process.env) {
  const result = {};
  for (const name of SAFE_PROVIDER_ENV_ALLOWLIST) {
    const value = env[name];
    if (typeof value === 'string') result[name] = value;
  }
  return result;
}
