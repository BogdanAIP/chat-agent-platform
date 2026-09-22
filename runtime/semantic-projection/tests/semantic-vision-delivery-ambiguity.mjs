import assert from 'node:assert/strict';

import { SemanticVisionClickRouter } from '../lib/semantic-vision-click-router.mjs';


const PNG_1X1 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=';

function textResult(text) {
  return { content: [{ type: 'text', text }] };
}

function screenshotResult() {
  return {
    content: [{
      type: 'image',
      mimeType: 'image/png',
      data: PNG_1X1,
    }],
  };
}

{
  const calls = [];
  const client = {
    async callTool(request) {
      calls.push(request);
      if (request.name === 'browser_snapshot') {
        return textResult('- button "Save" [ref=e1]');
      }
      if (request.name === 'browser_click') {
        throw new Error('INJECTED_SEMANTIC_CLICK_ACK_LOSS');
      }
      throw new Error(`unexpected tool ${request.name}`);
    },
  };
  const router = new SemanticVisionClickRouter({
    client,
    grounder: async () => {
      throw new Error('grounder must not run for exact semantic match');
    },
  });

  const result = await router.click({
    visualFallback: {
      targetText: 'Save',
      instruction: 'click Save',
    },
  });

  assert.equal(result.status, 'error');
  assert.equal(result.source, 'semantic');
  assert.equal(result.deliveryAttempted, true);
  assert.match(result.deliveryError ?? '', /INJECTED_SEMANTIC_CLICK_ACK_LOSS/);
  assert.equal(calls.filter(call => call.name === 'browser_click').length, 1);
}

{
  const calls = [];
  const client = {
    async callTool(request) {
      calls.push(request);
      if (request.name === 'browser_snapshot') {
        return textResult('- heading "Other" [ref=e1]');
      }
      if (request.name === 'browser_take_screenshot') {
        return screenshotResult();
      }
      if (request.name === 'browser_mouse_click_xy') {
        throw new Error('INJECTED_VISUAL_CLICK_ACK_LOSS');
      }
      throw new Error(`unexpected tool ${request.name}`);
    },
  };
  const router = new SemanticVisionClickRouter({
    client,
    grounder: async () => ({
      status: 'resolved',
      reason: 'fixture',
      point: { x: 0, y: 0 },
      bbox: { x1: 0, y1: 0, x2: 1, y2: 1 },
    }),
  });

  const result = await router.click({
    visualFallback: {
      targetText: 'Launch',
      instruction: 'click Launch',
    },
  });

  assert.equal(result.status, 'error');
  assert.equal(result.source, 'vision');
  assert.equal(result.deliveryAttempted, true);
  assert.match(result.deliveryError ?? '', /INJECTED_VISUAL_CLICK_ACK_LOSS/);
  assert.equal(calls.filter(call => call.name === 'browser_mouse_click_xy').length, 1);
}

console.log('SEMANTIC_VISION_SEMANTIC_ACK_LOSS_MARKED=PASS');
console.log('SEMANTIC_VISION_COORDINATE_ACK_LOSS_MARKED=PASS');
