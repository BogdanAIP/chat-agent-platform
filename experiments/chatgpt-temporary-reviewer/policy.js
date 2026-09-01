(() => {
  "use strict";

  const RUN_ID_RE = /^tmprev-[0-9a-f]{32}$/;
  const TOKEN_RE = /^[0-9a-f]{64}$/;
  const MAX_WAIT_MS = 45 * 60 * 1000;
  const STABLE_MS = 8000;

  function parseIntent(urlString) {
    let url;
    try {
      url = new URL(urlString);
    } catch {
      return { enabled: false, reason: "invalid-url" };
    }
    if (url.origin !== "https://chatgpt.com") return { enabled: false, reason: "wrong-origin" };
    if (url.searchParams.get("temporary-chat") !== "true") {
      return { enabled: false, reason: "temporary-chat-flag-missing" };
    }
    if (url.searchParams.get("cap_temp_review") !== "1") {
      return { enabled: false, reason: "not-opted-in" };
    }
    const runId = url.searchParams.get("cap_run_id") || "";
    const token = url.searchParams.get("cap_collector_token") || "";
    const prompt = url.searchParams.get("prompt") || "";
    if (!RUN_ID_RE.test(runId)) return { enabled: false, reason: "invalid-run-id" };
    if (!TOKEN_RE.test(token)) return { enabled: false, reason: "invalid-collector-token" };
    const sentinel = `CAP_TEMP_REVIEW_RUN_ID=${runId}`;
    if (!prompt.includes(sentinel) || !prompt.includes("REVIEW_REQUEST_V1")) {
      return { enabled: false, reason: "prompt-binding-mismatch" };
    }
    return {
      enabled: true,
      runId,
      token,
      prompt,
      sentinel,
      maxWaitMs: MAX_WAIT_MS,
      stableMs: STABLE_MS,
    };
  }

  function attemptKey(runId) {
    return `cap-temp-review:v1:send:${runId}`;
  }

  function captureKey(runId) {
    return `cap-temp-review:v1:capture:${runId}`;
  }

  function hasExpectedPrompt(text, intent) {
    return typeof text === "string" && text.includes(intent.sentinel) && text.includes("REVIEW_REQUEST_V1");
  }

  function resultIdentitySummary(text) {
    if (typeof text !== "string") return { structured: false };
    const required = [
      "REVIEW_RESULT_V1",
      "repository=BogdanAIP/chat-agent-platform",
      "pr_number=142",
      "base_sha=8318a592848cad66bb6d8e56b10b04b646bc9137",
      "head_sha=858dcb7dd065717ea0d59b1e7b931b13a844f8d4",
      "review_skill=code-review",
      "review_skill_version=1.1",
      "review_context=ordinary_chat_fresh",
    ];
    const missing = required.filter((marker) => !text.includes(marker));
    const statusMatch = text.match(/^status=(PASS|FINDINGS|ABSTAIN|STALE)$/m);
    return {
      structured: missing.length === 0 && Boolean(statusMatch),
      missing,
      status: statusMatch?.[1] || null,
    };
  }

  globalThis.CAPTemporaryReviewerPolicy = Object.freeze({
    RUN_ID_RE,
    TOKEN_RE,
    MAX_WAIT_MS,
    STABLE_MS,
    parseIntent,
    attemptKey,
    captureKey,
    hasExpectedPrompt,
    resultIdentitySummary,
  });
})();
