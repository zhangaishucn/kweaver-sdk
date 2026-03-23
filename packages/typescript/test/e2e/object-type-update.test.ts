/**
 * E2E: bkn object-type update (GET-merge-PUT) — add / update / remove data properties.
 *
 * - Read-only: needs KWEAVER_BASE_URL + valid ~/.kweaver token (ensure-token preflight).
 * - Mutating cycle: set E2E_RUN_DESTRUCTIVE=1 and optional E2E_OT_UPDATE_KN / E2E_OT_UPDATE_OT
 *   (defaults: football_league / player).
 *
 * Run (from packages/typescript):
 *   node --import tsx test/e2e/ensure-token.ts
 *   E2E_RUN_DESTRUCTIVE=1 npm run test:e2e
 */
import test from "node:test";
import assert from "node:assert/strict";
import { runCli, shouldSkipE2e, shouldRunDestructive } from "./setup.js";

function defaultKnOt(): { knId: string; otId: string } {
  const knId = process.env.E2E_OT_UPDATE_KN ?? "football_league";
  const otId = process.env.E2E_OT_UPDATE_OT ?? "player";
  return { knId, otId };
}

function shouldSkipDestructiveOtUpdate(): boolean {
  return shouldSkipE2e() || !shouldRunDestructive();
}

test("e2e: object-type get succeeds for configured update target", { skip: shouldSkipE2e() }, async () => {
  const { knId, otId } = defaultKnOt();
  const { code, stdout, stderr } = await runCli(["bkn", "object-type", "get", knId, otId]);
  if (code !== 0) {
    test.skip(`object-type get failed: ${stderr || stdout}`);
    return;
  }
  const raw = JSON.parse(stdout) as Record<string, unknown>;
  const ot = Array.isArray(raw.entries) ? (raw.entries[0] as Record<string, unknown>) : raw;
  assert.ok(ot && typeof ot === "object");
  assert.ok(Array.isArray(ot.data_properties) || ot.name !== undefined);
});

test(
  "e2e: object-type update add → update → remove temp property",
  { skip: shouldSkipDestructiveOtUpdate() },
  async () => {
    if (shouldSkipE2e()) {
      test.skip("no KWEAVER_BASE_URL");
      return;
    }
    const { knId, otId } = defaultKnOt();
    const { code: getCode, stderr: getErr } = await runCli(["bkn", "object-type", "get", knId, otId]);
    if (getCode !== 0) {
      test.skip(`object-type get failed: ${getErr}`);
      return;
    }

    const suffix = `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    const propName = `e2e_cli_tmp_${suffix}`;
    const addJson = JSON.stringify({
      name: propName,
      display_name: "E2E Temp",
      type: "string",
      comment: "kweaver-sdk e2e",
      mapped_field: {
        name: propName,
        type: "string",
        display_name: "E2E Temp",
      },
    });
    const updateJson = JSON.stringify({
      name: propName,
      display_name: "E2E Temp Updated",
      type: "string",
      comment: "kweaver-sdk e2e updated",
      mapped_field: {
        name: propName,
        type: "string",
        display_name: "E2E Temp Updated",
      },
    });

    const { code: c1, stderr: e1 } = await runCli([
      "bkn",
      "object-type",
      "update",
      knId,
      otId,
      "--add-property",
      addJson,
    ]);
    assert.equal(c1, 0, e1 || "add-property should succeed");

    const { code: c2, stderr: e2 } = await runCli([
      "bkn",
      "object-type",
      "update",
      knId,
      otId,
      "--update-property",
      updateJson,
    ]);
    assert.equal(c2, 0, e2 || "update-property should succeed");

    const { code: c3, stdout: outGet, stderr: e3 } = await runCli(["bkn", "object-type", "get", knId, otId]);
    assert.equal(c3, 0, e3 || "get after update");
    const parsed = JSON.parse(outGet) as Record<string, unknown>;
    const ot = Array.isArray(parsed.entries) ? (parsed.entries[0] as Record<string, unknown>) : parsed;
    const props = (Array.isArray(ot.data_properties) ? ot.data_properties : []) as Array<{
      name?: string;
      display_name?: string;
    }>;
    const found = props.find((p) => p.name === propName);
    assert.ok(found, "temp property should exist after update");
    assert.match(found.display_name ?? "", /Updated/);

    const { code: c4, stderr: e4 } = await runCli([
      "bkn",
      "object-type",
      "update",
      knId,
      otId,
      "--remove-property",
      propName,
    ]);
    assert.equal(c4, 0, e4 || "remove-property should succeed");

    const { code: c5, stdout: outFinal, stderr: e5 } = await runCli(["bkn", "object-type", "get", knId, otId]);
    assert.equal(c5, 0, e5);
    const rawFinal = JSON.parse(outFinal) as Record<string, unknown>;
    const otFinal = Array.isArray(rawFinal.entries)
      ? (rawFinal.entries[0] as Record<string, unknown>)
      : rawFinal;
    const propsFinal = (Array.isArray(otFinal.data_properties) ? otFinal.data_properties : []) as Array<{
      name?: string;
    }>;
    assert.ok(
      !propsFinal.some((p) => p.name === propName),
      "temp property should be removed",
    );
  },
);

test(
  "e2e: object-type update rejects merge flags combined with raw JSON body",
  { skip: shouldSkipE2e() },
  async () => {
    const { knId, otId } = defaultKnOt();
    const { code: getCode } = await runCli(["bkn", "object-type", "get", knId, otId]);
    if (getCode !== 0) {
      test.skip("target KN/OT not available");
      return;
    }
    const { code, stderr } = await runCli([
      "bkn",
      "object-type",
      "update",
      knId,
      otId,
      '{"name":"x"}',
      "--add-property",
      '{"name":"y","display_name":"Y","type":"string"}',
    ]);
    assert.equal(code, 1);
    assert.ok(
      stderr.includes("Do not combine") || stderr.includes("combine"),
      `expected combine error, got: ${stderr}`,
    );
  },
);

test(
  "e2e: kweaver call sets JSON content-type for PUT body (no 406)",
  { skip: shouldSkipE2e() },
  async () => {
    const { knId, otId } = defaultKnOt();
    const { code: getCode, stdout } = await runCli(["bkn", "object-type", "get", knId, otId]);
    if (getCode !== 0) {
      test.skip("object-type get failed");
      return;
    }
    const raw = JSON.parse(stdout) as Record<string, unknown>;
    const entry = Array.isArray(raw.entries) ? (raw.entries[0] as Record<string, unknown>) : raw;
    const stripKeys = new Set([
      "status",
      "creator",
      "updater",
      "create_time",
      "update_time",
      "module_type",
      "kn_id",
    ]);
    const bodyObj: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(entry)) {
      if (!stripKeys.has(k)) bodyObj[k] = v;
    }
    const path = `/api/ontology-manager/v1/knowledge-networks/${encodeURIComponent(knId)}/object-types/${encodeURIComponent(otId)}`;
    const { code, stderr } = await runCli([
      "call",
      path,
      "-X",
      "PUT",
      "--data-raw",
      JSON.stringify(bodyObj),
    ]);
    assert.equal(code, 0, stderr || "call PUT same schema should succeed");
    assert.ok(
      !stderr.includes("406") && !stderr.includes("ContentType"),
      `unexpected 406 / ContentType error: ${stderr}`,
    );
  },
);
