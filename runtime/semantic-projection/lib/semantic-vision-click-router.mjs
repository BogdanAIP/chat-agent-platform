import { SameSessionVisualGroundingBridge } from './visual-grounding-bridge.mjs';
import { createRuntimeBackedBridgeGrounder } from './runtime-backed-bridge-grounder.mjs';
import { RuntimeBackedVisualGrounder } from './runtime-backed-visual-grounder.mjs';

const MAX_SNAPSHOT_TEXT = 4 * 1024 * 1024;
const MAX_TARGET_TEXT = 2048;
const MAX_INSTRUCTION = 4096;

function resultText(result) {
  return (result?.content ?? [])
    .filter(block => block?.type === 'text' && typeof block.text === 'string')
    .map(block => block.text)
    .join('\n');
}

function normalizeRequiredText(value, label, maxLength) {
  if (typeof value !== 'string' || !value.trim()) throw new Error(`${label} must be non-empty text`);
  const normalized = value.trim();
  if (normalized.length > maxLength) throw new Error(`${label} exceeds ${maxLength} characters`);
  return normalized;
}

function normalizedName(value) {
  return String(value).replace(/\s+/g, ' ').trim().toLocaleLowerCase('en-US');
}

function normalizeFallbackIntent(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error('visualFallback must be one object');
  }
  const allowed = new Set(['instruction', 'targetText', 'semanticName']);
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) throw new Error(`visualFallback contains unsupported field: ${key}`);
  }
  const targetText = normalizeRequiredText(value.targetText, 'visualFallback.targetText', MAX_TARGET_TEXT);
  const instruction = normalizeRequiredText(value.instruction, 'visualFallback.instruction', MAX_INSTRUCTION);
  if (value.semanticName !== undefined) {
    const semanticName = normalizeRequiredText(value.semanticName, 'visualFallback.semanticName', MAX_TARGET_TEXT);
    if (normalizedName(semanticName) !== normalizedName(targetText)) {
      throw new Error('visualFallback.semanticName must normalize exactly to targetText');
    }
  }
  return { targetText, instruction };
}

function parseFirstQuotedText(line) {
  const start = line.indexOf('"');
  if (start < 0) return null;
  let escaped = false;
  let value = '';
  for (let index = start + 1; index < line.length; index += 1) {
    const char = line[index];
    if (escaped) { value += char; escaped = false; continue; }
    if (char === '\\') { escaped = true; continue; }
    if (char === '"') return value;
    value += char;
  }
  return null;
}

function parseSnapshotRole(line) {
  const match = line.match(/^\s*-\s+([A-Za-z][A-Za-z0-9_-]*)\s+"/);
  return match ? match[1].toLocaleLowerCase('en-US') : null;
}

export function exactAccessibilityCandidates(snapshotResult, targetText) {
  if (snapshotResult?.isError) {
    throw new Error(`semantic snapshot failed: ${resultText(snapshotResult) || 'unknown backend error'}`);
  }
  const text = resultText(snapshotResult);
  if (text.length > MAX_SNAPSHOT_TEXT) throw new Error(`semantic snapshot exceeds ${MAX_SNAPSHOT_TEXT} characters`);
  const expected = normalizedName(normalizeRequiredText(targetText, 'targetText', MAX_TARGET_TEXT));
  const refs = new Map();
  for (const line of text.split(/\r?\n/)) {
    const refMatch = line.match(/\[ref=([^\]\s]+)\]/);
    if (!refMatch) continue;
    const accessibleName = parseFirstQuotedText(line);
    if (accessibleName === null || normalizedName(accessibleName) !== expected) continue;
    refs.set(refMatch[1], {
      ref: refMatch[1],
      line,
      role: parseSnapshotRole(line),
      disabled: /\[disabled(?:=[^\]]+)?\]/i.test(line)
    });
  }
  return [...refs.values()];
}

function classifySemanticCandidates(candidates) {
  if (candidates.length === 0) return { status: 'miss', reason: 'semantic-exact-accessible-name-miss' };

  if (candidates.length === 1) {
    const candidate = candidates[0];
    if (candidate.role !== 'button') {
      return { status: 'blocked', reason: 'semantic-target-role-not-promoted' };
    }
    if (candidate.disabled) {
      return { status: 'blocked', reason: 'semantic-target-disabled' };
    }
    return { status: 'resolved', candidate, reason: 'semantic-exact-enabled-button' };
  }

  if (candidates.every(candidate => candidate.role === 'button')) {
    const enabled = candidates.filter(candidate => !candidate.disabled);
    const disabled = candidates.filter(candidate => candidate.disabled);
    if (enabled.length === 1 && disabled.length >= 1) {
      return { status: 'resolved', candidate: enabled[0], reason: 'semantic-unique-enabled-button-state' };
    }
  }

  return { status: 'blocked', reason: 'semantic-ambiguity-visual-escalation-not-promoted' };
}

function noAction(status, reason, extra = {}) {
  return { status, reason, acted: false, ...extra };
}

export class SemanticVisionClickRouter {
  #client;
  #bridge;

  constructor({ client, grounder, ttlMs = 30_000 } = {}) {
    if (!client || typeof client.callTool !== 'function') throw new Error('SemanticVisionClickRouter requires one Playwright MCP client');
    const effectiveGrounder = grounder ?? createRuntimeBackedBridgeGrounder(new RuntimeBackedVisualGrounder());
    if (typeof effectiveGrounder !== 'function') throw new Error('SemanticVisionClickRouter grounder must be a function');
    this.#client = client;
    this.#bridge = new SameSessionVisualGroundingBridge({ client, grounder: effectiveGrounder, ttlMs });
  }

  async click({ target = null, element = null, visualFallback } = {}) {
    const fallback = normalizeFallbackIntent(visualFallback);
    const snapshot = await this.#client.callTool({ name: 'browser_snapshot', arguments: {} });
    let candidates;
    try {
      candidates = exactAccessibilityCandidates(snapshot, fallback.targetText);
    } catch (error) {
      return noAction('error', `semantic-preflight-error:${error instanceof Error ? error.message : String(error)}`, { source: 'semantic' });
    }

    const semantic = classifySemanticCandidates(candidates);
    if (semantic.status === 'resolved') {
      const downstream = { target: semantic.candidate.ref, element: element ?? fallback.targetText };
      const click = await this.#client.callTool({ name: 'browser_click', arguments: downstream });
      if (click?.isError) {
        return noAction('error', `semantic-click-error:${resultText(click) || 'unknown backend error'}`, {
          source: 'semantic', backendResult: click, semanticCandidateCount: candidates.length
        });
      }
      return {
        status: 'acted', reason: semantic.reason, acted: true, source: 'semantic',
        backendResult: click, semanticCandidateCount: candidates.length
      };
    }

    if (semantic.status === 'blocked') {
      return noAction('abstain', semantic.reason, {
        source: 'semantic', semanticCandidateCount: candidates.length
      });
    }

    const prepared = await this.#bridge.prepare({
      target: target ?? fallback.targetText,
      instruction: fallback.instruction,
      kind: 'labeled_button',
      targetText: fallback.targetText
    });
    if (prepared.status !== 'resolved') {
      return noAction(prepared.status, prepared.reason ?? 'visual-fallback-not-resolved', {
        source: 'vision', semanticCandidateCount: 0
      });
    }
    const committed = await this.#bridge.commitClick(prepared.token);
    if (committed.status !== 'acted') {
      return noAction(committed.status, committed.reason ?? 'visual-fallback-not-committed', {
        source: 'vision', semanticCandidateCount: 0
      });
    }
    return {
      status: 'acted', reason: committed.reason ?? 'visual-click-committed', acted: true,
      source: 'vision', point: committed.point, semanticCandidateCount: 0
    };
  }

  clear() { this.#bridge.clear(); }
}

export function createSemanticVisionClickRouter(options) {
  return new SemanticVisionClickRouter(options);
}
