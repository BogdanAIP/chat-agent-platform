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
  const TEMPORARY_UI_SETTLE_MS = 10000;
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
    let temporaryUiPendingSince = null;
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

    function buttonReady(button) {
      if (!button?.isConnected || !visible(button) || button.disabled || button.getAttribute?.("aria-disabled") === "true") {
        return false;
      }
      for (let current = button; current; current = current.parentElement) {
        if (current.disabled || current.matches?.(":disabled") || current.getAttribute?.("aria-disabled") === "true") {
          return false;
        }
      }
      return true;
    }

    function currentComposerBinding() {
      const editor = policy.findComposerEditor();
      if (!editor) return null;
      const composer = editor.closest?.("form");
      if (!composer || !visible(composer)) return null;
      return { composer, editor };
    }

    function findSendBinding() {
      const current = currentComposerBinding();
      if (!current) return null;
      let buttons = [...document.querySelectorAll('button[data-testid="send-button"]')];
      // Some focused production-behavior fixtures expose querySelector only.
      // In a real DOM querySelectorAll and querySelector cannot disagree here.
      if (buttons.length === 0) {
        const fallback = document.querySelector('button[data-testid="send-button"]');
        if (fallback) buttons = [fallback];
      }
      const eligible = buttons.filter((button) =>
        buttonReady(button) && button.closest?.("form") === current.composer,
      );
      return eligible.length === 1 ? { ...current, button: eligible[0] } : null;
    }

    function canonicalPromptText(text) {
      return String(text ?? "").replace(/\r\n?/g, "\n");
    }

    function findComposerEditor(composer) {
      if (!composer) return null;
      const current = currentComposerBinding();
      return current?.composer === composer ? current.editor : null;
    }

    function contentEditablePromptText(editor) {
      if (!editor) return null;

      // Physical ChatGPT qualification proves one direct <p> per logical
      // prompt line. Use childNodes, not children: Element.children silently
      // omits direct Text/Comment nodes and could therefore project away live
      // composer content. Every direct node must belong to the proven shape.
      const nodes = editor.childNodes == null ? [] : [...editor.childNodes];
      if (nodes.length === 0) return null;

      const lines = [];
      for (const node of nodes) {
        if (
          node?.nodeType !== 1 ||
          String(node.tagName || "").toUpperCase() !== "P" ||
          typeof node.textContent !== "string"
        ) {
          return null;
        }
        lines.push(node.textContent);
      }

      return canonicalPromptText(lines.join("\n"));
    }

    function composerPromptText(composer) {
      if (!composer) return null;
      const editor = findComposerEditor(composer);
      if (!editor) return null;
      if (String(editor.tagName || "").toUpperCase() === "TEXTAREA" && typeof editor.value === "string") {
        return canonicalPromptText(editor.value);
      }
      return contentEditablePromptText(editor);
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
      const current = currentComposerBinding();
      if (!current) return { clean: true, changed: false };
      const { composer, editor } = current;
      if (!policy.hasExpectedPrompt(composer.textContent || "", intent)) return { clean: true, changed: false };
      let changed = false;
      try {
        if (typeof HTMLTextAreaElement !== "undefined" && editor instanceof HTMLTextAreaElement) {
          const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value")?.set;
          if (setter) setter.call(editor, "");
          else editor.value = "";
          editor.dispatchEvent(new Event("input", { bubbles: true }));
          changed = true;
        } else if (editor.getAttribute?.("contenteditable") === "true" || editor.isContentEditable) {
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

    function visibleConversationTurns(role) {
      return [...document.querySelectorAll(`[data-message-author-role="${role}"]`)]
        .filter((node) => visible(node))
        .map((node) => normalizeFull(node.innerText || node.textContent || ""))
        .filter(Boolean);
    }

    function allConversationTurnCount() {
      return document.querySelectorAll('[data-message-author-role="user"],[data-message-author-role="assistant"]').length;
    }

    function temporaryMatches(text) {
      const value = String(text || "");
      return [/temporary chat/i, /temporary/i, /временн(?:ый|ого|ом|ая|ую|ое)/i, /tempor[aä]r/i]
        .some((pattern) => pattern.test(value));
    }

    function attributeEvidence(node, names) {
      if (!node) return "";
      return normalize(names.map((name) => node.getAttribute?.(name)).filter(Boolean).join(" | "));
    }

    function externalTemporaryControlActive(node) {
      if (!node) return false;
      const pressed = String(node.getAttribute?.("aria-pressed") || "").toLowerCase();
      const selected = String(node.getAttribute?.("aria-selected") || "").toLowerCase();
      const current = String(node.getAttribute?.("aria-current") || "").toLowerCase();
      const state = String(node.getAttribute?.("data-state") || "").toLowerCase();
      return pressed === "true" || selected === "true" ||
        (current !== "" && current !== "false") ||
        ["active", "checked", "on", "selected"].includes(state);
    }

    function activeComposerTemporaryEvidence(composer) {
      const editor = findComposerEditor(composer);
      if (!editor) return [];
      const nodes = [editor, composer];
      if (typeof editor.querySelectorAll === "function") {
        nodes.push(...editor.querySelectorAll('[placeholder],[data-placeholder],[aria-label],[title],[data-testid],[data-mode],[data-chat-mode]'));
      }
      const seen = new Set();
      const evidence = [];
      for (const node of nodes) {
        if (!node || seen.has(node)) continue;
        seen.add(node);
        const text = attributeEvidence(node, [
          "placeholder",
          "data-placeholder",
          "aria-label",
          "title",
          "data-testid",
          "data-mode",
          "data-chat-mode",
        ]);
        if (text && temporaryMatches(text)) evidence.push(text);
      }
      return evidence;
    }

    function exactTemporaryPageTitle(text) {
      const value = normalizeFull(text).replace(/\s+/g, " ").trim();
      return [
        /^temporary chat$/i,
        /^временный чат$/i,
        /^tempor[aä]rer chat$/i,
      ].some((pattern) => pattern.test(value));
    }

    function temporaryPolicyCopyScore(text) {
      const value = normalizeFull(text).replace(/\s+/g, " ").trim();
      if (value.length < 20 || value.length > 500) return 0;
      const groups = [
        [/\bmemory\b/i, /памят/i, /erinner/i],
        [/\bplugins?\b/i, /плагин/i],
        [/custom instructions?/i, /пользовательск\w*\s+инструкц/i, /benutzerdefiniert\w*\s+anweis/i],
        [/\bhistory\b/i, /истори/i, /verlauf/i],
      ];
      return groups.filter((patterns) => patterns.some((pattern) => pattern.test(value))).length;
    }

    function activePageTemporaryEvidence(composer) {
      if (!composer || !visible(composer)) return [];
      const root = composer.closest?.('main,[role="main"]');
      if (!root || !visible(root) || typeof root.querySelectorAll !== "function") return [];

      const blockingOverlay = [...document.querySelectorAll('dialog,[role="dialog"],[role="menu"],[role="listbox"]')]
        .some((node) => visible(node));
      if (blockingOverlay) return [];

      const interactiveOrOverlaySelector = [
        "button",
        "a",
        '[role="button"]',
        '[role="menuitem"]',
        '[role="option"]',
        '[role="tab"]',
        '[role="switch"]',
        "dialog",
        '[role="dialog"]',
        '[role="menu"]',
        '[role="listbox"]',
      ].join(",");

      let title = "";
      for (const node of root.querySelectorAll('h1,h2,h3,h4,[role="heading"],div,p,span')) {
        if (!visible(node)) continue;
        if (composer === node || composer.contains?.(node) || node.contains?.(composer)) continue;
        if (node.closest?.(interactiveOrOverlaySelector)) continue;
        const text = normalizeFull(node.innerText || node.textContent || "").replace(/\s+/g, " ").trim();
        if (!exactTemporaryPageTitle(text)) continue;
        title = text;
        break;
      }
      if (!title) return [];

      let policyScore = 0;
      for (const node of root.querySelectorAll("p,div,span")) {
        if (!visible(node)) continue;
        if (composer === node || composer.contains?.(node) || node.contains?.(composer)) continue;
        if (node.closest?.(interactiveOrOverlaySelector)) continue;
        const score = temporaryPolicyCopyScore(node.innerText || node.textContent || "");
        if (score > policyScore) policyScore = score;
        if (policyScore >= 3) break;
      }
      if (policyScore < 3) return [];
      return [`active-temporary-page:${title}:policy-signals=${policyScore}`];
    }

    function observeTemporaryState(composer) {
      const candidates = [
        ...activeComposerTemporaryEvidence(composer),
        ...activePageTemporaryEvidence(composer),
      ];
      const personalizationEvidence = [];
      const personalizationModes = new Set();
      for (const node of document.querySelectorAll('button,[role="button"],[aria-label],[title],[data-testid]')) {
        if (!visible(node)) continue;
        if (composer && (composer === node || composer.contains?.(node) || node.contains?.(composer))) continue;
        const text = candidateText(node);
        if (!text) continue;
        if (temporaryMatches(text) && externalTemporaryControlActive(node)) candidates.push(text);
        const personalizationMode = policy.personalizationModeFromText(text);
        if (personalizationMode !== "unknown") {
          personalizationModes.add(personalizationMode);
          personalizationEvidence.push(text);
        }
      }
      const temporaryMode = candidates.length > 0;
      const freshContext = allConversationTurnCount() === 0;
      const personalizationState = personalizationModes.size === 1 ? [...personalizationModes][0] : "unknown";
      const personalizationDisabled = personalizationState === "non-personalized";
      const closedReadOnlyProfile = temporaryMode && freshContext && personalizationDisabled;
      return {
        temporary_mode: temporaryMode,
        positive_ui_evidence: temporaryMode,
        ui_evidence: candidates.slice(0, 8),
        fresh_context: freshContext,
        personalization_disabled: personalizationDisabled,
        personalization_state: personalizationState,
        personalization_ui_evidence: personalizationEvidence.slice(0, 8),
        // The accepted fresh_readonly_worker_v1 profile is closed by positive
        // active Temporary + fresh + non-personalized provider state. Do not
        // infer plugin safety from an open-ended list of current product brands.
        plugin_markers: closedReadOnlyProfile ? [] : ["closed-profile-not-proven"],
      };
    }

    function userDeliveryVisible() {
      if (recovered || typeof intent.prompt !== "string" || !intent.prompt) return false;
      // Exact prompt equivalence is already proven immediately before the one
      // physical click. The submitted user turn is provider-rendered UI and may
      // include non-message affordances such as "Expand", so post-Send delivery
      // evidence uses bounded correlation markers instead of re-projecting the
      // whole composer string.
      return conversationTurns("user").some((text) => policy.hasExpectedPrompt(text, intent));
    }

    function stopButtonPresent() {
      const primary = document.querySelector('button[data-testid="stop-button"]');
      if (primary && visible(primary)) return true;
      return [...document.querySelectorAll("button")].some((button) =>
        visible(button) && (
          button.getAttribute?.("data-testid") === "stop-button" ||
          /^(stop|останов)/i.test(normalize(button.getAttribute?.("aria-label") || button.textContent))
        ),
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
      const closedProfileProven =
        temporary.temporary_mode &&
        temporary.fresh_context &&
        temporary.personalization_disabled === true &&
        temporary.plugin_markers.length === 0;

      if (!closedProfileProven) {
        // ChatGPT may render the composer and Send before the dedicated
        // Temporary-page evidence reaches the live DOM. Retry only that
        // narrow presentation race. No Send authority exists while pending.
        const retryableTemporaryUiSettle =
          !temporary.temporary_mode &&
          temporary.fresh_context === true &&
          temporary.personalization_disabled === true;

        if (retryableTemporaryUiSettle) {
          const now = Date.now();

          if (temporaryUiPendingSince === null) {
            temporaryUiPendingSince = now;
            event("temporary-ui-not-proven", {
              ...temporary,
              qualification_pending: true,
              settle_ms: TEMPORARY_UI_SETTLE_MS,
            });
          }

          if (now - temporaryUiPendingSince < TEMPORARY_UI_SETTLE_MS) {
            authorityRequested = false;
            return;
          }
        }

        event("temporary-ui-not-proven", {
          ...temporary,
          qualification_pending: false,
        });
        stop("child-qualification-failed", temporary);
        return;
      }

      temporaryUiPendingSince = null;
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
      const captureGuardEpoch = authorization.guardEpoch;
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
      if (
        !current ||
        current.cleanupToken !== authorization.cleanupToken ||
        current.guardEpoch !== captureGuardEpoch
      ) {
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
        const turns = visibleConversationTurns("assistant");
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
        const binding = findSendBinding();
        if (!binding || !exactComposerPromptMatches(binding.composer)) return;
        void requestAuthority(binding.composer);
        return;
      }

      if (sendAuthorized && !sendClickedAt) {
        const binding = findSendBinding();
        if (!binding) return;
        const { button, composer } = binding;
        if (!exactComposerPromptMatches(composer)) {
          stop("prompt-binding-changed-before-send");
          return;
        }
        const currentQualification = observeTemporaryState(composer);
        if (
          !currentQualification.temporary_mode ||
          !currentQualification.fresh_context ||
          currentQualification.personalization_disabled !== true ||
          currentQualification.plugin_markers.length > 0
        ) {
          event("temporary-ui-changed-before-send", currentQualification);
          stop("child-qualification-changed-before-send", currentQualification);
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
      const turns = visibleConversationTurns("assistant");
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