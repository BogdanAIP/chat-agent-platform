import { createHash, randomUUID } from 'node:crypto';
import { spawn } from 'node:child_process';
import { mkdir, open, readFile, rm } from 'node:fs/promises';
import path from 'node:path';

import {
  BROWSERSKILL_IDENTITY,
  BROWSERSKILL_MODEL_TOOL_ACTIONS,
  assertBrowserSkillRuntimeIdentity,
} from './browserskill-capability-manifest.mjs';
import { semanticProviderEnvironment } from './semantic-activation.mjs';

const MAX_OUTPUT_BYTES = 4_000_000;
const DEFAULT_TIMEOUT_MS = 45_000;
const CANCEL_GRACE_MS = process.platform === 'win32' ? 15_000 : 3_000;

const BROWSERSKILL_ENV_KEYS = Object.freeze([
  'BSK_HOME',
  'BSK_BROWSER_WAIT_MS',
  'BSK_DOCTOR_BROWSER_WAIT_MS',
]);

const BROWSERSKILL_LEASE_SCHEMA_VERSION = 1;

function browserSkillLeaseKey(browserSelector) {
  return createHash('sha256').update(browserSelector, 'utf8').digest('hex').slice(0, 32);
}

export function createBrowserSkillLeaseStore({ stateRoot, browserSelector }) {
  if (typeof stateRoot !== 'string' || !stateRoot) {
    throw new TypeError('BrowserSkill lease store requires stateRoot');
  }
  if (typeof browserSelector !== 'string' || !browserSelector) {
    throw new TypeError('BrowserSkill lease store requires browserSelector');
  }

  const root = path.join(stateRoot, browserSkillLeaseKey(browserSelector));
  const leasePath = path.join(root, 'lease.json');
  const cleanupPath = path.join(root, 'cleanup.requested');

  async function syncWriteExclusive(filePath, text) {
    await mkdir(root, { recursive: true });
    const handle = await open(filePath, 'wx');
    try {
      await handle.writeFile(text, 'utf8');
      await handle.sync();
    } finally {
      await handle.close();
    }
  }

  return Object.freeze({
    async load() {
      let raw;
      try {
        raw = await readFile(leasePath, 'utf8');
      } catch (error) {
        if (error?.code === 'ENOENT') {
          await rm(cleanupPath, { force: true }).catch(() => {});
          return null;
        }
        throw error;
      }
      let lease;
      try {
        lease = JSON.parse(raw);
      } catch {
        throw new BrowserSkillProviderError(
          'BrowserSkill durable lease is corrupt; refusing a new session',
        );
      }
      if (
        lease?.schema_version !== BROWSERSKILL_LEASE_SCHEMA_VERSION ||
        lease?.source_commit !== BROWSERSKILL_IDENTITY.sourceCommit ||
        lease?.browser_selector !== browserSelector ||
        typeof lease?.request_id !== 'string' ||
        !lease.request_id ||
        typeof lease?.browser_instance_id !== 'string' ||
        !lease.browser_instance_id
      ) {
        throw new BrowserSkillProviderError(
          'BrowserSkill durable lease identity mismatch; refusing a new session',
        );
      }
      let cleanupRequested = false;
      try {
        await readFile(cleanupPath, 'utf8');
        cleanupRequested = true;
      } catch (error) {
        if (error?.code !== 'ENOENT') throw error;
      }
      return {
        requestId: lease.request_id,
        browserInstanceId: lease.browser_instance_id,
        sessionId: null,
        cleanupRequested,
      };
    },

    async create({ requestId, browserInstanceId }) {
      const payload = JSON.stringify({
        schema_version: BROWSERSKILL_LEASE_SCHEMA_VERSION,
        source_commit: BROWSERSKILL_IDENTITY.sourceCommit,
        browser_selector: browserSelector,
        request_id: requestId,
        browser_instance_id: browserInstanceId,
      });
      try {
        await syncWriteExclusive(leasePath, payload);
      } catch (error) {
        if (error?.code === 'EEXIST') {
          throw new BrowserSkillProviderError(
            'BrowserSkill durable lease already exists; reconcile it before a new start',
          );
        }
        throw error;
      }
    },

    async markCleanup() {
      await mkdir(root, { recursive: true });
      const handle = await open(cleanupPath, 'a');
      try {
        await handle.writeFile('cleanup-requested\n', 'utf8');
        await handle.sync();
      } finally {
        await handle.close();
      }
    },

    async clear() {
      await rm(cleanupPath, { force: true });
      await rm(leasePath, { force: true });
    },

    paths: Object.freeze({ root, leasePath, cleanupPath }),
  });
}

export function browserSkillChildEnvironment(env = process.env) {
  const result = semanticProviderEnvironment(env);
  for (const name of BROWSERSKILL_ENV_KEYS) {
    const value = env[name];
    if (typeof value === 'string') result[name] = value;
  }
  // Provider execution must not perform autonomous update checks or inherit
  // arbitrary CAP/tunnel credentials. Cancellation is the only forced BSK
  // control variable.
  result.BSK_AUTO_UPDATE = 'off';
  result.BSK_CANCEL_ON_STDIN_CLOSE = '1';
  return result;
}

export class BrowserSkillProviderError extends Error {
  constructor(
    message,
    {
      code = null,
      hint = null,
      timedOut = false,
      completedSteps = [],
      deliveryAttempted = null,
    } = {},
  ) {
    super(message);
    this.name = 'BrowserSkillProviderError';
    this.code = code;
    this.hint = hint;
    this.timedOut = timedOut;
    this.completedSteps = Object.freeze([...completedSteps]);
    this.deliveryAttempted = deliveryAttempted;
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

export function createBskJsonRunner({
  bskPath = 'bsk',
  spawnImpl = spawn,
  cancelGraceMs = CANCEL_GRACE_MS,
  settlementSlackMs = 1_000,
} = {}) {
  if (!Number.isInteger(cancelGraceMs) || cancelGraceMs < 0) {
    throw new TypeError('BrowserSkill cancelGraceMs must be a non-negative integer');
  }
  if (!Number.isInteger(settlementSlackMs) || settlementSlackMs < 0) {
    throw new TypeError('BrowserSkill settlementSlackMs must be a non-negative integer');
  }
  return async function run(args, { timeoutMs = DEFAULT_TIMEOUT_MS } = {}) {
    if (!Array.isArray(args) || args.some(value => typeof value !== 'string')) {
      throw new TypeError('BrowserSkill CLI args must be an array of strings');
    }

    return await new Promise((resolve, reject) => {
      let child;
      try {
        child = spawnImpl(bskPath, [...args, '--json'], {
          windowsHide: true,
          env: browserSkillChildEnvironment(process.env),
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
      let settlementDeadline = null;
      let terminalError = null;

      const cleanup = () => {
        clearTimeout(timer);
        if (forced !== null) clearTimeout(forced);
        if (settlementDeadline !== null) clearTimeout(settlementDeadline);
      };
      const finish = (fn, value) => {
        if (settled) return;
        settled = true;
        cleanup();
        fn(value);
      };
      const requestStop = error => {
        if (terminalError !== null) return;
        terminalError = error;
        try {
          if (process.platform === 'win32') child.stdin?.end();
          else child.kill('SIGINT');
        } catch {}
        forced = setTimeout(() => {
          try { child.kill('SIGKILL'); } catch {}
        }, cancelGraceMs);
        // Even a child that never emits close/error must release its caller.
        settlementDeadline = setTimeout(
          () => finish(reject, terminalError),
          cancelGraceMs + settlementSlackMs,
        );
      };
      const append = (kind, chunk) => {
        if (settled) return;
        const value = Buffer.isBuffer(chunk) ? chunk.toString('utf8') : String(chunk);
        if (kind === 'stdout') stdout += value;
        else stderr += value;
        if (
          terminalError === null &&
          Buffer.byteLength(stdout) + Buffer.byteLength(stderr) > MAX_OUTPUT_BYTES
        ) {
          requestStop(
            new BrowserSkillProviderError('BrowserSkill CLI output exceeded bounded limit'),
          );
        }
      };

      child.stdout?.on('data', chunk => append('stdout', chunk));
      child.stderr?.on('data', chunk => append('stderr', chunk));
      child.on('error', error => finish(reject, terminalError ?? error));
      child.on('close', code => {
        if (settled) return;
        if (terminalError !== null) {
          finish(reject, terminalError);
          return;
        }
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
        requestStop(
          new BrowserSkillProviderError(`bsk ${args.join(' ')} timed out`, { timedOut: true }),
        );
      }, timeoutMs);
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


function semanticControlFingerprint(control) {
  return JSON.stringify([control.role, control.name ?? null]);
}

function stableControlRef(fingerprint) {
  return '@cap-' + createHash('sha256').update(fingerprint, 'utf8').digest('hex').slice(0, 16);
}

export function projectBrowserSkillRefs(snapshotText, generation, context = '') {
  const nativeControls = parseBrowserSkillControls(snapshotText);
  const counts = new Map();
  for (const control of nativeControls) {
    const fingerprint = semanticControlFingerprint(control);
    counts.set(fingerprint, (counts.get(fingerprint) ?? 0) + 1);
  }

  const nativeToPublic = new Map();
  const publicToNative = new Map();
  const controls = nativeControls.map((control, index) => {
    const fingerprint = semanticControlFingerprint(control);
    const publicRef = counts.get(fingerprint) === 1
      ? stableControlRef(JSON.stringify([context, fingerprint]))
      : `@capg-${generation}-${index + 1}`;
    nativeToPublic.set(control.control_id, publicRef);
    publicToNative.set(publicRef, control.control_id);
    return { ...control, control_id: publicRef };
  });

  const text = String(snapshotText)
    .split(/\r?\n/)
    .map(line => line.replace(
      /^(\s*(?:[-*]\s+)?)(@e\d+)\b/,
      (full, prefix, nativeRef) => prefix + (nativeToPublic.get(nativeRef) ?? nativeRef),
    ))
    .join('\n');

  return { text, controls, publicToNative };
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
  stateRoot = null,
  leaseStore = stateRoot === null
    ? null
    : createBrowserSkillLeaseStore({ stateRoot, browserSelector }),
} = {}) {
  if (typeof browserSelector !== 'string' || !browserSelector.trim()) {
    throw new TypeError('BrowserSkill provider requires an exact browser instance id or unique label');
  }

  const providerGeneration = randomUUID();
  let browser = null;
  let owned = null;
  let activationPromise = null;
  let sessionPromise = null;
  let pendingStart = null;
  let cleanupPending = false;
  let leaseLoaded = false;
  let lastSubject = null;
  let refGeneration = 0;
  let currentPublicRefToNative = new Map();

  function invalidatePublicRefs() {
    currentPublicRefToNative = new Map();
  }

  async function ensureLeaseLoaded() {
    if (leaseLoaded) return;
    leaseLoaded = true;
    if (leaseStore === null) return;
    const recovered = await leaseStore.load();
    if (recovered !== null) {
      pendingStart = recovered;
      cleanupPending = recovered.cleanupRequested === true;
    }
  }

  async function persistNewLease(record) {
    if (leaseStore !== null) await leaseStore.create(record);
  }

  async function markDurableCleanup() {
    if (leaseStore !== null) await leaseStore.markCleanup();
  }

  async function clearDurableLease() {
    if (leaseStore !== null) await leaseStore.clear();
  }

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

  function exactRecoveredSession(status, expectedBrowserId, expectedSessionId = null) {
    const sessionId = resultSessionId(status);
    const browserId = resultBrowserId(status);
    if (!sessionId || browserId !== expectedBrowserId) return null;
    if (expectedSessionId !== null && sessionId !== expectedSessionId) return null;
    return { sessionId, browserId };
  }

  function adoptOwned({ requestId, sessionId, browserInstanceId }) {
    owned = Object.freeze({
      requestId,
      sessionId,
      browserInstanceId,
      providerGeneration,
    });
    pendingStart = null;
    cleanupPending = false;
    return owned;
  }

  async function claimOrReconcile(requestId, expectedBrowserId, expectedSessionId) {
    let claimed;
    try {
      claimed = await run(['session', 'request', requestId, '--claim'], { timeoutMs: 30_000 });
    } catch (error) {
      const reconciled = await requestStatus(requestId).catch(() => null);
      const recovered = exactRecoveredSession(
        reconciled,
        expectedBrowserId,
        expectedSessionId,
      );
      if (reconciled?.state === 'active' && recovered !== null) {
        return reconciled;
      }
      const cleaned = await cleanupRequest(requestId);
      if (cleaned?.state === 'closed') {
          pendingStart = null;
          await clearDurableLease();
        }
      throw new BrowserSkillProviderError(
        `BrowserSkill claim acknowledgement was lost and could not be reconciled: ${
          error instanceof Error ? error.message : String(error)
        }`,
        { deliveryAttempted: true },
      );
    }
    const recovered = exactRecoveredSession(claimed, expectedBrowserId, expectedSessionId);
    if (claimed?.state !== 'active' || recovered === null) {
      const cleaned = await cleanupRequest(requestId);
      if (cleaned?.state === 'closed') {
          pendingStart = null;
          await clearDurableLease();
        }
      throw new BrowserSkillProviderError(
        'BrowserSkill session start could not be claimed with exact identity',
      );
    }
    return claimed;
  }

  async function reconcilePendingStart() {
    if (pendingStart === null) return null;
    const current = pendingStart;
    if (current.cleanupRequested === true || (cleanupPending && owned === null)) {
      const cleaned = await cleanupRequest(current.requestId);
      if (cleaned?.state === 'closed') {
        pendingStart = null;
        cleanupPending = false;
        await clearDurableLease();
        return null;
      }
      throw new BrowserSkillProviderError(
        'BrowserSkill durable cleanup intent remains unresolved; refusing a new session',
      );
    }
    const status = await requestStatus(current.requestId).catch(() => null);
    if (status === null) {
      throw new BrowserSkillProviderError(
        'BrowserSkill has an unresolved session-start request; refusing a second start',
      );
    }

    const recovered = exactRecoveredSession(
      status,
      current.browserInstanceId,
      current.sessionId,
    );
    if (status.state === 'active' && recovered !== null) {
      return adoptOwned({
        requestId: current.requestId,
        sessionId: recovered.sessionId,
        browserInstanceId: recovered.browserId,
      });
    }
    if (status.state === 'ready' && recovered !== null) {
      await claimOrReconcile(
        current.requestId,
        current.browserInstanceId,
        recovered.sessionId,
      );
      return adoptOwned({
        requestId: current.requestId,
        sessionId: recovered.sessionId,
        browserInstanceId: recovered.browserId,
      });
    }
    if (status.state === 'closed') {
      pendingStart = null;
      await clearDurableLease();
      return null;
    }

    const cleaned = await cleanupRequest(current.requestId);
    if (cleaned?.state === 'closed') {
      pendingStart = null;
      await clearDurableLease();
      return null;
    }
    throw new BrowserSkillProviderError(
      'BrowserSkill session-start outcome remains unresolved; refusing a second start',
    );
  }

  async function reconcileOwnedCleanup() {
    if (!cleanupPending || owned === null) return;
    const current = owned;
    const cleaned = await cleanupRequest(current.requestId);
    if (cleaned?.state !== 'closed') {
      throw new BrowserSkillProviderError(
        'BrowserSkill owned-session cleanup remains unresolved; refusing further browser work',
      );
    }
    owned = null;
    cleanupPending = false;
    lastSubject = null;
    invalidatePublicRefs();
    await clearDurableLease();
  }

  async function ensureSession() {
    await ensureLeaseLoaded();
    if (cleanupPending && owned !== null) await reconcileOwnedCleanup();
    if (owned !== null) return owned;
    if (sessionPromise !== null) return await sessionPromise;

    sessionPromise = (async () => {
      // A persisted close intent is allowed to finish through the exact
      // BrowserSkill request id before browser reactivation. Any session that
      // CAP may resume, however, must first pass the pinned runtime/profile
      // provenance checks.
      if (
        pendingStart !== null &&
        (pendingStart.cleanupRequested === true || cleanupPending)
      ) {
        const cleanupResult = await reconcilePendingStart();
        if (cleanupResult !== null) return cleanupResult;
      }

      const selected = await activate();
      if (
        pendingStart !== null &&
        pendingStart.browserInstanceId !== selected.instance_id
      ) {
        throw new BrowserSkillProviderError(
          'BrowserSkill durable lease browser identity no longer matches the activated browser',
        );
      }
      const recovered = await reconcilePendingStart();
      if (recovered !== null) return recovered;

      const requestId = `${Date.now() + 5 * 60_000}:${randomUUID()}`;
      pendingStart = {
        requestId,
        browserInstanceId: selected.instance_id,
        sessionId: null,
        cleanupRequested: false,
      };
      await persistNewLease({
        requestId,
        browserInstanceId: selected.instance_id,
      });
      let prepared;
      try {
        prepared = await run(['session', 'request', requestId, '--prepare'], { timeoutMs: 30_000 });
      } catch (error) {
        throw error;
      }
      if (prepared?.state !== 'prepared') {
        const cleaned = await cleanupRequest(requestId);
        if (cleaned?.state === 'closed') {
          pendingStart = null;
          await clearDurableLease();
        }
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
          const cleaned = await cleanupRequest(requestId);
          if (cleaned?.state === 'closed') {
          pendingStart = null;
          await clearDurableLease();
        }
          throw error;
        }
      }

      if (
        typeof startReply?.session_id !== 'string' ||
        startReply?.browser_instance_id !== selected.instance_id
      ) {
        const cleaned = await cleanupRequest(requestId);
        if (cleaned?.state === 'closed') {
          pendingStart = null;
          await clearDurableLease();
        }
        throw new BrowserSkillProviderError('BrowserSkill session start returned mismatched identity');
      }

      pendingStart = {
        requestId,
        browserInstanceId: selected.instance_id,
        sessionId: startReply.session_id,
      };
      await claimOrReconcile(requestId, selected.instance_id, startReply.session_id);

      return adoptOwned({
        requestId,
        sessionId: startReply.session_id,
        browserInstanceId: selected.instance_id,
      });
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
    const beforeTabs = await tabs('all');
    const args = ['snapshot', '--session', session.sessionId];
    if (tabId !== null && tabId !== undefined) args.push('--tab-id', String(tabId));
    const snapshot = await run(args);
    const afterTabs = await tabs('all');
    const beforeTab = beforeTabs.find(item => item?.tab_id === snapshot?.tab_id);
    const afterTab = afterTabs.find(item => item?.tab_id === snapshot?.tab_id);
    if (
      !beforeTab ||
      !afterTab ||
      typeof beforeTab.url !== 'string' ||
      typeof afterTab.url !== 'string'
    ) {
      throw new BrowserSkillProviderError(
        'BrowserSkill snapshot could not bind exact before/after tab identity',
      );
    }
    const titleBefore = typeof beforeTab.title === 'string' ? beforeTab.title : '';
    const titleAfter = typeof afterTab.title === 'string' ? afterTab.title : '';
    const tabStable = (
      beforeTab.url === afterTab.url &&
      titleBefore === titleAfter &&
      beforeTab.window_id === afterTab.window_id &&
      beforeTab.scope === afterTab.scope
    );

    refGeneration += 1;
    const projected = projectBrowserSkillRefs(
      snapshot?.text ?? '',
      refGeneration,
      JSON.stringify([
        providerGeneration,
        session.sessionId,
        snapshot.tab_id,
        afterTab.url,
      ]),
    );
    currentPublicRefToNative = projected.publicToNative;
    const observation = {
      url: afterTab.url,
      title: titleAfter,
      document_id:
        `browserskill:${providerGeneration}:${session.browserInstanceId}:${session.sessionId}:${snapshot.tab_id}`,
      snapshot_text: projected.text,
      controls: projected.controls,
      settled: tabStable,
      complete: snapshot?.truncated !== true && tabStable,
      ambiguous: !tabStable,
    };
    lastSubject =
      `browserskill:${providerGeneration}:${session.browserInstanceId}:${session.sessionId}:${snapshot.tab_id}`;
    return {
      session,
      tabId: snapshot.tab_id,
      raw: snapshot,
      publicText: projected.text,
      observation,
      subject: lastSubject,
    };
  }


  async function callGrouped(tool, action, args = {}) {
    const key = `${tool}:${action}`;
    if (!BROWSERSKILL_GROUPED_ACTION_KEYS.includes(key)) {
      throw new BrowserSkillProviderError(`unknown BrowserSkill grouped capability: ${key}`);
    }

    const refPreserving = new Set([
      'browser_session:list',
      'browser_page:wait',
      'browser_inspect:html',
      'browser_inspect:screenshot',
      'browser_inspect:console',
      'browser_inspect:network',
      'browser_tabs:list',
    ]);
    if (!refPreserving.has(key)) invalidatePublicRefs();

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


  async function callExtended(capability, args = {}) {
    if (!['upload', 'download', 'evaluate', 'record-start', 'record-stop'].includes(capability)) {
      throw new BrowserSkillProviderError(`unknown BrowserSkill extended capability: ${capability}`);
    }

    if (capability === 'record-start') {
      const selected = await activate();
      const command = ['record', 'start', '--browser', selected.instance_id];
      addOption(command, '--tab-id', args.tabId);
      addOption(command, '--url', args.url);
      addOption(command, '--purpose', args.purpose);
      addOption(command, '--max-page-tokens', args.maxPageTokens);
      addBoolean(command, '--redact-values', args.redactValues);
      addOption(command, '--output', args.output);
      return await run(command, { timeoutMs: args.timeoutMs ?? 315_000 });
    }
    if (capability === 'record-stop') {
      const command = ['record', 'stop'];
      addOption(command, '--output', args.output);
      return await run(command);
    }

    const session = await ensureSession();
    const sid = session.sessionId;

    if (capability === 'upload') {
      if (!Array.isArray(args.files) || args.files.length === 0) {
        throw new TypeError('BrowserSkill upload requires non-empty files');
      }
      const command = ['upload'];
      if (args.target !== undefined) addTarget(command, args.target);
      addOption(command, '--ref', args.ref);
      addOption(command, '--selector', args.selector);
      for (const file of args.files) command.push('--file', String(file));
      addOption(command, '--mode', args.mode);
      command.push('--session', sid);
      addTab(command, args.tabId);
      addTimeout(command, args.timeoutMs);
      return await run(command, { timeoutMs: args.timeoutMs ?? 135_000 });
    }

    if (capability === 'download') {
      if (typeof args.out !== 'string' || !args.out) {
        throw new TypeError('BrowserSkill download requires out');
      }
      const command = ['download'];
      if (args.target !== undefined) addTarget(command, args.target);
      addOption(command, '--ref', args.ref);
      addOption(command, '--selector', args.selector);
      command.push('--out', args.out, '--session', sid);
      addTab(command, args.tabId);
      addTimeout(command, args.timeoutMs);
      addBoolean(command, '--overwrite', args.overwrite);
      return await run(command, { timeoutMs: args.timeoutMs ?? 135_000 });
    }

    if (capability === 'evaluate') {
      if (typeof args.expression !== 'string' || !args.expression) {
        throw new TypeError('BrowserSkill evaluate requires expression');
      }
      const command = ['evaluate', args.expression, '--session', sid];
      addTab(command, args.tabId);
      if (args.awaitPromise !== undefined) {
        command.push('--await-promise', String(Boolean(args.awaitPromise)));
      }
      if (args.returnByValue !== undefined) {
        command.push('--return-by-value', String(Boolean(args.returnByValue)));
      }
      addTimeout(command, args.timeoutMs);
      return await run(command);
    }

    throw new BrowserSkillProviderError(`BrowserSkill extended capability is unmapped: ${capability}`);
  }

  function resolvePublicTarget(target) {
    if (typeof target !== 'string' || !target) {
      throw new TypeError('BrowserSkill public target must be a non-empty string');
    }
    if (target.startsWith('@cap')) {
      const native = currentPublicRefToNative.get(target);
      if (native === undefined) {
        throw new BrowserSkillProviderError(
          'BrowserSkill CAP ref is stale or ambiguous after fresh observation',
          { deliveryAttempted: false },
        );
      }
      return native;
    }
    if (/^@?e\d+$/.test(target)) {
      throw new BrowserSkillProviderError(
        'raw BrowserSkill refs are provider-private; use the CAP ref from web_observe',
        { deliveryAttempted: false },
      );
    }
    return target;
  }

  async function call(toolName, args = {}) {
    if (toolName === 'browser_navigate') {
      if (typeof args.url !== 'string' || !args.url) throw new TypeError('browser_navigate requires url');
      const reply = await callGrouped('browser_page', 'navigate', { url: args.url });
      return textResult(JSON.stringify(reply), { provider: 'browserskill', delivery: reply });
    }

    if (toolName === 'browser_snapshot') {
      const captured = await snapshotObservation();
      return textResult(captured.publicText, {
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
      const lines = captured.publicText.split(/\r?\n/).filter(matcher);
      return textResult(lines.join('\n') || '(no matches)', {
        provider: 'browserskill',
        provider_subject: captured.subject,
        match_count: lines.length,
      });
    }

    if (toolName === 'browser_click') {
      if (typeof args.target !== 'string' || !args.target) throw new TypeError('browser_click requires target');
      const reply = await callGrouped('browser_interact', 'click', {
        target: resolvePublicTarget(args.target),
        clickCount: args.doubleClick === true ? 2 : undefined,
      });
      return textResult(JSON.stringify(reply), { provider: 'browserskill', delivery: reply });
    }

    if (toolName === 'browser_type') {
      if (typeof args.target !== 'string' || !args.target) throw new TypeError('browser_type requires target');
      if (typeof args.text !== 'string') throw new TypeError('browser_type requires text');
      if (args.slowly === true) {
        throw new BrowserSkillProviderError(
          'BrowserSkill fill has no truthful slowly=true equivalent',
          { deliveryAttempted: false },
        );
      }
      const completed = [];
      const nativeTarget = resolvePublicTarget(args.target);
      const fill = await callGrouped('browser_interact', 'fill', {
        target: nativeTarget,
        value: args.text,
      });
      completed.push('fill');
      if (args.submit === true) {
        try {
          const press = await callGrouped('browser_interact', 'press', {
            key: 'Enter',
            target: nativeTarget,
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
    if (owned === null) {
      if (pendingStart !== null) {
        const current = pendingStart;
        cleanupPending = true;
        current.cleanupRequested = true;
        await markDurableCleanup();
        const result = await cleanupRequest(current.requestId);
        if (result?.state === 'closed') {
          pendingStart = null;
          cleanupPending = false;
          await clearDurableLease();
        }
        return {
          stopped: result?.state === 'closed',
          requestId: current.requestId,
          sessionId: current.sessionId,
          result,
        };
      }
      return { stopped: false };
    }

    const current = owned;
    cleanupPending = true;
    await markDurableCleanup();
    const result = await cleanupRequest(current.requestId);
    if (result?.state === 'closed') {
      owned = null;
      cleanupPending = false;
      lastSubject = null;
      invalidatePublicRefs();
      await clearDurableLease();
    }
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
    callExtended,
    call,
    close,
    browserSubject() { return lastSubject; },
    get ownedSession() { return owned; },
  });
}
