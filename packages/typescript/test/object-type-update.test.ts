import test from "node:test";
import assert from "node:assert/strict";
import { applyObjectTypeMerge, stripObjectTypeForPut } from "../src/commands/bkn.js";

test("stripObjectTypeForPut removes read-only keys", () => {
  const out = stripObjectTypeForPut({
    id: "player",
    name: "球员",
    kn_id: "x",
    status: { doc_count: 0 },
    creator: {},
  });
  assert.equal(out.id, "player");
  assert.equal(out.name, "球员");
  assert.equal("kn_id" in out, false);
  assert.equal("status" in out, false);
  assert.equal("creator" in out, false);
});

test("applyObjectTypeMerge adds and replaces properties by name", () => {
  const t: Record<string, unknown> = {
    data_properties: [
      { name: "a", display_name: "A", type: "string" },
      { name: "b", display_name: "B", type: "integer" },
    ],
  };
  applyObjectTypeMerge(t, {
    addProperties: [{ name: "b", display_name: "B2", type: "string" }],
    removeProperties: [],
  });
  const props = t.data_properties as { name: string; display_name: string }[];
  assert.equal(props.length, 2);
  assert.equal(props.find((p) => p.name === "b")?.display_name, "B2");
});

test("applyObjectTypeMerge removes properties", () => {
  const t: Record<string, unknown> = {
    data_properties: [{ name: "x" }, { name: "y" }],
  };
  applyObjectTypeMerge(t, {
    addProperties: [],
    removeProperties: ["x"],
  });
  const props = t.data_properties as { name: string }[];
  assert.deepEqual(
    props.map((p) => p.name),
    ["y"],
  );
});

test("applyObjectTypeMerge sets tags and comment", () => {
  const t: Record<string, unknown> = {};
  applyObjectTypeMerge(t, {
    addProperties: [],
    removeProperties: [],
    tags: ["t1"],
    comment: "c",
  });
  assert.deepEqual(t.tags, ["t1"]);
  assert.equal(t.comment, "c");
});
