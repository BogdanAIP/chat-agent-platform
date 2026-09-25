#!/usr/bin/env node
// Qualification-only independent file-byte comparison after a Notepad candidate run.
// The expected and baseline files must be prepared separately from the UI executor.
import { createHash } from 'node:crypto';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';

function argumentsFrom(argv) {
  const names = new Set(['--before', '--expected', '--actual', '--decoy-before', '--decoy-after']);
  const args = {};
  for (let index = 0; index < argv.length; index += 2) {
    if (!names.has(argv[index]) || args[argv[index]] || !argv[index + 1]) {
      throw new Error('Usage: node scripts/check-notepad-candidate-effect.mjs --before FILE --expected FILE --actual FILE --decoy-before FILE --decoy-after FILE');
    }
    args[argv[index]] = argv[index + 1];
  }
  if (Object.keys(args).length !== names.size) {
    throw new Error('Missing required file: before, expected, actual, decoy-before and decoy-after are required');
  }
  return args;
}

const digest = bytes => createHash('sha256').update(bytes).digest('hex');

try {
  const args = argumentsFrom(process.argv.slice(2));
  const files = Object.keys(args);
  const identities = await Promise.all(files.map(async key => ({
    key, resolved: path.resolve(args[key]), info: await stat(args[key])
  })));
  for (let index = 0; index < identities.length; index += 1) {
    for (let other = index + 1; other < identities.length; other += 1) {
      const { key: left, resolved: leftPath, info: a } = identities[index];
      const { key: right, resolved: rightPath, info: b } = identities[other];
      if (leftPath === rightPath) {
        throw new Error(`Independent inputs must be different files: ${left}, ${right}`);
      }
      if (a.ino > 0 && b.ino > 0 && a.dev === b.dev && a.ino === b.ino) {
        throw new Error(`Independent inputs are the same physical file: ${left}, ${right}`);
      }
    }
  }
  const [before, expected, actual, decoyBefore, decoyAfter] = await Promise.all([
    '--before', '--expected', '--actual', '--decoy-before', '--decoy-after'
  ].map(key => readFile(args[key])));
  const effectDeclared = !before.equals(expected);
  const targetMatches = expected.equals(actual);
  const decoyUntouched = decoyBefore.equals(decoyAfter);
  const result = effectDeclared && targetMatches && decoyUntouched ? 'EFFECT_BYTES_MATCH' : 'EFFECT_NOT_PROVEN';
  console.log(JSON.stringify({
    result, effect_declared: effectDeclared, target_matches: targetMatches,
    decoy_untouched: decoyUntouched, actual_sha256: digest(actual),
    caution: 'File bytes only; CAP authorization, editor identity and completion require separate evidence.'
  }, null, 2));
  if (result !== 'EFFECT_BYTES_MATCH') process.exitCode = 1;
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
