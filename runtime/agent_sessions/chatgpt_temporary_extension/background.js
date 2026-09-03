importScripts("execution_generation.js");
"use strict";

const DB_NAME = "cap-agent-delegation-v1";
const DB_VERSION = 1;
const CLAIM_STORE = "send_claims";
const CONTROLLER_ORIGIN = "http://127.0.0.1:3078";
const HEX64_RE = /^[0-9a-f]{64}$/;
const HEAD40_RE = /^[0-9a-f]{40}$/;
const EXECUTION_GENERATION = globalThis.CAPChatGPTTemporaryExecutionGeneration || "";
const RUNTIME_ASSETS = ["manifest.json", "execution_generation.js", "policy.js", "background.js", "content.js"];

function initializeClaimDb() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(CLAIM_STORE)) db.createObjectStore(CLAIM_STORE);
    };
    request.onerror = () => reject(request.error || new Error("claim-db-init-failed"));
    request.onsuccess = () => {
      const db = request.result;
      const valid = db.version === DB_VERSION && db.objectStoreNames.contains(CLAIM_STORE);
      db.close();
      valid ? resolve(true) : reject(new Error("claim-db-schema-invalid"));
    };
  });
}

function openExistingClaimDb() {
  return new Promise((resolve, reject) => {
    let attemptedUpgrade = false;
    const request = indexedDB.open(DB_NAME);
    request.onupgradeneeded = () => {
      attemptedUpgrade = true;
      request.transaction?.abort();
    };
    request.onerror = () => reject(new Error(attemptedUpgrade ? "claim-db-schema-missing" : "claim-db-open-failed"));
    request.onsuccess = () => {
      const db = request.result;
      if (db.version !== DB_VERSION || !db.objectStoreNames.contains(CLAIM_STORE)) {
        db.close();
        reject(new Error("claim-db-schema-invalid"));
        return;
      }
      resolve(db);
    };
  });
}

async function sha256Hex(buffer) {
  const digest = await crypto.subtle.digest("SHA-256", buffer);
  return [...new Uint8Array(digest)].map((value) => value.toString(16).padStart(2, "0")).join("");
}

async function runtimeAttestation() {
  if (!HEX64_RE.test(EXECUTION_GENERATION)) throw new Error("execution-generation-invalid");
  const assets = {};
  for (const name of RUNTIME_ASSETS) {
    const response = await fetch(chrome.runtime.getURL(name), { cache: "no-store" });
    if (!response.ok) throw new Error(`runtime-asset-unavailable:${name}:${response.status}`);
    assets[name] = await sha256Hex(await response.arrayBuffer());
  }
  return {
    schema_version: 1,
    adapter_id: "chatgpt-temporary",
    execution_generation: EXECUTION_GENERATION,
    assets,
  };
}

async function claimBrowserSend(message) {
  if (!HEX64_RE.test(message.task_sha256 || "")) throw new Error("invalid-task-correlation");
  if (!HEAD40_RE.test(message.expected_runtime_head || "")) throw new Error("invalid-head-correlation");
  if (!HEX64_RE.test(message.prompt_sha256 || "")) throw new Error("invalid-prompt-correlation");
  const db = await openExistingClaimDb();
  return await new Promise((resolve, reject) => {
    let constraint = false;
    let finished = false;
    const finish = (value, error) => {
      if (finished) return;
      finished = true;
      db.close();
      if (error) reject(error);
      else resolve(value);
    };
    let transaction;
    try {
      transaction = db.transaction(CLAIM_STORE, "readwrite");
      const store = transaction.objectStore(CLAIM_STORE);
      const request = store.add(
        {
          schema_version: 1,
          run_id: message.run_id,
          delegation_id: message.delegation_id,
          delivery_id: message.delivery_id,
          task_sha256: message.task_sha256,
          expected_runtime_head: message.expected_runtime_head,
          prompt_sha256: message.prompt_sha256,
          claimed_at: new Date().toISOString(),
        },
        message.delivery_id,
      );
      request.onerror = () => {
        if (request.error?.name === "ConstraintError") constraint = true;
      };
    } catch (error) {
      finish(null, error);
      return;
    }
    transaction.oncomplete = () => finish({ granted: true, reason: "committed" }, null);
    transaction.onabort = () => {
      if (constraint) finish({ granted: false, reason: "already-claimed" }, null);
      else finish(null, transaction.error || new Error("claim-transaction-aborted"));
    };
    transaction.onerror = () => {
      if (!constraint) finish(null, transaction.error || new Error("claim-transaction-failed"));
    };
  });
}

async function claimRecordByDelivery(deliveryId) {
  const db = await openExistingClaimDb();
  return await new Promise((resolve, reject) => {
    let transaction;
    try {
      transaction = db.transaction(CLAIM_STORE, "readonly");
      const request = transaction.objectStore(CLAIM_STORE).get(deliveryId);
      request.onerror = () => reject(request.error || new Error("claim-read-failed"));
      request.onsuccess = () => resolve(request.result || null);
      transaction.oncomplete = () => db.close();
      transaction.onabort = () => {
        db.close();
        reject(transaction.error || new Error("claim-read-aborted"));
      };
    } catch (error) {
      db.close();
      reject(error);
    }
  });
}

async function claimRecordsForRecovery() {
  const db = await openExistingClaimDb();
  return await new Promise((resolve, reject) => {
    let transaction;
    try {
      transaction = db.transaction(CLAIM_STORE, "readonly");
      const request = transaction.objectStore(CLAIM_STORE).getAll();
      request.onerror = () => reject(request.error || new Error("claim-read-failed"));
      request.onsuccess = () => resolve(Array.isArray(request.result) ? request.result : []);
      transaction.oncomplete = () => db.close();
      transaction.onabort = () => {
        db.close();
        reject(transaction.error || new Error("claim-read-aborted"));
      };
    } catch (error) {
      db.close();
      reject(error);
    }
  });
}

function validCommon(message) {
  return message &&
    message.schema_version === 1 &&
    message.execution_generation === EXECUTION_GENERATION &&
    HEX64_RE.test(EXECUTION_GENERATION) &&
    HEX64_RE.test(message.run_id || "") &&
    HEX64_RE.test(message.delegation_id || "") &&
    HEX64_RE.test(message.delivery_id || "") &&
    HEAD40_RE.test(message.expected_runtime_head || "") &&
    HEX64_RE.test(message.prompt_sha256 || "");
}

function validClaimRecord(record) {
  return record &&
    record.schema_version === 1 &&
    HEX64_RE.test(record.run_id || "") &&
    HEX64_RE.test(record.delegation_id || "") &&
    HEX64_RE.test(record.delivery_id || "") &&
    HEX64_RE.test(record.task_sha256 || "") &&
    HEAD40_RE.test(record.expected_runtime_head || "") &&
    HEX64_RE.test(record.prompt_sha256 || "");
}

function exactClaimMatches(record, message) {
  return validClaimRecord(record) &&
    record.run_id === message.run_id &&
    record.delegation_id === message.delegation_id &&
    record.delivery_id === message.delivery_id &&
    record.task_sha256 === message.task_sha256 &&
    record.expected_runtime_head === message.expected_runtime_head &&
    record.prompt_sha256 === message.prompt_sha256;
}

function validObservedClaim(value) {
  return value &&
    HEX64_RE.test(value.delegation_id || "") &&
    HEX64_RE.test(value.delivery_id || "") &&
    HEX64_RE.test(value.task_sha256 || "");
}

function observedClaimMatches(record, observed) {
  return validClaimRecord(record) && validObservedClaim(observed) &&
    record.delegation_id === observed.delegation_id &&
    record.delivery_id === observed.delivery_id &&
    record.task_sha256 === observed.task_sha256;
}

function senderTab(sender) {
  const senderUrl = sender?.url || sender?.tab?.url || "";
  let origin;
  try {
    origin = new URL(senderUrl).origin;
  } catch {
    return null;
  }
  if (origin !== "https://chatgpt.com" || !Number.isInteger(sender?.tab?.id)) return null;
  return sender.tab.id;
}

async function controllerPost(message, path, body) {
  const response = await fetch(`${CONTROLLER_ORIGIN}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CAP-Agent-Token": message.run_id,
    },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  const value = await response.json().catch(() => ({ status: "invalid-controller-response" }));
  if (!response.ok) throw new Error(`controller-${response.status}:${value.reason || value.status || "rejected"}`);
  return value;
}

async function controllerStatus(message) {
  const response = await fetch(`${CONTROLLER_ORIGIN}/status`, {
    method: "GET",
    headers: { "X-CAP-Agent-Token": message.run_id },
    cache: "no-store",
  });
  const value = await response.json().catch(() => ({ status: "invalid-controller-response" }));
  if (!response.ok) throw new Error(`controller-${response.status}:${value.reason || value.status || "rejected"}`);
  return value;
}

function childEvidence(message, tabId) {
  return {
    schema_version: 1,
    adapter_id: "chatgpt-temporary",
    run_id: message.run_id,
    temporary_mode: message.temporary_mode === true,
    fresh_context: message.fresh_context === true,
    personalization_disabled: message.personalization_disabled === true,
    plugin_markers: Array.isArray(message.plugin_markers) ? message.plugin_markers.slice(0, 8) : ["invalid"],
    session_id: `chrome-tab:${tabId}`,
    conversation_id: typeof message.conversation_id === "string" && message.conversation_id ? message.conversation_id : null,
    observation_ref: `chatgpt-temporary:tab:${tabId}:pre-send:${Number(message.observation_seq) || 0}`,
  };
}

async function requestLocalSendAuthority(message, tabId) {
  const attestation = await runtimeAttestation();
  return await controllerPost(message, "/authorize-send", {
    schema_version: 1,
    run_id: message.run_id,
    delegation_id: message.delegation_id,
    delivery_id: message.delivery_id,
    expected_runtime_head: message.expected_runtime_head,
    prompt_sha256: message.prompt_sha256,
    browser_claim_committed: true,
    browser_claim_id: message.delivery_id,
    child_evidence: childEvidence(message, tabId),
    runtime_attestation: attestation,
  });
}

async function resumeIntent(message, sender) {
  if (message?.execution_generation !== EXECUTION_GENERATION || !HEX64_RE.test(EXECUTION_GENERATION)) {
    return { ok: false, enabled: false, reason: "execution-generation-mismatch" };
  }
  if (senderTab(sender) === null) return { ok: false, enabled: false, reason: "invalid-sender" };
  const observed = Array.isArray(message?.observed_claims) ? message.observed_claims.slice(0, 8) : [];
  if (!observed.length || observed.some((value) => !validObservedClaim(value))) {
    return { ok: true, enabled: false, reason: "no-observed-delivery-correlation" };
  }
  let records;
  try {
    records = await claimRecordsForRecovery();
  } catch (error) {
    return { ok: false, enabled: false, reason: `claim-read-failed:${error?.message || "Error"}` };
  }
  const candidates = records.filter((record) =>
    validClaimRecord(record) && observed.some((value) => observedClaimMatches(record, value))
  );
  const active = [];
  for (const record of candidates) {
    try {
      const status = await controllerStatus(record);
      if (status.delegation_id !== record.delegation_id || status.delivery_id !== record.delivery_id) continue;
      if (!["claimed", "unknown", "delivered"].includes(status.delivery_state)) continue;
      if (status.result_state !== "open") continue;
      active.push({ record, status });
    } catch {
      // Stale records are inert. Only the exact live controller can authenticate
      // a monitor-only recovery candidate.
    }
  }
  if (active.length !== 1) {
    return {
      ok: true,
      enabled: false,
      reason: active.length > 1 ? "ambiguous-active-claim" : "no-active-claim",
    };
  }
  const { record, status } = active[0];
  return {
    ok: true,
    enabled: true,
    monitor_only: true,
    execution_generation: EXECUTION_GENERATION,
    run_id: record.run_id,
    delegation_id: record.delegation_id,
    delivery_id: record.delivery_id,
    task_sha256: record.task_sha256,
    expected_runtime_head: record.expected_runtime_head,
    prompt_sha256: record.prompt_sha256,
    delivery_state: status.delivery_state,
    result_state: status.result_state,
  };
}

async function authorizeSend(message, sender) {
  const tabId = senderTab(sender);
  if (tabId === null) return { ok: false, send_authorized: false, reason: "invalid-sender" };

  let browserClaim;
  try {
    browserClaim = await claimBrowserSend(message);
  } catch (error) {
    return { ok: false, send_authorized: false, reason: `browser-claim-failed:${error?.message || "Error"}` };
  }

  if (!browserClaim.granted) {
    let existing;
    try {
      existing = await claimRecordByDelivery(message.delivery_id);
    } catch (error) {
      return { ok: false, send_authorized: false, monitor_only: false, reason: `existing-claim-read-failed:${error?.message || "Error"}` };
    }
    if (!exactClaimMatches(existing, message)) {
      return { ok: true, send_authorized: false, monitor_only: false, reason: "claim-correlation-mismatch" };
    }

    let status;
    try {
      status = await controllerStatus(message);
    } catch (error) {
      return { ok: false, send_authorized: false, monitor_only: false, reason: `claim-exists-status-unavailable:${error?.message || "Error"}` };
    }
    if (status.delegation_id !== message.delegation_id || status.delivery_id !== message.delivery_id) {
      return { ok: false, send_authorized: false, monitor_only: false, reason: "controller-status-correlation-mismatch" };
    }

    if (
      status.result_state === "open" &&
      status.delivery_state === "prepared" &&
      ["launch-attempted", "child-bound"].includes(status.launch_state)
    ) {
      try {
        const recovered = await requestLocalSendAuthority(message, tabId);
        return {
          ok: true,
          send_authorized: recovered.send_authorized === true,
          monitor_only: false,
          delivery_state: recovered.delivery_state,
          reason: recovered.send_authorized === true ? "recovered-local-authority" : recovered.status,
        };
      } catch (error) {
        return { ok: false, send_authorized: false, monitor_only: false, reason: `local-authority-recovery-failed:${error?.message || "Error"}` };
      }
    }

    const monitorOnly = ["claimed", "unknown", "delivered"].includes(status.delivery_state) && status.result_state === "open";
    return {
      ok: true,
      send_authorized: false,
      monitor_only: monitorOnly,
      reason: browserClaim.reason,
      delivery_state: status.delivery_state,
      result_state: status.result_state,
    };
  }

  try {
    const result = await requestLocalSendAuthority(message, tabId);
    return {
      ok: true,
      send_authorized: result.send_authorized === true,
      monitor_only: result.send_authorized !== true && ["claimed", "unknown", "delivered"].includes(result.delivery_state),
      delivery_state: result.delivery_state,
      reason: result.status,
    };
  } catch (error) {
    return { ok: false, send_authorized: false, monitor_only: false, reason: `local-authority-failed:${error?.message || "Error"}` };
  }
}

chrome.runtime.onInstalled.addListener(() => {
  void initializeClaimDb().catch((error) => console.error("[CAP Agent Session] claim DB init failed", error));
});
chrome.runtime.onStartup.addListener(() => {
  void initializeClaimDb().catch((error) => console.error("[CAP Agent Session] claim DB startup validation failed", error));
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.schema_version === 1 && message.kind === "resume-intent") {
    void resumeIntent(message, sender)
      .then(sendResponse)
      .catch((error) => sendResponse({ ok: false, enabled: false, reason: error?.message || "resume-failed" }));
    return true;
  }

  if (!validCommon(message)) {
    sendResponse({ ok: false, reason: "invalid-correlation-or-generation" });
    return false;
  }

  if (message.kind === "authorize-send") {
    void authorizeSend(message, sender).then(sendResponse).catch((error) => sendResponse({ ok: false, send_authorized: false, reason: error?.message || "authorize-failed" }));
    return true;
  }

  if (senderTab(sender) === null) {
    sendResponse({ ok: false, reason: "invalid-sender" });
    return false;
  }

  let path;
  let body;
  if (message.kind === "event") {
    path = "/event";
    body = {
      schema_version: 1,
      run_id: message.run_id,
      delegation_id: message.delegation_id,
      delivery_id: message.delivery_id,
      event: message.event,
      details: message.details || {},
    };
  } else if (message.kind === "delivery") {
    path = "/delivery";
    body = {
      schema_version: 1,
      run_id: message.run_id,
      delegation_id: message.delegation_id,
      delivery_id: message.delivery_id,
      task_sha256: message.task_sha256,
      outcome: message.outcome,
      evidence_ref: message.evidence_ref,
    };
  } else if (message.kind === "prepare-capture") {
    void runtimeAttestation()
      .then((attestation) => controllerPost(message, "/prepare-capture", {
        schema_version: 1,
        run_id: message.run_id,
        delegation_id: message.delegation_id,
        delivery_id: message.delivery_id,
        cleanup_token: message.cleanup_token,
        runtime_attestation: attestation,
      }))
      .then((value) => sendResponse({ ok: true, ...value }))
      .catch((error) => sendResponse({ ok: false, reason: error?.message || "capture-preparation-failed" }));
    return true;
  } else if (message.kind === "capture") {
    void controllerPost(message, "/capture", {
      schema_version: 1,
      run_id: message.run_id,
      delegation_id: message.delegation_id,
      delivery_id: message.delivery_id,
      cleanup_token: message.cleanup_token,
      capture_token: message.capture_token,
      result_text: message.result_text,
    })
      .then((value) => sendResponse({ ok: true, ...value }))
      .catch((error) => sendResponse({ ok: false, reason: error?.message || "capture-failed" }));
    return true;
  } else if (message.kind === "final-observation") {
    void runtimeAttestation()
      .then((attestation) => controllerPost(message, "/final-observation", {
        schema_version: 1,
        run_id: message.run_id,
        delegation_id: message.delegation_id,
        delivery_id: message.delivery_id,
        request_id: message.request_id,
        terminal_result_visible: message.terminal_result_visible === true,
        worker_generating: message.worker_generating === true,
        runtime_attestation: attestation,
      }))
      .then((value) => sendResponse({ ok: true, ...value }))
      .catch((error) => sendResponse({ ok: false, reason: error?.message || "final-observation-failed" }));
    return true;
  } else if (message.kind === "status") {
    void controllerStatus(message).then((value) => sendResponse({ ok: true, ...value })).catch((error) => sendResponse({ ok: false, reason: error?.message || "status-failed" }));
    return true;
  } else {
    sendResponse({ ok: false, reason: "unsupported-kind" });
    return false;
  }

  void controllerPost(message, path, body)
    .then((value) => sendResponse({ ok: true, ...value }))
    .catch((error) => sendResponse({ ok: false, reason: error?.message || "controller-request-failed" }));
  return true;
});
