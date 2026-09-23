import { createRequire } from 'node:module';
import process from 'node:process';

import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

import { semanticProviderEnvironment } from './semantic-activation.mjs';


const VERSION = '0.1.0';

function normalizeProviderResult(result) {
  const normalized = {
    content: Array.isArray(result?.content) ? result.content : [],
  };
  if (result?.isError) normalized.isError = true;
  if (result?.structuredContent !== undefined) {
    normalized.structuredContent = result.structuredContent;
  }
  return normalized;
}
const REQUIRED_TOOLS = new Set([
  'list_allowed_directories',
  'read_text_file',
  'search_files',
  'write_file',
]);

const require = createRequire(import.meta.url);
const FILESYSTEM_ENTRY = require.resolve(
  '@modelcontextprotocol/server-filesystem/dist/index.js',
);


export class FilesystemSemanticProvider {
  #workspaceRoot;
  #sessionPromise = null;

  constructor({ workspaceRoot }) {
    if (typeof workspaceRoot !== 'string' || !workspaceRoot) {
      throw new Error('FilesystemSemanticProvider requires one workspace root');
    }
    this.#workspaceRoot = workspaceRoot;
  }

  async #connect() {
    const client = new Client({
      name: 'chat-semantic-filesystem-provider',
      version: VERSION,
    });
    const transport = new StdioClientTransport({
      command: process.execPath,
      args: [FILESYSTEM_ENTRY, this.#workspaceRoot],
      env: semanticProviderEnvironment(),
    });
    try {
      await client.connect(transport);
      const inventory = await client.listTools();
      const names = new Set(inventory.tools.map(tool => tool.name));
      const missing = [...REQUIRED_TOOLS].filter(name => !names.has(name));
      if (missing.length > 0) {
        throw new Error(
          `filesystem provider is missing required tools: ${missing.join(', ')}`,
        );
      }
      return { client };
    } catch (error) {
      try { await client.close(); } catch {}
      throw error;
    }
  }

  async #session() {
    if (this.#sessionPromise === null) {
      this.#sessionPromise = this.#connect().catch(error => {
        this.#sessionPromise = null;
        throw error;
      });
    }
    return this.#sessionPromise;
  }

  async #call(name, args) {
    if (!REQUIRED_TOOLS.has(name)) {
      throw new Error(`filesystem provider refused non-allowlisted operation: ${name}`);
    }
    const { client } = await this.#session();
    return normalizeProviderResult(await client.callTool({ name, arguments: args }));
  }

  roots() {
    return this.#call('list_allowed_directories', {});
  }

  readText(args) {
    return this.#call('read_text_file', args);
  }

  search(args) {
    return this.#call('search_files', args);
  }

  writeText(args) {
    return this.#call('write_file', args);
  }

  async close() {
    const pending = this.#sessionPromise;
    this.#sessionPromise = null;
    if (pending === null) return;
    try {
      const { client } = await pending;
      await client.close();
    } catch {}
  }
}


export function createFilesystemSemanticProvider(options) {
  return new FilesystemSemanticProvider(options);
}
