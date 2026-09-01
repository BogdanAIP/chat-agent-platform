(() => {
  "use strict";

  const RUN_ID_RE = /^tmprev-[0-9a-f]{32}$/;
  const TOKEN_RE = /^[0-9a-f]{64}$/;
  const SHA_RE = /^[0-9a-f]{40}$/;
  const MAX_WAIT_MS = 45 * 60 * 1000;
  const STABLE_MS = 3000;

  function normalizeReviewText(text) {
    return String(text || "")
      .replace(/\u0000/g, "")
      .replace(/\\_/g, "_")
      .replace(/\u00a0/g, " ")
      .replace(/\r\n?/g, "\n");
  }

  function requestField(prompt, name) {
    const prefix = `${name}=`;
    for (const line of normalizeReviewText(prompt).split("\n")) {
      if (line.startsWith(prefix)) return line.slice(prefix.length).trim();
    }
    return "";
  }

  function parseIntent(urlString) {
    let url;
    try {
      url = new URL(urlString);
    } catch {
      return { enabled: false, reason: "invalid-url" };
    }
    if (url.origin !== "https://chatgpt.com") return { enabled: false, reason: "wrong-origin" };
    if (url.searchParams.get("temporary-chat") !== "true") return { enabled: false, reason: "temporary-chat-flag-missing" };
    if (url.searchParams.get("cap_temp_review") !== "1") return { enabled: false, reason: "not-opted-in" };

    const runId = url.searchParams.get("cap_run_id") || "";
    const token = url.searchParams.get("cap_collector_token") || "";
    const prompt = url.searchParams.get("prompt") || "";
    if (!RUN_ID_RE.test(runId)) return { enabled: false, reason: "invalid-run-id" };
    if (!TOKEN_RE.test(token)) return { enabled: false, reason: "invalid-collector-token" };

    const sentinel = `CAP_TEMP_REVIEW_RUN_ID=${runId}`;
    const completionMarker = `CAP_TEMP_REVIEW_COMPLETE=${runId}`;
    if (!prompt.includes(sentinel) || !prompt.includes("REVIEW_REQUEST_V1")) return { enabled: false, reason: "prompt-binding-mismatch" };

    const expected = {
      repository: requestField(prompt, "repository"),
      prNumber: requestField(prompt, "pr_number"),
      baseSha: requestField(prompt, "base_sha"),
      headSha: requestField(prompt, "head_sha"),
      reviewSkill: requestField(prompt, "review_skill"),
      reviewSkillVersion: requestField(prompt, "review_skill_version"),
      reviewContext: "ordinary_chat_fresh",
    };
    if (expected.repository !== "BogdanAIP/chat-agent-platform") return { enabled: false, reason: "unexpected-repository" };
    if (!/^\d+$/.test(expected.prNumber)) return { enabled: false, reason: "invalid-pr-number" };
    if (!SHA_RE.test(expected.baseSha) || !SHA_RE.test(expected.headSha)) return { enabled: false, reason: "invalid-review-sha" };
    if (expected.reviewSkill !== "code-review") return { enabled: false, reason: "invalid-review-skill" };

    return {
      enabled: true,
      runId,
      token,
      prompt,
      sentinel,
      completionMarker,
      expected,
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

  function parseResultFields(text) {
    const normalized = normalizeReviewText(text);
    const fields = new Map();
    for (const rawLine of normalized.split("\n")) {
      const line = rawLine.trim();
      const match = line.match(/^([A-Za-z][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$/);
      if (match && !fields.has(match[1])) fields.set(match[1], match[2]);
    }
    return { normalized, fields };
  }

  function resultIdentitySummary(text, intent) {
    if (typeof text !== "string" || !intent || !intent.expected) return { structured: false };
    const { normalized, fields } = parseResultFields(text);
    const expectedFields = new Map([
      ["repository", intent.expected.repository],
      ["pr_number", intent.expected.prNumber],
      ["base_sha", intent.expected.baseSha],
      ["head_sha", intent.expected.headSha],
      ["review_skill", intent.expected.reviewSkill],
      ["review_skill_version", intent.expected.reviewSkillVersion],
      ["review_context", intent.expected.reviewContext],
    ]);
    const missing = [];
    for (const [name, expected] of expectedFields) {
      if (fields.get(name) !== expected) missing.push(`${name}=${expected}`);
    }
    const status = fields.get("status") || null;
    const statusValid = new Set(["PASS", "FINDINGS", "ABSTAIN", "STALE"]).has(status);
    const headerPresent = /(^|\n)\s*REVIEW_RESULT_V1\s*(\n|$)/.test(normalized);
    const completionMarkerAtEnd = normalized.trimEnd().endsWith(intent.completionMarker);
    return {
      structured: headerPresent && missing.length === 0 && statusValid && completionMarkerAtEnd,
      missing,
      status,
      header_present: headerPresent,
      completion_marker_at_end: completionMarkerAtEnd,
    };
  }

  globalThis.CAPTemporaryReviewerPolicy = Object.freeze({
    RUN_ID_RE,
    TOKEN_RE,
    SHA_RE,
    MAX_WAIT_MS,
    STABLE_MS,
    normalizeReviewText,
    parseIntent,
    attemptKey,
    captureKey,
    hasExpectedPrompt,
    resultIdentitySummary,
  });
})();
