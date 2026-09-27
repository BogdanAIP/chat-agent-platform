import { randomUUID } from 'node:crypto';
import { spawn } from 'node:child_process';

import {
  BROWSERSKILL_IDENTITY,
  BROWSERSKILL_MODEL_TOOL_ACTIONS,
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


function addOption(command, flag, value) {
  if (value === undefined || value === null) return;
  command.push(flag, String(value));
}

function addBoolean(command, flag, value) {
  if (value === true) command.push(flag);
}

function addTarget(command, target) {
  if (typeof target !== 'string' || !target) {
    throw new TypeError('BrowserSkill target must be a non-empty string');
  }
  command.push(target);
}

function addTab(command, tabId) {
  if (tabId !== undefined && tabId !== null) command.push('--tab-id', String(tabId));
}

function addTimeout(command, timeoutMs) {
  if (timeoutMs !== undefined && timeoutMs !== null) {
    if (!Number.isInteger(timeoutMs) || timeoutMs <= 0) {
      throw new TypeError('BrowserSkill timeoutMs must be a positive integer');
    }
    command.push('--timeout', `${timeoutMs}ms`);
  }
}

export const BROWSERSKILL_GROUPED_ACTION_KEYS = Object.freeze(
  Object.entries(BROWSERSKILL_MODEL_TOOL_ACTIONS)
    .flatMap(([tool, actions]) => actions.map(action => `${tool}:${action}`))
    .sort(),
);

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
  let lastSubject = null;

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
    lastSubject = `browserskill:${session.browserInstanceId}:${session.sessionId}:${snapshot.tab_id}`;
    return {
      session,
      tabId: snapshot.tab_id,
      raw: snapshot,
      observation,
      subject: lastSubject,
    };
  }


  async function callGrouped(tool, action, args = {}) {
    const key = `${tool}:${action}`;
    if (!BROWSERSKILL_GROUPED_ACTION_KEYS.includes(key)) {
      throw new BrowserSkillProviderError(`unknown BrowserSkill grouped capability: ${key}`);
    }

    if (tool === 'browser_session') {
      if (action === 'start') {
        const session = await ensureSession();
        return { session_id: session.sessionId, browser_instance_id: session.browserInstanceId };
      }
      if (action === 'stop') return await close();
      if (action === 'list') return await run(['session', 'list']);
    }

    const session = await ensureSession();
    const sid = session.sessionId;

    if (tool === 'browser_page') {
      if (action === 'navigate') {
        if (typeof args.url !== 'string' || !args.url) throw new TypeError('navigate requires url');
        const command = ['navigate', '--session', sid, args.url];
        addTab(command, args.tabId);
        addOption(command, '--wait-until', args.waitUntil);
        addTimeout(command, args.timeoutMs);
        return await run(command);
      }
      if (action === 'back' || action === 'forward') {
        const command = [`navigate-${action}`, '--session', sid];
        addTab(command, args.tabId);
        addOption(command, '--wait-until', args.waitUntil);
        addTimeout(command, args.timeoutMs);
        return await run(command);
      }
      if (action === 'reload') {
        const command = ['reload', '--session', sid];
        addTab(command, args.tabId);
        addOption(command, '--wait-until', args.waitUntil);
        addTimeout(command, args.timeoutMs);
        addBoolean(command, '--hard', args.hard);
        return await run(command);
      }
      if (action === 'wait') {
        const command = ['wait-for-navigation', '--session', sid];
        addTab(command, args.tabId);
        addOption(command, '--wait-until', args.waitUntil);
        addTimeout(command, args.timeoutMs);
        return await run(command);
      }
    }

    if (tool === 'browser_inspect') {
      if (action === 'observe') {
        const command = ['observe', '--session', sid];
        addTab(command, args.tabId);
        addOption(command, '--cursor', args.cursor);
        addOption(command, '--max-depth', args.maxDepth);
        addOption(command, '--max-tokens', args.maxTokens);
        addBoolean(command, '--probe-hover', args.probeHover);
        addBoolean(command, '--debug-surfaces', args.debugSurfaces);
        return await run(command);
      }
      if (action === 'snapshot') {
        const command = ['snapshot', '--session', sid];
        addTab(command, args.tabId);
        addOption(command, '--max-depth', args.maxDepth);
        addOption(command, '--max-tokens', args.maxTokens);
        return await run(command);
      }
      if (action === 'html') {
        const command = ['get-html', '--session', sid];
        addTab(command, args.tabId);
        addOption(command, '--ref', args.ref);
        addOption(command, '--max-bytes', args.maxBytes);
        if (args.out !== undefined) addOption(command, '--out', args.out);
        return await run(command);
      }
      if (action === 'screenshot') {
        const command = ['screenshot', '--session', sid];
        addTab(command, args.tabId);
        addOption(command, '--ref', args.ref);
        addBoolean(command, '--full-page', args.fullPage);
        addOption(command, '--scope', args.scope);
        addTimeout(command, args.timeoutMs);
        if (args.out !== undefined) addOption(command, '--out', args.out);
        return await run(command, { timeoutMs: args.timeoutMs ?? 135_000 });
      }
      if (action === 'console' || action === 'network') {
        const command = [action, '--session', sid];
        addTab(command, args.tabId);
        addOption(command, '--since', args.since);
        addOption(command, '--limit', args.limit);
        addOption(command, '--max-text-chars', args.maxTextChars);
        if (action === 'console') addBoolean(command, '--include-stack', args.includeStack);
        return await run(command);
      }
      if (action === 'debug') {
        if (typeof args.debugAction !== 'string' || !args.debugAction) {
          throw new TypeError('browser_inspect debug requires debugAction');
        }
        const command = ['debug', args.debugAction, '--session', sid];
        addTab(command, args.tabId);
        for (const [flag, value] of [
          ['--run-id', args.runId],
          ['--name', args.name],
          ['--since', args.since],
          ['--limit', args.limit],
          ['--part', args.part],
          ['--offset', args.offset],
          ['--max-chars', args.maxChars],
          ['--pointer', args.pointer],
          ['--rule', args.rule],
          ['--rule-file', args.ruleFile],
          ['--replay', args.replay],
          ['--replay-file', args.replayFile],
          ['--budget', args.budget],
          ['--slow-ms', args.slowMs],
          ['--window-ms', args.windowMs],
          ['--url', args.url],
          ['--method', args.method],
          ['--resource-type', args.resourceType],
          ['--status', args.status],
          ['--state', args.state],
          ['--kind', args.kind],
          ['--wait-ms', args.waitMs],
          ['--command-id', args.commandId],
          ['--output', args.output],
        ]) addOption(command, flag, value);
        if (Array.isArray(args.fields) && args.fields.length) {
          command.push('--fields', args.fields.join(','));
        }
        addBoolean(command, '--include-controlled', args.includeControlled);
        return await run(command);
      }
    }

    if (tool === 'browser_interact') {
      if (action === 'click') {
        const command = ['click'];
        if (args.capture !== undefined) {
          addOption(command, '--capture', args.capture);
          addOption(command, '--image-x', args.imageX);
          addOption(command, '--image-y', args.imageY);
        } else {
          addTarget(command, args.target);
        }
        command.push('--session', sid);
        addTab(command, args.tabId);
        addOption(command, '--button', args.button);
        addOption(command, '--click-count', args.clickCount);
        if (Array.isArray(args.modifiers) && args.modifiers.length) {
          command.push('--modifiers', args.modifiers.join(','));
        }
        addTimeout(command, args.timeoutMs);
        return await run(command);
      }
      if (action === 'hover' || action === 'scroll-to' || action === 'focus' || action === 'blur') {
        const command = [action];
        addTarget(command, args.target);
        command.push('--session', sid);
        addTab(command, args.tabId);
        if (action === 'hover') {
          if (Array.isArray(args.modifiers) && args.modifiers.length) {
            command.push('--modifiers', args.modifiers.join(','));
          }
          if (args.settleMs !== undefined) command.push('--settle', `${args.settleMs}ms`);
        }
        addTimeout(command, args.timeoutMs);
        return await run(command);
      }
      if (action === 'wheel') {
        const command = ['wheel', '--session', sid];
        addTab(command, args.tabId);
        addOption(command, '--delta-x', args.deltaX ?? 0);
        addOption(command, '--delta-y', args.deltaY ?? 0);
        if (Array.isArray(args.modifiers) && args.modifiers.length) {
          command.push('--modifiers', args.modifiers.join(','));
        }
        addTimeout(command, args.timeoutMs);
        if (args.target !== undefined) addTarget(command, args.target);
        return await run(command);
      }
      if (action === 'fill') {
        const command = ['fill'];
        addTarget(command, args.target);
        if (typeof args.value !== 'string') throw new TypeError('fill requires value');
        command.push('--value', args.value, '--session', sid);
        addTab(command, args.tabId);
        addBoolean(command, '--no-clear', args.noClear);
        addTimeout(command, args.timeoutMs);
        return await run(command);
      }
      if (action === 'press') {
        if (typeof args.key !== 'string' || !args.key) throw new TypeError('press requires key');
        const command = ['press', args.key, '--session', sid];
        addTab(command, args.tabId);
        if (args.target !== undefined) {
          if (/^@?e\d+$/.test(args.target)) addOption(command, '--ref', args.target);
          else addOption(command, '--selector', args.target);
        }
        if (Array.isArray(args.modifiers) && args.modifiers.length) {
          command.push('--modifiers', args.modifiers.join(','));
        }
        addOption(command, '--hold-ms', args.holdMs);
        addTimeout(command, args.timeoutMs);
        return await run(command);
      }
      if (action === 'select') {
        const command = ['select'];
        addTarget(command, args.target);
        if (!Array.isArray(args.values) || args.values.length === 0) {
          throw new TypeError('select requires non-empty values');
        }
        for (const value of args.values) command.push('--value', String(value));
        command.push('--session', sid);
        addTab(command, args.tabId);
        addTimeout(command, args.timeoutMs);
        return await run(command);
      }
    }

    if (tool === 'browser_tabs') {
      if (action === 'list') {
        const command = ['tab', 'list', '--session', sid];
        addOption(command, '--scope', args.scope);
        return await run(command);
      }
      if (action === 'create') {
        const command = ['tab', 'create', '--session', sid];
        addOption(command, '--url', args.url);
        if (args.active === false) command.push('--no-active');
        addOption(command, '--index', args.index);
        return await run(command);
      }
      if (['select', 'close', 'borrow', 'return'].includes(action)) {
        if (!Number.isInteger(args.tabId)) throw new TypeError(`${action} requires tabId`);
        const command = ['tab', action, String(args.tabId), '--session', sid];
        // BrowserSkill's DSH provider intentionally does not bypass the user's
        // borrow confirmation with --no-confirm.
        if (action === 'borrow') addTimeout(command, args.timeoutMs);
        return await run(command, { timeoutMs: args.timeoutMs ?? DEFAULT_TIMEOUT_MS });
      }
    }

    if (tool === 'browser_assist') {
      if (action === 'resize') {
        if (!Number.isInteger(args.width) || !Number.isInteger(args.height)) {
          throw new TypeError('resize requires integer width/height');
        }
        return await run([
          'window', 'resize', '--session', sid,
          '--width', String(args.width), '--height', String(args.height),
        ]);
      }
      if (action === 'emulate') {
        const command = ['emulate', '--session', sid];
        addTab(command, args.tabId);
        addOption(command, '--device', args.device);
        addOption(command, '--width', args.width);
        addOption(command, '--height', args.height);
        addOption(command, '--dpr', args.dpr);
        addBoolean(command, '--mobile', args.mobile);
        addBoolean(command, '--no-mobile', args.noMobile);
        addOption(command, '--ua', args.ua);
        addOption(command, '--accept-language', args.acceptLanguage);
        addBoolean(command, '--touch', args.touch);
        addBoolean(command, '--no-touch', args.noTouch);
        addOption(command, '--max-touch-points', args.maxTouchPoints);
        addBoolean(command, '--off', args.off);
        return await run(command);
      }
      if (action === 'request-help') {
        if (typeof args.prompt !== 'string' || !args.prompt) {
          throw new TypeError('request-help requires prompt');
        }
        const command = ['request-help', '--session', sid, '--prompt', args.prompt];
        addTab(command, args.tabId);
        addOption(command, '--title', args.title);
        if (Array.isArray(args.targets)) {
          for (const target of args.targets) command.push('--target', String(target));
        }
        addTimeout(command, args.timeoutMs);
        addOption(command, '--completion-criteria', args.completionCriteria);
        return await run(command, { timeoutMs: args.timeoutMs ?? 315_000 });
      }
    }

    throw new BrowserSkillProviderError(`BrowserSkill grouped capability is classified but unmapped: ${key}`);
  }

  async function call(toolName, args = {}) {
    const session = await ensureSession();

    if (toolName === 'browser_navigate') {
      if (typeof args.url !== 'string' || !args.url) throw new TypeError('browser_navigate requires url');
      const reply = await callGrouped('browser_page', 'navigate', { url: args.url });
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
      const reply = await callGrouped('browser_interact', 'click', {
        target: args.target,
        clickCount: args.doubleClick === true ? 2 : undefined,
      });
      return textResult(JSON.stringify(reply), { provider: 'browserskill', delivery: reply });
    }

    if (toolName === 'browser_type') {
      if (typeof args.target !== 'string' || !args.target) throw new TypeError('browser_type requires target');
      if (typeof args.text !== 'string') throw new TypeError('browser_type requires text');
      if (args.slowly === true) {
        throw new BrowserSkillProviderError('BrowserSkill fill has no truthful slowly=true equivalent');
      }
      const completed = [];
      const fill = await callGrouped('browser_interact', 'fill', {
        target: args.target,
        value: args.text,
      });
      completed.push('fill');
      if (args.submit === true) {
        try {
          const press = await callGrouped('browser_interact', 'press', {
            key: 'Enter',
            target: args.target,
          });
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
    callGrouped,
    call,
    close,
    browserSubject() { return lastSubject; },
    get ownedSession() { return owned; },
  });
}
