import assert from 'node:assert/strict';
import process from 'node:process';

import {
  RuntimeBackedVisualGrounder,
  productionRunnerPathsForTest
} from '../lib/runtime-backed-visual-grounder.mjs';

function readyRuntime() {
  return JSON.stringify({
    profile: 'lfm25-vl-450m-f16',
    running: true,
    ready: true,
    conflict: false,
    port: 3068,
    state: 'ready'
  });
}

function tinyPng() {
  return Buffer.from(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl0mXQAAAAASUVORK5CYII=',
    'base64'
  );
}

{
  const calls = [];
  const fakeRun = async (command, args, options = {}) => {
    calls.push({ command, args, options });
    if (args.includes('Start') || args.includes('Touch')) {
      return { code: 0, stdout: readyRuntime(), stderr: '' };
    }
    return {
      code: 0,
      stdout: JSON.stringify({
        schema_version: 1,
        status: 'resolved',
        reason: 'promoted-icon-consistent',
        point: { x: 0.5, y: 0.5 },
        bbox: { x1: 0.1, y1: 0.1, x2: 0.9, y2: 0.9 }
      }),
      stderr: ''
    };
  };

  const runner = new RuntimeBackedVisualGrounder({
    runProcess: fakeRun,
    pythonExecutable: process.execPath
  });
  const result = await runner.ground({
    imageBytes: tinyPng(),
    mimeType: 'image/png',
    width: 1,
    height: 1,
    coordinateSpace: 'css_viewport',
    instruction: 'click Search',
    kind: 'icon_only'
  });

  assert.equal(result.status, 'resolved');
  assert.equal(calls.length, 3);
  assert(calls[0].args.includes('Start'));
  assert.equal(calls[1].command, process.execPath);

  const request = JSON.parse(calls[1].options.input);
  assert.equal(request.kind, 'icon_only');
  assert.equal(request.coordinate_space, 'css_viewport');
  assert.equal(Object.prototype.hasOwnProperty.call(request, 'model_path'), false);
  assert.equal(Object.prototype.hasOwnProperty.call(request, 'port'), false);

  assert(calls[2].args.includes('Touch'));
}

{
  let pythonCalled = false;
  const fakeRun = async (_command, args) => {
    if (args.includes('Start')) {
      return {
        code: 0,
        stdout: JSON.stringify({
          profile: 'unexpected-profile',
          running: true,
          ready: true,
          conflict: false,
          port: 3068,
          state: 'ready'
        }),
        stderr: ''
      };
    }
    pythonCalled = true;
    return { code: 0, stdout: '{}', stderr: '' };
  };
  const runner = new RuntimeBackedVisualGrounder({
    runProcess: fakeRun,
    pythonExecutable: process.execPath
  });
  await assert.rejects(
    runner.ground({
      imageBytes: tinyPng(),
      mimeType: 'image/png',
      width: 1,
      height: 1,
      coordinateSpace: 'css_viewport',
      instruction: 'click Search',
      kind: 'icon_only'
    }),
    /profile mismatch/
  );
  assert.equal(pythonCalled, false);
}

{
  let touchCalled = false;
  const fakeRun = async (_command, args) => {
    if (args.includes('Start')) return { code: 0, stdout: readyRuntime(), stderr: '' };
    if (args.includes('Touch')) {
      touchCalled = true;
      return { code: 0, stdout: readyRuntime(), stderr: '' };
    }
    return {
      code: 2,
      stdout: JSON.stringify({ schema_version: 1, status: 'error', reason: 'provider-failed' }),
      stderr: ''
    };
  };
  const runner = new RuntimeBackedVisualGrounder({
    runProcess: fakeRun,
    pythonExecutable: process.execPath
  });
  await assert.rejects(
    runner.ground({
      imageBytes: tinyPng(),
      mimeType: 'image/png',
      width: 1,
      height: 1,
      coordinateSpace: 'css_viewport',
      instruction: 'click Search',
      kind: 'icon_only'
    }),
    /production-grounder-error:provider-failed/
  );
  assert.equal(touchCalled, true, 'runtime use must be touched even when inference fails');
}

{
  const paths = productionRunnerPathsForTest();
  assert.equal(paths.reviewedProfile, 'lfm25-vl-450m-f16');
  assert.equal(paths.reviewedPort, 3068);
  assert(paths.controllerPath.endsWith('scripts\\local-vision-runtime.ps1') || paths.controllerPath.endsWith('scripts/local-vision-runtime.ps1'));
  assert(paths.grounderCliPath.endsWith('scripts\\production-visual-grounder.py') || paths.grounderCliPath.endsWith('scripts/production-visual-grounder.py'));
}

console.log('RUNTIME_BACKED_VISUAL_GROUNDER=PASS');
console.log('RUNTIME_BACKED_VISUAL_GROUNDER_FIXED_PROFILE=PASS');
console.log('RUNTIME_BACKED_VISUAL_GROUNDER_TOUCH_ON_ERROR=PASS');
