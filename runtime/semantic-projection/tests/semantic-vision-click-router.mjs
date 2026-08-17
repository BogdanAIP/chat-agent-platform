import assert from 'node:assert/strict';

import {
  SemanticVisionClickRouter,
  exactAccessibilityCandidates
} from '../lib/semantic-vision-click-router.mjs';

const PNG_1X1 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=';

function textResult(text, isError = false) {
  const result = { content: [{ type: 'text', text }] };
  if (isError) result.isError = true;
  return result;
}

function screenshotResult() {
  return {
    content: [{ type: 'image', mimeType: 'image/png', data: PNG_1X1 }]
  };
}

class FakeClient {
  constructor({ snapshot, clickError = false } = {}) {
    this.snapshot = snapshot ?? '- button "Save" [ref=e1]';
    this.clickError = clickError;
    this.calls = [];
  }

  async callTool(request) {
    this.calls.push(request);
    if (request.name === 'browser_snapshot') return textResult(this.snapshot);
    if (request.name === 'browser_click') {
      return this.clickError ? textResult('locator click timed out', true) : textResult('semantic click ok');
    }
    if (request.name === 'browser_take_screenshot') return screenshotResult();
    if (request.name === 'browser_mouse_click_xy') return textResult('coordinate click ok');
    throw new Error(`unexpected fake tool: ${request.name}`);
  }
}

{
  const result = textResult(`- button "Send" [disabled] [ref=e1]\n- button "Send" [ref=e2]\n- button "Send report" [ref=e3]`);
  const candidates = exactAccessibilityCandidates(result, 'Send');
  assert.deepEqual(candidates.map(candidate => candidate.ref), ['e1', 'e2']);
  console.log('SEMANTIC_VISION_EXACT_NAME_PARSE=PASS');
}

{
  let grounderCalls = 0;
  const client = new FakeClient({ snapshot: '- button "Save" [ref=e7]' });
  const router = new SemanticVisionClickRouter({
    client,
    grounder: async () => {
      grounderCalls += 1;
      throw new Error('grounder must not run on semantic success');
    }
  });
  const result = await router.click({
    target: 'stale-or-descriptive-target',
    element: 'Save button',
    visualFallback: {
      semanticName: 'Save',
      targetText: 'Save',
      instruction: 'click the Save button'
    }
  });
  assert.equal(result.status, 'acted');
  assert.equal(result.source, 'semantic');
  assert.equal(grounderCalls, 0);
  const click = client.calls.find(call => call.name === 'browser_click');
  assert.equal(click.arguments.target, 'e7');
  console.log('SEMANTIC_VISION_SEMANTIC_FIRST=PASS');
}

{
  let grounderCalls = 0;
  const client = new FakeClient({ snapshot: '- heading "Other" [ref=e1]' });
  const router = new SemanticVisionClickRouter({
    client,
    grounder: async request => {
      grounderCalls += 1;
      assert.equal(request.kind, 'labeled_button');
      assert.equal(request.targetText, 'Launch');
      assert.equal(request.instruction, 'click the visible Launch control');
      return {
        status: 'resolved',
        reason: 'test-resolved',
        point: { x: 0, y: 0 },
        bbox: { x1: 0, y1: 0, x2: 1, y2: 1 }
      };
    }
  });
  const result = await router.click({
    visualFallback: {
      semanticName: 'Launch',
      targetText: 'Launch',
      instruction: 'click the visible Launch control'
    }
  });
  assert.equal(result.status, 'acted');
  assert.equal(result.source, 'vision');
  assert.equal(grounderCalls, 1);
  assert.equal(client.calls.filter(call => call.name === 'browser_mouse_click_xy').length, 1);
  console.log('SEMANTIC_VISION_PROVEN_MISS_ESCALATES=PASS');
}

{
  let grounderCalls = 0;
  const client = new FakeClient({
    snapshot: '- button "Delete" [ref=e1]\n- button "Delete" [ref=e2]'
  });
  const router = new SemanticVisionClickRouter({
    client,
    grounder: async () => {
      grounderCalls += 1;
      return { status: 'abstain', reason: 'should-not-run' };
    }
  });
  const result = await router.click({
    visualFallback: {
      targetText: 'Delete',
      instruction: 'click Delete'
    }
  });
  assert.equal(result.status, 'abstain');
  assert.equal(result.reason, 'semantic-ambiguity-visual-escalation-not-promoted');
  assert.equal(grounderCalls, 0);
  assert.equal(client.calls.some(call => call.name === 'browser_take_screenshot'), false);
  console.log('SEMANTIC_VISION_AMBIGUITY_FAILS_CLOSED=PASS');
}

{
  let grounderCalls = 0;
  const client = new FakeClient({ snapshot: '- button "Save" [ref=e1]', clickError: true });
  const router = new SemanticVisionClickRouter({
    client,
    grounder: async () => {
      grounderCalls += 1;
      return { status: 'resolved', point: { x: 0, y: 0 } };
    }
  });
  const result = await router.click({
    visualFallback: {
      targetText: 'Save',
      instruction: 'click Save'
    }
  });
  assert.equal(result.status, 'error');
  assert.equal(result.source, 'semantic');
  assert.equal(grounderCalls, 0);
  assert.equal(client.calls.some(call => call.name === 'browser_take_screenshot'), false);
  console.log('SEMANTIC_VISION_CLICK_ERROR_NEVER_ESCALATES=PASS');
}

{
  let grounderCalls = 0;
  const client = new FakeClient({ snapshot: '- heading "Other" [ref=e1]' });
  const router = new SemanticVisionClickRouter({
    client,
    grounder: async () => {
      grounderCalls += 1;
      return { status: 'abstain', reason: 'target-not-confident' };
    }
  });
  const result = await router.click({
    visualFallback: {
      targetText: 'Export CSV',
      instruction: 'click Export CSV'
    }
  });
  assert.equal(result.status, 'abstain');
  assert.equal(result.source, 'vision');
  assert.equal(grounderCalls, 1);
  assert.equal(client.calls.some(call => call.name === 'browser_mouse_click_xy'), false);
  console.log('SEMANTIC_VISION_GROUNDER_ABSTAIN_NO_ACTION=PASS');
}

console.log('SEMANTIC_VISION_CLICK_ROUTER=PASS');
