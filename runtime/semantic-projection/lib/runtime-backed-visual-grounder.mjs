import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(here, '..', '..', '..');
const CONTROLLER_PATH = path.join(REPO_ROOT, 'scripts', 'local-vision-runtime.ps1');
const GROUNDER_CLI_PATH = path.join(REPO_ROOT, 'scripts', 'production-visual-grounder.py');
const REVIEWED_PROFILE = 'lfm25-vl-450m-f16';
const REVIEWED_PORT = 3068;
const MAX_OUTPUT_BYTES = 4 * 1024 * 1024;
const MAX_INPUT_PNG_BYTES = 8 * 1024 * 1024;

function defaultPythonExecutable() {
  const localAppData = process.env.LOCALAPPDATA;
  if (!localAppData) {
    throw new Error('LOCALAPPDATA is required to resolve the reviewed Stage 25 vision Python environment.');
  }
  return path.join(
    localAppData,
    'ChatAgentPlatform',
    'stage25',
    'python-vision-venv',
    'Scripts',
    'python.exe'
  );
}

function collectProcess(command, args, { input, timeoutMs = 150_000 } = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: REPO_ROOT,
      windowsHide: true,
      stdio: ['pipe', 'pipe', 'pipe']
    });
    const stdout = [];
    const stderr = [];
    let stdoutBytes = 0;
    let stderrBytes = 0;
    let settled = false;

    const timer = setTimeout(() => {
      if (settled) return;
      child.kill('SIGKILL');
      settled = true;
      reject(new Error(`internal visual-grounder child timed out after ${timeoutMs}ms`));
    }, timeoutMs);

    function append(chunks, chunk, current, label) {
      const next = current + chunk.length;
      if (next > MAX_OUTPUT_BYTES) {
        child.kill('SIGKILL');
        throw new Error(`${label} exceeded ${MAX_OUTPUT_BYTES} bytes`);
      }
      chunks.push(chunk);
      return next;
    }

    child.stdout.on('data', chunk => {
      try {
        stdoutBytes = append(stdout, chunk, stdoutBytes, 'stdout');
      } catch (error) {
        if (!settled) {
          settled = true;
          clearTimeout(timer);
          reject(error);
        }
      }
    });
    child.stderr.on('data', chunk => {
      try {
        stderrBytes = append(stderr, chunk, stderrBytes, 'stderr');
      } catch (error) {
        if (!settled) {
          settled = true;
          clearTimeout(timer);
          reject(error);
        }
      }
    });
    child.once('error', error => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      reject(error);
    });
    child.once('close', code => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve({
        code: Number.isInteger(code) ? code : -1,
        stdout: Buffer.concat(stdout).toString('utf8'),
        stderr: Buffer.concat(stderr).toString('utf8')
      });
    });

    if (input !== undefined) child.stdin.end(input);
    else child.stdin.end();
  });
}

function parseSingleJson(stdout, label) {
  if (typeof stdout !== 'string' || !stdout.trim()) {
    throw new Error(`${label} returned empty stdout`);
  }
  try {
    return JSON.parse(stdout.trim());
  } catch {
    throw new Error(`${label} did not return one valid JSON object`);
  }
}

function validateRuntimeStatus(status) {
  if (!status || typeof status !== 'object' || Array.isArray(status)) {
    throw new Error('vision runtime status must be an object');
  }
  if (status.profile !== REVIEWED_PROFILE) {
    throw new Error(`vision runtime profile mismatch: ${String(status.profile)}`);
  }
  if (status.port !== REVIEWED_PORT) {
    throw new Error(`vision runtime port mismatch: ${String(status.port)}`);
  }
  if (status.conflict === true || status.running !== true || status.ready !== true || status.state !== 'ready') {
    throw new Error(`vision runtime is not ready and exclusively owned: ${String(status.state)}`);
  }
  return status;
}

function normalizeGrounderPayload(payload) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload) || payload.schema_version !== 1) {
    throw new Error('production grounder returned malformed JSON contract');
  }
  if (payload.status === 'abstain') {
    return {
      status: 'abstain',
      reason: typeof payload.reason === 'string' && payload.reason ? payload.reason : 'grounder-abstain'
    };
  }
  if (payload.status === 'error') {
    throw new Error(`production-grounder-error:${String(payload.reason || 'unknown')}`);
  }
  if (payload.status !== 'resolved') {
    throw new Error(`production grounder returned unsupported status: ${String(payload.status)}`);
  }
  if (!payload.point || !payload.bbox) {
    throw new Error('resolved production grounder result requires point and bbox');
  }
  return {
    status: 'resolved',
    reason: typeof payload.reason === 'string' && payload.reason ? payload.reason : 'visual-resolved',
    point: payload.point,
    bbox: payload.bbox,
    diagnostics: payload.diagnostics
  };
}

export class RuntimeBackedVisualGrounder {
  #runProcess;
  #pythonExecutable;

  constructor({ runProcess = collectProcess, pythonExecutable } = {}) {
    if (typeof runProcess !== 'function') {
      throw new Error('runProcess must be a function');
    }
    this.#runProcess = runProcess;
    this.#pythonExecutable = pythonExecutable ?? defaultPythonExecutable();
    if (typeof this.#pythonExecutable !== 'string' || !this.#pythonExecutable.trim()) {
      throw new Error('pythonExecutable must be a non-empty path');
    }
  }

  async #runtime(action) {
    const result = await this.#runProcess(
      'pwsh.exe',
      [
        '-NoLogo',
        '-NoProfile',
        '-ExecutionPolicy',
        'Bypass',
        '-File',
        CONTROLLER_PATH,
        '-Action',
        action
      ],
      { timeoutMs: action === 'Start' ? 150_000 : 30_000 }
    );
    if (result.code !== 0) {
      throw new Error(`vision-runtime-${action.toLowerCase()}-failed`);
    }
    return parseSingleJson(result.stdout, `vision runtime ${action}`);
  }

  async ground({ imageBytes, mimeType, width, height, coordinateSpace, instruction, kind, targetText = null }) {
    if (!Buffer.isBuffer(imageBytes) || imageBytes.length < 1 || imageBytes.length > MAX_INPUT_PNG_BYTES) {
      throw new Error('runtime-backed grounder requires bounded PNG bytes');
    }
    if (mimeType !== 'image/png' || coordinateSpace !== 'css_viewport') {
      throw new Error('runtime-backed grounder requires image/png in css_viewport coordinates');
    }
    if (!Number.isInteger(width) || !Number.isInteger(height) || width < 1 || height < 1) {
      throw new Error('runtime-backed grounder requires positive integer CSS dimensions');
    }
    if (typeof instruction !== 'string' || !instruction.trim()) {
      throw new Error('runtime-backed grounder requires instruction');
    }
    if (typeof kind !== 'string' || !kind.trim()) {
      throw new Error('runtime-backed grounder requires target kind');
    }
    if (targetText !== null && typeof targetText !== 'string') {
      throw new Error('targetText must be text or null');
    }

    const started = validateRuntimeStatus(await this.#runtime('Start'));
    const request = JSON.stringify({
      schema_version: 1,
      image_base64: imageBytes.toString('base64'),
      width,
      height,
      coordinate_space: 'css_viewport',
      instruction: instruction.trim(),
      kind: kind.trim(),
      target_text: targetText === null ? null : targetText.trim()
    });

    let touchError;
    try {
      if (!fs.existsSync(this.#pythonExecutable)) {
        throw new Error(`reviewed Stage 25 vision Python environment is missing: ${this.#pythonExecutable}`);
      }
      const result = await this.#runProcess(
        this.#pythonExecutable,
        [GROUNDER_CLI_PATH],
        { input: request, timeoutMs: 150_000 }
      );
      const payload = parseSingleJson(result.stdout, 'production visual grounder');
      if (result.code !== 0 && payload.status !== 'error') {
        throw new Error(`production visual grounder exited ${result.code} without error status`);
      }
      return normalizeGrounderPayload(payload);
    } finally {
      try {
        const touched = await this.#runtime('Touch');
        validateRuntimeStatus(touched);
      } catch (error) {
        touchError = error;
      }
      // A successful grounding result is not silently downgraded after it has
      // been computed, but Touch failure is fatal before this method resolves
      // because the finally block completes before the return is observed.
      if (touchError) throw touchError;
      if (started.port !== REVIEWED_PORT) {
        throw new Error('vision runtime port changed during grounding');
      }
    }
  }
}

export function productionRunnerPathsForTest() {
  return {
    repoRoot: REPO_ROOT,
    controllerPath: CONTROLLER_PATH,
    grounderCliPath: GROUNDER_CLI_PATH,
    reviewedProfile: REVIEWED_PROFILE,
    reviewedPort: REVIEWED_PORT
  };
}
