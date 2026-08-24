import process from 'node:process';

import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

export const EXPECTED_SEMANTIC_TOOLS = Object.freeze([
  'procedure_run',
  'web_interact',
  'web_observe',
  'web_open',
  'workspace_read',
  'workspace_write'
]);

function stringEnvironment(source) {
  const env = {};
  for (const [key, value] of Object.entries(source ?? {})) {
    if (typeof value === 'string') env[key] = value;
  }
  return env;
}

export async function assertExpectedSemanticInventory({ entry, env = process.env }) {
  if (typeof entry !== 'string' || entry.length === 0) {
    throw new Error('semantic inventory guard requires one semantic entry path');
  }

  const client = new Client({
    name: 'chat-semantic-inventory-guard',
    version: '1.0.0'
  });
  const transport = new StdioClientTransport({
    command: process.execPath,
    args: [entry],
    env: stringEnvironment(env)
  });

  try {
    await client.connect(transport);
    const inventory = await client.listTools();
    const names = inventory.tools.map(tool => tool.name).sort();
    if (names.length !== EXPECTED_SEMANTIC_TOOLS.length) {
      throw new Error(
        `semantic inventory guard expected exactly six canonical tools; actual: ${names.join(', ')}`
      );
    }
    for (let index = 0; index < EXPECTED_SEMANTIC_TOOLS.length; index += 1) {
      if (names[index] !== EXPECTED_SEMANTIC_TOOLS[index]) {
        throw new Error(
          `semantic inventory guard expected exactly: ${EXPECTED_SEMANTIC_TOOLS.join(', ')}; actual: ${names.join(', ')}`
        );
      }
    }
    return names;
  } finally {
    await client.close().catch(() => {});
  }
}
