#!/usr/bin/env node
// Qualification-only inspection of one caller-specified application window.
// No input, invoke, set-value, screenshot, save, or CAP public route.
import { spawnSync } from 'node:child_process';

function parseArgs(argv) {
  if (argv.length !== 6 || argv[0] !== '--pid' || argv[2] !== '--hwnd'
      || argv[4] !== '--process' || !/^[1-9][0-9]*$/.test(argv[1])
      || !/^[1-9][0-9]*$/.test(argv[3])
      || !/^[a-z0-9][a-z0-9_.-]{0,127}$/i.test(argv[5])) {
    throw new Error('Usage: node scripts/probe-winapp-window.mjs --pid <PID> --hwnd <HWND> --process <image.exe>');
  }
  const pid = Number(argv[1]);
  const hwnd = Number(argv[3]);
  if (!Number.isSafeInteger(pid) || !Number.isSafeInteger(hwnd)) {
    throw new Error('PID and HWND must be safe positive integers');
  }
  return { pid, hwnd, processName: argv[5] };
}

function readWinAppJson(args) {
  const result = spawnSync('winapp', ['ui', ...args, '--json'], {
    shell: false, encoding: 'utf8', windowsHide: true, timeout: 20_000,
    maxBuffer: 2 * 1024 * 1024
  });
  if (result.error) throw new Error(`winapp unavailable or timed out: ${result.error.message}`);
  if (result.status !== 0) throw new Error(`winapp ui ${args[0]} failed with exit ${result.status}`);
  try { return JSON.parse(result.stdout); }
  catch { throw new Error(`winapp ui ${args[0]} did not return a single JSON result`); }
}

function countControls(nodes, counts = Object.create(null)) {
  for (const node of nodes) {
    const type = typeof node.type === 'string' ? node.type : 'unknown';
    counts[type] = (counts[type] ?? 0) + 1;
    if (Array.isArray(node.children)) countControls(node.children, counts);
  }
  return counts;
}

try {
  if (process.platform !== 'win32') throw new Error('This read-only UI probe requires a Windows desktop session');
  const { pid, hwnd, processName } = parseArgs(process.argv.slice(2));
  const status = readWinAppJson(['status', '-w', String(hwnd)]);
  if (status.processId !== pid || status.hwnd !== hwnd
      || typeof status.processName !== 'string'
      || status.processName.toLowerCase().replace(/\.exe$/, '')
          !== processName.toLowerCase().replace(/\.exe$/, '')) {
    throw new Error('Specified window does not belong to the expected process; no inspect performed');
  }
  const tree = readWinAppJson(['inspect', '-w', String(hwnd)]);
  if (!Array.isArray(tree.windows) || tree.windows.length < 1
      || tree.windows[0]?.hwnd !== hwnd || !Array.isArray(tree.windows[0]?.elements)) {
    throw new Error('Inspection returned no unambiguous tree for the specified HWND');
  }
  console.log(JSON.stringify({
    result: 'OBSERVED_ONLY', pid, hwnd, process_name: status.processName,
    control_types: countControls(tree.windows[0].elements),
    caution: 'Read-only structural observation. No text, file bytes, Save effect or CAP authority verified.'
  }, null, 2));
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
