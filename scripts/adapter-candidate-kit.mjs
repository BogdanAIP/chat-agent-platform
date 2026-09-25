#!/usr/bin/env node
// Read-only inventory. It never installs, launches or grants an adapter.
import { constants } from 'node:fs';
import { access, readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const manifestPath = path.join(root, 'config', 'adapter-candidate-kit.json');
const statuses = new Set([
  'current_scoped', 'current_optional', 'target_qualified',
  'comparison_candidate', 'reserve_candidate', 'future_candidate',
  'research_blocked', 'draft_unmerged'
]);

function usage() {
  console.log('Usage: node scripts/adapter-candidate-kit.mjs [--role ROLE] [--plan] [--json] [--check]');
  console.log('Read-only inventory; command detection is not an installation or qualification test.');
}

function argumentsFrom(argv) {
  const args = { role: null, json: false, check: false, plan: false };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === '--help') return null;
    if (argument === '--json') args.json = true;
    else if (argument === '--check') args.check = true;
    else if (argument === '--plan') args.plan = true;
    else if (argument === '--role' && argv[index + 1] && !argv[index + 1].startsWith('-')) {
      args.role = argv[++index];
    } else throw new Error(`Unknown or incomplete argument: ${argument}`);
  }
  return args;
}

async function exists(filePath) {
  try {
    await access(filePath, constants.F_OK);
    return true;
  } catch {
    return false;
  }
}

async function commandOnPath(command) {
  const entries = (process.env.PATH ?? '').split(path.delimiter).filter(Boolean);
  const extensions = process.platform === 'win32'
    ? (process.env.PATHEXT ?? '.COM;.EXE;.BAT;.CMD').split(';').filter(Boolean)
    : [''];
  for (const directory of entries) {
    for (const extension of extensions) {
      if (await exists(path.join(directory, `${command}${extension}`))) return true;
    }
  }
  return false;
}

function validate(manifest) {
  if (manifest.schema_version !== 1 || !Array.isArray(manifest.candidates)) {
    throw new Error('Unsupported candidate manifest schema');
  }
  const ids = new Set();
  for (const candidate of manifest.candidates) {
    if (!/^[a-z][a-z0-9-]+$/.test(candidate.id ?? '') || ids.has(candidate.id)) {
      throw new Error(`Invalid or repeated candidate id: ${candidate.id}`);
    }
    ids.add(candidate.id);
    if (!statuses.has(candidate.status) || typeof candidate.role !== 'string'
        || typeof candidate.component !== 'string' || typeof candidate.source !== 'string'
        || typeof candidate.first_check !== 'string') {
      throw new Error(`Incomplete candidate metadata: ${candidate.id}`);
    }
    if (candidate.source_ref && !/^[a-f0-9]{40}$/.test(candidate.source_ref)) {
      throw new Error(`Unpinned source reference: ${candidate.id}`);
    }
    for (const file of [candidate.local_anchor, candidate.qualification_asset, candidate.effect_check].filter(Boolean)) {
      if (!/^[a-z0-9_./-]+$/i.test(file)
          || file.split('/').includes('..') || path.isAbsolute(file)) {
        throw new Error(`Invalid project file: ${candidate.id}`);
      }
    }
    if (candidate.command && !/^[a-z0-9-]+$/i.test(candidate.command)) {
      throw new Error(`Invalid command name: ${candidate.id}`);
    }
  }
}

async function main() {
  const args = argumentsFrom(process.argv.slice(2));
  if (args === null) return usage();
  const manifest = JSON.parse(await readFile(manifestPath, 'utf8'));
  validate(manifest);
  const roles = [...new Set(manifest.candidates.map(candidate => candidate.role))].sort();
  if (args.role && !roles.includes(args.role)) {
    throw new Error(`Unknown role ${args.role}; use one of: ${roles.join(', ')}`);
  }
  const selected = manifest.candidates.filter(candidate => !args.role || candidate.role === args.role);
  const inspected = await Promise.all(selected.map(async candidate => ({
    ...candidate,
    project_anchor_present: candidate.local_anchor
      ? await exists(path.join(root, candidate.local_anchor)) : null,
    qualification_asset_present: candidate.qualification_asset
      ? await exists(path.join(root, candidate.qualification_asset)) : null,
    effect_check_present: candidate.effect_check
      ? await exists(path.join(root, candidate.effect_check)) : null,
    command_on_path: candidate.command ? await commandOnPath(candidate.command) : null
  })));
  const missingAnchors = inspected.filter(item => item.project_anchor_present === false
    || item.qualification_asset_present === false || item.effect_check_present === false);
  if (args.json) {
    console.log(JSON.stringify({ as_of: manifest.as_of, platform: process.platform,
      note: manifest.purpose, candidates: inspected, missing_project_anchors: missingAnchors.map(x => x.id) }, null, 2));
  } else {
    console.log(`CAP candidate inventory (${manifest.as_of}); ${inspected.length} entries; no adapter launched`);
    for (const item of inspected) {
      const command = item.command ? `; ${item.command} on PATH: ${item.command_on_path ? 'yes' : 'no'}` : '';
      const anchor = item.local_anchor ? `; project anchor: ${item.project_anchor_present ? 'present' : 'MISSING'}` : '';
      console.log(`${item.id} [${item.status}] ${item.component}${anchor}${command}`);
      if (args.plan) {
        if (item.qualification_asset) console.log(`  Existing probe: ${item.qualification_asset}`);
        if (item.effect_check) console.log(`  File effect check: ${item.effect_check}`);
        console.log(`  First check: ${item.first_check}`);
        if (item.blocker) console.log(`  Pending: ${item.blocker}`);
      }
    }
    if (args.check) console.log(`Manifest check: ${missingAnchors.length ? 'FAILED' : 'PASS'} (local anchors only)`);
  }
  if (args.check && missingAnchors.length) process.exitCode = 1;
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
