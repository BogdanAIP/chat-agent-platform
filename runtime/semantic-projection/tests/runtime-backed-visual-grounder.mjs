import assert from 'node:assert/strict';
import net from 'node:net';
import process from 'node:process';

import {
  RuntimeBackedVisualGrounder,
  collectRuntimeProcessForTest,
  productionRunnerPathsForTest
} from '../lib/runtime-backed-visual-grounder.mjs';

const paths = productionRunnerPathsForTest();

function readyRuntime() {
  return JSON.stringify({
    profile: 'lfm25-vl-450m-f16',
    running: true,
    ready: true,
    conflict: false,
    pid: 4242,
    port: 3068,
    state: 'ready'
  });
}

function readyListenerGuard() {
  return JSON.stringify({
    schema_version: 1,
    owned: true,
    pid: 4242,
    host: '127.0.0.1',
    port: 3068,
    listener_count: 1
  });
}

function isListenerGuard(args) {
  return args.some(value => String(value).endsWith('verify-local-vision-listener.ps1'));
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
    if (isListenerGuard(args)) {
      return { code: 0, stdout: readyListenerGuard(), stderr: '' };
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
  assert.equal(calls.length, 5);
  assert(calls[0].args.includes('Start'));
  assert.equal(calls[0].options.settleOnExit, true);
  assert(isListenerGuard(calls[1].args));
  assert(calls[1].args.includes('4242'));
  assert.equal(calls[2].command, process.execPath);

  const request = JSON.parse(calls[2].options.input);
  assert.equal(request.kind, 'icon_only');
  assert.equal(request.coordinate_space, 'css_viewport');
  assert.equal(Object.prototype.hasOwnProperty.call(request, 'model_path'), false);
  assert.equal(Object.prototype.hasOwnProperty.call(request, 'port'), false);

  assert(calls[3].args.includes('Touch'));
  assert.equal(calls[3].options.settleOnExit, true);
  assert(isListenerGuard(calls[4].args));
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
          pid: 4242,
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
  let pythonCalled = false;
  const fakeRun = async (_command, args) => {
    if (args.includes('Start')) {
      return {
        code: 1,
        stdout: '',
        stderr: 'Exception: Vision runtime admission denied: free physical=1.38 GB, virtual=8.90 GB.'
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
    /vision-runtime-start-failed:.*admission denied: free physical=1\.38 GB/i
  );
  assert.equal(pythonCalled, false, 'runtime start failure must stop before production grounder invocation');
}

{
  let pythonCalled = false;
  let stopCalled = false;
  const fakeRun = async (_command, args) => {
    if (args.includes('Start')) return { code: 0, stdout: readyRuntime(), stderr: '' };
    if (isListenerGuard(args)) {
      return {
        code: 1,
        stdout: '',
        stderr: 'Vision runtime listener ownership mismatch. Expected pid=4242 on 127.0.0.1:3068.'
      };
    }
    if (args.includes('Stop')) {
      stopCalled = true;
      return { code: 0, stdout: JSON.stringify({ state: 'stopped' }), stderr: '' };
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
    /vision-runtime-listener-ownership-failed:.*ownership mismatch/i
  );
  assert.equal(pythonCalled, false, 'listener ownership failure must stop before production grounder invocation');
  assert.equal(stopCalled, true, 'listener ownership failure must clean up the owned runtime process');
}

{
  let touchCalled = false;
  const fakeRun = async (_command, args) => {
    if (args.includes('Start')) return { code: 0, stdout: readyRuntime(), stderr: '' };
    if (args.includes('Touch')) {
      touchCalled = true;
      return { code: 0, stdout: readyRuntime(), stderr: '' };
    }
    if (isListenerGuard(args)) {
      return { code: 0, stdout: readyListenerGuard(), stderr: '' };
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

if (process.platform === 'win32') {
  const grandchildCode = 'setTimeout(() => {}, 5000);';
  const parentCode = [
    "const { spawn } = require('node:child_process');",
    `const child = spawn(process.execPath, ['-e', ${JSON.stringify(grandchildCode)}], {`,
    "  stdio: ['ignore', 'inherit', 'inherit'],",
    '  windowsHide: true',
    '});',
    'child.unref();',
    "process.stdout.write(JSON.stringify({ status: 'ready' }));"
  ].join('\n');
  const startedAt = Date.now();
  const result = await collectRuntimeProcessForTest(
    process.execPath,
    ['-e', parentCode],
    { timeoutMs: 1500, settleOnExit: true, exitDrainMs: 100 }
  );
  const elapsedMs = Date.now() - startedAt;
  assert.equal(result.code, 0);
  assert.deepEqual(JSON.parse(result.stdout), { status: 'ready' });
  assert(elapsedMs < 1200, `controller exit settlement took ${elapsedMs}ms`);
  console.log('RUNTIME_BACKED_VISUAL_GROUNDER_DESCENDANT_STDIO=PASS');

  const server = net.createServer(socket => socket.end());
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  const address = server.address();
  assert(address && typeof address === 'object');
  const previousTestMode = process.env.CHAT_VISION_RUNTIME_TEST_MODE;
  process.env.CHAT_VISION_RUNTIME_TEST_MODE = '1';
  try {
    const guardArgs = [
      '-NoLogo',
      '-NoProfile',
      '-ExecutionPolicy',
      'Bypass',
      '-File',
      paths.listenerGuardPath,
      '-ExpectedPid',
      String(process.pid),
      '-Port',
      String(address.port)
    ];
    const owned = await collectRuntimeProcessForTest(
      'pwsh.exe',
      guardArgs,
      { timeoutMs: 5000, settleOnExit: true, exitDrainMs: 100 }
    );
    assert.equal(owned.code, 0, `${owned.stderr}\n${owned.stdout}`);
    const ownedPayload = JSON.parse(owned.stdout);
    assert.equal(ownedPayload.owned, true);
    assert.equal(ownedPayload.pid, process.pid);
    assert.equal(ownedPayload.port, address.port);

    const wrongPid = process.pid === 1 ? 2 : 1;
    const rejected = await collectRuntimeProcessForTest(
      'pwsh.exe',
      guardArgs.map((value, index) => index === guardArgs.indexOf(String(process.pid)) ? String(wrongPid) : value),
      { timeoutMs: 5000, settleOnExit: true, exitDrainMs: 100 }
    );
    assert.notEqual(rejected.code, 0);
    assert.match(`${rejected.stderr}\n${rejected.stdout}`, /listener ownership mismatch/i);
    console.log('RUNTIME_BACKED_VISUAL_GROUNDER_LISTENER_OWNERSHIP=PASS');
  } finally {
    if (previousTestMode === undefined) delete process.env.CHAT_VISION_RUNTIME_TEST_MODE;
    else process.env.CHAT_VISION_RUNTIME_TEST_MODE = previousTestMode;
    await new Promise(resolve => server.close(resolve));
  }
}

{
  assert.equal(paths.reviewedProfile, 'lfm25-vl-450m-f16');
  assert.equal(paths.reviewedPort, 3068);
  assert(paths.controllerPath.endsWith('scripts\\local-vision-runtime.ps1') || paths.controllerPath.endsWith('scripts/local-vision-runtime.ps1'));
  assert(paths.listenerGuardPath.endsWith('scripts\\verify-local-vision-listener.ps1') || paths.listenerGuardPath.endsWith('scripts/verify-local-vision-listener.ps1'));
  assert(paths.grounderCliPath.endsWith('scripts\\production-visual-grounder.py') || paths.grounderCliPath.endsWith('scripts/production-visual-grounder.py'));
}

console.log('RUNTIME_BACKED_VISUAL_GROUNDER=PASS');
console.log('RUNTIME_BACKED_VISUAL_GROUNDER_FIXED_PROFILE=PASS');
console.log('RUNTIME_BACKED_VISUAL_GROUNDER_RUNTIME_DIAGNOSTICS=PASS');
console.log('RUNTIME_BACKED_VISUAL_GROUNDER_LISTENER_GUARD=PASS');
console.log('RUNTIME_BACKED_VISUAL_GROUNDER_TOUCH_ON_ERROR=PASS');
