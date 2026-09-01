(() => {
  "use strict";

  const HEX64_RE = /^[0-9a-f]{64}$/;
  const RESULT_BEGIN = "CAP_WORKER_RESULT_V1_BEGIN";
  const RESULT_END = "CAP_WORKER_RESULT_V1_END";

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

  function hasSingleResultBlock(text) {
    const value = String(text || "").trim();
    const beginCount = value.split(RESULT_BEGIN).length - 1;
    const endCount = value.split(RESULT_END).length - 1;
    if (beginCount !== 1 || endCount !== 1) return false;
    const before = value.slice(0, value.indexOf(RESULT_BEGIN)).trim();
    const endIndex = value.indexOf(RESULT_END);
    const after = value.slice(endIndex + RESULT_END.length).trim();
    return !before && !after;
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
    hasSingleResultBlock,
    conversationId,
  };
})();
