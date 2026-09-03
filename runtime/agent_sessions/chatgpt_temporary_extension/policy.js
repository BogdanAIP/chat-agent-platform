(() => {
  "use strict";

  const HEX64_RE = /^[0-9a-f]{64}$/;
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
    "prompt",
  ];
  let postDeliveryUiDisarmed = false;
  let browserGuardRequired = false;
  let postDeliveryGuardIntent = null;
  let postDeliveryGuardInterval = null;
  let postDeliveryStableSince = 0;
  let postDeliveryAckPending = false;
  let postDeliveryGuardEpoch = 0;

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
    const prompt = url.searchParams.get("prompt") || "";
    if (![runId, delegationId, deliveryId, taskSha256].every((value) => HEX64_RE.test(value))) {
      return { enabled: false, reason: "invalid-correlation" };
    }
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
      prompt,
      maxWaitMs: 30 * 60 * 1000,
      deliveryObserveMs: 20000,
      stableMs: 3000,
    };
  }

  function hasExpectedPrompt(text, intent) {
    const value = String(text || "");
    return value.includes("WORKER_TASK_V1") &&
      value.includes(`delegation_id=${intent.delegationId}`) &&
      value.includes(`delivery_id=${intent.deliveryId}`) &&
      value.includes(`task_sha256=${intent.taskSha256}`);
  }

  function personalizationModeFromText(text) {
    const value = String(text || "").replace(/\s+/g, " ").trim();
    if (!value) return "unknown";

    // Temporary Chat gained an explicit personalization choice in August 2026.
    // These are provider UI labels, not a guess from Temporary mode itself.
    // Unknown/ambiguous locales intentionally fail closed in content.js.
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
    const value = String(text || "").trim();
    const beginCount = value.split(RESULT_BEGIN).length - 1;
    const endCount = value.split(RESULT_END).length - 1;
    if (beginCount !== 1 || endCount !== 1) return false;
    const before = value.slice(0, value.indexOf(RESULT_BEGIN)).trim();
    const endIndex = value.indexOf(RESULT_END);
    const after = value.slice(endIndex + RESULT_END.length).trim();
    return !before && !after;
  }

  function resetPostDeliveryStability() {
    postDeliveryUiDisarmed = false;
    postDeliveryStableSince = 0;
    postDeliveryGuardEpoch += 1;
  }

  function hasSingleResultBlock(text) {
    if (!singleResultBlockShape(text)) return false;
    if (typeof document === "undefined" || typeof location === "undefined") return true;
    if (!browserGuardRequired || !postDeliveryGuardIntent || !postDeliveryUiDisarmed) return false;
    if (!currentPostDeliveryUiClean()) {
      resetPostDeliveryStability();
      return false;
    }
    return true;
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

  function guardComposerState(intent) {
    const editor = document.querySelector("#prompt-textarea") ||
      document.querySelector('form [contenteditable="true"],form textarea');
    if (!editor) return { clean: false, editor: null, bound: false };
    const text = guardEditorText(editor);
    return {
      clean: text.trim().length === 0,
      editor,
      bound: hasExpectedPrompt(text, intent),
    };
  }

  function currentPostDeliveryUiClean() {
    if (!browserGuardRequired || !postDeliveryGuardIntent) return false;
    return guardLaunchUrlClean() && guardComposerState(postDeliveryGuardIntent).clean;
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
    const required = [
      `delegation_id=${intent.delegationId}`,
      `delivery_id=${intent.deliveryId}`,
      `task_sha256=${intent.taskSha256}`,
    ];
    return [...document.querySelectorAll('[data-message-author-role="user"]')].some((node) => {
      const text = String(node.innerText || node.textContent || "");
      return required.every((marker) => text.includes(marker));
    });
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
        event: "delivery-visible",
        details: {
          post_delivery_ui_disarmed: true,
          launch_url_clean: true,
          composer_clean: true,
        },
      },
      (response) => callback(Boolean(response?.ok)),
    );
  }

  function sameGuardIntent(left, right) {
    return Boolean(left && right) &&
      left.runId === right.runId &&
      left.delegationId === right.delegationId &&
      left.deliveryId === right.deliveryId &&
      left.taskSha256 === right.taskSha256;
  }

  function validGuardIntent(intent) {
    return Boolean(intent) &&
      [intent.runId, intent.delegationId, intent.deliveryId, intent.taskSha256]
        .every((value) => HEX64_RE.test(value || ""));
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
    };
    resetPostDeliveryStability();

    postDeliveryGuardInterval = setInterval(() => {
      if (!guardDeliveryVisible(postDeliveryGuardIntent)) return;
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
      guardRecordCleanup(postDeliveryGuardIntent, (ok) => {
        postDeliveryAckPending = false;
        if (!ok || ackEpoch !== postDeliveryGuardEpoch) {
          if (!ok) resetPostDeliveryStability();
          return;
        }
        if (!currentPostDeliveryUiClean()) {
          resetPostDeliveryStability();
          return;
        }
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
    RESULT_BEGIN,
    RESULT_END,
    parseIntent,
    hasExpectedPrompt,
    personalizationModeFromText,
    singleResultBlockShape,
    hasSingleResultBlock,
    armPostDeliveryUiGuard,
    conversationId,
  };
})();