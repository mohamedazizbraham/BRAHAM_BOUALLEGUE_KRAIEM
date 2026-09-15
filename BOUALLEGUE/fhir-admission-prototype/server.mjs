import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PUBLIC_DIR = path.join(__dirname, 'public');
const PORT = Number(process.env.PORT || 3000);
const FHIR_BASE_URL = (process.env.FHIR_BASE_URL || 'https://hapi.fhir.org/baseR4').replace(/\/$/, '');

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
};

function sendJson(res, status, data) {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' });
  res.end(JSON.stringify(data));
}

function safePublicPath(urlPath) {
  const normalized = path.normalize(urlPath).replace(/^([.][.][/\\])+/, '');
  const target = path.join(PUBLIC_DIR, normalized === '/' ? 'index.html' : normalized);
  if (!target.startsWith(PUBLIC_DIR)) return null;
  return target;
}

async function readRequestBody(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  return Buffer.concat(chunks);
}

async function proxyFhir(req, res, url) {
  const upstreamPath = url.pathname.replace(/^\/api\/fhir/, '') || '/';
  const upstreamUrl = `${FHIR_BASE_URL}${upstreamPath}${url.search}`;
  const body = ['GET', 'HEAD'].includes(req.method) ? undefined : await readRequestBody(req);

  const headers = {
    Accept: 'application/fhir+json, application/json',
  };
  if (body?.length) headers['Content-Type'] = req.headers['content-type'] || 'application/fhir+json';

  try {
    const upstream = await fetch(upstreamUrl, {
      method: req.method,
      headers,
      body,
      redirect: 'manual',
    });

    const text = await upstream.text();
    res.writeHead(upstream.status, {
      'Content-Type': upstream.headers.get('content-type') || 'application/fhir+json; charset=utf-8',
      'Cache-Control': 'no-store',
      'X-FHIR-Upstream': upstreamUrl,
      ...(upstream.headers.get('location') ? { Location: upstream.headers.get('location') } : {}),
    });
    res.end(text);
  } catch (error) {
    sendJson(res, 502, {
      resourceType: 'OperationOutcome',
      issue: [{
        severity: 'error',
        code: 'exception',
        diagnostics: `Impossible de contacter le serveur FHIR amont: ${error.message}`,
      }],
    });
  }
}

async function serveStatic(req, res, url) {
  let target = safePublicPath(decodeURIComponent(url.pathname));
  if (!target) return sendJson(res, 403, { error: 'Forbidden' });

  try {
    const stat = await fs.stat(target);
    if (stat.isDirectory()) target = path.join(target, 'index.html');
    const data = await fs.readFile(target);
    res.writeHead(200, {
      'Content-Type': MIME[path.extname(target)] || 'application/octet-stream',
      'Cache-Control': 'no-store',
    });
    res.end(data);
  } catch {
    // SPA fallback
    try {
      const data = await fs.readFile(path.join(PUBLIC_DIR, 'index.html'));
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' });
      res.end(data);
    } catch {
      sendJson(res, 404, { error: 'Not found' });
    }
  }
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || `localhost:${PORT}`}`);

  if (url.pathname === '/api/config') {
    return sendJson(res, 200, { fhirBaseUrl: FHIR_BASE_URL, proxyBaseUrl: '/api/fhir' });
  }

  if (url.pathname.startsWith('/api/fhir')) {
    return proxyFhir(req, res, url);
  }

  return serveStatic(req, res, url);
});

server.listen(PORT, () => {
  console.log(`Prototype admission FHIR disponible sur http://localhost:${PORT}`);
  console.log(`Serveur FHIR amont: ${FHIR_BASE_URL}`);
});
