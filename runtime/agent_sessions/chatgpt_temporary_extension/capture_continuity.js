(() => {
  "use strict";

  const policy = globalThis.CAPChatGPTTemporaryPolicy;
  if (!policy || typeof MutationObserver === "undefined") return;

  const originalArm = policy.armPostDeliveryUiGuard.bind(policy);
  const originalCaptureAuthorization = policy.captureAuthorization.bind(policy);
  const originalInvalidate = policy.invalidatePostDeliveryAuthorization.bind(policy);
  const RELEVANT_SELECTOR = [
    '[data-message-author-role="user"]',
    '[data-message-author-role="assistant"]',
    '#prompt-textarea',
    '[contenteditable="true"]',
    'textarea',
    'button[data-testid="stop-button"]',
  ].join(',');

  let observer = null;
  let snapshotEpoch = null;
  let snapshotAssistantText = "";

  function elementFor(node) {
    if (!node) return null;
    if (node.nodeType === 1) return node;
    return node.parentElement || null;
  }

  function relevantNode(node) {
    const element = elementFor(node);
    if (!element) return false;
    return Boolean(
      element.matches?.(RELEVANT_SELECTOR) ||
      element.closest?.(RELEVANT_SELECTOR) ||
      element.querySelector?.(RELEVANT_SELECTOR)
    );
  }

  function relevantMutation(record) {
    if (relevantNode(record.target)) return true;
    for (const node of record.addedNodes || []) {
      if (relevantNode(node)) return true;
    }
    for (const node of record.removedNodes || []) {
      if (relevantNode(node)) return true;
    }
    return false;
  }

  function resetSnapshot() {
    snapshotEpoch = null;
    snapshotAssistantText = "";
  }

  function invalidateForMutation(records) {
    if (!records.some(relevantMutation)) return;
    resetSnapshot();
    originalInvalidate();
  }

  function assistantResultText() {
    const turns = [...document.querySelectorAll('[data-message-author-role="assistant"]')];
    const last = turns.at(-1);
    return String(last?.innerText || last?.textContent || "").replace(/\u0000/g, "").trim();
  }

  function stopButtonPresent() {
    if (document.querySelector('button[data-testid="stop-button"]')) return true;
    return [...document.querySelectorAll("button")].some((button) =>
      /^(stop|останов)/i.test(String(button.getAttribute?.("aria-label") || button.textContent || "").trim()),
    );
  }

  policy.armPostDeliveryUiGuard = (intent) => {
    const armed = originalArm(intent);
    if (!armed || observer) return armed;
    observer = new MutationObserver(invalidateForMutation);
    observer.observe(document.documentElement, {
      subtree: true,
      childList: true,
      characterData: true,
      attributes: true,
      attributeFilter: [
        "aria-hidden",
        "aria-disabled",
        "aria-readonly",
        "contenteditable",
        "disabled",
        "readonly",
        "hidden",
        "inert",
        "style",
        "class",
      ],
    });
    return true;
  };

  policy.invalidatePostDeliveryAuthorization = () => {
    resetSnapshot();
    return originalInvalidate();
  };

  policy.captureAuthorization = () => {
    const authorization = originalCaptureAuthorization();
    if (!authorization) {
      resetSnapshot();
      return null;
    }

    const assistantText = assistantResultText();
    if (!assistantText || stopButtonPresent()) {
      resetSnapshot();
      originalInvalidate();
      return null;
    }

    if (snapshotEpoch === authorization.guardEpoch && snapshotAssistantText !== assistantText) {
      resetSnapshot();
      originalInvalidate();
      return null;
    }

    if (snapshotEpoch !== authorization.guardEpoch) {
      snapshotEpoch = authorization.guardEpoch;
      snapshotAssistantText = assistantText;
    }
    return authorization;
  };
})();
