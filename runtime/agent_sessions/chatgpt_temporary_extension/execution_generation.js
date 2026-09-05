"use strict";

globalThis.CAPChatGPTTemporaryExecutionGeneration =
  "8ab4597f44f6fa09e131df226f046bccb2550d2e57c75be7497c9a2967e9500b";

(() => {
  if (
    typeof ServiceWorkerGlobalScope === "undefined" ||
    !(globalThis instanceof ServiceWorkerGlobalScope)
  ) {
    return;
  }

  const CONTROLLER_ORIGIN = "http://127.0.0.1:3078";
  const AUTH_VERSION = "1";
  const AUTH_DOMAIN = "CAP_AGENT_LOOPBACK_AUTH_V1";
  const AUTH_VERSION_HEADER = "X-CAP-Agent-Auth-Version";
  const AUTH_NONCE_HEADER = "X-CAP-Agent-Auth-Nonce";
  const AUTH_MAC_HEADER = "X-CAP-Agent-Auth-Mac";
  const PRE_FLIGHT_SECRET_HEADER = "X-CAP-Agent-Preflight";
  const RUN_SECRET_HEADER = "X-CAP-Agent-Token";
  const HEX64_RE = /^[0-9a-f]{64}$/;
  const textEncoder = new TextEncoder();
  const nativeFetch = globalThis.fetch.bind(globalThis);

  function bytesToHex(bytes) {
    return [...bytes].map((value) => value.toString(16).padStart(2, "0")).join("");
  }

  function hexToBytes(value) {
    if (!HEX64_RE.test(value || "")) throw new Error("controller-auth-secret-invalid");
    const bytes = new Uint8Array(32);
    for (let index = 0; index < bytes.length; index += 1) {
      bytes[index] = Number.parseInt(value.slice(index * 2, index * 2 + 2), 16);
    }
    return bytes;
  }

  async function sha256HexText(value) {
    const digest = await crypto.subtle.digest("SHA-256", textEncoder.encode(value));
    return bytesToHex(new Uint8Array(digest));
  }

  async function importHmacKey(secretHex, usage) {
    return await crypto.subtle.importKey(
      "raw",
      hexToBytes(secretHex),
      { name: "HMAC", hash: "SHA-256" },
      false,
      [usage],
    );
  }

  async function hmacHex(secretHex, value) {
    const key = await importHmacKey(secretHex, "sign");
    const signature = await crypto.subtle.sign("HMAC", key, textEncoder.encode(value));
    return bytesToHex(new Uint8Array(signature));
  }

  async function hmacVerify(secretHex, value, signatureHex) {
    const key = await importHmacKey(secretHex, "verify");
    return await crypto.subtle.verify(
      "HMAC",
      key,
      hexToBytes(signatureHex),
      textEncoder.encode(value),
    );
  }

  function randomNonce() {
    const bytes = new Uint8Array(32);
    crypto.getRandomValues(bytes);
    return bytesToHex(bytes);
  }

  function stripPrivateCapabilities(bodyText) {
    if (!bodyText) return "";
    let value;
    try {
      value = JSON.parse(bodyText);
    } catch {
      throw new Error("controller-auth-body-invalid-json");
    }
    if (!value || typeof value !== "object" || Array.isArray(value)) {
      throw new Error("controller-auth-body-invalid-object");
    }
    delete value.preflight_id;
    delete value.run_id;
    if (
      value.child_evidence &&
      typeof value.child_evidence === "object" &&
      !Array.isArray(value.child_evidence)
    ) {
      delete value.child_evidence.run_id;
    }
    return JSON.stringify(value);
  }

  function copyHeaders(input, init) {
    const headers = new Headers(input instanceof Request ? input.headers : undefined);
    if (init?.headers) {
      for (const [name, value] of new Headers(init.headers).entries()) {
        headers.set(name, value);
      }
    }
    return headers;
  }

  async function authenticatedControllerFetch(input, init = {}) {
    const url = new URL(input instanceof Request ? input.url : String(input));
    if (url.origin !== CONTROLLER_ORIGIN) {
      return nativeFetch(input, init);
    }

    const method = String(init.method || (input instanceof Request ? input.method : "GET")).toUpperCase();
    const headers = copyHeaders(input, init);
    const preflightSecret = headers.get(PRE_FLIGHT_SECRET_HEADER);
    const runSecret = headers.get(RUN_SECRET_HEADER);
    if (Boolean(preflightSecret) === Boolean(runSecret)) {
      throw new Error("controller-auth-secret-ambiguous");
    }
    const secret = preflightSecret || runSecret || "";
    if (!HEX64_RE.test(secret)) throw new Error("controller-auth-secret-invalid");

    headers.delete(PRE_FLIGHT_SECRET_HEADER);
    headers.delete(RUN_SECRET_HEADER);

    if (input instanceof Request && init.body === undefined && method !== "GET" && method !== "HEAD") {
      throw new Error("controller-auth-request-body-must-be-explicit");
    }
    if (init.body !== undefined && typeof init.body !== "string") {
      throw new Error("controller-auth-body-must-be-json-text");
    }
    const bodyText = method === "GET" || method === "HEAD" ? "" : stripPrivateCapabilities(init.body || "");
    const nonce = randomNonce();
    const bodyDigest = await sha256HexText(bodyText);
    const requestAuthInput = [
      AUTH_DOMAIN,
      "request",
      method,
      url.pathname,
      nonce,
      bodyDigest,
    ].join("\n");
    const requestMac = await hmacHex(secret, requestAuthInput);

    headers.set(AUTH_VERSION_HEADER, AUTH_VERSION);
    headers.set(AUTH_NONCE_HEADER, nonce);
    headers.set(AUTH_MAC_HEADER, requestMac);

    const requestInit = {
      ...init,
      method,
      headers,
      body: method === "GET" || method === "HEAD" ? undefined : bodyText,
    };
    const response = await nativeFetch(url.href, requestInit);
    const responseText = await response.text();

    const responseVersion = response.headers.get(AUTH_VERSION_HEADER);
    const responseNonce = response.headers.get(AUTH_NONCE_HEADER);
    const responseMac = response.headers.get(AUTH_MAC_HEADER) || "";
    if (
      responseVersion !== AUTH_VERSION ||
      responseNonce !== nonce ||
      !HEX64_RE.test(responseMac)
    ) {
      throw new Error("controller-auth-response-headers-invalid");
    }

    const responseDigest = await sha256HexText(responseText);
    const responseAuthInput = [
      AUTH_DOMAIN,
      "response",
      method,
      url.pathname,
      nonce,
      String(response.status),
      responseDigest,
    ].join("\n");
    if (!(await hmacVerify(secret, responseAuthInput, responseMac))) {
      throw new Error("controller-auth-response-mac-invalid");
    }

    return new Response(responseText, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
    });
  }

  globalThis.fetch = authenticatedControllerFetch;
})();
