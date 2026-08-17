import assert from 'node:assert/strict';

import { SameSessionVisualGroundingBridge } from '../lib/visual-grounding-bridge.mjs';

const tinyPngBase64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl0mXQAAAAASUVORK5CYII=';
let now = 0;
let clickCalls = 0;
let grounderCalls = 0;

const client = {
  async callTool(request) {
    if (request.name === 'browser_take_screenshot') {
      return {
        content: [{ type: 'image', mimeType: 'image/png', data: tinyPngBase64 }]
      };
    }
    if (request.name === 'browser_mouse_click_xy') {
      clickCalls += 1;
      return { content: [{ type: 'text', text: 'clicked' }] };
    }
    throw new Error(`unexpected fake tool: ${String(request.name)}`);
  }
};

const bridge = new SameSessionVisualGroundingBridge({
  client,
  ttlMs: 5,
  now: () => now,
  grounder: async () => {
    grounderCalls += 1;
    return {
      status: 'resolved',
      reason: 'unit-resolved',
      point: { x: 0.5, y: 0.5 },
      bbox: { x1: 0.1, y1: 0.1, x2: 0.9, y2: 0.9 }
    };
  }
});

const prepared = [];
for (let index = 0; index < 256; index += 1) {
  const result = await bridge.prepare(`target-${index}`);
  assert.equal(result.status, 'resolved', JSON.stringify(result));
  prepared.push(result.token);
}

const atCapacity = await bridge.prepare('target-over-capacity');
assert.deepEqual(atCapacity, {
  status: 'error',
  reason: 'visual-target-capacity-exceeded'
});
assert.equal(clickCalls, 0);

now = 6;
const afterExpiryPurge = await bridge.prepare('target-after-expiry');
assert.equal(afterExpiryPurge.status, 'resolved', JSON.stringify(afterExpiryPurge));

const expiredReplay = await bridge.commitClick(prepared[0]);
assert.equal(expiredReplay.status, 'abstain');
assert.equal(expiredReplay.reason, 'unknown-or-consumed-visual-target');
assert.equal(clickCalls, 0);

now = 10;
const explicitlyExpired = await bridge.prepare('target-explicit-expiry');
assert.equal(explicitlyExpired.status, 'resolved');
now = 16;
const expiredCommit = await bridge.commitClick(explicitlyExpired.token);
assert.equal(expiredCommit.status, 'abstain');
assert.equal(expiredCommit.reason, 'visual-target-expired');
assert.equal(clickCalls, 0);

assert(grounderCalls >= 258);
console.log('VISION_BRIDGE_TOKEN_CAPACITY=PASS');
console.log('VISION_BRIDGE_TOKEN_TTL_PURGE=PASS');
console.log('VISION_BRIDGE_EXPIRED_TOKEN_NO_ACTION=PASS');
