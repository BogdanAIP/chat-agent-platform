#!/usr/bin/env node

const endpoint = process.argv[2];
const markerPath = process.argv[3];

if (!endpoint || !markerPath) {
  throw new Error('Usage: node tests/adaptive-mcp-acceptance.mjs <mcp-url> <marker-path>');
}

let sessionId;
let requestId = 0;

function nextId() {
  requestId += 1;
  return requestId;
}

function parseJsonRpcBody(text, contentType) {
  const trimmed = text.trim();
  if (!trimmed) return null;

  if ((contentType || '').toLowerCase().includes('text/event-stream')) {
    const payloads = [];
    for (const line of trimmed.split(/\r?\n/)) {
      if (!line.startsWith('data:')) continue;
      const data = line.slice(5).trim();
      if (!data || data === '[DONE]') continue;
      payloads.push(JSON.parse(data));
    }
    if (payloads.length === 0) {
      throw new Error(`SSE response contained no JSON-RPC data: ${trimmed}`);
    }
    return payloads[payloads.length - 1];
  }

  return JSON.parse(trimmed);
}

async function postRpc(payload, { expectResponse = true } = {}) {
  const headers = {
    accept: 'application/json, text/event-stream',
    'content-type': 'application/json',
  };
  if (sessionId) headers['mcp-session-id'] = sessionId;

  const response = await fetch(endpoint, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`MCP HTTP ${response.status}: ${body}`);
  }

  const newSessionId = response.headers.get('mcp-session-id');
  if (newSessionId) sessionId = newSessionId;

  const text = await response.text();
  if (!expectResponse) return null;

  const message = parseJsonRpcBody(text, response.headers.get('content-type'));
  if (!message) throw new Error('Expected JSON-RPC response, got an empty body.');
  if (message.error) {
    throw new Error(`MCP error ${message.error.code}: ${message.error.message}`);
  }
  return message.result;
}

async function initialize() {
  const result = await postRpc({
    jsonrpc: '2.0',
    id: nextId(),
    method: 'initialize',
    params: {
      protocolVersion: '2025-06-18',
      capabilities: {},
      clientInfo: {
        name: 'chat-agent-platform-adaptive-acceptance',
        version: '1.0.0',
      },
    },
  });

  if (!sessionId) throw new Error('1MCP did not return an MCP session id.');
  if (!result?.protocolVersion) throw new Error('Initialize response did not contain protocolVersion.');

  await postRpc(
    {
      jsonrpc: '2.0',
      method: 'notifications/initialized',
      params: {},
    },
    { expectResponse: false },
  );
}

async function listTools() {
  return postRpc({
    jsonrpc: '2.0',
    id: nextId(),
    method: 'tools/list',
    params: {},
  });
}

async function callTool(name, args = {}) {
  const result = await postRpc({
    jsonrpc: '2.0',
    id: nextId(),
    method: 'tools/call',
    params: {
      name,
      arguments: args,
    },
  });

  if (result?.isError) {
    throw new Error(`Tool ${name} returned isError: ${JSON.stringify(result)}`);
  }
  return result;
}

function structured(result) {
  if (result?.structuredContent !== undefined) return result.structuredContent;
  const textItem = result?.content?.find((item) => item?.type === 'text' && typeof item.text === 'string');
  if (!textItem) return result;
  try {
    return JSON.parse(textItem.text);
  } catch {
    return textItem.text;
  }
}

function assertIncludes(haystack, needle, message) {
  if (!JSON.stringify(haystack).includes(needle)) {
    throw new Error(`${message}: missing ${needle}. Observed: ${JSON.stringify(haystack)}`);
  }
}

function assertManagementSuccess(result, operation) {
  if (result?.status !== 'success') {
    throw new Error(`${operation} failed. Observed: ${JSON.stringify(result)}`);
  }
}

async function waitForLazyTool(server, toolName) {
  let observed;
  for (let attempt = 0; attempt < 90; attempt += 1) {
    observed = structured(await callTool('tool_list', { server }));
    const tools = Array.isArray(observed?.tools) ? observed.tools : [];
    if (tools.some((tool) => tool?.name === toolName)) return observed;
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  throw new Error(
    `Adaptive backend ${server} did not publish ${toolName}. Observed: ${JSON.stringify(observed)}`,
  );
}

async function waitForLazyToolRemoval(server, toolName) {
  let observed;
  for (let attempt = 0; attempt < 60; attempt += 1) {
    observed = structured(await callTool('tool_list', { server }));
    const tools = Array.isArray(observed?.tools) ? observed.tools : [];
    if (!tools.some((tool) => tool?.name === toolName)) return;
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  throw new Error(
    `Adaptive backend ${server} still publishes ${toolName} after disable. Observed: ${JSON.stringify(observed)}`,
  );
}

async function main() {
  await initialize();

  const visible = await listTools();
  const names = (visible?.tools || []).map((tool) => tool.name);
  for (const required of [
    'tool_list',
    'tool_schema',
    'tool_invoke',
    '1mcp_1mcp_mcp_list',
    '1mcp_1mcp_mcp_status',
    '1mcp_1mcp_mcp_enable',
    '1mcp_1mcp_mcp_disable',
    '1mcp_1mcp_mcp_reload',
  ]) {
    if (!names.includes(required)) {
      throw new Error(`Adaptive Chat-facing surface is missing ${required}. Visible: ${names.join(', ')}`);
    }
  }

  // Keep mcp_list as a diagnostic only. 1MCP 0.35.0-beta.3 currently returns
  // an empty inventory here even though serve --config loaded the adaptive
  // runtime config. The important compatibility gate is whether the same MCP
  // session can enable a configured backend and immediately discover/invoke it
  // through the stable lazy-loading surface.
  const inventory = structured(await callTool('1mcp_1mcp_mcp_list', { format: 'json', detailed: true }));
  console.log(`ADAPTIVE_MCP_LIST_DIAGNOSTIC=${JSON.stringify(inventory)}`);

  try {
    const enableFilesystem = structured(await callTool('1mcp_1mcp_mcp_enable', { name: 'filesystem' }));
    assertManagementSuccess(enableFilesystem, 'Enable filesystem');
    await waitForLazyTool('filesystem', 'read_text_file');

    const read = structured(
      await callTool('tool_invoke', {
        server: 'filesystem',
        toolName: 'read_text_file',
        args: { path: markerPath },
      }),
    );
    assertIncludes(read, 'CHAT_ADAPTIVE_FILES_OK', 'Adaptive filesystem invocation');

    const disableFilesystem = structured(
      await callTool('1mcp_1mcp_mcp_disable', { name: 'filesystem', graceful: true }),
    );
    assertManagementSuccess(disableFilesystem, 'Disable filesystem');
    await waitForLazyToolRemoval('filesystem', 'read_text_file');

    const enablePlaywright = structured(await callTool('1mcp_1mcp_mcp_enable', { name: 'playwright' }));
    assertManagementSuccess(enablePlaywright, 'Enable playwright');
    await waitForLazyTool('playwright', 'browser_navigate');

    const page = structured(
      await callTool('tool_invoke', {
        server: 'playwright',
        toolName: 'browser_navigate',
        args: { url: 'https://example.com' },
      }),
    );
    assertIncludes(page, 'Example Domain', 'Adaptive browser invocation');

    await callTool('tool_invoke', {
      server: 'playwright',
      toolName: 'browser_close',
      args: {},
    });
    const disablePlaywright = structured(
      await callTool('1mcp_1mcp_mcp_disable', { name: 'playwright', graceful: true }),
    );
    assertManagementSuccess(disablePlaywright, 'Disable playwright');
    await waitForLazyToolRemoval('playwright', 'browser_navigate');
  } finally {
    for (const name of ['filesystem', 'playwright']) {
      try {
        await callTool('1mcp_1mcp_mcp_disable', { name, graceful: true, force: true });
      } catch {
        // Best-effort cleanup; the workflow stops the whole Runtime Scope next.
      }
    }
  }

  console.log('ADAPTIVE_MCP_ACCEPTANCE=passed');
}

await main();
