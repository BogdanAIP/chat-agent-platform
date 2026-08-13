import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);
const agentRoot = dirname(require.resolve('@1mcp/agent/package.json'));

async function patchFile(relativePath, expectedHash, replacements) {
  const path = join(agentRoot, relativePath);
  const original = await readFile(path, 'utf8');
  const actualHash = createHash('sha256').update(original).digest('hex');
  if (actualHash !== expectedHash) {
    throw new Error(`${relativePath} hash mismatch: expected ${expectedHash}, got ${actualHash}`);
  }

  let patched = original;
  for (const [before, after] of replacements) {
    const occurrences = patched.split(before).length - 1;
    if (occurrences !== 1) {
      throw new Error(`${relativePath} expected one patch anchor, found ${occurrences}`);
    }
    patched = patched.replace(before, after);
  }
  await writeFile(path, patched, 'utf8');
}

await patchFile(
  'build/core/configChangeHandler.js',
  '371587f5d19201f33e2fd18c2ad33b7db1552e763d80b0c36783e71754d09d1e',
  [[
    '        const newConfig = this.configManager.getTransportConfig();',
    `        const activeConfig = this.configManager.getTransportConfig();
        const declaredConfig = this.configManager.loadDeclaredServerConfigs();
        if (declaredConfig.errors.length > 0) {
            logger.warn('Skipping configuration changes because the declared configuration is invalid', {
                errors: declaredConfig.errors,
            });
            return;
        }
        // Active configs contain environment substitution. Declared configs retain
        // disabled entries so a disabled transition can still reach unloadMcpServer.
        const newConfig = { ...declaredConfig.staticServers, ...activeConfig };`,
  ]],
);

await patchFile(
  'build/core/server/serverManager.js',
  '02bfaed53dbbc94788feef13680d1fa1ee4b90c1ed04b9d53929c922a0d52ec3',
  [[
    `    async loadMcpServer(serverName, config) {
        const loadingManager = McpLoadingManager.current;
        await loadingManager.loadServer(serverName, config);
        if (config.disabled) {
            this.untrackMcpServer(serverName);
            return;
        }
        const loadingState = loadingManager.getStateTracker().getServerState(serverName)?.state;
        if (loadingState !== LoadingState.Ready) {
            this.untrackMcpServer(serverName);
            debugIf(() => ({
                message: \`Skipping lifecycle tracking for \${serverName}; loading state is \${loadingState ?? 'unknown'}\`,
            }));
            return;
        }
        this.recordMcpServerReady(serverName, config);
    }
    async unloadMcpServer(serverName) {`,
    `    async loadMcpServer(serverName, config) {
        const loadingManager = McpLoadingManager.current;
        try {
            await loadingManager.loadServer(serverName, config);
            if (config.disabled) {
                this.untrackMcpServer(serverName);
                return;
            }
            const loadingState = loadingManager.getStateTracker().getServerState(serverName)?.state;
            if (loadingState !== LoadingState.Ready) {
                this.untrackMcpServer(serverName);
                debugIf(() => ({
                    message: \`Skipping lifecycle tracking for \${serverName}; loading state is \${loadingState ?? 'unknown'}\`,
                }));
                return;
            }
            this.recordMcpServerReady(serverName, config);
        }
        finally {
            // Lazy mode keeps its own backend registry. Refresh it after every
            // load attempt, including a failed reload that removed an old client.
            await this.lazyLoadingOrchestrator?.refreshCapabilities();
        }
    }
    async unloadMcpServer(serverName) {`,
  ], [
    `        finally {
            this.untrackMcpServer(serverName);
        }
    }
    getMcpServerStatus() {`,
    `        finally {
            this.untrackMcpServer(serverName);
            // Keep the frozen Chat-facing tool list; only its lazy backend
            // registry changes when a catalog entry is disabled.
            await this.lazyLoadingOrchestrator?.refreshCapabilities();
        }
    }
    getMcpServerStatus() {`,
  ]],
);
