(() => {
  "use strict";

  const policy = globalThis.CAPChatGPTTemporaryPolicy;
  if (!policy) return;
  const executionGeneration = globalThis.CAPChatGPTTemporaryExecutionGeneration || "";
  if (!policy.HEX64_RE.test(executionGeneration)) return;

  const POST_DELIVERY_CLEANUP_TIMEOUT_MS = 10000;
  const STATUS_POLL_MS = 1000;
  const PREFLIGHT_RETRY_MS = 750;
  const PREFLIGHT_MAX_MS = 5 * 60 * 1000;
  const MAX_RECOVERY_CLAIMS = 8;
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

  function normalizeFull(text) {
    return String(text || "").replace(/\u0000/g, "").trim();
  }

  function observedRecoveryClaims() {
    const claims = [];
    const seen = new Set();
    for (const node of document.querySelectorAll('[data-message-author-role="user"]')) {
      const text = normalizeFull(node.innerText || node.textContent || "");
      const delegation = text.match(/(?:^|\n)delegation_id=([0-9a-f]{64})(?:\n|$)/);
      const delivery = text.match(/(?:^|\n)delivery_id=([0-9a-f]{64})(?:\n|$)/);
      const task = text.match(/(?:^|\n)task_sha256=([0-9a-f]{64})(?:\n|$)/);
      if (!delegation || !delivery || !task) continue;
      const key = `${delegation[1]}:${delivery[1]}:${task[1]}`;
      if (seen.has(key)) continue;
      seen.add(key);
      claims.push({
        delegation_id: delegation[1],
        delivery_id: delivery[1],
        task_sha256: task[1],
      });
      if (claims.length >= MAX_RECOVERY_CLAIMS) break;
    }
    return claims;
  }

  function requestResumeIntent() {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage(
        {
          schema_version: 1,
          kind: "resume-intent",
          execution_generation: executionGeneration,
          observed_claims: observedRecoveryClaims(),
        },
        (response) => resolve(response || {
          ok: false,
          enabled: false,
          reason: chrome.runtime.lastError?.message || "no-response",
        }),
      );
    });
  }

  function currentPreflightId() {
    let url;
    try {
      url = new URL(location.href);
    } catch {
      return null;
    }
    if (url.origin !== "https://chatgpt.com" || url.searchParams.get("cap_agent_preflight") !== "1") return null;
    const fragment = new URLSearchParams(url.hash.startsWith("#") ? url.hash.slice(1) : url.hash);
    const value = fragment.get("cap_preflight_id") || "";
    return policy.HEX64_RE.test(value) ? value : null;
  }

  function validatedPreflightNavigation(response) {
    if (!response?.ok || response.status !== "preflight-navigation-ready") return null;
    if (response.execution_generation !== executionGeneration || typeof response.navigate_url !== "string") return null;
    const parsed = policy.parseIntent(response.navigate_url);
    if (!parsed.enabled) return null;
    if (parsed.delegationId !== response.delegation_id || parsed.deliveryId !== response.delivery_id) return null;
    return response.navigate_url;
  }

  function runPreflightUntilNavigation() {
    const startedAt = Date.now();
    let pending = false;
    let timer = null;

    const tick = async () => {
      if (pending) return;
      if (Date.now() - startedAt > PREFLIGHT_MAX_MS) {
        if (timer !== null) clearInterval(timer);
        console.info("[CAP Agent Session] preflight timed out without committed navigation proof");
        return;
      }
      if (currentPreflightId() === null) {
        if (timer !== null) clearInterval(timer);
        return;
      }
      pending = true;
      try {
        const response = await requestResumeIntent();
        const target = validatedPreflightNavigation(response);
        if (!target) return;
        if (timer !== null) clearInterval(timer);
        // The neutral preflight tab is the sole task-navigation owner. replace()
        // avoids creating a second task tab and removes the preflight entry from
        // this tab's forward/back history; restart safety still depends on the
        // ephemeral MV3 live mapping, not on browser-history cleanup.
        location.replace(target);
      } finally {
        pending = false;
      }
    };

    timer = setInterval(() => { void tick(); }, PREFLIGHT_RETRY_MS);
    void tick();
  }

  function recoveredIntent(response) {
    return {
      enabled: true,
      runId: response.run_id,
      delegationId: response.delegation_id,
      deliveryId: response.delivery_id,
      taskSha256: response.task_sha256,
      expectedHead: response.expected_runtime_head,
      promptSha256: response.prompt_sha256,
      prompt: "",
      maxWaitMs: 30 * 60 * 1000,
      deliveryObserveMs: 20000,
      stableMs: 3000,
      recoveredDeliveryState: response.delivery_state,
    };
  }

  async function sha256Text(text) {
    const bytes = new TextEncoder().encode(String(text || ""));
    const digest = await crypto.subtle.digest("SHA-256", bytes);
    return [...new Uint8Array(digest)]
      .map((value) => value.toString(16).padStart(2, "0"))
      .join("");
  }

  function start(intent, recovered) {
    if (!policy.HEAD40_RE.test(intent.expectedHead || "") || !policy.HEX64_RE.test(intent.promptSha256 || "")) return;

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
    let deliveryPostPending = false;
    const deliveryEvidenceRefs = { delivered: "", unknown: "" };
    let postDeliveryCleanupStartedAt = 0;
    let postDeliveryCleanupStableSince = 0;
    let postDeliveryCleanupComplete = false;
    let statusPollPending = false;
    let lastStatusPollAt = 0;
    let finalObservationSentFor = "";
    let recoveryConversationBound = recovered;
    let recoveryConversationBindPending = false;
    let lastRecoveryConversationBindAt = 0;
    const deadline = Date.now() + intent.maxWaitMs;

    function normalize(text) {
      return String(text || "").replace(/\s+/g, " ").trim().slice(0, 500);
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
            expected_runtime_head: intent.expectedHead,
            prompt_sha256: intent.promptSha256,
            execution_generation: executionGeneration,
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

    function canonicalPromptText(text) {
      return String(text ?? "").replace(/\r\n?/g, "\n");
    }

    function findComposerEditor(composer) {
      if (!composer) return null;
      return composer.querySelector("#prompt-textarea") ||
        composer.querySelector('[contenteditable="true"]') ||
        composer.querySelector("textarea");
    }

    function composerPromptText(composer) {
      if (!composer) return null;
      const editor = findComposerEditor(composer);
      if (!editor) return null;
      if (String(editor.tagName || "").toUpperCase() === "TEXTAREA" && typeof editor.value === "string") {
        return canonicalPromptText(editor.value);
      }
      const visibleText = typeof editor.innerText === "string" ? editor.innerText : editor.textContent;
      return visibleText == null ? null : canonicalPromptText(visibleText);
    }

    function exactComposerPromptMatches(composer) {
      if (recovered || typeof intent.prompt !== "string" || !intent.prompt) return false;
      const observed = composerPromptText(composer);
      return observed !== null && policy.exactPromptMatches(observed, intent.prompt);
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
      if (!state.query_present && !state.private_fragment_present) return { clean: true, changed: false };
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
      if (!policy.hasExpectedPrompt(composer.textContent || "", intent)) return { clean: true, changed: false };
      const editor = findComposerEditor(composer);
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
            editor.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "deleteContentBackward", data: null }));
          }
          changed = true;
        }
      } catch {
        return { clean: false, changed };
      }
      return { clean: !policy.hasExpectedPrompt(composer.textContent || "", intent), changed };
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
          const details = { launch_url_clean: launch.clean, composer_clean: composer.clean };
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
      event("post-delivery-cleanup-complete", { launch_url_clean: true, composer_clean: true });
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
      for (const node of document.querySelectorAll('button,[role="button"],[aria-label],[title],[data-testid]')) {
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
      if (recovered || typeof intent.prompt !== "string" || !intent.prompt) return false;
      return conversationTurns("user").some((text) => policy.exactPromptMatches(text, intent.prompt));
    }

    function stopButtonPresent() {
      return Boolean(
        document.querySelector('button[data-testid="stop-button"]') ||
        [...document.querySelectorAll("button")].some((button) => /^(stop|останов)/i.test(normalize(button.getAttribute("aria-label") || button.textContent))),
      );
    }

    function resetCaptureAuthority() {
      captureStarted = false;
      postDeliveryCleanupComplete = false;
      postDeliveryCleanupStableSince = 0;
      policy.invalidatePostDeliveryAuthorization();
    }

    function staleCaptureAuthority(reason) {
      const value = String(reason || "");
      return value.includes("worker capture cleanup token is stale or missing") ||
        value.includes("worker capture preparation token is stale or missing");
    }

    function retryableCaptureTransportFailure(reason) {
      const value = String(reason || "").toLowerCase();
      return value === "no-response" ||
        value.includes("failed to fetch") ||
        value.includes("networkerror") ||
        value.includes("network error") ||
        value.includes("load failed") ||
        value.includes("fetch failed") ||
        value.includes("message port closed") ||
        value.includes("receiving end does not exist");
    }

    function deliveryEvidenceRef(outcome, kind) {
      if (!["delivered", "unknown"].includes(outcome)) return "";
      if (!deliveryEvidenceRefs[outcome]) {
        observationSeq += 1;
        deliveryEvidenceRefs[outcome] = `chatgpt-temporary:delivery:${intent.deliveryId}:${kind}:${observationSeq}`;
      }
      return deliveryEvidenceRefs[outcome];
    }

    async function requestAuthority(composer) {
      if (authorityRequested) return;
      authorityRequested = true;
      if (!recovered) {
        if (!exactComposerPromptMatches(composer)) {
          stop("live-composer-prompt-mismatch-before-authority");
          return;
        }
        const promptDigest = await sha256Text(intent.prompt);
        if (promptDigest !== intent.promptSha256) {
          stop("launch-prompt-digest-mismatch");
          return;
        }
        if (!exactComposerPromptMatches(composer)) {
          stop("live-composer-prompt-changed-before-authority");
          return;
        }
      }
      const temporary = observeTemporaryState(composer);
      if (!temporary.temporary_mode || !temporary.fresh_context || temporary.personalization_disabled !== true || temporary.plugin_markers.length > 0) {
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

    async function bindRecoveryConversation() {
      if (recovered || recoveryConversationBound || recoveryConversationBindPending || !sendAuthorized || !sendClickedAt) return;
      const conversationId = policy.conversationId(location.href);
      if (!conversationId) return;
      const now = Date.now();
      if (now - lastRecoveryConversationBindAt < 500) return;
      lastRecoveryConversationBindAt = now;
      recoveryConversationBindPending = true;
      try {
        const response = await sendMessage("bind-recovery-conversation", {
          task_sha256: intent.taskSha256,
        });
        if (response?.ok && response.bound === true && response.conversation_id === conversationId) {
          recoveryConversationBound = true;
          return;
        }
        const reason = response?.reason || "conversation-binding-unavailable";
        if (["claim-correlation-mismatch", "claim-tab-mismatch", "conversation-binding-mismatch", "conversation-binding-invalid"].includes(reason)) {
          stop("recovery-conversation-binding-rejected", { reason });
        }
      } finally {
        recoveryConversationBindPending = false;
      }
    }

    async function postDelivery(outcome, evidenceRef) {
      if (deliveryPostPending) return false;
      deliveryPostPending = true;
      try {
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
      } finally {
        deliveryPostPending = false;
      }
    }

    async function captureResult(text) {
      if (captureStarted || deliveryState !== "delivered" || !postDeliveryCleanupComplete) return;
      const authorization = policy.captureAuthorization();
      if (!authorization) {
        postDeliveryCleanupComplete = false;
        return;
      }
      captureStarted = true;
      const prepared = await sendMessage("prepare-capture", {
        cleanup_token: authorization.cleanupToken,
      });
      if (!prepared?.ok || !policy.HEX64_RE.test(prepared.capture_token || "")) {
        const reason = prepared?.reason || "capture-preparation-failed";
        if (staleCaptureAuthority(reason)) resetCaptureAuthority();
        else captureStarted = false;
        event("result-capture-failed", { reason });
        return;
      }
      const current = policy.captureAuthorization();
      if (!current || current.cleanupToken !== authorization.cleanupToken) {
        resetCaptureAuthority();
        return;
      }
      const response = await sendMessage("capture", {
        cleanup_token: current.cleanupToken,
        capture_token: prepared.capture_token,
        result_text: text,
      });
      if (response?.ok) {
        stop("result-recorded", { worker_status: response.worker_status || null });
        return;
      }
      const reason = response?.reason || "capture-failed";
      event("result-capture-failed", { reason });
      if (staleCaptureAuthority(reason) || retryableCaptureTransportFailure(reason)) {
        resetCaptureAuthority();
        return;
      }
      captureStarted = false;
      stop("result-capture-failed", { reason });
    }

    async function pollControllerStatus() {
      if (statusPollPending || !sendClickedAt) return;
      const now = Date.now();
      if (now - lastStatusPollAt < STATUS_POLL_MS) return;
      lastStatusPollAt = now;
      statusPollPending = true;
      try {
        const status = await sendMessage("status");
        if (!status?.ok) return;
        if (status.delegation_id !== intent.delegationId || status.delivery_id !== intent.deliveryId) {
          stop("controller-status-correlation-mismatch");
          return;
        }
        if (status.result_state === "recorded") {
          stop("result-recorded", {
            worker_status: status.result_status || null,
            recovered_from_status: true,
          });
          return;
        }
        if (status.result_state !== "open") return;
        if (status.delivery_state === "delivered" && deliveryState !== "delivered") {
          deliveryState = "delivered";
          deliveryOutcomeAt = Date.now();
        } else if (status.delivery_state === "unknown" && deliveryState === "claimed") {
          deliveryState = "unknown";
          deliveryOutcomeAt = Date.now();
        }
        if (deliveryState !== "delivered") return;
        const requestId = status.final_observation_request_id;
        if (!policy.HEX64_RE.test(requestId || "") || requestId === finalObservationSentFor) return;
        const turns = conversationTurns("assistant");
        const last = turns.at(-1) || "";
        const response = await sendMessage("final-observation", {
          request_id: requestId,
          terminal_result_visible: policy.singleResultBlockShape(last),
          worker_generating: stopButtonPresent(),
        });
        if (response?.ok) finalObservationSentFor = requestId;
      } finally {
        statusPollPending = false;
      }
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
        if (!composer || !exactComposerPromptMatches(composer)) return;
        void requestAuthority(composer);
        return;
      }

      if (sendAuthorized && !sendClickedAt) {
        const button = findSendButton();
        if (!buttonReady(button)) return;
        const composer = findComposer(button);
        if (!composer || !exactComposerPromptMatches(composer)) {
          stop("prompt-binding-changed-before-send");
          return;
        }
        sendClickedAt = Date.now();
        event("send-clicked", { at_ms: sendClickedAt });
        button.click();
        return;
      }

      if (!sendClickedAt) return;
      void pollControllerStatus();
      if (!recoveryConversationBound) void bindRecoveryConversation();
      const visibleDelivery = userDeliveryVisible();
      if (visibleDelivery && deliveryState !== "delivered") {
        void postDelivery("delivered", deliveryEvidenceRef("delivered", "visible"));
        return;
      }
      if (!visibleDelivery && deliveryState === "claimed" && Date.now() - sendClickedAt >= intent.deliveryObserveMs && !deliveryOutcomeAt) {
        void postDelivery("unknown", deliveryEvidenceRef("unknown", "ambiguous"));
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
      if (lastAssistantChangedAt && Date.now() - lastAssistantChangedAt >= intent.stableMs) void captureResult(last);
    }

    if (!policy.armPostDeliveryUiGuard(intent)) {
      stop("post-delivery-guard-unavailable");
      return;
    }
    event("adapter-loaded", { href: location.href.slice(0, 2048), recovered, execution_generation: executionGeneration });
    intervalId = setInterval(tick, 500);
    tick();
  }

  const initial = policy.parseIntent(location.href);
  if (initial.enabled) {
    start(initial, false);
    return;
  }

  if (currentPreflightId() !== null) {
    runPreflightUntilNavigation();
    return;
  }

  void requestResumeIntent().then((response) => {
    if (!response?.ok || response.enabled !== true || response.monitor_only !== true) return;
    if (response.execution_generation !== executionGeneration) return;
    if (![response.run_id, response.delegation_id, response.delivery_id, response.task_sha256, response.prompt_sha256].every((value) => policy.HEX64_RE.test(value || ""))) return;
    if (!policy.HEAD40_RE.test(response.expected_runtime_head || "")) return;
    const currentConversationId = policy.conversationId(location.href);
    if (!currentConversationId || response.conversation_id !== currentConversationId) return;
    start(recoveredIntent(response), true);
  });
})();