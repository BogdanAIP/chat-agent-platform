import { spawn } from 'node:child_process';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';


const MAX_PLAYWRIGHT_SNAPSHOT_CHARS = 1_000_000;
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
const VALUE_STATE_ROLES = new Set([
  'textbox', 'searchbox', 'combobox', 'spinbutton',
]);
const CHECKED_STATE_ROLES = new Set([
  'checkbox', 'menuitemcheckbox', 'menuitemradio', 'radio', 'switch',
]);
const SELECTED_STATE_ROLES = new Set([
  'gridcell', 'option', 'row', 'tab', 'treeitem',
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
  if (!VALUE_STATE_ROLES.has(role)) return null;
  const refEnd = line.indexOf(']');
  if (refEnd < 0) return null;
  const suffix = line.slice(refEnd + 1).replace(/^\s*(?:\[[^\]]+\]\s*)*/, '').trim();
  // @playwright/mcp omits the `: value` suffix for an observable empty
  // value-state control. For roles whose accessibility state has a value,
  // absence of that suffix therefore means the observed value is "", not
  // "unknown". This distinction is required by the pre-action delta guard.
  if (!suffix.startsWith(':')) return '';
  const value = suffix.slice(1).trim();
  return value.length <= 4096 ? value : null;
}

function checkedStateFromLine(line, role) {
  if (/\[checked\]/.test(line)) return true;
  if (/\[unchecked\]/.test(line)) return false;
  if (/\[checked=(?:mixed|undefined)\]/.test(line)) return null;
  return CHECKED_STATE_ROLES.has(role) ? false : null;
}

function selectedStateFromLine(line, role) {
  if (/\[selected\]/.test(line)) return true;
  if (/\[unselected\]/.test(line)) return false;
  return SELECTED_STATE_ROLES.has(role) ? false : null;
}

function stripSnapshotFence(value) {
  let snapshotText = value.trim();
  if (snapshotText.startsWith('```yaml')) snapshotText = snapshotText.slice('```yaml'.length).trimStart();
  else if (snapshotText.startsWith('```')) snapshotText = snapshotText.slice(3).trimStart();
  if (snapshotText.endsWith('```')) snapshotText = snapshotText.slice(0, -3).trimEnd();
  return snapshotText;
}

function snapshotSection(rawText) {
  const section = rawText.match(/^[ \t]*### Snapshot[ \t]*$/m);
  if (!section || section.index === undefined) return null;
  const start = section.index + section[0].length;
  let body = rawText.slice(start).replace(/^\r?\n/, '');
  const nextSection = body.search(/^[ \t]*### [^\r\n]+[ \t]*$/m);
  if (nextSection >= 0) body = body.slice(0, nextSection);
  return body.trim();
}

export function parsePlaywrightSnapshotResult(result) {
  if (result?.isError) throw new Error('playwright snapshot returned an error');
  const rawText = textOf(result);
  if (!rawText) throw new Error('playwright snapshot returned no text');
  if (rawText.length > MAX_PLAYWRIGHT_SNAPSHOT_CHARS) {
    throw new Error('playwright snapshot exceeds the bounded observation limit');
  }

  // Playwright emits Page Title only when it is non-empty. about:blank therefore
  // has a Page URL but no Page Title line; normalize the missing title to "".
  // Keep metadata parsing line-local so section boundaries are never consumed.
  const urlMatch = rawText.match(/^[ \t]*- Page URL:[ \t]*(.*?)[ \t]*$/m);
  const titleMatch = rawText.match(/^[ \t]*- Page Title:[ \t]*(.*?)[ \t]*$/m);
  if (!urlMatch) {
    throw new Error('playwright snapshot is missing Page URL');
  }

  // @playwright/mcp 0.0.78 renders explicit browser_snapshot state as
  // "### Page" followed by a separate "### Snapshot" section. Keep the older
  // inline Page Snapshot form as a bounded compatibility fallback.
  let snapshotPayload = snapshotSection(rawText);
  if (snapshotPayload === null) {
    const marker = rawText.match(/^[ \t]*- Page Snapshot:[ \t]*$/m);
    if (!marker || marker.index === undefined) {
      throw new Error('playwright snapshot is missing Snapshot content');
    }
    snapshotPayload = rawText.slice(marker.index + marker[0].length).trim();
  }
  const snapshotText = stripSnapshotFence(snapshotPayload);

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
      checked: checkedStateFromLine(line, role),
      selected: selectedStateFromLine(line, role),
      visible: true,
      value: controlValueFromLine(line, role),
    });
  }

  return {
    url: urlMatch[1],
    title: titleMatch?.[1] ?? '',
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

function requireVerifierResult(result) {
  if (!['pass', 'fail', 'unknown'].includes(result?.status)) {
    throw new Error(result?.reason || 'browser verifier unavailable');
  }
  return result;
}

export async function verifyPlaywrightNavigation({ before, after, expectedUrl }) {
  return requireVerifierResult(await runVerifier({
    operation: 'verify_navigation',
    subject: 'isolated-playwright-primary-page',
    before,
    after,
    expected_url: expectedUrl,
  }));
}

export async function verifyPlaywrightInteraction({ before, after, expected }) {
  return requireVerifierResult(await runVerifier({
    operation: 'verify_interaction',
    subject: 'isolated-playwright-primary-page',
    before,
    after,
    expected,
  }));
}
