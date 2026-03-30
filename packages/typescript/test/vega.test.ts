import test from "node:test";
import assert from "node:assert/strict";

import { KWeaverClient } from "../src/client.js";

const BASE = "https://mock.kweaver.test";
const TOKEN = "test-token-abc";

function makeClient(): KWeaverClient {
  return new KWeaverClient({ baseUrl: BASE, accessToken: TOKEN });
}

function mockFetch(response: unknown, statusCode = 200) {
  const orig = globalThis.fetch;
  const calls: Array<{ url: string; method: string; body?: string }> = [];

  globalThis.fetch = async (input: string | URL | Request, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
    const method = init?.method ?? "GET";
    const body = init?.body ? String(init.body) : undefined;
    calls.push({ url, method, body });
    const text = typeof response === "string" ? response : JSON.stringify(response);
    return new Response(text, { status: statusCode });
  };

  return { calls, restore: () => { globalThis.fetch = orig; } };
}

// ── catalog health-status: ids must be in the path, not query ──────────────

test("vega.catalogHealthStatus sends ids in the URL path, not query params", async () => {
  const mock = mockFetch({ entries: [{ id: "c-1", health_status: "healthy" }] });
  try {
    const client = makeClient();
    await client.vega.catalogHealthStatus("c-1");
    const url = new URL(mock.calls[0].url);
    // Correct: /api/vega-backend/v1/catalogs/c-1/health-status
    assert.equal(url.pathname, "/api/vega-backend/v1/catalogs/c-1/health-status");
    // ids should NOT be a query param
    assert.equal(url.searchParams.get("ids"), null, "ids must not be in query params");
  } finally {
    mock.restore();
  }
});

test("vega.catalogHealthStatus handles comma-separated multi-ids in path", async () => {
  const mock = mockFetch({ entries: [] });
  try {
    await makeClient().vega.catalogHealthStatus("c-1,c-2");
    const url = new URL(mock.calls[0].url);
    assert.equal(url.pathname, "/api/vega-backend/v1/catalogs/c-1,c-2/health-status");
  } finally {
    mock.restore();
  }
});

// ── resource preview: endpoint does not exist on backend ───────────────────

test("vega resource has no previewResource method (backend has no preview endpoint)", () => {
  const client = makeClient();
  assert.equal(
    typeof (client.vega as Record<string, unknown>).previewResource,
    "undefined",
    "previewResource should not exist — backend has no /resources/{id}/preview endpoint",
  );
});
