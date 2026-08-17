const STRIPPED_CHILD_ENVIRONMENT_KEYS = Object.freeze([
  'CONTROL_PLANE_API_KEY'
]);

export function sanitizedBackendEnvironment(source = process.env) {
  if (!source || typeof source !== 'object') {
    throw new Error('Backend environment source must be an object.');
  }

  const env = {};
  for (const [key, value] of Object.entries(source)) {
    if (typeof value === 'string' && !STRIPPED_CHILD_ENVIRONMENT_KEYS.includes(key)) {
      env[key] = value;
    }
  }
  return env;
}

export function scrubProjectionOnlySecrets(target = process.env) {
  if (!target || typeof target !== 'object') {
    throw new Error('Projection environment target must be an object.');
  }

  for (const key of STRIPPED_CHILD_ENVIRONMENT_KEYS) {
    if (Object.prototype.hasOwnProperty.call(target, key)) {
      delete target[key];
    }
  }
}

export { STRIPPED_CHILD_ENVIRONMENT_KEYS };
