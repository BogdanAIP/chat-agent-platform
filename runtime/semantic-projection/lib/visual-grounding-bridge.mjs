import { createHash, randomUUID } from 'node:crypto';

const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const TOKEN_PREFIX = 'visual-target:';
const MAX_PREPARED_TARGETS = 256;
const STRUCTURED_TARGET_KEYS = new Set(['target', 'instruction', 'kind', 'targetText']);

function resultText(result) {
  return (result?.content ?? [])
    .filter(block => block?.type === 'text' && typeof block.text === 'string')
    .map(block => block.text)
    .join('\n');
}

function parsePngDimensions(bytes) {
  if (!Buffer.isBuffer(bytes) || bytes.length < 24 || !bytes.subarray(0, 8).equals(PNG_SIGNATURE)) {
    throw new Error('Visual grounding capture must be a valid PNG image.');
  }
  const width = bytes.readUInt32BE(16);
  const height = bytes.readUInt32BE(20);
  if (width <= 0 || height <= 0) {
    throw new Error('Visual grounding capture has invalid PNG dimensions.');
  }
  return { width, height };
}

export function parseScreenshotResult(result) {
  if (result?.isError) {
    throw new Error(`Playwright screenshot failed: ${resultText(result) || 'unknown backend error'}`);
  }
  const imageBlocks = (result?.content ?? []).filter(
    block => block?.type === 'image' && typeof block.data === 'string'
  );
  if (imageBlocks.length !== 1) {
    throw new Error(`Expected exactly one screenshot image block, found ${imageBlocks.length}.`);
  }
  const block = imageBlocks[0];
  const mimeType = block.mimeType ?? block.contentType;
  if (mimeType !== 'image/png') {
    throw new Error(`Expected image/png screenshot, got ${String(mimeType)}.`);
  }
  let bytes;
  try {
    bytes = Buffer.from(block.data, 'base64');
  } catch (error) {
    throw new Error(`Screenshot image is not valid base64: ${error instanceof Error ? error.message : String(error)}`);
  }
  const { width, height } = parsePngDimensions(bytes);
  return {
    bytes,
    mimeType,
    width,
    height,
    sha256: createHash('sha256').update(bytes).digest('hex')
  };
}

function validateFiniteNumber(value, label) {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    throw new Error(`${label} must be a finite number.`);
  }
  return value;
}

function normalizeText(value, label, maxLength) {
  if (typeof value !== 'string' || !value.trim()) {
    throw new Error(`${label} must be non-empty text.`);
  }
  const normalized = value.trim();
  if (normalized.length > maxLength) {
    throw new Error(`${label} exceeds ${maxLength} characters.`);
  }
  return normalized;
}

function normalizeTargetRequest(input) {
  if (typeof input === 'string') {
    return { target: normalizeText(input, 'Visual grounding target', 4096) };
  }
  if (!input || typeof input !== 'object' || Array.isArray(input)) {
    throw new Error('Visual grounding target must be text or one structured target object.');
  }
  for (const key of Object.keys(input)) {
    if (!STRUCTURED_TARGET_KEYS.has(key)) {
      throw new Error(`Structured visual target contains unsupported field: ${key}.`);
    }
  }
  const target = normalizeText(input.target, 'Structured visual target.target', 4096);
  const instruction = normalizeText(input.instruction, 'Structured visual target.instruction', 4096);
  const kind = normalizeText(input.kind, 'Structured visual target.kind', 128);
  let targetText = null;
  if (input.targetText !== undefined && input.targetText !== null) {
    if (typeof input.targetText !== 'string' || input.targetText.length > 2048) {
      throw new Error('Structured visual target.targetText must be text, null, or omitted and at most 2048 characters.');
    }
    targetText = input.targetText.trim() || null;
  }
  return { target, instruction, kind, targetText };
}

function normalizeGroundingResult(result, capture) {
  if (!result || typeof result !== 'object' || Array.isArray(result)) {
    throw new Error('Grounder result must be an object.');
  }
  if (result.status === 'abstain') {
    return {
      status: 'abstain',
      reason: typeof result.reason === 'string' && result.reason ? result.reason : 'grounder-abstain'
    };
  }
  if (result.status !== 'resolved') {
    throw new Error('Grounder status must be resolved or abstain.');
  }
  if (!result.point || typeof result.point !== 'object' || Array.isArray(result.point)) {
    throw new Error('Resolved grounder result requires point.');
  }
  const x = validateFiniteNumber(result.point.x, 'point.x');
  const y = validateFiniteNumber(result.point.y, 'point.y');
  if (x < 0 || y < 0 || x >= capture.width || y >= capture.height) {
    throw new Error(
      `Grounder point (${x}, ${y}) lies outside CSS screenshot bounds ${capture.width}x${capture.height}.`
    );
  }
  let bbox;
  if (result.bbox !== undefined) {
    if (!result.bbox || typeof result.bbox !== 'object' || Array.isArray(result.bbox)) {
      throw new Error('bbox must be an object when provided.');
    }
    const x1 = validateFiniteNumber(result.bbox.x1, 'bbox.x1');
    const y1 = validateFiniteNumber(result.bbox.y1, 'bbox.y1');
    const x2 = validateFiniteNumber(result.bbox.x2, 'bbox.x2');
    const y2 = validateFiniteNumber(result.bbox.y2, 'bbox.y2');
    if (x1 < 0 || y1 < 0 || x2 > capture.width || y2 > capture.height || x2 <= x1 || y2 <= y1) {
      throw new Error('bbox lies outside the CSS screenshot or is not a positive rectangle.');
    }
    if (x < x1 || x > x2 || y < y1 || y > y2) {
      throw new Error('Resolved click point must lie inside bbox when bbox is provided.');
    }
    bbox = { x1, y1, x2, y2 };
  }
  return {
    status: 'resolved',
    point: { x, y },
    bbox,
    reason: typeof result.reason === 'string' && result.reason ? result.reason : 'visual-resolved'
  };
}

export class SameSessionVisualGroundingBridge {
  #client;
  #grounder;
  #ttlMs;
  #now;
  #targets = new Map();

  constructor({ client, grounder, ttlMs = 10_000, now = () => Date.now() }) {
    if (!client || typeof client.callTool !== 'function') {
      throw new Error('SameSessionVisualGroundingBridge requires an MCP client with callTool().');
    }
    if (typeof grounder !== 'function') {
      throw new Error('SameSessionVisualGroundingBridge requires a grounder callback.');
    }
    if (!Number.isInteger(ttlMs) || ttlMs < 1 || ttlMs > 120_000) {
      throw new Error('ttlMs must be an integer between 1 and 120000.');
    }
    if (typeof now !== 'function') {
      throw new Error('now must be a function.');
    }
    this.#client = client;
    this.#grounder = grounder;
    this.#ttlMs = ttlMs;
    this.#now = now;
  }

  #purgeExpiredTargets() {
    const current = this.#now();
    for (const [token, prepared] of this.#targets) {
      if (current > prepared.expiresAt) {
        this.#targets.delete(token);
      }
    }
  }

  async #captureCssViewport() {
    const result = await this.#client.callTool({
      name: 'browser_take_screenshot',
      arguments: {
        type: 'png',
        fullPage: false,
        scale: 'css'
      }
    });
    return parseScreenshotResult(result);
  }

  async prepare(target) {
    const targetRequest = normalizeTargetRequest(target);
    this.#purgeExpiredTargets();
    const capture = await this.#captureCssViewport();
    let raw;
    try {
      raw = await this.#grounder({
        target: targetRequest.target,
        instruction: targetRequest.instruction,
        kind: targetRequest.kind,
        targetText: targetRequest.targetText,
        imageBytes: capture.bytes,
        mimeType: capture.mimeType,
        width: capture.width,
        height: capture.height,
        coordinateSpace: 'css_viewport'
      });
    } catch (error) {
      return {
        status: 'error',
        reason: `grounder-error:${error instanceof Error ? error.message : String(error)}`
      };
    }

    let grounding;
    try {
      grounding = normalizeGroundingResult(raw, capture);
    } catch (error) {
      return {
        status: 'error',
        reason: `grounder-contract:${error instanceof Error ? error.message : String(error)}`
      };
    }

    if (grounding.status === 'abstain') {
      return grounding;
    }

    this.#purgeExpiredTargets();
    if (this.#targets.size >= MAX_PREPARED_TARGETS) {
      return { status: 'error', reason: 'visual-target-capacity-exceeded' };
    }

    const token = `${TOKEN_PREFIX}${randomUUID()}`;
    this.#targets.set(token, {
      target: targetRequest.target,
      captureSha256: capture.sha256,
      width: capture.width,
      height: capture.height,
      point: grounding.point,
      bbox: grounding.bbox,
      expiresAt: this.#now() + this.#ttlMs
    });

    return {
      status: 'resolved',
      token,
      source: 'vision',
      coordinateSpace: 'css_viewport',
      point: grounding.point,
      bbox: grounding.bbox,
      captureSha256: capture.sha256,
      viewport: { width: capture.width, height: capture.height },
      reason: grounding.reason
    };
  }

  async commitClick(token) {
    if (typeof token !== 'string' || !token.startsWith(TOKEN_PREFIX)) {
      this.#purgeExpiredTargets();
      return { status: 'abstain', reason: 'invalid-visual-target-token' };
    }
    const prepared = this.#targets.get(token);
    if (!prepared) {
      this.#purgeExpiredTargets();
      return { status: 'abstain', reason: 'unknown-or-consumed-visual-target' };
    }

    // One-shot semantics: consume before any possible page mutation. A failed or
    // stale commit must be re-prepared from a fresh capture rather than replayed.
    this.#targets.delete(token);
    this.#purgeExpiredTargets();

    if (this.#now() > prepared.expiresAt) {
      return { status: 'abstain', reason: 'visual-target-expired' };
    }

    let fresh;
    try {
      fresh = await this.#captureCssViewport();
    } catch (error) {
      return {
        status: 'error',
        reason: `freshness-capture-error:${error instanceof Error ? error.message : String(error)}`
      };
    }

    if (
      fresh.width !== prepared.width ||
      fresh.height !== prepared.height ||
      fresh.sha256 !== prepared.captureSha256
    ) {
      return {
        status: 'abstain',
        reason: 'stale-visual-capture',
        preparedSha256: prepared.captureSha256,
        currentSha256: fresh.sha256
      };
    }

    const click = await this.#client.callTool({
      name: 'browser_mouse_click_xy',
      arguments: {
        x: prepared.point.x,
        y: prepared.point.y,
        button: 'left',
        clickCount: 1
      }
    });
    if (click?.isError) {
      return {
        status: 'error',
        reason: `coordinate-click-error:${resultText(click) || 'unknown backend error'}`
      };
    }
    return {
      status: 'acted',
      reason: 'visual-click-committed',
      point: prepared.point
    };
  }

  clear() {
    this.#targets.clear();
  }
}
