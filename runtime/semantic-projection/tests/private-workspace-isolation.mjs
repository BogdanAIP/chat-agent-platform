import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import {
  assertPrivateWorkspaceIsolation,
  prepareSemanticRuntimeEnvironment
} from '../bin/semantic-projection-launcher.mjs';

const root = fs.mkdtempSync(path.join(os.tmpdir(), 'semantic-private-workspace-'));

try {
  const localAppData = path.join(root, 'local-app-data');
  const managerRoot = path.join(localAppData, 'ChatAgentPlatform');
  const reviewerState = path.join(
    managerRoot,
    'state',
    'procedure-runtime',
    'independent-review-v1'
  );
  const safeWorkspace = path.join(root, 'workspace');
  const tempDir = path.join(root, 'tmp');

  fs.mkdirSync(reviewerState, { recursive: true });
  fs.mkdirSync(safeWorkspace, { recursive: true });
  fs.mkdirSync(tempDir, { recursive: true });
  fs.writeFileSync(
    path.join(reviewerState, 'operation.genesis.json'),
    JSON.stringify({ review_run_id: 'a'.repeat(64) }),
    'utf8'
  );

  const baseOptions = {
    platform: 'win32',
    pid: 4242,
    tempDir
  };

  const safe = assertPrivateWorkspaceIsolation({
    ...baseOptions,
    env: {
      LOCALAPPDATA: localAppData,
      CHAT_LOCAL_FILES_ROOT: safeWorkspace
    }
  });
  assert.equal(safe.workspaceRoot, fs.realpathSync.native(safeWorkspace));
  assert.equal(safe.managerRoot, fs.realpathSync.native(managerRoot));

  const prepared = prepareSemanticRuntimeEnvironment({
    ...baseOptions,
    env: {
      LOCALAPPDATA: localAppData,
      CHAT_LOCAL_FILES_ROOT: safeWorkspace
    }
  });
  assert.equal(
    prepared.env.PLAYWRIGHT_MCP_OUTPUT_DIR,
    prepared.playwrightOutputDirectory
  );

  for (const unsafeWorkspace of [
    managerRoot,
    path.join(managerRoot, 'state'),
    path.join(managerRoot, 'state', 'procedure-runtime'),
    localAppData
  ]) {
    assert.throws(
      () => assertPrivateWorkspaceIsolation({
        ...baseOptions,
        env: {
          LOCALAPPDATA: localAppData,
          CHAT_LOCAL_FILES_ROOT: unsafeWorkspace
        }
      }),
      /path-disjoint from manager-owned state/
    );
  }

  const aliasRoot = path.join(root, 'manager-alias');
  fs.symlinkSync(
    managerRoot,
    aliasRoot,
    process.platform === 'win32' ? 'junction' : 'dir'
  );
  assert.throws(
    () => assertPrivateWorkspaceIsolation({
      ...baseOptions,
      env: {
        LOCALAPPDATA: localAppData,
        CHAT_LOCAL_FILES_ROOT: path.join(aliasRoot, 'state')
      }
    }),
    /path-disjoint from manager-owned state/
  );

  console.log('SEMANTIC_PRIVATE_WORKSPACE_ISOLATION=PASS');
} finally {
  fs.rmSync(root, { recursive: true, force: true });
}
