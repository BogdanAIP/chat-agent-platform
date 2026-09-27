const EFFECT_CLASSES = new Set([
  'PROVIDER_INTERNAL',
  'READ_ONLY_EVIDENCE',
  'TRANSIENT_INPUT',
  'BROWSER_MUTATION_EXISTING_CAP_CONTRACT',
  'CROSS_CAPABILITY_GRANT_REQUIRED',
  'NEW_CONSEQUENCE_CONTRACT_REQUIRED',
  'HUMAN_ASSIST',
]);

export const BROWSERSKILL_IDENTITY = Object.freeze({
  version: '0.3.1',
  protocolVersion: '1.3',
  sourceCommit: 'da6bf4eed2dd7256567e152df8c903c87f6598c3',
  cliTag: 'cli-v0.3.1',
  extensionTag: 'ext-v0.3.1',
});

export const BROWSERSKILL_MODEL_TOOL_ACTIONS = Object.freeze({
  browser_session: Object.freeze(['start', 'stop', 'list']),
  browser_page: Object.freeze(['navigate', 'back', 'forward', 'reload', 'wait']),
  browser_inspect: Object.freeze([
    'observe',
    'snapshot',
    'html',
    'screenshot',
    'console',
    'network',
    'debug',
  ]),
  browser_interact: Object.freeze([
    'click',
    'hover',
    'wheel',
    'scroll-to',
    'focus',
    'blur',
    'fill',
    'select',
    'press',
  ]),
  browser_tabs: Object.freeze(['list', 'create', 'select', 'close', 'borrow', 'return']),
  browser_assist: Object.freeze(['resize', 'emulate', 'request-help']),
});

export const BROWSERSKILL_PROTOCOL_METHODS = Object.freeze({
  'audit.request': 'NEW_CONSEQUENCE_CONTRACT_REQUIRED',

  'system.handshake': 'PROVIDER_INTERNAL',
  'system.ping': 'PROVIDER_INTERNAL',
  'system.status': 'PROVIDER_INTERNAL',

  'session.start': 'PROVIDER_INTERNAL',
  'session.start_tracked': 'PROVIDER_INTERNAL',
  'session.request': 'PROVIDER_INTERNAL',
  'session.stop': 'PROVIDER_INTERNAL',
  'session.stop_all': 'PROVIDER_INTERNAL',
  'session.list': 'PROVIDER_INTERNAL',

  'browser.list': 'READ_ONLY_EVIDENCE',

  'tool.session_start': 'PROVIDER_INTERNAL',
  'tool.session_stop': 'PROVIDER_INTERNAL',
  'tool.window_resize': 'BROWSER_MUTATION_EXISTING_CAP_CONTRACT',
  'tool.emulate': 'BROWSER_MUTATION_EXISTING_CAP_CONTRACT',

  'tool.tab_list': 'READ_ONLY_EVIDENCE',
  'tool.tab_create': 'BROWSER_MUTATION_EXISTING_CAP_CONTRACT',
  'tool.tab_close': 'BROWSER_MUTATION_EXISTING_CAP_CONTRACT',
  'tool.tab_borrow': 'BROWSER_MUTATION_EXISTING_CAP_CONTRACT',
  'tool.tab_return': 'BROWSER_MUTATION_EXISTING_CAP_CONTRACT',
  'tool.tab_select': 'BROWSER_MUTATION_EXISTING_CAP_CONTRACT',

  'tool.navigate': 'BROWSER_MUTATION_EXISTING_CAP_CONTRACT',
  'tool.navigate_back': 'BROWSER_MUTATION_EXISTING_CAP_CONTRACT',
  'tool.navigate_forward': 'BROWSER_MUTATION_EXISTING_CAP_CONTRACT',
  'tool.reload': 'BROWSER_MUTATION_EXISTING_CAP_CONTRACT',

  'tool.click': 'BROWSER_MUTATION_EXISTING_CAP_CONTRACT',
  'tool.hover': 'TRANSIENT_INPUT',
  'tool.wheel': 'BROWSER_MUTATION_EXISTING_CAP_CONTRACT',
  'tool.scroll_to': 'BROWSER_MUTATION_EXISTING_CAP_CONTRACT',
  'tool.focus': 'BROWSER_MUTATION_EXISTING_CAP_CONTRACT',
  'tool.blur': 'BROWSER_MUTATION_EXISTING_CAP_CONTRACT',
  'tool.fill': 'BROWSER_MUTATION_EXISTING_CAP_CONTRACT',
  'tool.press': 'BROWSER_MUTATION_EXISTING_CAP_CONTRACT',
  'tool.select': 'BROWSER_MUTATION_EXISTING_CAP_CONTRACT',

  'tool.upload': 'CROSS_CAPABILITY_GRANT_REQUIRED',
  'tool.download': 'CROSS_CAPABILITY_GRANT_REQUIRED',

  'tool.snapshot': 'READ_ONLY_EVIDENCE',
  'tool.observe': 'TRANSIENT_INPUT',
  'tool.get_html': 'READ_ONLY_EVIDENCE',
  'tool.screenshot': 'READ_ONLY_EVIDENCE',
  'tool.screenshot_full_page': 'TRANSIENT_INPUT',
  'tool.screenshot_read': 'READ_ONLY_EVIDENCE',
  'tool.screenshot_release': 'PROVIDER_INTERNAL',
  'tool.console': 'READ_ONLY_EVIDENCE',
  'tool.network': 'READ_ONLY_EVIDENCE',

  // Debug is parameter-sensitive upstream: read/export/teardown and live
  // request-control/replay share one RPC. CAP therefore refuses the whole
  // method until its sub-actions have truthful consequence contracts.
  'tool.debug': 'NEW_CONSEQUENCE_CONTRACT_REQUIRED',

  // The daemon cannot statically prove evaluate is read-only.
  'tool.evaluate': 'NEW_CONSEQUENCE_CONTRACT_REQUIRED',

  'tool.wait_for_navigation': 'READ_ONLY_EVIDENCE',
  'tool.wait_ms': 'READ_ONLY_EVIDENCE',
  'tool.request_help': 'HUMAN_ASSIST',

  // Recording changes browser chrome and introduces capture/retention privacy
  // semantics. Keep all record lifecycle methods explicit instead of omitting
  // them from the provider contract.
  'tool.record_start': 'NEW_CONSEQUENCE_CONTRACT_REQUIRED',
  'tool.record_stop': 'NEW_CONSEQUENCE_CONTRACT_REQUIRED',
  'tool.record_await': 'NEW_CONSEQUENCE_CONTRACT_REQUIRED',

  'transfer.begin': 'PROVIDER_INTERNAL',
  'transfer.chunk': 'PROVIDER_INTERNAL',
  'transfer.finish': 'PROVIDER_INTERNAL',
  'transfer.read': 'PROVIDER_INTERNAL',
  'transfer.release': 'PROVIDER_INTERNAL',

  'cancel': 'PROVIDER_INTERNAL',
});



export const BROWSERSKILL_RUNTIME_STATUS = Object.freeze({
  'browser_session:start': 'PROVIDER_INTERNAL',
  'browser_session:stop': 'PROVIDER_INTERNAL',
  'browser_session:list': 'PROVIDER_INTERNAL',

  'browser_page:navigate': 'PUBLIC_CURRENT',
  'browser_page:back': 'MAPPED_PENDING_PUBLIC_CONTRACT',
  'browser_page:forward': 'MAPPED_PENDING_PUBLIC_CONTRACT',
  'browser_page:reload': 'MAPPED_PENDING_PUBLIC_CONTRACT',
  'browser_page:wait': 'MAPPED_PENDING_PUBLIC_CONTRACT',

  'browser_inspect:observe': 'MAPPED_PENDING_PUBLIC_CONTRACT',
  'browser_inspect:snapshot': 'PUBLIC_CURRENT',
  'browser_inspect:html': 'MAPPED_PENDING_PUBLIC_CONTRACT',
  'browser_inspect:screenshot': 'MAPPED_PENDING_PUBLIC_CONTRACT',
  'browser_inspect:console': 'MAPPED_PENDING_PUBLIC_CONTRACT',
  'browser_inspect:network': 'MAPPED_PENDING_PUBLIC_CONTRACT',
  'browser_inspect:debug': 'MAPPED_BLOCKED_NEW_CONSEQUENCE_CONTRACT',

  'browser_interact:click': 'PUBLIC_CURRENT',
  'browser_interact:hover': 'MAPPED_PENDING_PUBLIC_CONTRACT',
  'browser_interact:wheel': 'MAPPED_PENDING_PUBLIC_CONTRACT',
  'browser_interact:scroll-to': 'MAPPED_PENDING_PUBLIC_CONTRACT',
  'browser_interact:focus': 'MAPPED_PENDING_PUBLIC_CONTRACT',
  'browser_interact:blur': 'MAPPED_PENDING_PUBLIC_CONTRACT',
  'browser_interact:fill': 'PUBLIC_CURRENT',
  'browser_interact:select': 'MAPPED_PENDING_PUBLIC_CONTRACT',
  'browser_interact:press': 'MAPPED_PENDING_PUBLIC_CONTRACT',

  'browser_tabs:list': 'MAPPED_PENDING_PUBLIC_CONTRACT',
  'browser_tabs:create': 'MAPPED_PENDING_PUBLIC_CONTRACT',
  'browser_tabs:select': 'MAPPED_PENDING_PUBLIC_CONTRACT',
  'browser_tabs:close': 'MAPPED_PENDING_PUBLIC_CONTRACT',
  'browser_tabs:borrow': 'MAPPED_PENDING_PUBLIC_CONTRACT',
  'browser_tabs:return': 'MAPPED_PENDING_PUBLIC_CONTRACT',

  'browser_assist:resize': 'MAPPED_PENDING_PUBLIC_CONTRACT',
  'browser_assist:emulate': 'MAPPED_PENDING_PUBLIC_CONTRACT',
  'browser_assist:request-help': 'MAPPED_HUMAN_ASSIST_CONTRACT',

  'extended:upload': 'MAPPED_CROSS_CAPABILITY_GRANT_REQUIRED',
  'extended:download': 'MAPPED_CROSS_CAPABILITY_GRANT_REQUIRED',
  'extended:evaluate': 'MAPPED_BLOCKED_NEW_CONSEQUENCE_CONTRACT',
  'extended:record-start': 'MAPPED_BLOCKED_NEW_CONSEQUENCE_CONTRACT',
  'extended:record-stop': 'MAPPED_BLOCKED_NEW_CONSEQUENCE_CONTRACT',
});

export function validateBrowserSkillManifest() {
  const entries = Object.entries(BROWSERSKILL_PROTOCOL_METHODS);
  if (entries.length === 0) throw new Error('BrowserSkill capability manifest must not be empty');

  for (const [method, effectClass] of entries) {
    if (typeof method !== 'string' || method.length === 0) {
      throw new Error('BrowserSkill capability manifest contains an invalid method name');
    }
    if (!EFFECT_CLASSES.has(effectClass)) {
      throw new Error(`BrowserSkill method ${method} has unknown CAP effect class ${effectClass}`);
    }
  }

  for (const [tool, actions] of Object.entries(BROWSERSKILL_MODEL_TOOL_ACTIONS)) {
    if (!tool.startsWith('browser_')) {
      throw new Error(`BrowserSkill model-facing tool has unexpected name: ${tool}`);
    }
    if (!Array.isArray(actions) || actions.length === 0) {
      throw new Error(`BrowserSkill model-facing tool has no actions: ${tool}`);
    }
    if (new Set(actions).size !== actions.length) {
      throw new Error(`BrowserSkill model-facing tool has duplicate actions: ${tool}`);
    }
    for (const action of actions) {
      const key = `${tool}:${action}`;
      if (!Object.prototype.hasOwnProperty.call(BROWSERSKILL_RUNTIME_STATUS, key)) {
        throw new Error(`BrowserSkill grouped action has no runtime status: ${key}`);
      }
    }
  }

  const groupedKeys = Object.entries(BROWSERSKILL_MODEL_TOOL_ACTIONS)
    .flatMap(([tool, actions]) => actions.map(action => `${tool}:${action}`));
  const declaredGrouped = Object.keys(BROWSERSKILL_RUNTIME_STATUS)
    .filter(key => !key.startsWith('extended:'));
  if (
    groupedKeys.length !== declaredGrouped.length ||
    groupedKeys.some(key => !declaredGrouped.includes(key))
  ) {
    throw new Error('BrowserSkill runtime status must exactly cover pinned grouped actions');
  }

  return true;
}

export function assertBrowserSkillRuntimeIdentity({ version, protocolVersion }) {
  if (version !== BROWSERSKILL_IDENTITY.version) {
    throw new Error(
      `unsupported BrowserSkill version ${String(version)}; reviewed version is ${BROWSERSKILL_IDENTITY.version}`,
    );
  }
  if (protocolVersion !== BROWSERSKILL_IDENTITY.protocolVersion) {
    throw new Error(
      `unsupported BrowserSkill protocol ${String(protocolVersion)}; reviewed protocol is ${BROWSERSKILL_IDENTITY.protocolVersion}`,
    );
  }
  return true;
}

validateBrowserSkillManifest();
