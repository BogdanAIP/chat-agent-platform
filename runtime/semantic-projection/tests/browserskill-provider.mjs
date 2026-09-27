import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { PassThrough } from 'node:stream';

import {
  BrowserSkillProviderError,
  BROWSERSKILL_GROUPED_ACTION_KEYS,
  browserSkillChildEnvironment,
  createBskJsonRunner,
  createBrowserSkillCliProvider,
  parseBrowserSkillControls,
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
assert.equal(
  snapshot.structuredContent?.provider_subject,
  'browserskill:browser-a:s-owned:17',
);
const normalized = snapshot.structuredContent?.normalized_browser_observation;
assert.equal(normalized.url, 'https://example.com/');
assert.equal(normalized.title, 'Example');
assert.equal(normalized.controls.length, 3);
assert.deepEqual(normalized.controls.find(item => item.control_id === '@e1'), {
  control_id: '@e1',
  role: 'button',
  name: 'Save',
  enabled: true,
  checked: null,
  selected: null,
  visible: true,
  value: null,
});
assert.equal(normalized.controls.find(item => item.control_id === '@e2')?.value, '');
assert.equal(normalized.controls.find(item => item.control_id === '@e3')?.checked, true);

await provider.call('browser_navigate', { url: 'https://example.com/' });
await provider.call('browser_click', { target: '@e1' });
await provider.call('browser_type', { target: '@e2', text: 'HELLO' });

await assert.rejects(
  provider.call('browser_type', { target: '@e2', text: 'HELLO', slowly: true }),
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
    if (command.includes('session request') && command.endsWith('--claim')) return { state: 'active' };
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
console.log('BROWSERSKILL_NORMALIZED_OBSERVATION=PASS');
console.log('BROWSERSKILL_FOREIGN_IDENTITY_FAIL_CLOSED=PASS');
console.log('BROWSERSKILL_CHILD_ENV_SECRET_SCRUB=PASS');
console.log('BROWSERSKILL_HUNG_CHILD_BOUNDED_CANCEL=PASS');
console.log('BROWSERSKILL_ALL_GROUPED_ACTIONS_MAPPED=PASS');
console.log('BROWSERSKILL_EXTENDED_MECHANICS_MAPPED=PASS');
