import { spawn } from 'node:child_process';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';


const MAX_PLAYWRIGHT_SNAPSHOT_CHARS = 1_100_000;
const MAX_VERIFIER_RESPONSE_BYTES = 128_000;
const VERIFIER_TIMEOUT_MS = 7_500;
const SAFE_CHILD_ENV_ALLOWLIST = new Set([
  'PATH', 'Path', 'PATHEXT',
  'SystemRoot', 'SYSTEMROOT', 'WINDIR', 'COMSPEC',
  'TEMP', 'TMP', 'TMPDIR',
  'LOCALAPPDATA', 'HOME', 'USERPROFILE',
  'PROGRAMFILES', 'ProgramFiles', 'PROGRAMFILES(X86)',
  'LANG', 'LC_ALL', 'PYTHONUTF8', 'PYTHONIOENCODING'
]);

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, '..', '..', '..');
const verifierCli = path.join(repoRoot, 'runtime', 'control_plane', 'browser_transition_cli.py');

function safeChildEnvironment() {
  const env = {};
  for (const name of SAFE_CHILD_ENV_ALLOWLIST) {
    const value = process.env[name];
    if (typeof value === 'string') env[name] = value;
  }
  return env;
}

function textOf(result) {
  return (result?.content ?? [])
    .filter(block => block?.type === 'text' && typeof block.text === 'string')
    .map(block => block.text)
    .join('\n');
}

function decodeQuoted(value) {
  return value.replaceAll('\\"', '"').replaceAll('\\\\', '\\');
}

function controlValueFromLine(line, role) {
  if (!['textbox', 'searchbox', 'combobox', 'spinbutton'].includes(role)) return null;
  const refEnd = line.indexOf(']');
  if (refEnd < 0) return null;
  const suffix = line.slice(refEnd + 1).replace(/^\s*(?:\[[^\]]+\]\s*)*/, '').trim();
  if (!suffix.startsWith(':')) return null;
  const value = suffix.slice(1).trim();
  return value.length <= 4096 ? value : null;
}

export function parsePlaywrightSnapshotResult(result) {
  if (result?.isError) throw new Error('playwright snapshot returned an error');
  const rawText = textOf(result);
  if (!rawText) throw new Error('playwright snapshot returned no text');
  if (rawText.length > MAX_PLAYWRIGHT_SNAPSHOT_CHARS) {
    throw new Error('playwright snapshot exceeds the bounded observation limit');
  }

  const urlMatch = rawText.match(/^\s*- Page URL:\s*(.*?)\s*$/m);
  const titleMatch = rawText.match(/^\s*- Page Title:\s*(.*?)\s*$/m);
  const marker = rawText.match(/^\s*- Page Snapshot:\s*$/m);
  if (!urlMatch || !titleMatch || !marker || marker.index === undefined) {
    throw new Error('playwright snapshot is missing Page URL, Page Title or Page Snapshot');
  }

  let snapshotText = rawText.slice(marker.index + marker[0].length).trim();
  if (snapshotText.startsWith('```yaml')) snapshotText = snapshotText.slice('```yaml'.length).trimStart();
  else if (snapshotText.startsWith('```')) snapshotText = snapshotText.slice(3).trimStart();
  if (snapshotText.endsWith('```')) snapshotText = snapshotText.slice(0, -3).trimEnd();

  const controls = [];
  for (const line of snapshotText.split(/\r?\n/)) {
    const ref = line.match(/\[ref=([^\]\s]+)\]/);
    if (!ref) continue;
    const structural = line.match(/^\s*-\s+([A-Za-z][A-Za-z0-9_-]*)(?:\s+"((?:\\.|[^"\\])*)")?/);
    if (!structural) continue;
    const role = structural[1];
    const name = structural[2] === undefined ? null : decodeQuoted(structural[2]);
    controls.push({
      control_id: ref[1],
      role,
      name,
      enabled: !/\[disabled\]/.test(line),
      checked: /\[checked\]/.test(line) ? true : (/\[unchecked\]/.test(line) ? false : null),
      selected: /\[selected\]/.test(line) ? true : null,
      visible: true,
      value: controlValueFromLine(line, role),
    });
  }

  return {
    url: urlMatch[1],
    title: titleMatch[1],
    document_id: null,
    snapshot_text: snapshotText,
    controls,
    settled: true,
    complete: true,
    ambiguous: false,
  };
}

function runVerifier(request) {
  return new Promise(resolve => {
    const child = spawn('python', [verifierCli], {
      cwd: repoRoot,
      env: safeChildEnvironment(),
      stdio: ['pipe', 'pipe', 'ignore'],
      windowsHide: true,
    });
    let stdout = Buffer.alloc(0);
    let settled = false;
    const finish = value => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve(value);
    };
    const timer = setTimeout(() => {
      try { child.kill(); } catch {}
      finish({ status: 'error', reason: 'browser_verifier_timeout' });
    }, VERIFIER_TIMEOUT_MS);

    child.stdout.on('data', chunk => {
      stdout = Buffer.concat([stdout, Buffer.from(chunk)]);
      if (stdout.length > MAX_VERIFIER_RESPONSE_BYTES) {
        try { child.kill(); } catch {}
        finish({ status: 'error', reason: 'browser_verifier_response_too_large' });
      }
    });
    child.on('error', error => finish({ status: 'error', reason: `browser_verifier_spawn_${error.name}` }));
    child.on('close', () => {
      if (settled) return;
      try {
        const parsed = JSON.parse(stdout.toString('utf8'));
        finish(parsed && typeof parsed === 'object' ? parsed : { status: 'error', reason: 'browser_verifier_invalid_response' });
      } catch {
        finish({ status: 'error', reason: 'browser_verifier_invalid_json' });
      }
    });
    child.stdin.end(JSON.stringify(request));
  });
}

export async function verifyPlaywrightNavigation({ before, after, expectedUrl }) {
  const result = await runVerifier({
    operation: 'verify_navigation',
    subject: 'isolated-playwright-primary-page',
    before,
    after,
    expected_url: expectedUrl,
  });
  if (!['pass', 'fail', 'unknown'].includes(result?.status)) {
    throw new Error(result?.reason || 'browser verifier unavailable');
  }
  return result;
}
