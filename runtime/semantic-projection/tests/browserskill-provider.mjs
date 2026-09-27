import assert from 'node:assert/strict';

import {
  BrowserSkillProviderError,
  createBrowserSkillCliProvider,
  parseBrowserSkillControls,
} from '../lib/browserskill-cli-provider.mjs';

function key(args) {
  return args.join(' ');
}

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

console.log('BROWSERSKILL_SESSION_ACK_LOSS_RECONCILIATION=PASS');
console.log('BROWSERSKILL_NO_DUPLICATE_SESSION_START=PASS');
console.log('BROWSERSKILL_NORMALIZED_OBSERVATION=PASS');
console.log('BROWSERSKILL_FOREIGN_IDENTITY_FAIL_CLOSED=PASS');
