import test from "node:test";
import assert from "node:assert/strict";
import { runCli, shouldSkipE2e, shouldRunDestructive } from "./setup.js";

async function findAccessibleAgent(): Promise<string | null> {
  const { code, stdout } = await runCli(["agent", "list", "--limit", "10"]);
  if (code !== 0) return null;
  const list = JSON.parse(stdout) as { id?: string }[] | { entries?: { id?: string }[] };
  const entries = Array.isArray(list) ? list : (list as { entries?: { id?: string }[] }).entries ?? [];
  for (const entry of entries) {
    const id = entry?.id;
    if (!id) continue;
    const { code: getCode, stderr } = await runCli(["agent", "get", id]);
    if (getCode === 0) return id;
    if (stderr.includes("403")) continue;
  }
  return null;
}

test("e2e: agent list returns JSON array", { skip: shouldSkipE2e() }, async () => {
  const { code, stdout } = await runCli(["agent", "list", "--limit", "5"]);
  assert.equal(code, 0);
  const parsed = JSON.parse(stdout) as unknown;
  assert.ok(Array.isArray(parsed) || (typeof parsed === "object" && (parsed as Record<string, unknown>).entries));
});

test("e2e: agent get returns agent details", { skip: shouldSkipE2e() }, async () => {
  const agentId = await findAccessibleAgent();
  if (!agentId) {
    test.skip("no accessible agent found (all returned 403)");
    return;
  }
  const { code, stdout } = await runCli(["agent", "get", agentId]);
  assert.equal(code, 0);
  const agent = JSON.parse(stdout) as Record<string, unknown>;
  assert.ok(agent.id || agent.name, "agent should have id or name");
});

test("e2e: agent get verbose returns full JSON", { skip: shouldSkipE2e() }, async () => {
  const agentId = await findAccessibleAgent();
  if (!agentId) {
    test.skip("no accessible agent found");
    return;
  }
  const { code, stdout } = await runCli(["agent", "get", agentId, "--verbose"]);
  assert.equal(code, 0);
  const agent = JSON.parse(stdout) as Record<string, unknown>;
  assert.ok(agent.config !== undefined || agent.kn_ids !== undefined || agent.status !== undefined);
});

test("e2e: agent chat returns non-empty response (destructive)", { skip: !shouldRunDestructive() || shouldSkipE2e() }, async () => {
  const agentId = await findAccessibleAgent();
  if (!agentId) {
    test.skip("no accessible agent found");
    return;
  }
  const { code, stdout } = await runCli(["agent", "chat", agentId, "-m", "hello"]);
  assert.equal(code, 0);
  assert.ok(stdout.length > 0, "agent chat should return non-empty response");
});
