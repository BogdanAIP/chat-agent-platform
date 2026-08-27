import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import process from 'node:process';
import { URL } from 'node:url';

function parseArgs(argv) {
  const out = { port: 0, root: null, gateToken: null, generation: null };
  for (let i = 0; i < argv.length; i += 1) {
    const value = argv[i];
    if (value === '--root') out.root = argv[++i];
    else if (value === '--port') out.port = Number.parseInt(argv[++i], 10);
    else if (value === '--gate-token') out.gateToken = argv[++i];
    else if (value === '--generation') out.generation = argv[++i];
  }
  if (!out.root) throw new Error('--root is required');
  if (!out.gateToken) throw new Error('--gate-token is required');
  if (!out.generation) throw new Error('--generation is required');
  if (!Number.isInteger(out.port) || out.port < 0 || out.port > 65535) throw new Error('invalid --port');
  return out;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function writeJson(file, value) {
  fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

function writeJsonAtomic(file, value) {
  const temporary = `${file}.new-${process.pid}`;
  fs.writeFileSync(temporary, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
  fs.renameSync(temporary, file);
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

const { root, port, gateToken, generation } = parseArgs(process.argv.slice(2));
fs.mkdirSync(root, { recursive: true });
const seedPath = path.join(root, 'fixture-seed.json');
const statePath = path.join(root, 'server-state.json');
const finishPath = path.join(root, 'finish-gate.json');
const auditPath = path.join(root, 'audit.jsonl');
const snapshotPath = path.join(root, 'frozen-snapshot.json');

const seed = readJson(seedPath);
if (!Array.isArray(seed.cases) || !seed.target_id || !seed.expected) {
  throw new Error('fixture-seed.json is missing cases/target_id/expected');
}

const originalCases = clone(seed.cases);
let cases = clone(seed.cases);
let saveCount = 0;
let frozen = false;
const mutatedIds = new Set();
const auditEntries = [];
fs.writeFileSync(auditPath, '', 'utf8');

function targetCase() {
  return cases.find(item => item.id === seed.target_id) ?? null;
}

function currentState() {
  return { cases: clone(cases), save_count: saveCount, mutated_ids: [...mutatedIds] };
}

function recomputeFinishGate() {
  const target = targetCase();
  const oldTarget = originalCases.find(item => item.id === seed.target_id);
  const decoys = cases.filter(item => item.id !== seed.target_id);
  const originalDecoys = originalCases.filter(item => item.id !== seed.target_id);
  const checks = {
    target_exists: Boolean(target),
    address_exact: target?.address === seed.expected.address,
    status_exact: target?.status === seed.expected.status,
    comment_exact: target?.comment === seed.expected.comment,
    old_address_absent_in_target: Boolean(target) && target.address !== oldTarget?.address,
    decoys_unchanged: JSON.stringify(decoys) === JSON.stringify(originalDecoys),
    only_target_ever_mutated: [...mutatedIds].every(id => id === seed.target_id),
  };
  const status = Object.values(checks).every(Boolean) ? 'done' : 'not_done';
  const gate = {
    status,
    target_id: seed.target_id,
    checks,
    save_count: saveCount,
    mutated_ids: [...mutatedIds],
  };
  writeJson(statePath, currentState());
  writeJson(finishPath, gate);
  return gate;
}

function appendAudit(entry) {
  const record = { at: new Date().toISOString(), ...entry };
  auditEntries.push(clone(record));
  fs.appendFileSync(auditPath, `${JSON.stringify(record)}\n`, 'utf8');
}

function freezeSnapshot() {
  if (!frozen) frozen = true;
  const finish = recomputeFinishGate();
  const snapshot = {
    schema_version: 1,
    fixture_generation: generation,
    frozen: true,
    frozen_at: new Date().toISOString(),
    seed: clone(seed),
    state: currentState(),
    finish: clone(finish),
    audit: clone(auditEntries),
  };
  writeJsonAtomic(snapshotPath, snapshot);
  return snapshot;
}

function layout(title, body) {
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${escapeHtml(title)}</title>
<style>
body { font-family: system-ui, sans-serif; max-width: 920px; margin: 32px auto; padding: 0 18px; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #bbb; padding: 8px; text-align: left; }
label { display: block; margin-top: 12px; }
input[type=text], textarea { width: min(680px, 95%); padding: 7px; }
fieldset { margin-top: 14px; }
.actions { margin-top: 18px; display: flex; gap: 12px; }
.notice { padding: 8px 12px; background: #f2f2f2; }
</style>
</head>
<body>${body}</body>
</html>`;
}

function homePage(url) {
  const q = (url.searchParams.get('q') ?? '').trim().toLowerCase();
  const visible = q
    ? cases.filter(item => [item.id, item.client, item.address, item.status].some(value => String(value).toLowerCase().includes(q)))
    : cases;
  const rows = visible.map(item => `<tr>
<td>${escapeHtml(item.id)}</td>
<td>${escapeHtml(item.client)}</td>
<td>${escapeHtml(item.status)}</td>
<td><a href="/case/${encodeURIComponent(item.id)}">Open ${escapeHtml(item.id)}</a></td>
</tr>`).join('\n');
  return layout('Case Desk', `
<h1>Case Desk</h1>
<p class="notice">Customer support cases. Similar customer names may refer to different case IDs.</p>
<form method="get" action="/">
<label for="search">Search cases</label>
<input id="search" name="q" type="text" value="${escapeHtml(url.searchParams.get('q') ?? '')}">
<button type="submit">Search</button>
</form>
<h2>Cases</h2>
<table>
<thead><tr><th>Case ID</th><th>Customer</th><th>Status</th><th>Action</th></tr></thead>
<tbody>${rows || '<tr><td colspan="4">No matching cases</td></tr>'}</tbody>
</table>`);
}

function detailPage(item) {
  return layout(`Case ${item.id}`, `
<p><a href="/">Back to cases</a></p>
<h1>Case ${escapeHtml(item.id)}</h1>
<dl>
<dt>Customer</dt><dd>${escapeHtml(item.client)}</dd>
<dt>Status</dt><dd>${escapeHtml(item.status)}</dd>
<dt>Delivery address</dt><dd>${escapeHtml(item.address)}</dd>
<dt>Comment</dt><dd>${escapeHtml(item.comment)}</dd>
</dl>
<div class="actions"><a href="/case/${encodeURIComponent(item.id)}/edit">Edit case ${escapeHtml(item.id)}</a></div>`);
}

function editPage(item) {
  const statusRadio = status => `<label><input type="radio" name="status" value="${status}" ${item.status === status ? 'checked' : ''}> ${status}</label>`;
  return layout(`Edit ${item.id}`, `
<p><a href="/case/${encodeURIComponent(item.id)}">Cancel edit</a></p>
<h1>Edit case ${escapeHtml(item.id)}</h1>
<p>Customer: <strong>${escapeHtml(item.client)}</strong></p>
<form method="post" action="/case/${encodeURIComponent(item.id)}/save">
<label for="address">Delivery address</label>
<input id="address" name="address" type="text" value="${escapeHtml(item.address)}">
<label for="comment">Comment</label>
<textarea id="comment" name="comment" rows="4">${escapeHtml(item.comment)}</textarea>
<fieldset><legend>Status</legend>${statusRadio('Pending')}${statusRadio('Approved')}</fieldset>
<div class="actions"><button type="submit">Save case</button></div>
</form>`);
}

function sendHtml(response, status, html) {
  response.writeHead(status, { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' });
  response.end(html);
}

function sendJson(response, status, value) {
  response.writeHead(status, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' });
  response.end(`${JSON.stringify(value)}\n`);
}

function collectBody(request) {
  return new Promise((resolve, reject) => {
    let body = '';
    request.setEncoding('utf8');
    request.on('data', chunk => {
      body += chunk;
      if (body.length > 64 * 1024) reject(new Error('request body too large'));
    });
    request.on('end', () => resolve(body));
    request.on('error', reject);
  });
}

recomputeFinishGate();

const server = http.createServer(async (request, response) => {
  try {
    const url = new URL(request.url, 'http://127.0.0.1');
    if (request.method === 'GET' && url.pathname === '/health') {
      return sendJson(response, 200, { status: 'ok', finish: recomputeFinishGate().status, frozen, generation });
    }

    if (request.method === 'POST' && url.pathname === '/__gate/freeze') {
      if (request.headers['x-gate-token'] !== gateToken) {
        return sendJson(response, 403, { status: 'forbidden' });
      }
      const snapshot = freezeSnapshot();
      return sendJson(response, 200, {
        status: 'frozen',
        generation,
        snapshot_file: path.basename(snapshotPath),
        finish: snapshot.finish.status,
      });
    }

    if (request.method === 'GET' && url.pathname === '/') {
      return sendHtml(response, 200, homePage(url));
    }

    let match = url.pathname.match(/^\/case\/([^/]+)$/);
    if (request.method === 'GET' && match) {
      const id = decodeURIComponent(match[1]);
      const item = cases.find(candidate => candidate.id === id);
      return item ? sendHtml(response, 200, detailPage(item)) : sendHtml(response, 404, layout('Not found', '<h1>Case not found</h1>'));
    }

    match = url.pathname.match(/^\/case\/([^/]+)\/edit$/);
    if (request.method === 'GET' && match) {
      const id = decodeURIComponent(match[1]);
      const item = cases.find(candidate => candidate.id === id);
      return item ? sendHtml(response, 200, editPage(item)) : sendHtml(response, 404, layout('Not found', '<h1>Case not found</h1>'));
    }

    match = url.pathname.match(/^\/case\/([^/]+)\/save$/);
    if (request.method === 'POST' && match) {
      if (frozen) return sendJson(response, 423, { status: 'frozen' });
      const id = decodeURIComponent(match[1]);
      const index = cases.findIndex(candidate => candidate.id === id);
      if (index < 0) return sendHtml(response, 404, layout('Not found', '<h1>Case not found</h1>'));
      const body = await collectBody(request);
      // A save request may have started before the freeze request while its
      // body was still arriving. Re-check after body collection so no commit
      // can cross the quiesce boundary.
      if (frozen) return sendJson(response, 423, { status: 'frozen' });
      const form = new URLSearchParams(body);
      const address = form.get('address') ?? '';
      const comment = form.get('comment') ?? '';
      const status = form.get('status') ?? '';
      if (!['Pending', 'Approved'].includes(status)) return sendHtml(response, 400, layout('Invalid', '<h1>Invalid status</h1>'));
      const before = clone(cases[index]);
      cases[index] = { ...cases[index], address, comment, status };
      saveCount += 1;
      mutatedIds.add(id);
      appendAudit({ event: 'save', id, before, after: clone(cases[index]) });
      recomputeFinishGate();
      response.writeHead(303, { location: `/case/${encodeURIComponent(id)}`, 'cache-control': 'no-store' });
      return response.end();
    }

    return sendHtml(response, 404, layout('Not found', '<h1>Not found</h1>'));
  } catch (error) {
    return sendJson(response, 500, { status: 'error', message: error?.message ?? String(error) });
  }
});

server.listen(port, '127.0.0.1', () => {
  const address = server.address();
  const actualPort = typeof address === 'object' && address ? address.port : port;
  console.log(`READY ${JSON.stringify({ url: `http://127.0.0.1:${actualPort}/`, root, generation })}`);
});

for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, () => server.close(() => process.exit(0)));
}
