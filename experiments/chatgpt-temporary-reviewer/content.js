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

  function sendToCollector(kind, payload) {
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
      if (patterns.some((pattern) => pattern.test(joined))) {
        candidates.push(joined.slice(0, 500));
      }
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

  function normalizeFull(text) {
    return String(text || "").replace(/\u0000/g, "").trim();
  }

  async function captureFinal(text) {
    if (sessionStorage.getItem(policy.captureKey(intent.runId))) {
      stop("capture-already-recorded");
      return;
    }
    const identity = policy.resultIdentitySummary(text);
    const captureKind = identity.structured ? "structured" : "unstructured";
    const response = await sendToCollector("capture", {
      temporary_state: temporaryEvidence || {},
      capture_kind: captureKind,
      result_text: text.slice(0, 300000),
      diagnostics: {
        identity,
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
      event("timeout", { last_assistant_excerpt: last.slice(0, 8000) });
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
      const button = findSendButton();
      if (!buttonReady(button)) return;
      const composer = findComposer(button);
      if (!composer || !policy.hasExpectedPrompt(composer.textContent || "", intent)) return;

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
      event("send-attempted", { temporary_state: temporaryEvidence });
      button.click();
      return;
    }

    if (stopButtonPresent()) return;
    const turns = assistantTurns();
    const last = turns.at(-1) || "";
    if (!last) return;
    if (last !== lastAssistantText) {
      lastAssistantText = last;
      lastAssistantChangedAt = Date.now();
      return;
    }
    if (lastAssistantChangedAt && Date.now() - lastAssistantChangedAt >= intent.stableMs) {
      void captureFinal(last);
    }
  }

  event("probe-loaded", { href: location.href });
  intervalId = setInterval(tick, 500);
  tick();
})();
