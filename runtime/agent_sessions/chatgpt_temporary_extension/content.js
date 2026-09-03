(() => {
  "use strict";

  const policy = globalThis.CAPChatGPTTemporaryPolicy;
  if (!policy) return;

  const POST_DELIVERY_CLEANUP_TIMEOUT_MS = 10000;
  const LAUNCH_QUERY_KEYS = [
    "temporary-chat",
    "cap_agent_delegate",
    "cap_delegation_id",
    "cap_delivery_id",
    "cap_task_sha256",
    "prompt",
  ];

  function requestResumeIntent() {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage(
        { schema_version: 1, kind: "resume-intent" },
        (response) => resolve(response || { ok: false, enabled: false, reason: chrome.runtime.lastError?.message || "no-response" }),
      );
    });
  }

  function recoveredIntent(response) {
    return {
      enabled: true,
      runId: response.run_id,
      delegationId: response.delegation_id,
      deliveryId: response.delivery_id,
      taskSha256: response.task_sha256,
      prompt: "",
      maxWaitMs: 30 * 60 * 1000,
      deliveryObserveMs: 20000,
      stableMs: 3000,
      recoveredDeliveryState: response.delivery_state,
    };
  }

  function start(intent, recovered) {
    let stopped = false;
    let intervalId = null;
    let authorityRequested = recovered;
    let sendAuthorized = false;
    let monitorOnly = recovered;
    let sendClickedAt = recovered ? Date.now() : 0;
    let deliveryState = recovered ? intent.recoveredDeliveryState : "prepared";
    let deliveryOutcomeAt = recovered && deliveryState !== "claimed" ? Date.now() : 0;
    let captureStarted = false;
    let lastAssistantText = "";
    let lastAssistantChangedAt = 0;
    let observationSeq = 0;
    let postDeliveryCleanupStartedAt = 0;
    let postDeliveryCleanupStableSince = 0;
    let postDeliveryCleanupComplete = false;
    const deadline = Date.now() + intent.maxWaitMs;

    function normalize(text) {
      return String(text || "").replace(/\s+/g, " ").trim().slice(0, 500);
    }

    function normalizeFull(text) {
      return String(text || "").replace(/\u0000/g, "").trim();
    }

    function visible(node) {
      if (!node?.isConnected) return false;
      const rect = node.getBoundingClientRect();
      const style = getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && style.visibility !== "hidden" && style.display !== "none";
    }

    function candidateText(node) {
      if (!node) return "";
      return normalize([
        node.getAttribute?.("aria-label"),
        node.getAttribute?.("title"),
        node.getAttribute?.("data-testid"),
        node.textContent,
      ].filter(Boolean).join(" | "));
    }

    function sendMessage(kind, payload = {}) {
      return new Promise((resolve) => {
        chrome.runtime.sendMessage(
          {
            schema_version: 1,
            kind,
            run_id: intent.runId,
            delegation_id: intent.delegationId,
            delivery_id: intent.deliveryId,
            ...payload,
          },
          (response) => resolve(response || { ok: false, reason: chrome.runtime.lastError?.message || "no-response" }),
        );
      });
    }

    function event(name, details = {}) {
      void sendMessage("event", { event: name, details });
    }

    function stop(reason, details = {}) {
      if (stopped) return;
      stopped = true;
      if (intervalId !== null) clearInterval(intervalId);
      event("stopped", { reason, ...details });
      console.info(`[CAP Agent Session] stopped: ${reason}`, details);
    }

    function findSendButton() {
      return document.querySelector('button[data-testid="send-button"]');
    }

    function buttonReady(button) {
      return Boolean(button?.isConnected) && !button.disabled && button.getAttribute("aria-disabled") !== "true";
    }

    function findComposer(button) {
      if (!button) return null;
      return button.closest("form") || button.parentElement;
    }

    function launchIntentState() {
      try {
        const url = new URL(location.href);
        const fragment = new URLSearchParams(url.hash.startsWith("#") ? url.hash.slice(1) : url.hash);
        return {
          url,
          fragment,
          query_present: LAUNCH_QUERY_KEYS.some((key) => url.searchParams.has(key)),
          private_fragment_present: fragment.has("cap_run_id"),
        };
      } catch {
        return null;
      }
    }

    function sanitizeLaunchUrl() {
      const state = launchIntentState();
      if (!state) return { clean: false, changed: false };
      if (!state.query_present && !state.private_fragment_present) {
        return { clean: true, changed: false };
      }

      try {
        for (const key of LAUNCH_QUERY_KEYS) state.url.searchParams.delete(key);
        state.fragment.delete("cap_run_id");
        const fragmentText = state.fragment.toString();
        const nextUrl = `${state.url.pathname}${state.url.search}${fragmentText ? `#${fragmentText}` : ""}`;
        history.replaceState(history.state, "", nextUrl);
      } catch {
        return { clean: false, changed: false };
      }

      const after = launchIntentState();
      return {
        clean: Boolean(after && !after.query_present && !after.private_fragment_present),
        changed: true,
      };
    }

    function clearBoundPromptFromComposer() {
      const button = findSendButton();
      const composer = findComposer(button);
      if (!composer) return { clean: true, changed: false };
      if (!policy.hasExpectedPrompt(composer.textContent || "", intent)) {
        return { clean: true, changed: false };
      }

      const editor = composer.querySelector('#prompt-textarea,[contenteditable="true"],textarea');
      if (!editor) return { clean: false, changed: false };

      let changed = false;
      try {
        if (editor instanceof HTMLTextAreaElement) {
          const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value")?.set;
          if (setter) setter.call(editor, "");
          else editor.value = "";
          editor.dispatchEvent(new Event("input", { bubbles: true }));
          changed = true;
        } else if (editor.getAttribute("contenteditable") === "true" || editor.isContentEditable) {
          editor.focus({ preventScroll: true });
          const selection = window.getSelection();
          const range = document.createRange();
          range.selectNodeContents(editor);
          selection?.removeAllRanges();
          selection?.addRange(range);
          let deleted = false;
          try {
            deleted = typeof document.execCommand === "function" && document.execCommand("delete", false, null) === true;
          } finally {
            selection?.removeAllRanges();
          }
          if (!deleted && policy.hasExpectedPrompt(editor.textContent || "", intent)) {
            editor.replaceChildren();
            editor.dispatchEvent(new InputEvent("input", {
              bubbles: true,
              inputType: "deleteContentBackward",
              data: null,
            }));
          }
          changed = true;
        }
      } catch {
        return { clean: false, changed };
      }

      return {
        clean: !policy.hasExpectedPrompt(composer.textContent || "", intent),
        changed,
      };
    }

    function ensurePostDeliveryCleanup() {
      if (deliveryState !== "delivered") return false;
      if (postDeliveryCleanupComplete) return true;

      const now = Date.now();
      if (!postDeliveryCleanupStartedAt) postDeliveryCleanupStartedAt = now;

      const launch = sanitizeLaunchUrl();
      const composer = clearBoundPromptFromComposer();
      const clean = launch.clean && composer.clean;

      if (!clean) {
        postDeliveryCleanupStableSince = 0;
        if (now - postDeliveryCleanupStartedAt >= POST_DELIVERY_CLEANUP_TIMEOUT_MS) {
          const details = {
            launch_url_clean: launch.clean,
            composer_clean: composer.clean,
          };
          event("post-delivery-cleanup-failed", details);
          stop("post-delivery-cleanup-failed", details);
        }
        return false;
      }

      if (launch.changed || composer.changed) {
        postDeliveryCleanupStableSince = now;
        return false;
      }
      if (!postDeliveryCleanupStableSince) {
        postDeliveryCleanupStableSince = now;
        return false;
      }
      if (now - postDeliveryCleanupStableSince < intent.stableMs) return false;

      postDeliveryCleanupComplete = true;
      event("post-delivery-cleanup-complete", {
        launch_url_clean: true,
        composer_clean: true,
      });
      return true;
    }

    function conversationTurns(role) {
      return [...document.querySelectorAll(`[data-message-author-role="${role}"]`)]
        .map((node) => normalizeFull(node.innerText || node.textContent || ""))
        .filter(Boolean);
    }

    function allConversationTurnCount() {
      return document.querySelectorAll('[data-message-author-role="user"],[data-message-author-role="assistant"]').length;
    }

    function observeTemporaryState(composer) {
      const temporaryPatterns = [/temporary chat/i, /temporary/i, /временн(?:ый|ого|ом|ая|ую|ое)/i, /tempor[aä]r/i];
      const candidates = [];
      const personalizationEvidence = [];
      const personalizationModes = new Set();
      const pluginMarkers = new Set();
      const nodes = document.querySelectorAll('button,[role="button"],[aria-label],[title],[data-testid]');
      for (const node of nodes) {
        if (!visible(node)) continue;
        if (composer && (composer === node || composer.contains(node) || node.contains(composer))) continue;
        const text = candidateText(node);
        if (!text) continue;
        if (temporaryPatterns.some((pattern) => pattern.test(text))) candidates.push(text);
        const personalizationMode = policy.personalizationModeFromText(text);
        if (personalizationMode !== "unknown") {
          personalizationModes.add(personalizationMode);
          personalizationEvidence.push(text);
        }
        for (const marker of ["GitHub", "Chat Local Bridge Test", "Google Drive", "Gmail", "Canva"]) {
          if (text.includes(marker)) pluginMarkers.add(marker);
        }
      }
      const temporaryMode = candidates.length > 0;
      const personalizationState = personalizationModes.size === 1 ? [...personalizationModes][0] : "unknown";
      return {
        temporary_mode: temporaryMode,
        positive_ui_evidence: temporaryMode,
        ui_evidence: candidates.slice(0, 8),
        fresh_context: allConversationTurnCount() === 0,
        personalization_disabled: personalizationState === "non-personalized",
        personalization_state: personalizationState,
        personalization_ui_evidence: personalizationEvidence.slice(0, 8),
        plugin_markers: [...pluginMarkers],
      };
    }

    function userDeliveryVisible() {
      const required = [
        `delegation_id=${intent.delegationId}`,
        `delivery_id=${intent.deliveryId}`,
        `task_sha256=${intent.taskSha256}`,
      ];
      return conversationTurns("user").some((text) => required.every((marker) => text.includes(marker)));
    }

    function stopButtonPresent() {
      return Boolean(
        document.querySelector('button[data-testid="stop-button"]') ||
        [...document.querySelectorAll("button")].some((button) => /^(stop|останов)/i.test(normalize(button.getAttribute("aria-label") || button.textContent))),
      );
    }

    async function requestAuthority(composer) {
      if (authorityRequested) return;
      authorityRequested = true;
      const temporary = observeTemporaryState(composer);
      if (
        !temporary.temporary_mode ||
        !temporary.fresh_context ||
        temporary.personalization_disabled !== true ||
        temporary.plugin_markers.length > 0
      ) {
        event("temporary-ui-not-proven", temporary);
        stop("child-qualification-failed", temporary);
        return;
      }
      observationSeq += 1;
      const response = await sendMessage("authorize-send", {
        task_sha256: intent.taskSha256,
        temporary_mode: temporary.temporary_mode,
        fresh_context: temporary.fresh_context,
        personalization_disabled: temporary.personalization_disabled,
        plugin_markers: temporary.plugin_markers,
        conversation_id: policy.conversationId(location.href),
        observation_seq: observationSeq,
      });
      if (!response?.ok) {
        event("browser-claim-failed", { reason: response?.reason || "authority-unavailable" });
        stop("send-authority-unavailable", { reason: response?.reason || "authority-unavailable" });
        return;
      }
      if (response.send_authorized === true) {
        sendAuthorized = true;
        deliveryState = response.delivery_state || "claimed";
        event("browser-claim-committed", { delivery_state: deliveryState });
        return;
      }
      if (response.monitor_only === true) {
        monitorOnly = true;
        deliveryState = response.delivery_state || "unknown";
        sendClickedAt = Date.now();
        deliveryOutcomeAt = deliveryState === "claimed" ? 0 : Date.now();
        event("browser-claim-committed", { delivery_state: deliveryState, monitor_only: true });
        return;
      }
      event("local-send-authority-denied", { reason: response.reason || "denied", delivery_state: response.delivery_state || null });
      stop("local-send-authority-denied");
    }

    async function postDelivery(outcome, evidenceRef) {
      const response = await sendMessage("delivery", {
        task_sha256: intent.taskSha256,
        outcome,
        evidence_ref: evidenceRef,
      });
      if (!response?.ok) return false;
      deliveryState = response.delivery_state || outcome;
      deliveryOutcomeAt = Date.now();
      event(outcome === "delivered" ? "delivery-visible" : "delivery-ambiguous", {
        delivery_state: deliveryState,
        evidence_ref: evidenceRef,
      });
      return true;
    }

    async function captureResult(text) {
      if (captureStarted || deliveryState !== "delivered" || !postDeliveryCleanupComplete) return;
      captureStarted = true;
      const response = await sendMessage("capture", { result_text: text });
      if (response?.ok) {
        stop("result-recorded", { worker_status: response.worker_status || null });
        return;
      }
      captureStarted = false;
      event("result-capture-failed", { reason: response?.reason || "capture-failed" });
      stop("result-capture-failed", { reason: response?.reason || "capture-failed" });
    }

    function tick() {
      if (stopped) return;
      if (Date.now() > deadline) {
        event("timeout", { delivery_state: deliveryState, send_clicked: sendClickedAt > 0, monitor_only: monitorOnly });
        stop("timeout", { delivery_state: deliveryState });
        return;
      }
      if (location.origin !== "https://chatgpt.com") {
        stop("origin-changed");
        return;
      }

      if (!sendAuthorized && !monitorOnly && !authorityRequested) {
        const button = findSendButton();
        if (!buttonReady(button)) return;
        const composer = findComposer(button);
        if (!composer || !policy.hasExpectedPrompt(composer.textContent || "", intent)) return;
        void requestAuthority(composer);
        return;
      }

      if (sendAuthorized && !sendClickedAt) {
        const button = findSendButton();
        if (!buttonReady(button)) return;
        const composer = findComposer(button);
        if (!composer || !policy.hasExpectedPrompt(composer.textContent || "", intent)) {
          stop("prompt-binding-changed-before-send");
          return;
        }
        sendClickedAt = Date.now();
        event("send-clicked", { at_ms: sendClickedAt });
        button.click();
        return;
      }

      if (!sendClickedAt) return;

      const visibleDelivery = userDeliveryVisible();
      if (visibleDelivery && deliveryState !== "delivered") {
        observationSeq += 1;
        void postDelivery(
          "delivered",
          `chatgpt-temporary:delivery:${intent.deliveryId}:visible:${observationSeq}`,
        );
        return;
      }
      if (!visibleDelivery && deliveryState === "claimed" && Date.now() - sendClickedAt >= intent.deliveryObserveMs && !deliveryOutcomeAt) {
        observationSeq += 1;
        void postDelivery(
          "unknown",
          `chatgpt-temporary:delivery:${intent.deliveryId}:ambiguous:${observationSeq}`,
        );
        return;
      }

      if (deliveryState !== "delivered") return;
      if (!ensurePostDeliveryCleanup()) return;
      if (stopButtonPresent()) return;
      const turns = conversationTurns("assistant");
      const last = turns.at(-1) || "";
      if (!last) return;
      if (last !== lastAssistantText) {
        lastAssistantText = last;
        lastAssistantChangedAt = Date.now();
        return;
      }
      if (!policy.hasSingleResultBlock(last)) return;
      if (lastAssistantChangedAt && Date.now() - lastAssistantChangedAt >= intent.stableMs) {
        void captureResult(last);
      }
    }

    event("adapter-loaded", { href: location.href.slice(0, 2048), recovered });
    intervalId = setInterval(tick, 500);
    tick();
  }

  const initial = policy.parseIntent(location.href);
  if (initial.enabled) {
    start(initial, false);
    return;
  }

  void requestResumeIntent().then((response) => {
    if (!response?.ok || response.enabled !== true || response.monitor_only !== true) return;
    if (![response.run_id, response.delegation_id, response.delivery_id, response.task_sha256].every((value) => policy.HEX64_RE.test(value || ""))) return;
    start(recoveredIntent(response), true);
  });
})();