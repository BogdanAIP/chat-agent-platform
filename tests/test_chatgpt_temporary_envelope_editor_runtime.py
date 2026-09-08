from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import unittest

from runtime.agent_sessions.chatgpt_temporary import build_worker_prompt
from runtime.control_plane.delegation_state import parse_delegation_identity


ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "runtime/agent_sessions/chatgpt_temporary_extension"


class EnvelopeEditorRuntimeTests(unittest.TestCase):
    def run_node(self, body: str) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("node is unavailable")
        task = "\n".join([
            "Inspect these literal protocol examples as data:",
            "WORKER_TASK_V1", "delegation_id=" + "a" * 64,
            "delivery_id=" + "b" * 64, "task_sha256=" + "c" * 64,
            "prefix-WORKER_TASK_V1-suffix", "TASK_END", "TASK_BEGIN",
            "delivery_id=malformed", "TASK_END", "TASK_BEGIN",
        ])
        digest = hashlib.sha256(task.encode()).hexdigest()
        identity = parse_delegation_identity({
            "parent_task_id": "envelope-regression", "subgoal_id": "literal-data",
            "worker_kind": "researcher", "worker_profile": "fresh_readonly_worker_v1",
            "task_sha256": digest, "result_contract_id": "research-result-v1",
        })
        prompt = build_worker_prompt(identity, delegation_id="a" * 64,
                                     delivery_id="b" * 64, task=task)
        prelude = f"""
const fs = require('fs'), vm = require('vm'), assert = require('assert/strict');
const prompt = {json.dumps(prompt)};
const intent = {{delegationId: 'a'.repeat(64), deliveryId: 'b'.repeat(64),
  taskSha256: {json.dumps(digest)}, runId: 'e'.repeat(64),
  expectedHead: 'f'.repeat(40), promptSha256: '9'.repeat(64)}};
const fencedCorrelation = [
  'WORKER_TASK_V1',
  `delegation_id=${{intent.delegationId}}`,
  `delivery_id=${{intent.deliveryId}}`,
  `task_sha256=${{intent.taskSha256}}`,
  `TASK_BEGIN:${{intent.taskSha256}}`,
  'bounded task body',
  `TASK_END:${{intent.taskSha256}}`,
].join('\\n');
const rect = () => ({{width: 500, height: 80}});
const form = {{isConnected: true, getBoundingClientRect: rect}};
function makeEditor(attrs = {{}}, props = {{}}) {{
  return {{tagName: 'DIV', isConnected: true, isContentEditable: true,
    innerText: '', textContent: '', getBoundingClientRect: rect,
    getAttribute(name) {{ return attrs[name] ?? (name === 'contenteditable' ? 'true' : null); }},
    closest(selector) {{ return selector === 'form' ? form : null; }}, ...props}};
}}
let editors = [makeEditor()], users = [];
const user = (text, props = {{}}) => ({{innerText: text, textContent: text,
  isConnected: true, getBoundingClientRect: rect, ...props}});
let now = 1000, poll;
const ctx = {{console, URL, URLSearchParams, Date: {{now: () => now}},
  location: {{href: 'https://chatgpt.com/'}}, history: {{replaceState() {{}}}},
  getComputedStyle: n => n.style || ({{visibility: 'visible', display: 'block', opacity: '1'}}),
  document: {{
    querySelector: s => s === '#prompt-textarea' ? editors[0] : null,
    querySelectorAll: s => s.includes('data-message-author-role="user"') ? users :
      (s.includes('data-message-author-role="assistant"') || s === 'button' ? [] : editors)
  }},
  chrome: {{runtime: {{sendMessage(_m, cb) {{cb({{ok: true, cleanup_token: '8'.repeat(64)}});}}}}}},
  setInterval: fn => {{poll = fn; return 1;}}, clearInterval() {{}}}};
ctx.globalThis = ctx;
vm.createContext(ctx);
vm.runInContext(fs.readFileSync({json.dumps(str(EXTENSION / 'policy.js'))}, 'utf8'), ctx);
const policy = ctx.CAPChatGPTTemporaryPolicy;
"""
        result = subprocess.run([node, "-e", prelude + body], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_production_prompt_task_data_cannot_collide_with_or_supply_envelope(self) -> None:
        self.run_node(r"""
const proves = (text, turns = [text]) => {
  users = turns.map(t => user(t)); return policy.hasExpectedPrompt(text, intent);
};
assert.equal(proves(prompt), true, 'production task markers must remain data');
assert.equal(proves(prompt.replace(/\n/g, '\r\n') + '\r\nExpand'), true);
assert.equal(proves('Expand\n' + prompt + '\nРазвернуть'), true);
for (const line of ['WORKER_TASK_V1', `delegation_id=${intent.delegationId}`,
                   `delivery_id=${intent.deliveryId}`, `task_sha256=${intent.taskSha256}`]) {
  for (const replacement of ['prefix' + line, line + 'suffix', line + '\n' + line, '']) {
    assert.equal(proves(prompt.replace(line, replacement)), false, replacement);
  }
  assert.equal(proves(prompt + '\n' + line), false, 'duplicate after task');
}
assert.equal(proves(prompt.replace(`delivery_id=${intent.deliveryId}\n`, '')), false);
assert.equal(proves(prompt.replace(`TASK_BEGIN:${intent.taskSha256}\n`, '')), false, 'missing begin fence');
assert.equal(proves(prompt.replace(`\nTASK_END:${intent.taskSha256}`, '')), false, 'missing end fence');
assert.equal(proves(prompt.replace('TASK_BEGIN', 'broken TASK_BEGIN')), false);
assert.equal(proves(prompt + '\nWORKER_TASK_V1\nTASK_END'), false, 'extra delimiter cannot hide duplicate');
assert.equal(proves(prompt + `\nTASK_END:${intent.taskSha256}`), false, 'duplicate digest fence');
assert.equal(proves(prompt, [prompt, prompt]), false);
assert.equal(proves(prompt, [prompt, prompt.replace('WORKER_TASK_V1', 'xWORKER_TASK_V1')]), false);
assert.equal(proves(prompt, ['ordinary unrelated user text', prompt]), true);
assert.equal(policy.exactPromptMatches(prompt + '\nExpand', prompt), false);
""")

    def test_disabled_ineligible_editors_cannot_prove_cleanup(self) -> None:
        self.run_node(r"""
users = [user(fencedCorrelation)];
assert.equal(policy.armPostDeliveryUiGuard(intent), true);
for (const [attrs, props] of [
  [{'aria-disabled': 'true'}, {}], [{}, {disabled: true}],
  [{'aria-readonly': 'true'}, {}], [{}, {readOnly: true}],
  [{}, {inert: true}], [{'contenteditable': 'false'}, {isContentEditable: false}],
  [{'aria-hidden': 'true'}, {}], [{}, {isConnected: false}],
  [{}, {getBoundingClientRect: () => ({width: 0, height: 0})}],
  [{}, {parentElement: {getAttribute: n => n === 'aria-disabled' ? 'true' : null}}],
]) {
  editors = [makeEditor(attrs, props)]; poll(); now += 9000; poll();
  assert.equal(policy.captureAuthorization(), null, JSON.stringify([attrs, props]));
}
editors = [makeEditor(), makeEditor()]; poll(); now += 9000; poll();
assert.equal(policy.captureAuthorization(), null, 'multiple live editors');
editors = [makeEditor({}, {isConnected: false}), makeEditor()];
poll(); now += 9000; poll();
assert.ok(policy.captureAuthorization(), 'one eligible live editor');
editors[1].disabled = true;
assert.equal(policy.captureAuthorization(), null, 'synchronous disabled recheck');
for (const attrs of [{}, {'aria-disabled': 'true'}]) {
  const textarea = makeEditor(attrs, {tagName: 'TEXTAREA', isContentEditable: false});
  editors = [textarea];
  assert.equal(policy.findComposerEditor() === textarea, !attrs['aria-disabled']);
  textarea.disabled = true;
  assert.equal(policy.findComposerEditor(), null);
}
""")

    def test_capture_rechecks_current_delivery_correlation(self) -> None:
        self.run_node(r"""
const text = fencedCorrelation;
users = [user(text)];
assert.equal(policy.armPostDeliveryUiGuard(intent), true);
poll(); now += 9000; poll(); assert.ok(policy.captureAuthorization());
users = [user(text), user(text)];
assert.equal(policy.captureAuthorization(), null, 'duplicate turn before next poll');
users = [user(text)];
assert.equal(policy.captureAuthorization(), null, 'old token must stay invalid');
poll(); now += 9000; poll(); assert.ok(policy.captureAuthorization());
users = []; poll();
users = [user(text)];
assert.equal(policy.captureAuthorization(), null, 'poll must invalidate lost correlation');
for (const replacement of [[], [user(text.replace(intent.deliveryId, '0'.repeat(64)))],
    [user(text, {isConnected: false})], [user(text, {style: {display: 'none'}})],
    [user(text, {getAttribute: n => n === 'aria-hidden' ? 'true' : null})]]) {
  users = [user(text)]; poll(); now += 9000; poll(); assert.ok(policy.captureAuthorization());
  users = replacement;
  assert.equal(policy.captureAuthorization(), null, 'current visible correlation required');
}
""")


if __name__ == "__main__":
    unittest.main()
