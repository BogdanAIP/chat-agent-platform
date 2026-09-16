(() => {
  "use strict";

  const RUN_ID_PATTERN = /^[A-Za-z0-9._:-]{8,128}$/;
  const DEFAULT_PLUGIN = "Chat Local Bridge Test";
  const MAX_WAIT_MS = 30_000;

  function parseIntent(urlString) {
    let url;
    try {
      url = new URL(urlString);
    } catch {
      return { enabled: false, reason: "invalid-url" };
    }

    if (url.origin !== "https://chatgpt.com") {
      return { enabled: false, reason: "wrong-origin" };
    }

    if (url.searchParams.get("cap_autosend") !== "1") {
      return { enabled: false, reason: "not-opted-in" };
    }

    const runId = url.searchParams.get("cap_run_id") || "";
    if (!RUN_ID_PATTERN.test(runId)) {
      return { enabled: false, reason: "invalid-run-id" };
    }

    const prompt = url.searchParams.get("prompt") || "";
    const sentinel = `CAP_AUTOSEND_RUN_ID=${runId}`;
    if (!prompt.includes(sentinel)) {
      return { enabled: false, reason: "sentinel-mismatch" };
    }

    const plugin = (url.searchParams.get("cap_plugin") || DEFAULT_PLUGIN).trim();
    if (!plugin || plugin.length > 128) {
      return { enabled: false, reason: "invalid-plugin" };
    }

    return {
      enabled: true,
      runId,
      prompt,
      plugin,
      sentinel,
      maxWaitMs: MAX_WAIT_MS,
    };
  }

  function attemptKey(runId) {
    return `cap-autosend:v1:${runId}`;
  }

  function containsRequiredComposerText(text, intent) {
    if (!intent?.enabled || typeof text !== "string") return false;
    return text.includes(intent.plugin) && text.includes(intent.sentinel);
  }

  globalThis.CAPAutoSendPolicy = Object.freeze({
    RUN_ID_PATTERN,
    DEFAULT_PLUGIN,
    MAX_WAIT_MS,
    parseIntent,
    attemptKey,
    containsRequiredComposerText,
  });
})();
