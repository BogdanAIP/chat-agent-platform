(() => {
  "use strict";

  const HEX64_RE = /^[0-9a-f]{64}$/;
  const HEAD40_RE = /^[0-9a-f]{40}$/;
  const RESULT_BEGIN = "CAP_WORKER_RESULT_V1_BEGIN";
  const RESULT_END = "CAP_WORKER_RESULT_V1_END";
  const POST_DELIVERY_UI_STABLE_MS = 8000;
  const POST_DELIVERY_UI_POLL_MS = 500;
  const LAUNCH_QUERY_KEYS = [
    "temporary-chat",
    "cap_agent_delegate",
    "cap_delegation_id",
    "cap_delivery_id",
    "cap_task_sha256",
    "cap_expected_head",
    "cap_prompt_sha256",
    "prompt",
  ];
  const TASK_CORRELATION_MARKERS = [
    "WORKER_TASK_V1",
    "delegation_id=",
    "delivery_id=",
    "task_sha256=",
  ];
  const CAPTURE_AUTHORITY_SELECTOR = [
    '[data-message-author-role="user"]',
    '[data-message-author-role="assistant"]',
    '#prompt-textarea',
    '[contenteditable="true"]',
    'textarea',
    'button[data-testid="stop-button"]',
  ].join(",");
  const STOP_AUTHORITY_ATTRIBUTES = new Set(["aria-label", "data-testid"]);
  let postDeliveryUiDisarmed = false;
  let postDeliveryCleanupToken = null;
  let browserGuardRequired = false;
  let postDeliveryGuardIntent = null;
  let postDeliveryGuardInterval = null;
  let postDeliveryGuardObserver = null;
  let postDeliveryStableSince = 0;
  let postDeliveryAckPending = false;
  let postDeliveryGuardEpoch = 0;
  let postDeliveryAssistantSnapshotEpoch = null;
  let postDeliveryAssistantSnapshotText = "";

  function parseIntent(urlString) {
    let url;
    try {
      url = new URL(urlString);
    } catch {
      return { enabled: false, reason: "invalid-url" };
    }
    if (url.origin !== "https://chatgpt.com") return { enabled: false, reason: "wrong-origin" };
    if (url.searchParams.get("temporary-chat") !== "true") return { enabled: false, reason: "temporary-flag-missing" };
    if (url.searchParams.get("cap_agent_delegate") !== "1") return { enabled: false, reason: "delegate-flag-missing" };

    const fragmentParams = new URLSearchParams(url.hash.startsWith("#") ? url.hash.slice(1) : url.hash);
    const runId = fragmentParams.get("cap_run_id") || "";
    const delegationId = url.searchParams.get("cap_delegation_id") || "";
    const deliveryId = url.searchParams.get("cap_delivery_id") || "";
    const taskSha256 = url.searchParams.get("cap_task_sha256") || "";
    const expectedHead = url.searchParams.get("cap_expected_head") || "";
    const promptSha256 = url.searchParams.get("cap_prompt_sha256") || "";
    const prompt = url.searchParams.get("prompt") || "";
    if (![runId, delegationId, deliveryId, taskSha256, promptSha256].every((value) => HEX64_RE.test(value))) {
      return { enabled: false, reason: "invalid-correlation" };
    }
    if (!HEAD40_RE.test(expectedHead)) return { enabled: false, reason: "invalid-expected-head" };
    if (url.searchParams.has("cap_run_id")) return { enabled: false, reason: "private-run-id-in-query" };
    if (!prompt || prompt.length > 120000) return { enabled: false, reason: "invalid-prompt" };
    for (const marker of [
      "WORKER_TASK_V1",
      `delegation_id=${delegationId}`,
      `delivery_id=${deliveryId}`,
      `task_sha256=${taskSha256}`,
      RESULT_BEGIN,
      RESULT_END,
    ]) {
      if (!prompt.includes(marker)) return { enabled: false, reason: "prompt-binding-mismatch" };
    }
    if (prompt.includes(runId)) return { enabled: false, reason: "private-run-id-leaked-to-prompt" };

    return {
      enabled: true,
      runId,
      delegationId,
      deliveryId,
      taskSha256,
      expectedHead,
      promptSha256,
      prompt,
      maxWaitMs: 30 * 60 * 1000,
      deliveryObserveMs: 20000,
      stableMs: 3000,
    };
  }

  function canonicalPromptText(text) {
    return String(text ?? "").replace(/\r\n?/g, "\n");
  }

  function correlationCandidateText(text) {
    const value = canonicalPromptText(text).replace(/\u0000/g, "");
    return TASK_CORRELATION_MARKERS.some((marker) => value.includes(marker));
  }

  function exactTaskCorrelationShape(text, intent) {
    if (!intent) return false;
    const lines = canonicalPromptText(text).split("\n");
    const start = lines.findIndex((line) => correlationCandidateText(line));
    if (start < 0 || lines[start] !== "WORKER_TASK_V1") return false;
    let cursor = start + 1;
    if (lines[cursor] === "") cursor += 1;
    if (lines[cursor++] !== `delegation_id=${intent.delegationId}`) return false;
    if (lines[cursor++] !== `delivery_id=${intent.deliveryId}`) return false;
    if (lines[cursor]?.startsWith("worker_kind=")) {
      if (!/^worker_kind=[a-z][a-z0-9._-]{0,63}$/.test(lines[cursor++])) return false;
      if (lines[cursor++] !== "worker_profile=fresh_readonly_worker_v1") return false;
      if (!/^result_contract_id=[a-z][a-z0-9._-]{0,63}$/.test(lines[cursor++])) return false;
    }
    if (lines[cursor++] !== `task_sha256=${intent.taskSha256}`) return false;

    const beginMarker = `TASK_BEGIN:${intent.taskSha256}`;
    const endMarker = `TASK_END:${intent.taskSha256}`;
    const begins = lines.flatMap((line, index) => line.includes(beginMarker) ? [index] : []);
    const ends = lines.flatMap((line, index) => line.includes(endMarker) ? [index] : []);
    const begin = begins[0] ?? -1;
    const end = ends[0] ?? -1;
    if (
      begins.length !== 1 ||
      ends.length !== 1 ||
      begin < cursor ||
      end <= begin ||
      lines[begin] !== beginMarker ||
      lines[end] !== endMarker
    ) return false;
    const outside = [
      ...lines.slice(0, start),
      ...lines.slice(cursor, begin),
      ...lines.slice(end + 1),
    ];
    return outside.every((line) => !correlationCandidateText(line) &&
      !line.includes("TASK_BEGIN") && !line.includes("TASK_END"));
  }

  function visibleUserCorrelationState(intent) {
    if (typeof document === "undefined" || typeof document.querySelectorAll !== "function") return null;
    let candidateCount = 0;
    let matchCount = 0;
    for (const node of document.querySelectorAll('[data-message-author-role="user"]')) {
      const text = String(node?.innerText || node?.textContent || "");
      if (!correlationCandidateText(text)) continue;
      candidateCount += 1;
      if (guardVisible(node) && exactTaskCorrelationShape(text, intent)) matchCount += 1;
    }
    return { candidateCount, matchCount };
  }

  function hasExpectedPrompt(text, intent) {
    if (!exactTaskCorrelationShape(text, intent)) return false;
    const visible = visibleUserCorrelationState(intent);
    if (visible === null || visible.candidateCount === 0) return true;
    return visible.candidateCount === 1 && visible.matchCount === 1;
  }

  function exactPromptMatches(observed, expected) {
    if (typeof observed !== "string" || typeof expected !== "string" || !expected) return false;
    return canonicalPromptText(observed) === canonicalPromptText(expected);
  }

  function personalizationModeFromText(text) {
    const value = String(text || "").replace(/\s+/g, " ").trim();
    if (!value) return "unknown";

    const nonPersonalizedPatterns = [
      /\bnon[-\s]?personalized\b/i,
      /\bnot personalized\b/i,
      /без персонализац/i,
      /неперсонализ/i,
      /nicht personalisiert/i,
    ];
    if (nonPersonalizedPatterns.some((pattern) => pattern.test(value))) {
      return "non-personalized";
    }

    const personalizedPatterns = [
      /\bpersonalized\b/i,
      /персонализ/i,
      /\bpersonalisiert\b/i,
    ];
    if (personalizedPatterns.some((pattern) => pattern.test(value))) {
      return "personalized";
    }
    return "unknown";
  }

  function singleResultBlockShape(text) {
    const value = canonicalPromptText(String(text || "").trim());
    const lines = value.split("\n");
    if (lines.length < 3 || lines[0] !== RESULT_BEGIN || lines.at(-1) !== RESULT_END) return false;
    const body = lines.slice(1, -1).join("\n").trim();
    if (!body) return false;
    try {
      const parsed = JSON.parse(body);
      return Boolean(parsed) && typeof parsed === "object" && !Array.isArray(parsed);
    } catch {
      return false;
    }
  }

  function resetAssistantCaptureSnapshot() {
    postDeliveryAssistantSnapshotEpoch = null;
    postDeliveryAssistantSnapshotText = "";
  }

  function resetPostDeliveryStability() {
    postDeliveryUiDisarmed = false;
    postDeliveryCleanupToken = null;
    postDeliveryStableSince = 0;
    resetAssistantCaptureSnapshot();
    postDeliveryGuardEpoch += 1;
  }

  function invalidatePostDeliveryAuthorization() {
    if (!browserGuardRequired || !postDeliveryGuardIntent) return false;
    resetPostDeliveryStability();
    return true;
  }

  function currentPostDeliveryUiClean() {
    if (!browserGuardRequired || !postDeliveryGuardIntent) return false;
    return guardDeliveryVisible(postDeliveryGuardIntent) &&
      guardLaunchUrlClean() && guardComposerState(postDeliveryGuardIntent).clean;
  }

  function currentAssistantResultText() {
    if (typeof document === "undefined" || typeof document.querySelectorAll !== "function") return undefined;
    const turns = [...document.querySelectorAll('[data-message-author-role="assistant"]')];
    if (turns.length === 0) return undefined;
    const visibleTurns = turns.filter((node) => guardVisible(node));
    if (visibleTurns.length === 0) return null;
    const last = visibleTurns.at(-1);
    return String(last?.innerText || last?.textContent || "").replace(/\u0000/g, "").trim();
  }

  function guardStopButtonPresent() {
    if (typeof document === "undefined" || typeof document.querySelector !== "function") return false;
    const primary = document.querySelector('button[data-testid="stop-button"]');
    if (primary && guardVisible(primary)) return true;
    if (typeof document.querySelectorAll !== "function") return false;
    return [...document.querySelectorAll("button")].some((button) =>
      guardVisible(button) && (
        button?.getAttribute?.("data-testid") === "stop-button" ||
        /^(stop|останов)/i.test(String(button?.getAttribute?.("aria-label") || button?.textContent || "").trim())
      ),
    );
  }

  function captureAuthorization() {
    if (!browserGuardRequired || !postDeliveryGuardIntent || !postDeliveryUiDisarmed) return null;
    if (!HEX64_RE.test(postDeliveryCleanupToken || "")) return null;
    // MutationObserver callbacks are microtask-delivered. Drain any qualifying
    // records already detected but not yet callback-processed before returning
    // the authority used by the immediately following one-time capture dispatch.
    if (!flushPendingPostDeliveryMutations()) return null;
    if (!currentPostDeliveryUiClean()) {
      resetPostDeliveryStability();
      return null;
    }

    const assistantText = currentAssistantResultText();
    if (assistantText === null) {
      resetPostDeliveryStability();
      return null;
    }
    if (assistantText !== undefined) {
      if (!assistantText || guardStopButtonPresent()) {
        resetPostDeliveryStability();
        return null;
      }
      if (
        postDeliveryAssistantSnapshotEpoch === postDeliveryGuardEpoch &&
        postDeliveryAssistantSnapshotText !== assistantText
      ) {
        resetPostDeliveryStability();
        return null;
      }
      if (postDeliveryAssistantSnapshotEpoch !== postDeliveryGuardEpoch) {
        postDeliveryAssistantSnapshotEpoch = postDeliveryGuardEpoch;
        postDeliveryAssistantSnapshotText = assistantText;
      }
    }

    return {
      cleanupToken: postDeliveryCleanupToken,
      guardEpoch: postDeliveryGuardEpoch,
    };
  }

  function hasSingleResultBlock(text) {
    if (!singleResultBlockShape(text)) return false;
    if (typeof document === "undefined" || typeof location === "undefined") return true;
    return captureAuthorization() !== null;
  }

  function guardEditorText(editor) {
    if (!editor) return "";
    if (typeof HTMLTextAreaElement !== "undefined" && editor instanceof HTMLTextAreaElement) {
      return String(editor.value || "");
    }
    if (typeof HTMLInputElement !== "undefined" && editor instanceof HTMLInputElement) {
      return String(editor.value || "");
    }
    return String(editor.innerText || editor.textContent || "").replace(/\u0000/g, "").trim();
  }

  function guardVisible(node) {
    if (!node?.isConnected || typeof node.getBoundingClientRect !== "function") return false;
    const rect = node.getBoundingClientRect();
    if (!(rect.width > 0 && rect.height > 0)) return false;
    for (let current = node; current; current = current.parentElement) {
      const style = getComputedStyle(current);
      if (current.hidden || current.inert || current.getAttribute?.("aria-hidden") === "true" ||
          ["hidden", "collapse"].includes(style.visibility) || style.display === "none" ||
          style.opacity === "0") return false;
    }
    return true;
  }

  function eligibleComposerEditor(editor) {
    if (!guardVisible(editor)) return false;
    for (let node = editor; node; node = node.parentElement) {
      if (node.hidden || node.inert || node.disabled || node.readOnly ||
          ["aria-hidden", "aria-disabled", "aria-readonly"].some((name) =>
            String(node.getAttribute?.(name)).toLowerCase() === "true")) return false;
      if (node.matches?.(":disabled")) return false;
    }
    if (String(editor.tagName || "").toUpperCase() === "TEXTAREA") return true;
    if (editor.getAttribute?.("contenteditable") === "false") return false;
    return editor.getAttribute?.("contenteditable") === "true" || editor.isContentEditable === true;
  }

  function guardFindComposerEditor() {
    const candidates = [];
    const seen = new Set();
    const primary = document.querySelector("#prompt-textarea");
    const discovered = [...document.querySelectorAll('#prompt-textarea,[contenteditable="true"],textarea')];
    const ordered = primary ? [primary, ...discovered] : discovered;

    for (const editor of ordered) {
      if (!editor || seen.has(editor)) continue;
      seen.add(editor);
      if (!eligibleComposerEditor(editor)) continue;

      const form = editor.closest?.("form");
      if (!form || !guardVisible(form)) continue;

      candidates.push(editor);
    }

    return candidates.length === 1 ? candidates[0] : null;
  }

  function guardComposerState(intent) {
    const editor = guardFindComposerEditor();
    if (!editor) return { clean: false, editor: null, bound: false };
    const text = guardEditorText(editor);
    return {
      clean: text.trim().length === 0,
      editor,
      bound: hasExpectedPrompt(text, intent),
    };
  }

  function guardLaunchUrlClean() {
    try {
      const url = new URL(location.href);
      const fragment = new URLSearchParams(url.hash.startsWith("#") ? url.hash.slice(1) : url.hash);
      return !LAUNCH_QUERY_KEYS.some((key) => url.searchParams.has(key)) && !fragment.has("cap_run_id");
    } catch {
      return false;
    }
  }

  function guardSanitizeLaunchUrl() {
    try {
      const url = new URL(location.href);
      const fragment = new URLSearchParams(url.hash.startsWith("#") ? url.hash.slice(1) : url.hash);
      for (const key of LAUNCH_QUERY_KEYS) url.searchParams.delete(key);
      fragment.delete("cap_run_id");
      const fragmentText = fragment.toString();
      const nextUrl = `${url.pathname}${url.search}${fragmentText ? `#${fragmentText}` : ""}`;
      history.replaceState(history.state, "", nextUrl);
      return guardLaunchUrlClean();
    } catch {
      return false;
    }
  }

  function guardClearBoundComposer(intent) {
    const state = guardComposerState(intent);
    if (!state.editor) return { clean: false, changed: false };
    if (state.clean) return { clean: true, changed: false };
    if (!state.bound) return { clean: false, changed: false };
    const editor = state.editor;
    try {
      if (typeof HTMLTextAreaElement !== "undefined" && editor instanceof HTMLTextAreaElement) {
        const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value")?.set;
        if (setter) setter.call(editor, "");
        else editor.value = "";
        editor.dispatchEvent(new InputEvent("input", {
          bubbles: true,
          inputType: "deleteContentBackward",
          data: null,
        }));
      } else {
        editor.focus({ preventScroll: true });
        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(editor);
        selection?.removeAllRanges();
        selection?.addRange(range);
        try {
          if (typeof document.execCommand === "function") document.execCommand("delete", false, null);
        } finally {
          selection?.removeAllRanges();
        }
        if (guardEditorText(editor).trim()) {
          editor.replaceChildren();
          editor.dispatchEvent(new InputEvent("input", {
            bubbles: true,
            inputType: "deleteContentBackward",
            data: null,
          }));
        }
      }
    } catch {
      return { clean: false, changed: true };
    }
    return { clean: guardComposerState(intent).clean, changed: true };
  }

  function guardDeliveryVisible(intent) {
    const visible = visibleUserCorrelationState(intent);
    return Boolean(visible && visible.candidateCount === 1 && visible.matchCount === 1);
  }

  function guardRecordCleanup(intent, callback) {
    chrome.runtime.sendMessage(
      {
        schema_version: 1,
        kind: "event",
        run_id: intent.runId,
        delegation_id: intent.delegationId,
        delivery_id: intent.deliveryId,
        execution_generation: globalThis.CAPChatGPTTemporaryExecutionGeneration || "",
        expected_runtime_head: intent.expectedHead,
        prompt_sha256: intent.promptSha256,
        event: "delivery-visible",
        details: {
          post_delivery_ui_disarmed: true,
          launch_url_clean: true,
          composer_clean: true,
        },
      },
      (response) => callback(response || { ok: false }),
    );
  }

  function sameGuardIntent(left, right) {
    return Boolean(left && right) &&
      left.runId === right.runId &&
      left.delegationId === right.delegationId &&
      left.deliveryId === right.deliveryId &&
      left.taskSha256 === right.taskSha256 &&
      left.expectedHead === right.expectedHead &&
      left.promptSha256 === right.promptSha256;
  }

  function validGuardIntent(intent) {
    return Boolean(intent) &&
      [intent.runId, intent.delegationId, intent.deliveryId, intent.taskSha256, intent.promptSha256]
        .every((value) => HEX64_RE.test(value || "")) &&
      HEAD40_RE.test(intent.expectedHead || "");
  }

  function authorityElement(node) {
    if (!node) return null;
    if (node.nodeType === 1) return node;
    return node.parentElement || null;
  }

  function authorityNode(node, includeDescendants) {
    const element = authorityElement(node);
    if (!element) return false;
    if (element.matches?.(CAPTURE_AUTHORITY_SELECTOR) || element.closest?.(CAPTURE_AUTHORITY_SELECTOR)) {
      return true;
    }
    return Boolean(includeDescendants && element.querySelector?.(CAPTURE_AUTHORITY_SELECTOR));
  }

  function stopAuthorityMutation(record) {
    const element = authorityElement(record?.target);
    if (!element) return false;
    const button = String(element.tagName || "").toUpperCase() === "BUTTON"
      ? element
      : element.closest?.("button");
    if (!button) return false;
    if (record.type === "attributes") return STOP_AUTHORITY_ATTRIBUTES.has(record.attributeName);
    return record.type === "characterData" || record.type === "childList";
  }

  function stopControlNode(node, includeDescendants) {
    const element = authorityElement(node);
    if (!element) return false;
    const candidates = [];
    if (String(element.tagName || "").toUpperCase() === "BUTTON") candidates.push(element);
    if (includeDescendants && typeof element.querySelectorAll === "function") {
      candidates.push(...element.querySelectorAll("button"));
    }
    return candidates.some((button) =>
      /^(stop|останов)/i.test(String(button?.getAttribute?.("aria-label") || button?.textContent || "").trim()),
    );
  }

  function authorityMutation(records) {
    for (const record of records || []) {
      // Attribute changes on an ancestor are authority-relevant whenever that
      // ancestor contains a correlated turn, composer/editor, or stop control.
      // guardVisible()/eligibleComposerEditor() intentionally walk ancestors,
      // so the mutation classifier must use the same containment direction.
      if (stopAuthorityMutation(record)) return true;
      if (authorityNode(record.target, record.type === "attributes")) return true;
      for (const node of record.addedNodes || []) {
        if (stopControlNode(node, true) || authorityNode(node, true)) return true;
      }
      for (const node of record.removedNodes || []) {
        if (stopControlNode(node, true) || authorityNode(node, true)) return true;
      }
    }
    return false;
  }

  function flushPendingPostDeliveryMutations() {
    if (!postDeliveryGuardObserver || typeof postDeliveryGuardObserver.takeRecords !== "function") return true;
    const pending = postDeliveryGuardObserver.takeRecords();
    if (!authorityMutation(pending)) return true;
    resetPostDeliveryStability();
    return false;
  }

  function ensurePostDeliveryMutationGuard() {
    if (postDeliveryGuardObserver || typeof MutationObserver === "undefined" || !document?.documentElement) {
      return;
    }
    postDeliveryGuardObserver = new MutationObserver((records) => {
      if (authorityMutation(records)) resetPostDeliveryStability();
    });
    postDeliveryGuardObserver.observe(document.documentElement, {
      subtree: true,
      childList: true,
      characterData: true,
      attributes: true,
      attributeFilter: [
        "aria-hidden",
        "aria-disabled",
        "aria-readonly",
        "aria-label",
        "data-testid",
        "contenteditable",
        "disabled",
        "readonly",
        "hidden",
        "inert",
        "style",
        "class",
      ],
    });
  }

  function armPostDeliveryUiGuard(intent) {
    if (
      typeof document === "undefined" ||
      typeof location === "undefined" ||
      !globalThis.chrome?.runtime?.sendMessage ||
      !validGuardIntent(intent)
    ) return false;

    if (postDeliveryGuardIntent !== null) {
      return sameGuardIntent(postDeliveryGuardIntent, intent);
    }

    browserGuardRequired = true;
    postDeliveryGuardIntent = {
      runId: intent.runId,
      delegationId: intent.delegationId,
      deliveryId: intent.deliveryId,
      taskSha256: intent.taskSha256,
      expectedHead: intent.expectedHead,
      promptSha256: intent.promptSha256,
    };
    resetPostDeliveryStability();
    ensurePostDeliveryMutationGuard();

    postDeliveryGuardInterval = setInterval(() => {
      if (!guardDeliveryVisible(postDeliveryGuardIntent)) {
        resetPostDeliveryStability();
        return;
      }
      const urlClean = guardSanitizeLaunchUrl();
      const composer = guardClearBoundComposer(postDeliveryGuardIntent);
      const clean = urlClean && composer.clean;
      const now = Date.now();

      if (!clean || composer.changed) {
        resetPostDeliveryStability();
        return;
      }

      if (postDeliveryUiDisarmed) {
        if (!currentPostDeliveryUiClean()) resetPostDeliveryStability();
        return;
      }

      if (!postDeliveryStableSince) {
        postDeliveryStableSince = now;
        return;
      }
      if (now - postDeliveryStableSince < POST_DELIVERY_UI_STABLE_MS) return;
      if (postDeliveryAckPending) return;

      postDeliveryAckPending = true;
      const ackEpoch = postDeliveryGuardEpoch;
      guardRecordCleanup(postDeliveryGuardIntent, (response) => {
        postDeliveryAckPending = false;
        if (!response?.ok || ackEpoch !== postDeliveryGuardEpoch) {
          if (!response?.ok) resetPostDeliveryStability();
          return;
        }
        if (!HEX64_RE.test(response.cleanup_token || "")) {
          resetPostDeliveryStability();
          return;
        }
        if (!currentPostDeliveryUiClean()) {
          resetPostDeliveryStability();
          return;
        }
        postDeliveryCleanupToken = response.cleanup_token;
        postDeliveryUiDisarmed = true;
      });
    }, POST_DELIVERY_UI_POLL_MS);

    return postDeliveryGuardInterval !== null;
  }

  function conversationId(urlString) {
    try {
      const path = new URL(urlString).pathname;
      const match = path.match(/^\/c\/([A-Za-z0-9_-]{8,128})(?:\/|$)/);
      return match ? match[1] : null;
    } catch {
      return null;
    }
  }

  globalThis.CAPChatGPTTemporaryPolicy = {
    HEX64_RE,
    HEAD40_RE,
    RESULT_BEGIN,
    RESULT_END,
    parseIntent,
    hasExpectedPrompt,
    exactPromptMatches,
    eligibleComposerEditor,
    findComposerEditor: guardFindComposerEditor,
    personalizationModeFromText,
    singleResultBlockShape,
    hasSingleResultBlock,
    captureAuthorization,
    invalidatePostDeliveryAuthorization,
    armPostDeliveryUiGuard,
    conversationId,
  };
})();