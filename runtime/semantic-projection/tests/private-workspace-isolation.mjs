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
  const managerStateRoot = path.join(managerRoot, 'state');
  const reviewerState = path.join(
    managerStateRoot,
    'procedure-runtime',
    'independent-review-v1'
  );
  const qualificationWorkspace = path.join(
    managerRoot,
    'qualification-worktrees',
    'case-1'
  );
  const safeWorkspace = path.join(root, 'workspace');
  const customParent = path.join(root, 'custom-private-parent');
  const customStateRoot = path.join(customParent, 'procedure-state');
  const customReviewRoot = path.join(customStateRoot, 'independent-review-v1');
  const tempDir = path.join(root, 'tmp');

  fs.mkdirSync(reviewerState, { recursive: true });
  fs.mkdirSync(qualificationWorkspace, { recursive: true });
  fs.mkdirSync(safeWorkspace, { recursive: true });
  fs.mkdirSync(customReviewRoot, { recursive: true });
  fs.mkdirSync(tempDir, { recursive: true });
  fs.writeFileSync(
    path.join(reviewerState, 'operation.genesis.json'),
    JSON.stringify({ review_run_id: 'a'.repeat(64) }),
    'utf8'
  );
  fs.writeFileSync(
    path.join(customReviewRoot, 'custom-operation.genesis.json'),
    JSON.stringify({ review_run_id: 'b'.repeat(64) }),
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
  assert.equal(safe.managerStateRoot, fs.realpathSync.native(managerStateRoot));
  assert.equal(safe.configuredReviewRoot, null);

  const safeCustom = assertPrivateWorkspaceIsolation({
    ...baseOptions,
    env: {
      LOCALAPPDATA: localAppData,
      CHAT_LOCAL_FILES_ROOT: safeWorkspace,
      CHAT_PROCEDURE_STATE_ROOT: customStateRoot
    }
  });
  assert.equal(
    safeCustom.configuredReviewRoot,
    fs.realpathSync.native(customReviewRoot)
  );

  const qualification = assertPrivateWorkspaceIsolation({
    ...baseOptions,
    env: {
      LOCALAPPDATA: localAppData,
      CHAT_LOCAL_FILES_ROOT: qualificationWorkspace
    }
  });
  assert.equal(
    qualification.workspaceRoot,
    fs.realpathSync.native(qualificationWorkspace)
  );

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
    managerStateRoot,
    path.join(managerStateRoot, 'procedure-runtime'),
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
      /path-disjoint from private manager state/
    );
  }

  for (const unsafeWorkspace of [
    customParent,
    customStateRoot,
    customReviewRoot,
    path.join(customReviewRoot, 'nested-workspace')
  ]) {
    fs.mkdirSync(unsafeWorkspace, { recursive: true });
    assert.throws(
      () => assertPrivateWorkspaceIsolation({
        ...baseOptions,
        env: {
          LOCALAPPDATA: localAppData,
          CHAT_LOCAL_FILES_ROOT: unsafeWorkspace,
          CHAT_PROCEDURE_STATE_ROOT: customStateRoot
        }
      }),
      /path-disjoint from configured independent-review state/
    );
  }

  // Reject the future private review directory before it exists, so starting a
  // session cannot create a readable state placement later in that same session.
  const futureWorkspace = path.join(root, 'future-custom-workspace');
  const futureStateRoot = path.join(futureWorkspace, 'future-state');
  fs.mkdirSync(futureWorkspace, { recursive: true });
  assert.throws(
    () => assertPrivateWorkspaceIsolation({
      ...baseOptions,
      env: {
        LOCALAPPDATA: localAppData,
        CHAT_LOCAL_FILES_ROOT: futureWorkspace,
        CHAT_PROCEDURE_STATE_ROOT: futureStateRoot
      }
    }),
    /path-disjoint from configured independent-review state/
  );
  assert.equal(fs.existsSync(futureStateRoot), false);

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
    /path-disjoint from private manager state/
  );

  const customAlias = path.join(root, 'custom-review-alias');
  fs.symlinkSync(
    customReviewRoot,
    customAlias,
    process.platform === 'win32' ? 'junction' : 'dir'
  );
  assert.throws(
    () => assertPrivateWorkspaceIsolation({
      ...baseOptions,
      env: {
        LOCALAPPDATA: localAppData,
        CHAT_LOCAL_FILES_ROOT: customAlias,
        CHAT_PROCEDURE_STATE_ROOT: customStateRoot
      }
    }),
    /path-disjoint from configured independent-review state/
  );

  console.log('SEMANTIC_PRIVATE_WORKSPACE_ISOLATION=PASS');
  console.log('SEMANTIC_CONFIGURED_REVIEW_STATE_ISOLATION=PASS');
  console.log('SEMANTIC_QUALIFICATION_WORKTREE_REMAINS_ALLOWED=PASS');
} finally {
  fs.rmSync(root, { recursive: true, force: true });
}
