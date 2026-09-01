"use strict";

const RUN_ID_RE = /^tmprev-[0-9a-f]{32}$/;
const TOKEN_RE = /^[0-9a-f]{64}$/;
const COLLECTOR_ORIGIN = "http://127.0.0.1:3077";

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  const senderUrl = sender?.url || sender?.tab?.url || "";
  let origin;
  try {
    origin = new URL(senderUrl).origin;
  } catch {
    sendResponse({ ok: false, reason: "invalid-sender-url" });
    return false;
  }
  if (origin !== "https://chatgpt.com") {
    sendResponse({ ok: false, reason: "wrong-sender-origin" });
    return false;
  }
  if (!message || message.schema_version !== 1) {
    sendResponse({ ok: false, reason: "invalid-message-schema" });
    return false;
  }
  if (!RUN_ID_RE.test(message.run_id || "") || !TOKEN_RE.test(message.token || "")) {
    sendResponse({ ok: false, reason: "invalid-correlation" });
    return false;
  }
  if (!new Set(["event", "capture", "bundle"]).has(message.kind)) {
    sendResponse({ ok: false, reason: "invalid-kind" });
    return false;
  }

  if (message.kind === "bundle") {
    fetch(`${COLLECTOR_ORIGIN}/bundle`, {
      method: "GET",
      headers: { "X-CAP-Collector-Token": message.token },
      cache: "no-store",
    })
      .then(async (response) => {
        const text = await response.text();
        sendResponse({ ok: response.ok, status: response.status, text });
      })
      .catch((error) => sendResponse({ ok: false, reason: `collector-unreachable:${error?.name || "Error"}` }));
    return true;
  }

  const endpoint = `${COLLECTOR_ORIGIN}/${message.kind}`;
  const body = message.kind === "event"
    ? {
        schema_version: 1,
        run_id: message.run_id,
        event: message.event,
        details: message.details || {},
      }
    : {
        schema_version: 1,
        run_id: message.run_id,
        temporary_state: message.temporary_state || {},
        capture_kind: message.capture_kind,
        result_text: message.result_text,
        diagnostics: message.diagnostics || {},
      };

  fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CAP-Collector-Token": message.token,
    },
    body: JSON.stringify(body),
  })
    .then(async (response) => {
      const text = await response.text();
      sendResponse({ ok: response.ok, status: response.status, body: text.slice(0, 1024) });
    })
    .catch((error) => sendResponse({ ok: false, reason: `collector-unreachable:${error?.name || "Error"}` }));
  return true;
});
