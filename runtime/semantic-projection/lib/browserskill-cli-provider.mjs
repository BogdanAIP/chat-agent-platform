import { randomUUID } from 'node:crypto';
import { spawn } from 'node:child_process';

import {
  BROWSERSKILL_IDENTITY,
  assertBrowserSkillRuntimeIdentity,
} from './browserskill-capability-manifest.mjs';

const MAX_OUTPUT_BYTES = 4_000_000;
const DEFAULT_TIMEOUT_MS = 45_000;
const CANCEL_GRACE_MS = process.platform === 'win32' ? 15_000 : 3_000;

export class BrowserSkillProviderError extends Error {
  constructor(message, { code = null, hint = null, timedOut = false, completedSteps = [] } = {}) {
    super(message);
    this.name = 'BrowserSkillProviderError';
    this.code = code;
    this.hint = hint;
    this.timedOut = timedOut;
    this.completedSteps = Object.freeze([...completedSteps]);
  }
}

function jsonError(stdout, stderr, label, code) {
  const body = stdout.trim();
  try {
    const parsed = JSON.parse(body);
    const message = parsed?.message ?? stderr.trim() ?? `bsk ${label} failed`;
    const hint = typeof parsed?.hint === 'string' ? parsed.hint : null;
    return new BrowserSkillProviderError(
      `bsk ${label} failed: ${message}${hint ? ` (hint: ${hint})` : ''}`,
      { code: parsed?.code ?? code, hint },
    );
  } catch {
    return new BrowserSkillProviderError(
      `bsk ${label} failed: ${stderr.trim() || body || `exit ${code}`}`,
      { code },
    );
  }
}

export function createBskJsonRunner({ bskPath = 'bsk', spawnImpl = spawn } = {}) {
  return async function run(args, { timeoutMs = DEFAULT_TIMEOUT_MS } = {}) {
    if (!Array.isArray(args) || args.some(value => typeof value !== 'string')) {
      throw new TypeError('BrowserSkill CLI args must be an array of strings');
    }

    return await new Promise((resolve, reject) => {
      let child;
      try {
        child = spawnImpl(bskPath, [...args, '--json'], {
          windowsHide: true,
          env: {
            ...process.env,
            BSK_CANCEL_ON_STDIN_CLOSE: '1',
          },
          stdio: ['pipe', 'pipe', 'pipe'],
        });
      } catch (error) {
        reject(error);
        return;
      }

      let stdout = '';
      let stderr = '';
      let settled = false;
      let forced = null;

      const cleanup = () => {
        clearTimeout(timer);
        if (forced !== null) clearTimeout(forced);
      };
      const finish = (fn, value) => {
        if (settled) return;
        settled = true;
        cleanup();
        fn(value);
      };
      const requestStop = () => {
        try {
          if (process.platform === 'win32') child.stdin?.end();
          else child.kill('SIGINT');
        } catch {}
        forced = setTimeout(() => {
          try { child.kill('SIGKILL'); } catch {}
        }, CANCEL_GRACE_MS);
        forced.unref?.();
      };
      const append = (kind, chunk) => {
        const value = Buffer.isBuffer(chunk) ? chunk.toString('utf8') : String(chunk);
        if (kind === 'stdout') stdout += value;
        else stderr += value;
        if (Buffer.byteLength(stdout) + Buffer.byteLength(stderr) > MAX_OUTPUT_BYTES) {
          requestStop();
          finish(reject, new BrowserSkillProviderError('BrowserSkill CLI output exceeded bounded limit'));
        }
      };

      child.stdout?.on('data', chunk => append('stdout', chunk));
      child.stderr?.on('data', chunk => append('stderr', chunk));
      child.on('error', error => finish(reject, error));
      child.on('close', code => {
        if (settled) return;
        if (code !== 0) {
          finish(reject, jsonError(stdout, stderr, args.join(' '), code));
          return;
        }
        try {
          finish(resolve, JSON.parse(stdout.trim()));
        } catch {
          finish(
            reject,
            new BrowserSkillProviderError(
              `bsk ${args.join(' ')} did not produce JSON: ${stdout.trim().slice(0, 200) || '(empty)'}`,
            ),
          );
        }
      });

      const timer = setTimeout(() => {
        requestStop();
        finish(
          reject,
          new BrowserSkillProviderError(`bsk ${args.join(' ')} timed out`, { timedOut: true }),
        );
      }, timeoutMs);
      timer.unref?.();
    });
  };
}

function exactBrowser(browsers, selector) {
  if (!Array.isArray(browsers)) throw new Error('BrowserSkill browsers result must be an array');
  const matches = browsers.filter(
    browser => browser?.instance_id === selector || browser?.label === selector,
  );
  if (matches.length !== 1) {
    throw new BrowserSkillProviderError(
      matches.length === 0
        ? `BrowserSkill browser selector did not match: ${selector}`
        : `BrowserSkill browser selector is ambiguous: ${selector}`,
    );
  }
  const selected = matches[0];
  assertBrowserSkillRuntimeIdentity({
    version: selected.extension_version,
    protocolVersion: selected.extension_protocol_version,
  });
  return selected;
}

function textResult(text, structuredContent = undefined) {
  const result = { content: [{ type: 'text', text }] };
  if (structuredContent !== undefined) result.structuredContent = structuredContent;
  return result;
}

function decodeQuoted(raw) {
  if (raw === undefined) return null;
  try { return JSON.parse(`"${raw}"`); } catch { return raw; }
}

function parseControlValue(line, role) {
  const quoted = line.match(/\bvalue="((?:\\.|[^"\\])*)"/);
  if (quoted) return decodeQuoted(quoted[1]);
  if (role === 'textbox' && /\[empty\]/.test(line)) return '';
  return null;
}

export function parseBrowserSkillControls(snapshotText) {
  const controls = [];
  for (const line of String(snapshotText).split(/\r?\n/)) {
    const match = line.match(/^\s*(?:[-*]\s+)?(@e\d+)\s+([A-Za-z][A-Za-z0-9_-]*)(?:\s+"((?:\\.|[^"\\])*)")?/);
    if (!match) continue;
    const [, controlId, role, rawName] = match;
    let checked = null;
    if (/\[checked\]/.test(line)) checked = true;
    else if (/\[unchecked\]/.test(line)) checked = false;
    let selected = null;
    if (/\[selected\]/.test(line)) selected = true;
    else if (/\[not selected\]/.test(line)) selected = false;
    controls.push({
      control_id: controlId,
      role,
      name: decodeQuoted(rawName),
      enabled: !/\[disabled\]/.test(line),
      checked,
      selected,
      visible: true,
      value: parseControlValue(line, role),
    });
  }
  return controls;
}

function resultSessionId(status) {
  const session = status?.session;
  const id = session?.session_id ?? session?.id;
  return typeof id === 'string' && id ? id : null;
}

function resultBrowserId(status) {
  const session = status?.session;
  const id = session?.browser_instance_id ?? session?.browser_id;
  return typeof id === 'string' && id ? id : null;
}

export function createBrowserSkillCliProvider({
  browserSelector,
  bskPath = 'bsk',
  run = createBskJsonRunner({ bskPath }),
  sessionName = 'CAP BrowserSkill',
  noFocus = true,
} = {}) {
  if (typeof browserSelector !== 'string' || !browserSelector.trim()) {
    throw new TypeError('BrowserSkill provider requires an exact browser instance id or unique label');
  }

  const providerGeneration = randomUUID();
  let browser = null;
  let owned = null;
  let activationPromise = null;
  let sessionPromise = null;

  async function activate() {
    if (browser !== null) return browser;
    if (activationPromise !== null) return await activationPromise;
    activationPromise = (async () => {
      const status = await run(['status']);
      assertBrowserSkillRuntimeIdentity({
        version: status?.daemon_version,
        protocolVersion: status?.protocol_version,
      });
      if (Array.isArray(status?.version_skew_browsers) && status.version_skew_browsers.length > 0) {
        throw new BrowserSkillProviderError('BrowserSkill reports browser/daemon version skew');
      }
      browser = exactBrowser(await run(['browsers']), browserSelector);
      return browser;
    })();
    try {
      return await activationPromise;
    } finally {
      activationPromise = null;
    }
  }

  async function requestStatus(requestId) {
    return await run(['session', 'request', requestId], { timeoutMs: 40_000 });
  }

  async function cleanupRequest(requestId) {
    try {
      return await run(['session', 'request', requestId, '--cancel'], { timeoutMs: 40_000 });
    } catch {
      return null;
    }
  }

  async function ensureSession() {
    if (owned !== null) return owned;
    if (sessionPromise !== null) return await sessionPromise;

    sessionPromise = (async () => {
      const selected = await activate();
      const requestId = `${Date.now() + 5 * 60_000}:${randomUUID()}`;
      const prepared = await run(['session', 'request', requestId, '--prepare'], { timeoutMs: 30_000 });
      if (prepared?.state !== 'prepared') {
        throw new BrowserSkillProviderError('BrowserSkill session start did not enter prepared state');
      }

      let startReply = null;
      try {
        const args = [
          'session', 'start',
          '--request-id', requestId,
          '--browser', selected.instance_id,
          '--name', sessionName,
        ];
        if (noFocus) args.push('--no-focus');
        startReply = await run(args, { timeoutMs: 45_000 });
      } catch (error) {
        // A start transport failure is not proof of no session. Reconcile the
        // exact request before deciding whether cleanup is required.
        const reconciled = await requestStatus(requestId).catch(() => null);
        const recoveredSessionId = resultSessionId(reconciled);
        const recoveredBrowserId = resultBrowserId(reconciled);
        if (
          recoveredSessionId &&
          recoveredBrowserId === selected.instance_id &&
          ['ready', 'active'].includes(reconciled?.state)
        ) {
          startReply = {
            session_id: recoveredSessionId,
            browser_instance_id: recoveredBrowserId,
            recovered_after_ack_loss: true,
          };
        } else {
          await cleanupRequest(requestId);
          throw error;
        }
      }

      if (
        typeof startReply?.session_id !== 'string' ||
        startReply?.browser_instance_id !== selected.instance_id
      ) {
        await cleanupRequest(requestId);
        throw new BrowserSkillProviderError('BrowserSkill session start returned mismatched identity');
      }

      const claimed = await run(['session', 'request', requestId, '--claim'], { timeoutMs: 30_000 });
      if (claimed?.state !== 'active') {
        await cleanupRequest(requestId);
        throw new BrowserSkillProviderError('BrowserSkill session start could not be claimed');
      }

      owned = Object.freeze({
        requestId,
        sessionId: startReply.session_id,
        browserInstanceId: selected.instance_id,
        providerGeneration,
      });
      return owned;
    })();

    try {
      return await sessionPromise;
    } finally {
      sessionPromise = null;
    }
  }

  async function tabs(scope = 'all') {
    const session = await ensureSession();
    const reply = await run(['tab', 'list', '--session', session.sessionId, '--scope', scope]);
    return Array.isArray(reply?.tabs) ? reply.tabs : [];
  }

  async function snapshotObservation({ tabId = null } = {}) {
    const session = await ensureSession();
    const args = ['snapshot', '--session', session.sessionId];
    if (tabId !== null && tabId !== undefined) args.push('--tab-id', String(tabId));
    const snapshot = await run(args);
    const listed = await tabs('all');
    const tab = listed.find(item => item?.tab_id === snapshot?.tab_id);
    if (!tab || typeof tab.url !== 'string') {
      throw new BrowserSkillProviderError('BrowserSkill snapshot could not bind exact tab URL');
    }
    const observation = {
      url: tab.url,
      title: typeof tab.title === 'string' ? tab.title : '',
      document_id: `browserskill:${session.browserInstanceId}:${session.sessionId}:${snapshot.tab_id}`,
      snapshot_text: typeof snapshot?.text === 'string' ? snapshot.text : '',
      controls: parseBrowserSkillControls(snapshot?.text ?? ''),
      settled: true,
      complete: snapshot?.truncated !== true,
      ambiguous: false,
    };
    return {
      session,
      tabId: snapshot.tab_id,
      raw: snapshot,
      observation,
      subject: `browserskill:${session.browserInstanceId}:${session.sessionId}:${snapshot.tab_id}`,
    };
  }

  async function call(toolName, args = {}) {
    const session = await ensureSession();

    if (toolName === 'browser_navigate') {
      if (typeof args.url !== 'string' || !args.url) throw new TypeError('browser_navigate requires url');
      const reply = await run(['navigate', '--session', session.sessionId, args.url]);
      return textResult(JSON.stringify(reply), { provider: 'browserskill', delivery: reply });
    }

    if (toolName === 'browser_snapshot') {
      const captured = await snapshotObservation();
      return textResult(captured.raw.text, {
        provider: 'browserskill',
        provider_subject: captured.subject,
        normalized_browser_observation: captured.observation,
        raw_snapshot: captured.raw,
      });
    }

    if (toolName === 'browser_find') {
      const captured = await snapshotObservation();
      let matcher;
      if (typeof args.text === 'string') {
        matcher = line => line.includes(args.text);
      } else if (typeof args.regex === 'string') {
        const regex = new RegExp(args.regex);
        matcher = line => regex.test(line);
      } else {
        throw new TypeError('browser_find requires text or regex');
      }
      const lines = captured.raw.text.split(/\r?\n/).filter(matcher);
      return textResult(lines.join('\n') || '(no matches)', {
        provider: 'browserskill',
        provider_subject: captured.subject,
        match_count: lines.length,
      });
    }

    if (toolName === 'browser_click') {
      if (typeof args.target !== 'string' || !args.target) throw new TypeError('browser_click requires target');
      const command = ['click', args.target, '--session', session.sessionId];
      if (args.doubleClick === true) command.push('--click-count', '2');
      const reply = await run(command);
      return textResult(JSON.stringify(reply), { provider: 'browserskill', delivery: reply });
    }

    if (toolName === 'browser_type') {
      if (typeof args.target !== 'string' || !args.target) throw new TypeError('browser_type requires target');
      if (typeof args.text !== 'string') throw new TypeError('browser_type requires text');
      if (args.slowly === true) {
        throw new BrowserSkillProviderError('BrowserSkill fill has no truthful slowly=true equivalent');
      }
      const completed = [];
      const fill = await run([
        'fill', args.target,
        '--value', args.text,
        '--session', session.sessionId,
      ]);
      completed.push('fill');
      if (args.submit === true) {
        try {
          const press = await run([
            'press', 'Enter',
            '--ref', args.target,
            '--session', session.sessionId,
          ]);
          completed.push('press');
          return textResult(JSON.stringify({ fill, press }), {
            provider: 'browserskill',
            completed_steps: completed,
          });
        } catch (error) {
          throw new BrowserSkillProviderError(
            `BrowserSkill type+submit partially completed after fill: ${error instanceof Error ? error.message : String(error)}`,
            { completedSteps: completed },
          );
        }
      }
      return textResult(JSON.stringify(fill), {
        provider: 'browserskill',
        completed_steps: completed,
      });
    }

    throw new BrowserSkillProviderError(`unsupported CAP Browser downstream operation for BrowserSkill: ${toolName}`);
  }

  async function close() {
    const current = owned;
    owned = null;
    if (current === null) return { stopped: false };
    const result = await cleanupRequest(current.requestId);
    return {
      stopped: result?.state === 'closed',
      requestId: current.requestId,
      sessionId: current.sessionId,
      result,
    };
  }

  return Object.freeze({
    id: 'browserskill',
    providerGeneration,
    activate,
    ensureSession,
    snapshotObservation,
    call,
    close,
    get ownedSession() { return owned; },
  });
}
