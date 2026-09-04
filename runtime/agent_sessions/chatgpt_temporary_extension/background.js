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
const LIVE_LAUNCHES = new Map();
const LIVE_PRE_SEND_CLAIMS = new Set();

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

function senderUrl(sender) {
  return sender?.url || sender?.tab?.url || "";
}

function senderTab(sender) {
  let origin;
  try {
    origin = new URL(senderUrl(sender)).origin;
  } catch {
    return null;
  }
  if (origin !== "https://chatgpt.com" || !Number.isInteger(sender?.tab?.id)) return null;
  return sender.tab.id;
}

function preflightIdFromSender(sender) {
  let url;
  try {
    url = new URL(senderUrl(sender));
  } catch {
    return null;
  }
  if (url.origin !== "https://chatgpt.com" || url.searchParams.get("cap_agent_preflight") !== "1") return null;
  const fragment = new URLSearchParams(url.hash.startsWith("#") ? url.hash.slice(1) : url.hash);
  const value = fragment.get("cap_preflight_id") || "";
  return HEX64_RE.test(value) ? value : null;
}

async function preflightPost(preflightId, path, body) {
  const response = await fetch(`${CONTROLLER_ORIGIN}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CAP-Agent-Preflight": preflightId,
    },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  const value = await response.json().catch(() => ({ status: "invalid-controller-response" }));
  if (!response.ok) throw new Error(`controller-${response.status}:${value.reason || value.status || "rejected"}`);
  return value;
}

function liveLaunchForOwnerTab(tabId) {
  for (const [launchHandle, live] of LIVE_LAUNCHES.entries()) {
    if (live.owner_tab_id === tabId) return { launchHandle, live };
  }
  return null;
}

function validPreparedLaunch(prepared) {
  if (
    prepared?.status !== "handoff-prepared" ||
    !HEX64_RE.test(prepared.launch_handle || "") ||
    !HEX64_RE.test(prepared.run_id || "") ||
    !HEX64_RE.test(prepared.delegation_id || "") ||
    !HEX64_RE.test(prepared.delivery_id || "") ||
    !HEX64_RE.test(prepared.task_sha256 || "") ||
    !HEAD40_RE.test(prepared.expected_runtime_head || "") ||
    !HEX64_RE.test(prepared.prompt_sha256 || "") ||
    typeof prepared.launch_url !== "string" ||
    !prepared.launch_url
  ) {
    return false;
  }
  let url;
  try {
    url = new URL(prepared.launch_url);
  } catch {
    return false;
  }
  if (url.origin !== "https://chatgpt.com" || url.searchParams.get("cap_agent_delegate") !== "1") return false;
  const fragment = new URLSearchParams(url.hash.startsWith("#") ? url.hash.slice(1) : url.hash);
  if (fragment.get("cap_run_id") !== prepared.launch_handle) return false;
  if (prepared.launch_url.includes(prepared.run_id)) return false;
  return true;
}

function exactLivePreparedMatch(live, prepared) {
  return live &&
    live.run_id === prepared.run_id &&
    live.delegation_id === prepared.delegation_id &&
    live.delivery_id === prepared.delivery_id &&
    live.task_sha256 === prepared.task_sha256 &&
    live.expected_runtime_head === prepared.expected_runtime_head &&
    live.prompt_sha256 === prepared.prompt_sha256 &&
    live.launch_url === prepared.launch_url;
}

function exactCommittedStatus(live, launchHandle, status) {
  return status &&
    status.status === "ready" &&
    status.delegation_id === live.delegation_id &&
    status.delivery_id === live.delivery_id &&
    status.launch_handle === launchHandle &&
    status.expected_runtime_head === live.expected_runtime_head &&
    status.execution_generation === EXECUTION_GENERATION &&
    status.prompt_sha256 === live.prompt_sha256 &&
    ["launch-attempted", "child-bound"].includes(status.launch_state) &&
    status.delivery_state === "prepared" &&
    status.result_state === "open";
}

async function controllerStatusWithRun(live) {
  const response = await fetch(`${CONTROLLER_ORIGIN}/status`, {
    method: "GET",
    headers: { "X-CAP-Agent-Token": live.run_id },
    cache: "no-store",
  });
  const value = await response.json().catch(() => ({ status: "invalid-controller-response" }));
  if (!response.ok) throw new Error(`controller-${response.status}:${value.reason || value.status || "rejected"}`);
  return value;
}

async function reconcileLiveLaunch(launchHandle, live) {
  try {
    const status = await controllerStatusWithRun(live);
    if (exactCommittedStatus(live, launchHandle, status)) {
      live.commit_state = "committed";
      return {
        ok: true,
        status: "preflight-navigation-ready",
        navigate_url: live.launch_url,
        delegation_id: live.delegation_id,
        delivery_id: live.delivery_id,
      };
    }
    return { ok: false, status: "preflight-commit-unresolved", reason: "controller-status-not-committed" };
  } catch (error) {
    return {
      ok: false,
      status: "preflight-commit-unresolved",
      reason: `controller-status-unavailable:${error?.message || "Error"}`,
    };
  }
}

async function commitLiveLaunch(launchHandle, live) {
  try {
    const committed = await preflightPost(live.preflight_id, "/preflight-commit", {
      schema_version: 1,
      preflight_id: live.preflight_id,
      launch_handle: launchHandle,
      execution_generation: EXECUTION_GENERATION,
      runtime_attestation: await runtimeAttestation(),
    });
    if (
      committed.status !== "launch-committed" ||
      committed.delegation_id !== live.delegation_id ||
      committed.delivery_id !== live.delivery_id ||
      committed.launch_state !== "launch-attempted"
    ) {
      throw new Error("invalid-preflight-commit");
    }
    live.commit_state = "committed";
    return {
      ok: true,
      status: "preflight-navigation-ready",
      navigate_url: live.launch_url,
      delegation_id: live.delegation_id,
      delivery_id: live.delivery_id,
    };
  } catch (error) {
    // A transport exception does not mean the state-changing commit failed.
    // Keep the only live private mapping and reconcile from token-authenticated
    // durable controller state. Deleting the mapping here would strand a
    // successfully committed launch when the HTTP acknowledgement was lost.
    live.commit_state = "ambiguous";
    const reconciled = await reconcileLiveLaunch(launchHandle, live);
    if (reconciled.ok) return reconciled;
    return {
      ok: false,
      status: "preflight-commit-unresolved",
      reason: `commit-ambiguous:${error?.message || "Error"};${reconciled.reason || "unresolved"}`,
    };
  }
}

async function prepareLiveLaunch(preflightId, sender) {
  const tabId = senderTab(sender);
  if (tabId === null) return { ok: false, reason: "invalid-sender" };
  if (!HEX64_RE.test(preflightId || "")) return { ok: false, reason: "invalid-preflight-capability" };

  const owned = liveLaunchForOwnerTab(tabId);
  if (owned) {
    if (owned.live.commit_state === "committed" || owned.live.commit_state === "ambiguous") {
      const reconciled = await reconcileLiveLaunch(owned.launchHandle, owned.live);
      if (reconciled.ok) return reconciled;
    }
    return await commitLiveLaunch(owned.launchHandle, owned.live);
  }

  const attestation = await runtimeAttestation();
  const prepared = await preflightPost(preflightId, "/preflight", {
    schema_version: 1,
    preflight_id: preflightId,
    execution_generation: EXECUTION_GENERATION,
    runtime_attestation: attestation,
  });
  if (!validPreparedLaunch(prepared)) throw new Error("invalid-preflight-handoff");

  const existing = LIVE_LAUNCHES.get(prepared.launch_handle);
  if (existing) {
    if (!exactLivePreparedMatch(existing, prepared)) throw new Error("preflight-live-correlation-mismatch");
    // A later neutral preflight for the same stable handle may refresh the
    // controller's ephemeral preflight capability after controller restart,
    // but navigation ownership never transfers away from the original tab.
    existing.preflight_id = preflightId;
    if (existing.owner_tab_id !== tabId) {
      return {
        ok: true,
        status: "preflight-owned-by-other-tab",
        delegation_id: existing.delegation_id,
        delivery_id: existing.delivery_id,
      };
    }
    return await commitLiveLaunch(prepared.launch_handle, existing);
  }

  const live = {
    run_id: prepared.run_id,
    delegation_id: prepared.delegation_id,
    delivery_id: prepared.delivery_id,
    task_sha256: prepared.task_sha256,
    expected_runtime_head: prepared.expected_runtime_head,
    prompt_sha256: prepared.prompt_sha256,
    launch_url: prepared.launch_url,
    owner_tab_id: tabId,
    preflight_id: preflightId,
    commit_state: "prepared",
  };
  LIVE_LAUNCHES.set(prepared.launch_handle, live);
  return await commitLiveLaunch(prepared.launch_handle, live);
}

function resolveLiveMessage(message) {
  if (!message || message.schema_version !== 1 || message.execution_generation !== EXECUTION_GENERATION) return null;
  // content.js retains the legacy field name ``run_id``. Its value is now the
  // opaque launch handle from the task URL, never the private controller token.
  const launchHandle = message.run_id || "";
  if (!HEX64_RE.test(launchHandle)) return null;
  const live = LIVE_LAUNCHES.get(launchHandle);
  if (!live) return null;
  if (
    message.delegation_id !== live.delegation_id ||
    message.delivery_id !== live.delivery_id ||
    message.expected_runtime_head !== live.expected_runtime_head ||
    message.prompt_sha256 !== live.prompt_sha256
  ) {
    return null;
  }
  if (message.task_sha256 !== undefined && message.task_sha256 !== live.task_sha256) return null;
  return { ...message, launch_handle: launchHandle, run_id: live.run_id, task_sha256: live.task_sha256 };
}

async function claimBrowserSend(message, tabId) {
  if (!HEX64_RE.test(message.task_sha256 || "")) throw new Error("invalid-task-correlation");
  if (!HEAD40_RE.test(message.expected_runtime_head || "")) throw new Error("invalid-head-correlation");
  if (!HEX64_RE.test(message.prompt_sha256 || "")) throw new Error("invalid-prompt-correlation");
  if (!Number.isInteger(tabId) || tabId < 0) throw new Error("invalid-tab-correlation");
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
          delegation_id: message.delegation_id,
          delivery_id: message.delivery_id,
          task_sha256: message.task_sha256,
          expected_runtime_head: message.expected_runtime_head,
          prompt_sha256: message.prompt_sha256,
          claim_tab_id: tabId,
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
    transaction.oncomplete = () => {
      LIVE_PRE_SEND_CLAIMS.add(message.delivery_id);
      finish({ granted: true, reason: "committed" }, null);
    };
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

function validCommon(message) {
  return message &&
    message.schema_version === 1 &&
    message.execution_generation === EXECUTION_GENERATION &&
    HEX64_RE.test(EXECUTION_GENERATION) &&
    HEX64_RE.test(message.run_id || "") &&
    HEX64_RE.test(message.delegation_id || "") &&
    HEX64_RE.test(message.delivery_id || "") &&
    HEX64_RE.test(message.task_sha256 || "") &&
    HEAD40_RE.test(message.expected_runtime_head || "") &&
    HEX64_RE.test(message.prompt_sha256 || "");
}

function validClaimRecord(record) {
  return record &&
    record.schema_version === 1 &&
    HEX64_RE.test(record.delegation_id || "") &&
    HEX64_RE.test(record.delivery_id || "") &&
    HEX64_RE.test(record.task_sha256 || "") &&
    HEAD40_RE.test(record.expected_runtime_head || "") &&
    HEX64_RE.test(record.prompt_sha256 || "") &&
    Number.isInteger(record.claim_tab_id) && record.claim_tab_id >= 0;
}

function exactClaimMatches(record, message) {
  return validClaimRecord(record) &&
    record.delegation_id === message.delegation_id &&
    record.delivery_id === message.delivery_id &&
    record.task_sha256 === message.task_sha256 &&
    record.expected_runtime_head === message.expected_runtime_head &&
    record.prompt_sha256 === message.prompt_sha256;
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

async function authorizeSend(message, sender) {
  const tabId = senderTab(sender);
  if (tabId === null) return { ok: false, send_authorized: false, reason: "invalid-sender" };

  let browserClaim;
  try {
    browserClaim = await claimBrowserSend(message, tabId);
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
      if (!LIVE_PRE_SEND_CLAIMS.has(message.delivery_id)) {
        return {
          ok: true,
          send_authorized: false,
          monitor_only: false,
          delivery_state: status.delivery_state,
          result_state: status.result_state,
          reason: "browser-claim-owner-context-expired",
        };
      }
      if (existing.claim_tab_id !== tabId) {
        return {
          ok: true,
          send_authorized: false,
          monitor_only: false,
          delivery_state: status.delivery_state,
          result_state: status.result_state,
          reason: "browser-claim-owned-by-other-tab",
        };
      }
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

    return {
      ok: true,
      send_authorized: false,
      monitor_only: false,
      reason: "temporary-profile-ephemeral",
      delivery_state: status.delivery_state,
      result_state: status.result_state,
    };
  }

  try {
    const result = await requestLocalSendAuthority(message, tabId);
    return {
      ok: true,
      send_authorized: result.send_authorized === true,
      monitor_only: false,
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

chrome.runtime.onMessage.addListener((incoming, sender, sendResponse) => {
  if (incoming?.schema_version === 1 && incoming.kind === "resume-intent") {
    const preflightId = preflightIdFromSender(sender);
    if (preflightId !== null) {
      void prepareLiveLaunch(preflightId, sender)
        .then((value) => sendResponse({
          ok: value.ok === true,
          enabled: false,
          status: value.status || null,
          reason: value.reason || (value.ok === true ? value.status : "preflight-failed"),
          navigate_url: value.navigate_url || null,
          delegation_id: value.delegation_id || null,
          delivery_id: value.delivery_id || null,
          execution_generation: EXECUTION_GENERATION,
        }))
        .catch((error) => sendResponse({ ok: false, enabled: false, reason: error?.message || "preflight-failed" }));
      return true;
    }
    sendResponse({ ok: true, enabled: false, reason: "temporary-profile-ephemeral" });
    return false;
  }

  const message = resolveLiveMessage(incoming);
  if (!message || !validCommon(message)) {
    sendResponse({ ok: false, reason: "live-launch-context-expired-or-invalid" });
    return false;
  }

  if (message.kind === "authorize-send") {
    void authorizeSend(message, sender)
      .then(sendResponse)
      .catch((error) => sendResponse({ ok: false, send_authorized: false, reason: error?.message || "authorize-failed" }));
    return true;
  }

  if (message.kind === "bind-recovery-conversation") {
    sendResponse({ ok: true, bound: false, reason: "temporary-profile-ephemeral" });
    return false;
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
      .then((value) => {
        if (value.result_state === "recorded") LIVE_LAUNCHES.delete(message.launch_handle);
        sendResponse({ ok: true, ...value });
      })
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
    void controllerStatus(message)
      .then((value) => sendResponse({ ok: true, ...value }))
      .catch((error) => sendResponse({ ok: false, reason: error?.message || "status-failed" }));
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
