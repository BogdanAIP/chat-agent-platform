import { createRequire } from 'node:module';
import path from 'node:path';
import process from 'node:process';

import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

import { semanticProviderEnvironment } from './semantic-activation.mjs';


const VERSION = '0.1.0';
const DEFENSE_BLOCKED_ORIGINS = [
  'http://169.254.169.254:*',
  'https://169.254.169.254:*',
  'http://metadata.google.internal:*',
  'https://metadata.google.internal:*',
].join(';');

const REQUIRED_TOOLS = new Set([
  'browser_navigate',
  'browser_find',
  'browser_snapshot',
  'browser_click',
  'browser_type',
  'browser_take_screenshot',
  'browser_mouse_click_xy',
]);

const require = createRequire(import.meta.url);
const PLAYWRIGHT_MANIFEST = require.resolve('@playwright/mcp/package.json');
const PLAYWRIGHT_ENTRY = path.join(path.dirname(PLAYWRIGHT_MANIFEST), 'cli.js');


export class PlaywrightBrowserSemanticProvider {
  #sessionPromise = null;

  async #connect() {
    const client = new Client({
      name: 'chat-semantic-playwright-provider',
      version: VERSION,
    });
    const transport = new StdioClientTransport({
      command: process.execPath,
      args: [
        PLAYWRIGHT_ENTRY,
        '--headless',
        '--browser',
        'chrome',
        '--isolated',
        '--image-responses',
        'allow',
        '--blocked-origins',
        DEFENSE_BLOCKED_ORIGINS,
        '--block-service-workers',
        '--codegen',
        'none',
        '--caps',
        'vision',
        '--timeout-action',
        '15000',
      ],
      env: semanticProviderEnvironment(),
    });
    try {
      await client.connect(transport);
      const inventory = await client.listTools();
      const names = new Set(inventory.tools.map(tool => tool.name));
      const missing = [...REQUIRED_TOOLS].filter(name => !names.has(name));
      if (missing.length > 0) {
        throw new Error(
          `Playwright browser provider is missing required tools: ${missing.join(', ')}`,
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
      throw new Error(`Playwright browser provider refused non-allowlisted operation: ${name}`);
    }
    const { client } = await this.#session();
    return client.callTool({ name, arguments: args });
  }

  navigate(url) {
    return this.#call('browser_navigate', { url });
  }

  find(args) {
    return this.#call('browser_find', args);
  }

  snapshot(args = {}) {
    return this.#call('browser_snapshot', args);
  }

  click(args) {
    return this.#call('browser_click', args);
  }

  type(args) {
    return this.#call('browser_type', args);
  }

  takeScreenshot(args = {}) {
    return this.#call('browser_take_screenshot', args);
  }

  mouseClickXY(args) {
    return this.#call('browser_mouse_click_xy', args);
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


export function createPlaywrightBrowserSemanticProvider() {
  return new PlaywrightBrowserSemanticProvider();
}
