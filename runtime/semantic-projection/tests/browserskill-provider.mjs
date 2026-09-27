import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { mkdtemp, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { PassThrough } from 'node:stream';

import {
  BrowserSkillProviderError,
  BROWSERSKILL_GROUPED_ACTION_KEYS,
  browserSkillChildEnvironment,
  createBskJsonRunner,
  createBrowserSkillCliProvider,
  createBrowserSkillLeaseStore,
  parseBrowserSkillControls,
  projectBrowserSkillRefs,
} from '../lib/browserskill-cli-provider.mjs';

function key(args) {
  return args.join(' ');
}

const childEnv = browserSkillChildEnvironment({
  PATH: 'C:\\bin',
  SystemRoot: 'C:\\Windows',
  USERPROFILE: 'C:\\Users\\tester',
  USERNAME: 'tester',
  BSK_HOME: 'C:\\Users\\tester\\.bsk',
  BSK_BROWSER_WAIT_MS: '2500',
  CONTROL_PLANE_API_KEY: 'must-not-leak',
  OPENAI_API_KEY: 'must-not-leak',
});
assert.equal(childEnv.USERNAME, 'tester');
assert.equal(childEnv.BSK_HOME, 'C:\\Users\\tester\\.bsk');
assert.equal(childEnv.BSK_BROWSER_WAIT_MS, '2500');
assert.equal(childEnv.BSK_AUTO_UPDATE, 'off');
assert.equal(childEnv.BSK_CANCEL_ON_STDIN_CLOSE, '1');
assert.equal('CONTROL_PLANE_API_KEY' in childEnv, false);
assert.equal('OPENAI_API_KEY' in childEnv, false);

let gracefulStops = 0;
let forcedKills = 0;
function hungSpawn() {
  const child = new EventEmitter();
  child.stdout = new PassThrough();
  child.stderr = new PassThrough();
  child.stdin = new PassThrough();
  const originalEnd = child.stdin.end.bind(child.stdin);
  child.stdin.end = (...args) => {
    gracefulStops += 1;
    return originalEnd(...args);
  };
  child.kill = signal => {
    if (signal === 'SIGINT') gracefulStops += 1;
    if (signal === 'SIGKILL') forcedKills += 1;
    return true;
  };
  return child;
}
const hungRunner = createBskJsonRunner({
  spawnImpl: hungSpawn,
  cancelGraceMs: 5,
  settlementSlackMs: 5,
});
await assert.rejects(
  hungRunner(['status'], { timeoutMs: 5 }),
  error => error instanceof BrowserSkillProviderError && error.timedOut === true,
);
assert.ok(gracefulStops >= 1, 'timeout must request graceful BrowserSkill cancellation');
assert.equal(forcedKills, 1, 'hung BrowserSkill CLI must be force-killed after bounded grace');

const calls = [];
let startCalls = 0;
const run = async args => {
  calls.push([...args]);
  const command = key(args);

  if (command === 'status') {
    return {
      daemon_version: '0.3.1',
      protocol_version: '1.3',
      version_skew_browsers: [],
    };
  }
  if (command === 'browsers') {
    return [{
      instance_id: 'browser-a',
      label: 'profile-a',
      extension_version: '0.3.1',
      extension_protocol_version: '1.3',
    }];
  }
  if (command.includes('session request') && command.endsWith('--prepare')) {
    return { state: 'prepared' };
  }
  if (command.startsWith('session start ')) {
    startCalls += 1;
    // Simulate the exact consequence-bearing ambiguity: Chrome/daemon created
    // the session, but the CLI acknowledgement did not reach CAP.
    throw new BrowserSkillProviderError('injected session start ACK loss', { timedOut: true });
  }
  if (command.includes('session request') && !command.includes('--')) {
    return {
      state: 'ready',
      session: {
        session_id: 's-owned',
        browser_instance_id: 'browser-a',
      },
    };
  }
  if (command.includes('session request') && command.endsWith('--claim')) {
    return {
      state: 'active',
      session: {
        session_id: 's-owned',
        browser_instance_id: 'browser-a',
      },
    };
  }
  if (command.includes('session request') && command.endsWith('--cancel')) {
    return { state: 'closed' };
  }
  if (command === 'snapshot --session s-owned') {
    return {
      text:
        '@e1 button "Save"\n' +
        '@e2 textbox "Name" [empty]\n' +
        '@e3 checkbox "Remember" [checked]\n',
      ref_count: 3,
      tab_id: 17,
      truncated: false,
    };
  }
  if (command === 'tab list --session s-owned --scope all') {
    return {
      tabs: [{
        tab_id: 17,
        title: 'Example',
        url: 'https://example.com/',
        active: true,
        scope: 'agent',
      }],
    };
  }
  if (command === 'navigate --session s-owned https://example.com/') {
    return { tab_id: 17, final_url: 'https://example.com/', reached: 'load' };
  }
  if (command === 'click @e1 --session s-owned') {
    return { tab_id: 17, used_ref: 'e1' };
  }
  if (command === 'fill @e2 --value HELLO --session s-owned') {
    return { tab_id: 17, used_ref: 'e2', value: 'HELLO' };
  }
  throw new Error(`unexpected fake bsk command: ${command}`);
};

const provider = createBrowserSkillCliProvider({
  browserSelector: 'profile-a',
  run,
});

const session = await provider.ensureSession();
assert.equal(session.sessionId, 's-owned');
assert.equal(session.browserInstanceId, 'browser-a');
assert.equal(startCalls, 1, 'ACK-loss reconciliation must never issue a second session start');

const snapshot = await provider.call('browser_snapshot', {});
assert.equal(snapshot.structuredContent?.provider, 'browserskill');
const subject = snapshot.structuredContent?.provider_subject;
assert.match(
  subject,
  /^browserskill:[0-9a-f-]{36}:browser-a:s-owned:17$/,
);
assert.equal(subject, provider.browserSubject());

const normalized = snapshot.structuredContent?.normalized_browser_observation;
assert.equal(normalized.url, 'https://example.com/');
assert.equal(normalized.title, 'Example');
assert.equal(normalized.controls.length, 3);
assert.equal(snapshot.content[0].text.includes('@e1'), false, 'native BrowserSkill refs must stay private');

const save = normalized.controls.find(item => item.name === 'Save');
const name = normalized.controls.find(item => item.name === 'Name');
const remember = normalized.controls.find(item => item.name === 'Remember');
assert.match(save.control_id, /^@cap-[0-9a-f]{16}$/);
assert.match(name.control_id, /^@cap-[0-9a-f]{16}$/);
assert.match(remember.control_id, /^@cap-[0-9a-f]{16}$/);
assert.deepEqual(save, {
  control_id: save.control_id,
  role: 'button',
  name: 'Save',
  enabled: true,
  checked: null,
  selected: null,
  visible: true,
  value: null,
});
assert.equal(name.value, '');
assert.equal(remember.checked, true);

// A fresh pre-action snapshot rebuilds BrowserSkill's native @eN store.
// The public stable CAP ref must resolve to the fresh native ref, not reuse
// the previous generation's BrowserSkill ref directly.
const refreshed = await provider.call('browser_snapshot', {});
const refreshedSave = refreshed.structuredContent.normalized_browser_observation.controls
  .find(item => item.name === 'Save');
assert.equal(refreshedSave.control_id, save.control_id);

await provider.call('browser_navigate', { url: 'https://example.com/' });
const afterNavigate = await provider.call('browser_snapshot', {});
const saveAfterNavigate = afterNavigate.structuredContent.normalized_browser_observation.controls
  .find(item => item.name === 'Save');
assert.equal(saveAfterNavigate.control_id, save.control_id);
await provider.call('browser_click', { target: saveAfterNavigate.control_id });

const afterClick = await provider.call('browser_snapshot', {});
const nameAfterClick = afterClick.structuredContent.normalized_browser_observation.controls
  .find(item => item.name === 'Name');
assert.equal(nameAfterClick.control_id, name.control_id);
await provider.call('browser_type', { target: nameAfterClick.control_id, text: 'HELLO' });

await assert.rejects(
  provider.call('browser_type', { target: nameAfterClick.control_id, text: 'HELLO', slowly: true }),
  /no truthful slowly=true equivalent/,
);

await assert.rejects(
  provider.call('browser_evaluate', { expression: 'document.cookie' }),
  /unsupported CAP Browser downstream operation/,
);

const closed = await provider.close();
assert.equal(closed.stopped, true);
assert.equal(closed.sessionId, 's-owned');

const parsed = parseBrowserSkillControls(
  '@e7 option "One" [selected]\n@e8 button "Disabled" [disabled]\n',
);
assert.equal(parsed[0].selected, true);
assert.equal(parsed[1].enabled, false);

const duplicateGenerationOne = projectBrowserSkillRefs(
  '@e1 button "Same"\n@e2 button "Same"\n',
  11,
);
const duplicateGenerationTwo = projectBrowserSkillRefs(
  '@e7 button "Same"\n@e8 button "Same"\n',
  12,
);
assert.match(duplicateGenerationOne.controls[0].control_id, /^@capg-11-/);
assert.match(duplicateGenerationOne.controls[1].control_id, /^@capg-11-/);
assert.notEqual(
  duplicateGenerationOne.controls[0].control_id,
  duplicateGenerationTwo.controls[0].control_id,
  'ambiguous same-role/name controls must not acquire a stable cross-observation ref',
);
assert.equal(duplicateGenerationOne.text.includes('@e1'), false);

const sameControlPageA = projectBrowserSkillRefs(
  '@e1 button "Save"\n',
  21,
  'session-1:tab-1:https://example.com/a',
);
const sameControlPageB = projectBrowserSkillRefs(
  '@e9 button "Save"\n',
  22,
  'session-1:tab-1:https://example.com/b',
);
assert.notEqual(
  sameControlPageA.controls[0].control_id,
  sameControlPageB.controls[0].control_id,
  'stable CAP refs must be scoped to page/session context',
);

// Durable request lease must survive a CAP/provider process restart without
// creating a second BrowserSkill session.
{
  const stateRoot = await mkdtemp(path.join(os.tmpdir(), 'cap-bsk-lease-'));
  let starts = 0;
  const durableRun = async args => {
    const command = key(args);
    if (command === 'status') {
      return { daemon_version: '0.3.1', protocol_version: '1.3', version_skew_browsers: [] };
    }
    if (command === 'browsers') {
      return [{
        instance_id: 'durable-browser',
        label: 'durable-profile',
        extension_version: '0.3.1',
        extension_protocol_version: '1.3',
      }];
    }
    if (command.endsWith('--prepare')) return { state: 'prepared' };
    if (command.startsWith('session start ')) {
      starts += 1;
      return { session_id: 'durable-session', browser_instance_id: 'durable-browser' };
    }
    if (command.endsWith('--claim')) {
      return {
        state: 'active',
        session: {
          session_id: 'durable-session',
          browser_instance_id: 'durable-browser',
        },
      };
    }
    if (
      command.includes('session request') &&
      !command.endsWith('--prepare') &&
      !command.endsWith('--claim') &&
      !command.endsWith('--cancel')
    ) {
      return {
        state: 'active',
        session: {
          session_id: 'durable-session',
          browser_instance_id: 'durable-browser',
        },
      };
    }
    if (command.endsWith('--cancel')) return { state: 'closed' };
    throw new Error(`unexpected durable command: ${command}`);
  };

  try {
    const firstProvider = createBrowserSkillCliProvider({
      browserSelector: 'durable-profile',
      run: durableRun,
      stateRoot,
    });
    const firstSession = await firstProvider.ensureSession();
    assert.equal(firstSession.sessionId, 'durable-session');
    assert.equal(starts, 1);

    // Deliberately do not close firstProvider: this models abrupt CAP death.
    const secondProvider = createBrowserSkillCliProvider({
      browserSelector: 'durable-profile',
      run: durableRun,
      stateRoot,
    });
    const recoveredSession = await secondProvider.ensureSession();
    assert.equal(recoveredSession.sessionId, 'durable-session');
    assert.equal(starts, 1, 'durable lease recovery must not issue a second session start');
    assert.equal((await secondProvider.close()).stopped, true);

    const store = createBrowserSkillLeaseStore({
      stateRoot,
      browserSelector: 'durable-profile',
    });
    assert.equal(await store.load(), null, 'confirmed close must remove durable BrowserSkill lease');
  } finally {
    await rm(stateRoot, { recursive: true, force: true });
  }
}

// A durable lease must not bypass the reviewed BrowserSkill runtime pin after
// CAP restarts.
{
  const stateRoot = await mkdtemp(path.join(os.tmpdir(), 'cap-bsk-version-drift-'));
  const store = createBrowserSkillLeaseStore({
    stateRoot,
    browserSelector: 'drifted-runtime-profile',
  });
  await store.create({
    requestId: `${Date.now() + 300_000}:00000000-0000-4000-8000-000000000001`,
    browserInstanceId: 'drifted-runtime-browser',
  });
  let starts = 0;
  const driftedRuntimeProvider = createBrowserSkillCliProvider({
    browserSelector: 'drifted-runtime-profile',
    stateRoot,
    run: async args => {
      const command = key(args);
      if (command === 'status') {
        return {
          daemon_version: '0.3.2',
          protocol_version: '1.3',
          version_skew_browsers: [],
        };
      }
      if (command.startsWith('session start ')) starts += 1;
      throw new Error(`unexpected drifted-runtime command: ${command}`);
    },
  });
  try {
    await assert.rejects(
      driftedRuntimeProvider.ensureSession(),
      /unsupported BrowserSkill version/,
    );
    assert.equal(starts, 0, 'runtime version drift must fail before session adoption/start');
  } finally {
    await store.clear();
    await rm(stateRoot, { recursive: true, force: true });
  }
}

let mismatchCancel = 0;
const mismatchedProvider = createBrowserSkillCliProvider({
  browserSelector: 'browser-a',
  run: async args => {
    const command = key(args);
    if (command === 'status') {
      return {
        daemon_version: '0.3.1',
        protocol_version: '1.3',
        version_skew_browsers: [],
      };
    }
    if (command === 'browsers') {
      return [{
        instance_id: 'browser-a',
        label: 'profile-a',
        extension_version: '0.3.1',
        extension_protocol_version: '1.3',
      }];
    }
    if (command.endsWith('--prepare')) return { state: 'prepared' };
    if (command.startsWith('session start ')) {
      return { session_id: 'foreign-session', browser_instance_id: 'browser-b' };
    }
    if (command.endsWith('--cancel')) {
      mismatchCancel += 1;
      return { state: 'closed' };
    }
    throw new Error(`unexpected mismatch command: ${command}`);
  },
});
await assert.rejects(
  mismatchedProvider.ensureSession(),
  /mismatched identity/,
);
assert.equal(mismatchCancel, 1, 'mismatched provider identity must trigger exact request cleanup');


// Claim acknowledgement loss must reconcile the same request and must not
// create a second Agent Window.
{
  let starts = 0;
  let claims = 0;
  const claimLossProvider = createBrowserSkillCliProvider({
    browserSelector: 'claim-profile',
    run: async args => {
      const command = key(args);
      if (command === 'status') {
        return { daemon_version: '0.3.1', protocol_version: '1.3', version_skew_browsers: [] };
      }
      if (command === 'browsers') {
        return [{
          instance_id: 'claim-browser',
          label: 'claim-profile',
          extension_version: '0.3.1',
          extension_protocol_version: '1.3',
        }];
      }
      if (command.endsWith('--prepare')) return { state: 'prepared' };
      if (command.startsWith('session start ')) {
        starts += 1;
        return { session_id: 'claim-session', browser_instance_id: 'claim-browser' };
      }
      if (command.endsWith('--claim')) {
        claims += 1;
        throw new BrowserSkillProviderError('injected claim ACK loss', { timedOut: true });
      }
      if (
        command.includes('session request') &&
        !command.endsWith('--prepare') &&
        !command.endsWith('--claim') &&
        !command.endsWith('--cancel')
      ) {
        return {
          state: 'active',
          session: {
            session_id: 'claim-session',
            browser_instance_id: 'claim-browser',
          },
        };
      }
      if (command.endsWith('--cancel')) return { state: 'closed' };
      throw new Error(`unexpected claim-loss command: ${command}`);
    },
  });
  const recovered = await claimLossProvider.ensureSession();
  assert.equal(recovered.sessionId, 'claim-session');
  assert.equal(starts, 1);
  assert.equal(claims, 1);
  assert.equal((await claimLossProvider.close()).stopped, true);
}

// A failed close must retain exact ownership and quarantine new starts until
// the original request is proven closed.
{
  let starts = 0;
  let cancels = 0;
  const cleanupProvider = createBrowserSkillCliProvider({
    browserSelector: 'cleanup-profile',
    run: async args => {
      const command = key(args);
      if (command === 'status') {
        return { daemon_version: '0.3.1', protocol_version: '1.3', version_skew_browsers: [] };
      }
      if (command === 'browsers') {
        return [{
          instance_id: 'cleanup-browser',
          label: 'cleanup-profile',
          extension_version: '0.3.1',
          extension_protocol_version: '1.3',
        }];
      }
      if (command.endsWith('--prepare')) return { state: 'prepared' };
      if (command.startsWith('session start ')) {
        starts += 1;
        return { session_id: 'cleanup-session', browser_instance_id: 'cleanup-browser' };
      }
      if (command.endsWith('--claim')) {
        return {
          state: 'active',
          session: {
            session_id: 'cleanup-session',
            browser_instance_id: 'cleanup-browser',
          },
        };
      }
      if (command.endsWith('--cancel')) {
        cancels += 1;
        return { state: cancels >= 3 ? 'closed' : 'cancelling' };
      }
      throw new Error(`unexpected cleanup command: ${command}`);
    },
  });
  await cleanupProvider.ensureSession();
  const firstClose = await cleanupProvider.close();
  assert.equal(firstClose.stopped, false);
  await assert.rejects(
    cleanupProvider.ensureSession(),
    /cleanup remains unresolved/,
  );
  assert.equal(starts, 1, 'unresolved cleanup must block a replacement BrowserSkill session');
  const finalClose = await cleanupProvider.close();
  assert.equal(finalClose.stopped, true);
  assert.equal(starts, 1);
}

// The snapshot is admissible only when tab identity is stable on both sides
// of capture. Navigation between tab-list before/after must become ambiguous.
{
  let tabReads = 0;
  const driftProvider = createBrowserSkillCliProvider({
    browserSelector: 'drift-profile',
    run: async args => {
      const command = key(args);
      if (command === 'status') {
        return { daemon_version: '0.3.1', protocol_version: '1.3', version_skew_browsers: [] };
      }
      if (command === 'browsers') {
        return [{
          instance_id: 'drift-browser',
          label: 'drift-profile',
          extension_version: '0.3.1',
          extension_protocol_version: '1.3',
        }];
      }
      if (command.endsWith('--prepare')) return { state: 'prepared' };
      if (command.startsWith('session start ')) {
        return { session_id: 'drift-session', browser_instance_id: 'drift-browser' };
      }
      if (command.endsWith('--claim')) {
        return {
          state: 'active',
          session: {
            session_id: 'drift-session',
            browser_instance_id: 'drift-browser',
          },
        };
      }
      if (command === 'tab list --session drift-session --scope all') {
        tabReads += 1;
        return {
          tabs: [{
            tab_id: 71,
            title: tabReads === 1 ? 'Before' : 'After',
            url: tabReads === 1 ? 'https://example.com/before' : 'https://example.com/after',
            window_id: 9,
            scope: 'agent',
          }],
        };
      }
      if (command === 'snapshot --session drift-session') {
        return { text: '@e1 button "Save"\n', ref_count: 1, tab_id: 71, truncated: false };
      }
      if (command.endsWith('--cancel')) return { state: 'closed' };
      throw new Error(`unexpected drift command: ${command}`);
    },
  });
  const captured = await driftProvider.snapshotObservation();
  assert.equal(captured.observation.ambiguous, true);
  assert.equal(captured.observation.settled, false);
  assert.equal(captured.observation.complete, false);
  await driftProvider.close();
}

// Duplicate semantic controls get generation-scoped CAP refs. An old one must
// fail before physical delivery after a fresh observation.
{
  let clicks = 0;
  const staleProvider = createBrowserSkillCliProvider({
    browserSelector: 'stale-profile',
    run: async args => {
      const command = key(args);
      if (command === 'status') {
        return { daemon_version: '0.3.1', protocol_version: '1.3', version_skew_browsers: [] };
      }
      if (command === 'browsers') {
        return [{
          instance_id: 'stale-browser',
          label: 'stale-profile',
          extension_version: '0.3.1',
          extension_protocol_version: '1.3',
        }];
      }
      if (command.endsWith('--prepare')) return { state: 'prepared' };
      if (command.startsWith('session start ')) {
        return { session_id: 'stale-session', browser_instance_id: 'stale-browser' };
      }
      if (command.endsWith('--claim')) {
        return {
          state: 'active',
          session: {
            session_id: 'stale-session',
            browser_instance_id: 'stale-browser',
          },
        };
      }
      if (command === 'tab list --session stale-session --scope all') {
        return {
          tabs: [{
            tab_id: 81,
            title: 'Stable',
            url: 'https://example.com/stable',
            window_id: 10,
            scope: 'agent',
          }],
        };
      }
      if (command === 'snapshot --session stale-session') {
        return {
          text: '@e1 button "Same"\n@e2 button "Same"\n',
          ref_count: 2,
          tab_id: 81,
          truncated: false,
        };
      }
      if (command.startsWith('click ')) {
        clicks += 1;
        return { tab_id: 81 };
      }
      if (command.endsWith('--cancel')) return { state: 'closed' };
      throw new Error(`unexpected stale-ref command: ${command}`);
    },
  });
  const first = await staleProvider.call('browser_snapshot', {});
  const staleRef = first.structuredContent.normalized_browser_observation.controls[0].control_id;
  assert.match(staleRef, /^@capg-/);
  await staleProvider.call('browser_snapshot', {});
  await assert.rejects(
    staleProvider.call('browser_click', { target: staleRef }),
    error => (
      error instanceof BrowserSkillProviderError &&
      error.deliveryAttempted === false &&
      /stale or ambiguous/.test(error.message)
    ),
  );
  assert.equal(clicks, 0, 'stale CAP ref must fail before BrowserSkill click delivery');
  await staleProvider.close();
}

// Every upstream grouped action must be physically mapped by the provider, not
// merely listed in a manifest. This fake runner lets all CLI commands complete
// without touching a real browser or asking a human for confirmation.
{
  const mappedCommands = [];
  const fullRun = async args => {
    mappedCommands.push([...args]);
    const command = key(args);
    if (command === 'status') {
      return { daemon_version: '0.3.1', protocol_version: '1.3', version_skew_browsers: [] };
    }
    if (command === 'browsers') {
      return [{
        instance_id: 'browser-full',
        label: 'profile-full',
        extension_version: '0.3.1',
        extension_protocol_version: '1.3',
      }];
    }
    if (command.includes('session request') && command.endsWith('--prepare')) return { state: 'prepared' };
    if (command.startsWith('session start ')) {
      return { session_id: 's-full', browser_instance_id: 'browser-full' };
    }
    if (command.includes('session request') && command.endsWith('--claim')) {
      return {
        state: 'active',
        session: { session_id: 's-full', browser_instance_id: 'browser-full' },
      };
    }
    if (command.includes('session request') && command.endsWith('--cancel')) return { state: 'closed' };
    if (command === 'session list') return { sessions: [] };
    return { ok: true, tabs: [], state: 'ok' };
  };
  const fullProvider = createBrowserSkillCliProvider({
    browserSelector: 'profile-full',
    run: fullRun,
  });

  const argsFor = {
    'browser_session:start': {},
    'browser_session:list': {},

    'browser_page:navigate': { url: 'https://example.com/' },
    'browser_page:back': {},
    'browser_page:forward': {},
    'browser_page:reload': {},
    'browser_page:wait': {},

    'browser_inspect:observe': {},
    'browser_inspect:snapshot': {},
    'browser_inspect:html': {},
    'browser_inspect:screenshot': {},
    'browser_inspect:console': {},
    'browser_inspect:network': {},
    'browser_inspect:debug': { debugAction: 'status' },

    'browser_interact:click': { target: '@e1' },
    'browser_interact:hover': { target: '@e1' },
    'browser_interact:wheel': { deltaY: 120 },
    'browser_interact:scroll-to': { target: '@e1' },
    'browser_interact:focus': { target: '@e1' },
    'browser_interact:blur': { target: '@e1' },
    'browser_interact:fill': { target: '@e1', value: 'value' },
    'browser_interact:select': { target: '@e1', values: ['one'] },
    'browser_interact:press': { key: 'Enter', target: '@e1' },

    'browser_tabs:list': {},
    'browser_tabs:create': { url: 'https://example.com/' },
    'browser_tabs:select': { tabId: 10 },
    'browser_tabs:close': { tabId: 10 },
    'browser_tabs:borrow': { tabId: 10 },
    'browser_tabs:return': { tabId: 10 },

    'browser_assist:resize': { width: 900, height: 700 },
    'browser_assist:emulate': { device: 'iphone-14' },
    'browser_assist:request-help': { prompt: 'test only' },
  };

  const stopKey = 'browser_session:stop';
  const mappedKeys = [];
  for (const capability of BROWSERSKILL_GROUPED_ACTION_KEYS) {
    if (capability === stopKey) continue;
    const [tool, action] = capability.split(':');
    assert.ok(
      Object.prototype.hasOwnProperty.call(argsFor, capability),
      `test fixture missing args for ${capability}`,
    );
    await fullProvider.callGrouped(tool, action, argsFor[capability]);
    mappedKeys.push(capability);
  }
  await fullProvider.callGrouped('browser_session', 'stop', {});
  mappedKeys.push(stopKey);

  assert.deepEqual(
    [...mappedKeys].sort(),
    [...BROWSERSKILL_GROUPED_ACTION_KEYS].sort(),
    'all pinned BrowserSkill grouped actions must execute through one explicit CLI mapping',
  );
  assert.ok(mappedCommands.some(args => args[0] === 'debug'), 'debug mapping must be executable');
  assert.ok(mappedCommands.some(args => args[0] === 'request-help'), 'human-assist mapping must be explicit');
  assert.ok(
    mappedCommands.some(args => args[0] === 'tab' && args[1] === 'borrow'),
    'borrow mapping must remain explicit without using --no-confirm',
  );
  assert.equal(
    mappedCommands.some(args => args.includes('--no-confirm')),
    false,
    'CAP must not silently bypass BrowserSkill user-tab borrow confirmation',
  );

  await fullProvider.callExtended('upload', {
    target: '@e2',
    files: ['one.txt', 'two.txt'],
    mode: 'input',
  });
  await fullProvider.callExtended('download', {
    target: '@e3',
    out: 'download.bin',
  });
  await fullProvider.callExtended('evaluate', {
    expression: 'document.title',
  });
  await fullProvider.callExtended('record-start', {
    url: 'https://example.com/',
    purpose: 'mapping-test',
    output: 'trace',
  });
  await fullProvider.callExtended('record-stop', {
    output: 'trace',
  });

  assert.ok(mappedCommands.some(args => args[0] === 'upload'));
  assert.ok(mappedCommands.some(args => args[0] === 'download'));
  assert.ok(mappedCommands.some(args => args[0] === 'evaluate'));
  assert.ok(mappedCommands.some(args => args[0] === 'record' && args[1] === 'start'));
  assert.ok(mappedCommands.some(args => args[0] === 'record' && args[1] === 'stop'));
}

console.log('BROWSERSKILL_SESSION_ACK_LOSS_RECONCILIATION=PASS');
console.log('BROWSERSKILL_NO_DUPLICATE_SESSION_START=PASS');
console.log('BROWSERSKILL_CLAIM_ACK_LOSS_RECONCILIATION=PASS');
console.log('BROWSERSKILL_CRASH_RECOVERY_DURABLE_LEASE=PASS');
console.log('BROWSERSKILL_CRASH_RECOVERY_VERSION_PIN=PASS');
console.log('BROWSERSKILL_UNRESOLVED_CLEANUP_QUARANTINE=PASS');
console.log('BROWSERSKILL_NORMALIZED_OBSERVATION=PASS');
console.log('BROWSERSKILL_NATIVE_REFS_PRIVATE=PASS');
console.log('BROWSERSKILL_AMBIGUOUS_REFS_GENERATION_SCOPED=PASS');
console.log('BROWSERSKILL_STABLE_REFS_PAGE_SCOPED=PASS');
console.log('BROWSERSKILL_STALE_REF_NO_DELIVERY=PASS');
console.log('BROWSERSKILL_SNAPSHOT_TAB_DRIFT_AMBIGUOUS=PASS');
console.log('BROWSERSKILL_FOREIGN_IDENTITY_FAIL_CLOSED=PASS');
console.log('BROWSERSKILL_CHILD_ENV_SECRET_SCRUB=PASS');
console.log('BROWSERSKILL_HUNG_CHILD_BOUNDED_CANCEL=PASS');
console.log('BROWSERSKILL_ALL_GROUPED_ACTIONS_MAPPED=PASS');
console.log('BROWSERSKILL_EXTENDED_MECHANICS_MAPPED=PASS');
