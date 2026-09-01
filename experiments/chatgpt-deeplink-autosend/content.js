(() => {
  "use strict";

  const policy = globalThis.CAPAutoSendPolicy;
  if (!policy) return;

  const intent = policy.parseIntent(location.href);
  if (!intent.enabled) return;

  const key = policy.attemptKey(intent.runId);
  if (sessionStorage.getItem(key)) {
    console.info("[CAP AutoSend] run already attempted; no action", intent.runId);
    return;
  }

  let stopped = false;
  let observer = null;
  let intervalId = null;
  const deadline = Date.now() + intent.maxWaitMs;

  function stop(reason) {
    if (stopped) return;
    stopped = true;
    observer?.disconnect();
    if (intervalId !== null) clearInterval(intervalId);
    console.info(`[CAP AutoSend] stopped: ${reason}`);
  }

  function findSendButton() {
    return document.querySelector('button[data-testid="send-button"]');
  }

  function findComposer(button) {
    const form = button.closest("form");
    if (form) return form;

    let node = button.parentElement;
    for (let depth = 0; node && depth < 8; depth += 1, node = node.parentElement) {
      if (policy.containsRequiredComposerText(node.textContent || "", intent)) return node;
    }
    return null;
  }

  function buttonIsReady(button) {
    if (!button || !button.isConnected) return false;
    if (button.disabled) return false;
    if (button.getAttribute("aria-disabled") === "true") return false;
    return true;
  }

  function trySend() {
    if (stopped) return;
    if (Date.now() > deadline) {
      stop("timeout-before-safe-send");
      return;
    }

    const currentIntent = policy.parseIntent(location.href);
    if (!currentIntent.enabled || currentIntent.runId !== intent.runId) {
      stop("url-contract-changed");
      return;
    }

    if (sessionStorage.getItem(key)) {
      stop("run-already-attempted");
      return;
    }

    const button = findSendButton();
    if (!buttonIsReady(button)) return;

    const composer = findComposer(button);
    if (!composer) return;

    const composerText = composer.textContent || "";
    if (!policy.containsRequiredComposerText(composerText, intent)) return;

    sessionStorage.setItem(
      key,
      JSON.stringify({ state: "attempted", at: new Date().toISOString(), href: location.href }),
    );

    stop("send-attempt-dispatched");
    console.info("[CAP AutoSend] dispatching one Send click", intent.runId);
    button.click();
  }

  observer = new MutationObserver(trySend);
  observer.observe(document.documentElement, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ["disabled", "aria-disabled"],
  });

  intervalId = setInterval(trySend, 250);
  trySend();
})();
