(() => {
  "use strict";

  const policy = globalThis.CAPTemporaryReviewerPolicy;
  if (!policy) return;
  const intent = policy.parseIntent(location.href);
  if (!intent.enabled) return;

  const deadline = Date.now() + intent.maxWaitMs;
  let stopped = false;
  let intervalId = null;
  let lastAssistantText = "";
  let lastAssistantChangedAt = 0;
  let sendAttemptedAt = 0;
  let temporaryEvidence = null;
  let bundleInjected = !intent.bundleMode;
  let bundleLoading = false;
  let bundleFailure = null;
  const webActivityEvidence = new Set();

  function sendToCollector(kind, payload = {}) {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage(
        {
          schema_version: 1,
          kind,
          run_id: intent.runId,
          token: intent.token,
          ...payload,
        },
        (response) => resolve(response || { ok: false, reason: chrome.runtime.lastError?.message || "no-response" }),
      );
    });
  }

  function event(name, details = {}) {
    void sendToCollector("event", { event: name, details });
  }

  function stop(reason, details = {}) {
    if (stopped) return;
    stopped = true;
    if (intervalId !== null) clearInterval(intervalId);
    console.info(`[CAP Temporary Reviewer] stopped: ${reason}`, details);
    event("stopped", { reason, ...details });
  }

  function findSendButton() {
    return document.querySelector('button[data-testid="send-button"]');
  }

  function findPromptEditor() {
    return document.querySelector('#prompt-textarea') ||
      document.querySelector('textarea[placeholder]') ||
      document.querySelector('[contenteditable="true"][data-placeholder]') ||
      document.querySelector('[contenteditable="true"]');
  }

  function findComposer(button) {
    if (!button) return null;
    const form = button.closest("form");
    if (form) return form;
    let node = button.parentElement;
    for (let depth = 0; node && depth < 8; depth += 1, node = node.parentElement) {
      if (policy.hasExpectedPrompt(node.textContent || "", intent)) return node;
    }
    return null;
  }

  function buttonReady(button) {
    return Boolean(button?.isConnected) && !button.disabled && button.getAttribute("aria-disabled") !== "true";
  }

  function normalize(text) {
    return String(text || "").replace(/\s+/g, " ").trim().slice(0, 300);
  }

  function normalizeFull(text) {
    return String(text || "").replace(/\u0000/g, "").trim();
  }

  function editorText(editor) {
    if (!editor) return "";
    if (typeof editor.value === "string") return editor.value;
    return editor.innerText || editor.textContent || "";
  }

  async function sha256Hex(text) {
    const bytes = new TextEncoder().encode(text);
    const digest = await crypto.subtle.digest("SHA-256", bytes);
    return [...new Uint8Array(digest)].map((value) => value.toString(16).padStart(2, "0")).join("");
  }

  function appendTextToEditor(editor, appendix) {
    if (!editor) return false;
    const before = editorText(editor);
    const addition = `\n\n${appendix}`;
    editor.focus();

    if (typeof editor.value === "string") {
      const descriptor = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(editor), "value");
      if (descriptor?.set) descriptor.set.call(editor, before + addition);
      else editor.value = before + addition;
      editor.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText", data: addition }));
      editor.dispatchEvent(new Event("change", { bubbles: true }));
    } else {
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(editor);
      range.collapse(false);
      selection?.removeAllRanges();
      selection?.addRange(range);
      const inserted = document.execCommand("insertText", false, addition);
      if (!inserted) {
        editor.textContent = before + addition;
        editor.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText", data: addition }));
      }
    }
    return editorText(editor).includes(`bundle_nonce=${intent.bundleNonce}`) &&
      editorText(editor).includes("REVIEW_EVIDENCE_BUNDLE_V1");
  }

  async function loadAndInjectBundle() {
    if (!intent.bundleMode || bundleInjected || bundleLoading || bundleFailure) return;
    bundleLoading = true;
    try {
      const response = await sendToCollector("bundle");
      if (!response?.ok || typeof response.text !== "string") {
        throw new Error(response?.reason || `bundle-fetch-status-${response?.status || "unknown"}`);
      }
      const digest = await sha256Hex(response.text);
      if (digest !== intent.bundleSha256) {
        throw new Error(`bundle-sha256-mismatch:${digest}`);
      }
      if (!response.text.includes(`bundle_nonce=${intent.bundleNonce}`) || !response.text.includes("REVIEW_EVIDENCE_BUNDLE_V1")) {
        throw new Error("bundle-content-binding-mismatch");
      }
      event("bundle-fetched", { bytes: new TextEncoder().encode(response.text).length, sha256: digest });
      const editor = findPromptEditor();
      if (!editor) throw new Error("prompt-editor-not-found");
      const appendix = [
        "----- BEGIN PRIVATE READ-ONLY EVIDENCE BUNDLE -----",
        response.text,
        "----- END PRIVATE READ-ONLY EVIDENCE BUNDLE -----",
      ].join("\n");
      if (!appendTextToEditor(editor, appendix)) throw new Error("bundle-editor-verification-failed");
      bundleInjected = true;
      event("bundle-injected", { sha256: digest, bundle_nonce_bound: true });
    } catch (error) {
      bundleFailure = error?.message || "bundle-injection-failed";
      event("bundle-injection-failed", { reason: bundleFailure });
    } finally {
      bundleLoading = false;
    }
  }

  function observeTemporaryState(composer) {
    const patterns = [/temporary chat/i, /temporary/i, /временн(?:ый|ого|ом|ая|ую|ое)/i];
    const candidates = [];
    const nodes = document.querySelectorAll('button,[role="button"],[aria-label],[title],[data-testid]');
    for (const node of nodes) {
      if (!node.isConnected) continue;
      if (composer && (composer === node || composer.contains(node) || node.contains(composer))) continue;
      const pieces = [
        node.getAttribute("aria-label"),
        node.getAttribute("title"),
        node.getAttribute("data-testid"),
        node.textContent,
      ].map(normalize).filter(Boolean);
      const joined = pieces.join(" | ");
      if (patterns.some((pattern) => pattern.test(joined))) candidates.push(joined.slice(0, 500));
    }
    const bodyText = document.body?.innerText || "";
    const pluginMarkers = ["GitHub", "Chat Local Bridge Test"].filter((marker) => bodyText.includes(marker));
    return {
      url_temporary_flag: new URL(location.href).searchParams.get("temporary-chat") === "true",
      positive_ui_evidence: candidates.length > 0,
      ui_evidence: candidates.slice(0, 8),
      visible_plugin_markers: pluginMarkers,
    };
  }

  function observeWebActivity() {
    if (!intent.bundleMode || !sendAttemptedAt) return;
    const patterns = [
      /search(?:ed|ing)? the web/i,
      /searched\s+\d+\s+sites?/i,
      /search performed/i,
      /поиск выполнен/i,
      /поиск в интернете/i,
      /выполнен поиск/i,
    ];
    const nodes = document.querySelectorAll('button,[role="button"],summary,[aria-label],[data-testid]');
    for (const node of nodes) {
      const joined = normalize([
        node.getAttribute("aria-label"),
        node.getAttribute("data-testid"),
        node.textContent,
      ].filter(Boolean).join(" | "));
      if (joined && patterns.some((pattern) => pattern.test(joined))) webActivityEvidence.add(joined.slice(0, 300));
    }
  }

  function stopButtonPresent() {
    return Boolean(
      document.querySelector('button[data-testid="stop-button"]') ||
      [...document.querySelectorAll("button")].some((button) => /^(stop|останов)/i.test(normalize(button.getAttribute("aria-label") || button.textContent))),
    );
  }

  function assistantTurns() {
    const direct = [...document.querySelectorAll('[data-message-author-role="assistant"]')]
      .map((node) => normalizeFull(node.innerText || node.textContent || ""))
      .filter(Boolean);
    if (direct.length) return direct;

    const articles = [...document.querySelectorAll('article[data-testid^="conversation-turn"]')];
    return articles
      .map((article) => {
        const assistant = article.querySelector('[data-message-author-role="assistant"]');
        return assistant ? normalizeFull(assistant.innerText || assistant.textContent || "") : "";
      })
      .filter(Boolean);
  }

  function hasTerminalMarker(text) {
    return normalizeFull(text).endsWith(intent.completionMarker);
  }

  async function captureFinal(text) {
    if (sessionStorage.getItem(policy.captureKey(intent.runId))) {
      stop("capture-already-recorded");
      return;
    }
    if (!hasTerminalMarker(text)) return;

    const identity = policy.resultIdentitySummary(text, intent);
    if (intent.bundleMode && webActivityEvidence.size > 0) {
      identity.structured = false;
      identity.visible_web_activity = [...webActivityEvidence];
      identity.missing = [...(identity.missing || []), "visible_web_activity=none"];
    }
    const captureKind = identity.structured ? "structured" : "unstructured";
    const response = await sendToCollector("capture", {
      temporary_state: temporaryEvidence || {},
      capture_kind: captureKind,
      result_text: text.slice(0, 300000),
      diagnostics: {
        identity,
        bundle_mode: intent.bundleMode,
        bundle_injected: bundleInjected,
        visible_web_activity: [...webActivityEvidence],
        href: location.href,
        send_attempted_at_ms: sendAttemptedAt,
        captured_at: new Date().toISOString(),
      },
    });
    if (response?.ok) {
      sessionStorage.setItem(policy.captureKey(intent.runId), JSON.stringify({ at: new Date().toISOString(), captureKind }));
      stop("result-captured", { capture_kind: captureKind, status: identity.status });
    } else {
      event("capture-upload-failed", { response });
    }
  }

  function tick() {
    if (stopped) return;
    if (Date.now() > deadline) {
      const turns = assistantTurns();
      const last = turns.at(-1) || "";
      event("timeout", {
        terminal_marker_seen: hasTerminalMarker(last),
        bundle_injected: bundleInjected,
        bundle_failure: bundleFailure,
        last_assistant_excerpt: last.slice(-8000),
      });
      stop("timeout");
      return;
    }

    const current = policy.parseIntent(location.href);
    if (!current.enabled || current.runId !== intent.runId) {
      stop("url-contract-changed", { reason: current.reason || "run-id-changed" });
      return;
    }

    if (!sendAttemptedAt) {
      if (sessionStorage.getItem(policy.attemptKey(intent.runId))) {
        sendAttemptedAt = Date.now();
        return;
      }

      if (intent.bundleMode && !bundleInjected) {
        if (bundleFailure) {
          stop("bundle-injection-failed", { reason: bundleFailure });
          return;
        }
        void loadAndInjectBundle();
        return;
      }

      const button = findSendButton();
      if (!buttonReady(button)) return;
      const composer = findComposer(button);
      if (!composer || !policy.hasExpectedPrompt(composer.textContent || "", intent)) return;
      if (intent.bundleMode && !composer.textContent.includes(`bundle_nonce=${intent.bundleNonce}`)) return;

      temporaryEvidence = observeTemporaryState(composer);
      if (!temporaryEvidence.positive_ui_evidence) {
        event("temporary-ui-not-proven", temporaryEvidence);
        return;
      }

      sessionStorage.setItem(
        policy.attemptKey(intent.runId),
        JSON.stringify({ state: "attempted", at: new Date().toISOString(), href: location.href }),
      );
      sendAttemptedAt = Date.now();
      event("send-attempted", { temporary_state: temporaryEvidence, bundle_mode: intent.bundleMode });
      button.click();
      return;
    }

    observeWebActivity();
    if (stopButtonPresent()) return;
    const turns = assistantTurns();
    const last = turns.at(-1) || "";
    if (!last) return;
    if (last !== lastAssistantText) {
      lastAssistantText = last;
      lastAssistantChangedAt = Date.now();
      return;
    }
    if (!hasTerminalMarker(last)) return;
    if (lastAssistantChangedAt && Date.now() - lastAssistantChangedAt >= intent.stableMs) {
      void captureFinal(last);
    }
  }

  event("probe-loaded", { href: location.href, bundle_mode: intent.bundleMode });
  intervalId = setInterval(tick, 500);
  tick();
})();
