# E2E Examples Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create 6 runnable TypeScript examples + shared setup that demonstrate the full KWeaver SDK capabilities through a progressive narrative.

**Architecture:** Each example is an independent `.ts` script in `examples/` that runs against a real KWeaver instance. A shared `setup.ts` provides client initialization and BKN/agent discovery helpers. Examples progress from Simple API (01) through Client API (02-05) to mixed low-level API (06).

**Tech Stack:** TypeScript, tsx runner, ESM modules, Node 22+

**Spec:** `docs/superpowers/specs/2026-03-20-e2e-examples-design.md`

---

### Task 1: Shared Setup Helper — `examples/setup.ts`

**Files:**
- Create: `examples/setup.ts`

- [ ] **Step 1: Create setup.ts with client init and BKN discovery**

```typescript
// Monorepo import — published users would use: import { KWeaverClient } from "@kweaver-ai/kweaver-sdk";
import { KWeaverClient } from "../packages/typescript/src/index.js";

/**
 * Initialize a KWeaverClient from ~/.kweaver/ credentials.
 */
export function createClient(): KWeaverClient {
  return new KWeaverClient();
}

/**
 * Find the first BKN that has object types with data.
 * Returns { knId, knName } or throws if none found.
 */
export async function findKnWithData(
  client: KWeaverClient,
): Promise<{ knId: string; knName: string }> {
  const kns = await client.knowledgeNetworks.list({ limit: 20 });
  for (const kn of kns) {
    const item = kn as { id?: string; name?: string };
    if (!item.id) continue;
    const ots = await client.knowledgeNetworks.listObjectTypes(item.id);
    if (Array.isArray(ots) && ots.length > 0) {
      return { knId: item.id, knName: item.name ?? item.id };
    }
  }
  throw new Error("No BKN with data found. Ensure your KWeaver instance has at least one BKN with object types.");
}

/**
 * Find the first accessible agent.
 * Returns { agentId, agentName } or throws if none found.
 */
export async function findAgent(
  client: KWeaverClient,
): Promise<{ agentId: string; agentName: string }> {
  const list = await client.agents.list({ limit: 10 });
  const first = list[0] as { id?: string; name?: string } | undefined;
  if (!first?.id) {
    throw new Error("No accessible agent found.");
  }
  return { agentId: first.id, agentName: first.name ?? first.id };
}

/**
 * Pretty-print a JSON value with indentation.
 */
export function pp(value: unknown): void {
  console.log(JSON.stringify(value, null, 2));
}
```

- [ ] **Step 2: Verify setup.ts compiles**

Run: `npx tsx --eval "import './examples/setup.js'" 2>&1`
Expected: No compilation errors (may get runtime error about credentials, that's OK)

- [ ] **Step 3: Commit**

```bash
git add examples/setup.ts
git commit -m "feat(examples): add shared setup helper with client init and discovery"
```

---

### Task 2: Example 01 — `examples/01-quick-start.ts`

**Files:**
- Create: `examples/01-quick-start.ts`

- [ ] **Step 1: Create 01-quick-start.ts using Simple API**

```typescript
/**
 * Example 01: Quick Start — 5 minutes to your first search
 *
 * Demonstrates: Simple API, auto-auth from ~/.kweaver/, BKN listing, semantic search.
 *
 * Run: npx tsx examples/01-quick-start.ts
 */
// Monorepo import — published users would use: import kweaver from "@kweaver-ai/kweaver-sdk/kweaver";
import kweaver from "../packages/typescript/src/kweaver.js";

async function main() {
  // 1. Configure — reads credentials from ~/.kweaver/ automatically
  kweaver.configure({ config: true });
  console.log("✓ Configured from ~/.kweaver/\n");

  // 2. List available knowledge networks
  const knList = await kweaver.bkns({ limit: 10 });
  console.log(`Found ${knList.length} knowledge network(s):`);
  for (const kn of knList) {
    const item = kn as { id?: string; name?: string };
    console.log(`  - ${item.name} (${item.id})`);
  }

  if (knList.length === 0) {
    console.log("\nNo BKNs found. Create one first.");
    return;
  }

  // 3. Pick the first BKN and do a semantic search
  const first = knList[0] as { id?: string; name?: string };
  const bknId = first.id!;
  console.log(`\nSearching in "${first.name}"...`);

  const result = await kweaver.search("数据", { bknId, maxConcepts: 5 });
  console.log(`\nSearch results (${result.hits_total ?? 0} hits):`);
  for (const concept of result.concepts ?? []) {
    const c = concept as { concept_name?: string; intent_score?: number };
    console.log(`  - ${c.concept_name} (score: ${c.intent_score})`);
  }
}

main().catch(console.error);
```

- [ ] **Step 2: Verify it compiles**

Run: `npx tsx --eval "import './examples/01-quick-start.js'" 2>&1 | head -5`
Expected: No syntax/import errors

- [ ] **Step 3: Commit**

```bash
git add examples/01-quick-start.ts
git commit -m "feat(examples): add 01-quick-start — configure, discover, search"
```

---

### Task 3: Example 02 — `examples/02-explore-schema.ts`

**Files:**
- Create: `examples/02-explore-schema.ts`

- [ ] **Step 1: Create 02-explore-schema.ts using Client API**

```typescript
/**
 * Example 02: Explore Schema — discover object types, relations, and actions
 *
 * Demonstrates: KWeaverClient, BKN statistics, schema trifecta (OT/RT/AT).
 *
 * Run: npx tsx examples/02-explore-schema.ts
 */
import { createClient, findKnWithData, pp } from "./setup.js";

async function main() {
  const client = createClient();
  const { knId, knName } = await findKnWithData(client);
  console.log(`Using BKN: ${knName} (${knId})\n`);

  // 1. Get BKN details with statistics
  const detail = await client.knowledgeNetworks.get(knId, { include_statistics: true });
  console.log("=== BKN Statistics ===");
  pp(detail);

  // 2. List object types
  const objectTypes = await client.knowledgeNetworks.listObjectTypes(knId);
  console.log(`\n=== Object Types (${(objectTypes as unknown[]).length}) ===`);
  for (const ot of objectTypes as Array<{ id?: string; name?: string; properties?: unknown[] }>) {
    console.log(`  ${ot.name} (${ot.id}) — ${ot.properties?.length ?? 0} properties`);
  }

  // 3. List relation types
  const relationTypes = await client.knowledgeNetworks.listRelationTypes(knId);
  console.log(`\n=== Relation Types (${(relationTypes as unknown[]).length}) ===`);
  for (const rt of relationTypes as Array<{
    id?: string; name?: string;
    source_object_type?: { name?: string };
    target_object_type?: { name?: string };
  }>) {
    console.log(`  ${rt.source_object_type?.name} —[${rt.name}]→ ${rt.target_object_type?.name}  (${rt.id})`);
  }

  // 4. List action types
  const actionTypes = await client.knowledgeNetworks.listActionTypes(knId);
  console.log(`\n=== Action Types (${(actionTypes as unknown[]).length}) ===`);
  for (const at of actionTypes as Array<{ id?: string; name?: string }>) {
    console.log(`  ${at.name} (${at.id})`);
  }
}

main().catch(console.error);
```

- [ ] **Step 2: Verify it compiles**

Run: `npx tsx --eval "import './examples/02-explore-schema.js'" 2>&1 | head -5`
Expected: No syntax/import errors

- [ ] **Step 3: Commit**

```bash
git add examples/02-explore-schema.ts
git commit -m "feat(examples): add 02-explore-schema — OT/RT/AT discovery"
```

---

### Task 4: Example 03 — `examples/03-query-and-traverse.ts`

**Files:**
- Create: `examples/03-query-and-traverse.ts`

- [ ] **Step 1: Create 03-query-and-traverse.ts with instance query, subgraph, and Context Loader**

```typescript
/**
 * Example 03: Query & Traverse — instance queries, subgraph traversal, Context Loader (MCP)
 *
 * Demonstrates: Conditional filtering, property reads, subgraph traversal, MCP Layer 1+2.
 *
 * Run: npx tsx examples/03-query-and-traverse.ts
 */
import { createClient, findKnWithData, pp } from "./setup.js";

async function main() {
  const client = createClient();
  const { knId, knName } = await findKnWithData(client);
  console.log(`Using BKN: ${knName} (${knId})\n`);

  // --- Part 1: Direct Client API queries ---

  // 1. Find the first object type to query
  const objectTypes = await client.knowledgeNetworks.listObjectTypes(knId);
  const ots = objectTypes as Array<{ id?: string; name?: string }>;
  if (ots.length === 0) {
    console.log("No object types found.");
    return;
  }
  const ot = ots[0];
  console.log(`=== Querying instances of "${ot.name}" ===`);

  // 2. Query instances (no filter, just limit)
  const instances = await client.bkn.queryInstances(knId, ot.id!, {
    page: 1,
    size: 5,
  });
  console.log("\nInstances (first 5):");
  pp(instances);

  // 3. Query properties
  const properties = await client.bkn.queryProperties(knId, ot.id!, {});
  console.log("\nProperties:");
  pp(properties);

  // 4. Subgraph traversal (if relation types exist)
  const relationTypes = await client.knowledgeNetworks.listRelationTypes(knId);
  const rts = relationTypes as Array<{
    id?: string; name?: string;
    source_object_type?: { id?: string };
    target_object_type?: { id?: string };
  }>;

  if (rts.length > 0) {
    const rt = rts[0];
    console.log(`\n=== Subgraph via "${rt.name}" ===`);
    const subgraph = await client.bkn.querySubgraph(knId, {
      relation_type_paths: [{
        relation_types: [{
          relation_type_id: rt.id,
          source_object_type_id: rt.source_object_type?.id,
          target_object_type_id: rt.target_object_type?.id,
        }],
      }],
      limit: 5,
    });
    console.log("Subgraph result:");
    pp(subgraph);
  }

  // --- Part 2: Context Loader (MCP protocol) ---
  // The Context Loader provides the same query capabilities via MCP,
  // allowing external AI agents to access knowledge graph data.

  console.log("\n=== Context Loader (MCP) ===");

  // Initialize Context Loader — requires the MCP endpoint URL
  const baseUrl = (client as unknown as { baseUrl: string }).baseUrl;
  const mcpUrl = `${baseUrl}/api/agent-retrieval/v1/mcp`;
  const cl = client.contextLoader(mcpUrl, knId);

  // Layer 1: Schema search — discover types by natural language
  console.log("Layer 1 — Schema search:");
  const schemaResults = await cl.schemaSearch({ query: "数据", max_concepts: 5 });
  pp(schemaResults);

  // Layer 2: Instance query via MCP (if we found an object type)
  if (ot.id) {
    console.log(`\nLayer 2 — Instance query for "${ot.name}" via MCP:`);
    const mpcInstances = await cl.queryInstances({
      ot_id: ot.id,
      condition: { operation: "and", sub_conditions: [] },
      limit: 5,
    });
    pp(mpcInstances);
  }
}

main().catch(console.error);
```

- [ ] **Step 2: Verify it compiles**

Run: `npx tsx --eval "import './examples/03-query-and-traverse.js'" 2>&1 | head -5`
Expected: No syntax/import errors

- [ ] **Step 3: Commit**

```bash
git add examples/03-query-and-traverse.ts
git commit -m "feat(examples): add 03-query-and-traverse — instances, subgraph, MCP"
```

---

### Task 5: Example 04 — `examples/04-actions.ts`

**Files:**
- Create: `examples/04-actions.ts`

- [ ] **Step 1: Create 04-actions.ts with action execution and log tracking**

```typescript
/**
 * Example 04: Actions — execute actions and track results
 *
 * Demonstrates: Action discovery, execution, async polling, execution logs.
 *
 * Run: npx tsx examples/04-actions.ts
 */
import { createClient, findKnWithData, pp } from "./setup.js";

async function main() {
  const client = createClient();
  const { knId, knName } = await findKnWithData(client);
  console.log(`Using BKN: ${knName} (${knId})\n`);

  // 1. List available action types
  const actionTypes = await client.knowledgeNetworks.listActionTypes(knId);
  const ats = actionTypes as Array<{ id?: string; name?: string; description?: string }>;
  console.log(`=== Action Types (${ats.length}) ===`);
  for (const at of ats) {
    console.log(`  ${at.name} (${at.id}) — ${at.description ?? ""}`);
  }

  if (ats.length === 0) {
    console.log("\nNo action types found. This BKN has no executable actions.");
    return;
  }

  // 2. Query an action type to see its schema/parameters
  const at = ats[0];
  console.log(`\n=== Action Detail: "${at.name}" ===`);
  const actionDetail = await client.bkn.queryAction(knId, at.id!, {});
  pp(actionDetail);

  // 3. List action execution logs (historical runs)
  console.log("\n=== Action Logs ===");
  const logs = await client.bkn.listActionLogs(knId, { atId: at.id, limit: 5 });
  console.log(`Found ${logs.length} log(s) for "${at.name}":`);
  for (const log of logs as Array<{ id?: string; status?: string; created_at?: string }>) {
    console.log(`  [${log.status}] ${log.id} — ${log.created_at ?? ""}`);
  }

  // 4. Get detail of the most recent log (if any)
  if (logs.length > 0) {
    const firstLog = logs[0] as { id?: string };
    if (firstLog.id) {
      console.log(`\n=== Log Detail: ${firstLog.id} ===`);
      const detail = await client.bkn.getActionLog(knId, firstLog.id);
      pp(detail);
    }
  }

  // Note: To actually execute an action, uncomment below.
  // This is a write operation — it will trigger real side effects.
  //
  // const execution = await client.bkn.executeAction(knId, at.id!, { params: {} });
  // console.log("Execution started:", execution);
  //
  // // Poll until complete
  // const execResult = execution as { execution_id?: string };
  // if (execResult.execution_id) {
  //   let status: unknown;
  //   do {
  //     await new Promise((r) => setTimeout(r, 2000));
  //     status = await client.bkn.getExecution(knId, execResult.execution_id);
  //     console.log("Status:", (status as { status?: string }).status);
  //   } while ((status as { status?: string }).status === "running");
  //   console.log("Final result:");
  //   pp(status);
  // }
}

main().catch(console.error);
```

- [ ] **Step 2: Verify it compiles**

Run: `npx tsx --eval "import './examples/04-actions.js'" 2>&1 | head -5`
Expected: No syntax/import errors

- [ ] **Step 3: Commit**

```bash
git add examples/04-actions.ts
git commit -m "feat(examples): add 04-actions — action discovery, logs, execution"
```

---

### Task 6: Example 05 — `examples/05-agent-conversation.ts`

**Files:**
- Create: `examples/05-agent-conversation.ts`

- [ ] **Step 1: Create 05-agent-conversation.ts with chat and streaming**

```typescript
/**
 * Example 05: Agent Conversation — chat with an AI agent over the knowledge graph
 *
 * Demonstrates: Agent discovery, single-shot chat, streaming, progress chain, conversation history.
 *
 * Run: npx tsx examples/05-agent-conversation.ts
 */
import { createClient, findAgent, pp } from "./setup.js";
import type { ProgressItem } from "../packages/typescript/src/index.js";

async function main() {
  const client = createClient();

  // 1. List available agents
  const agentList = await client.agents.list({ limit: 10 });
  console.log(`=== Available Agents (${agentList.length}) ===`);
  for (const a of agentList as Array<{ id?: string; name?: string; description?: string }>) {
    console.log(`  ${a.name} (${a.id}) — ${a.description ?? ""}`);
  }

  const { agentId, agentName } = await findAgent(client);
  console.log(`\nUsing agent: ${agentName} (${agentId})\n`);

  // 2. Single-shot chat
  console.log("=== Single-Shot Chat ===");
  const reply = await client.agents.chat(agentId, "你好，请介绍一下你能做什么");
  console.log(`Reply: ${reply.text}\n`);

  // Show the agent's reasoning/progress chain
  if (reply.progress && reply.progress.length > 0) {
    console.log("Progress chain:");
    for (const step of reply.progress) {
      console.log(`  [${step.skill_info?.type ?? "step"}] ${step.skill_info?.name ?? step.agent_name} → ${step.status}`);
    }
  }

  // 3. Streaming chat — real-time text output
  // Note: onTextDelta receives the FULL accumulated text each time, not a delta.
  // We track the previous length to print only the new portion.
  console.log("\n=== Streaming Chat ===");
  process.stdout.write("Reply: ");
  let prevLen = 0;
  const streamResult = await client.agents.stream(
    agentId,
    "请列出知识网络中的主要概念",
    {
      onTextDelta: (fullText: string) => {
        process.stdout.write(fullText.slice(prevLen));
        prevLen = fullText.length;
      },
      onProgress: (progress: ProgressItem[]) => {
        for (const p of progress) {
          if (p.skill_info?.name) {
            process.stderr.write(`\n  [progress] ${p.skill_info.name} → ${p.status ?? ""}\n`);
          }
        }
      },
    },
  );
  console.log("\n");

  // 4. Conversation history
  const conversationId = reply.conversationId;
  if (conversationId) {
    console.log("=== Conversation History ===");
    const messages = await client.conversations.listMessages(conversationId, { limit: 10 });
    console.log(`${(messages as unknown[]).length} message(s) in conversation ${conversationId}:`);
    for (const msg of messages as Array<{ role?: string; content?: string }>) {
      const preview = (msg.content ?? "").slice(0, 80);
      console.log(`  [${msg.role}] ${preview}${(msg.content?.length ?? 0) > 80 ? "..." : ""}`);
    }
  }

  // 5. List all conversation sessions for this agent
  console.log("\n=== Conversation Sessions ===");
  const sessions = await client.conversations.list(agentId, { limit: 5 });
  console.log(`${(sessions as unknown[]).length} session(s):`);
  for (const s of sessions as Array<{ id?: string; created_at?: string }>) {
    console.log(`  ${s.id} — ${s.created_at ?? ""}`);
  }
}

main().catch(console.error);
```

- [ ] **Step 2: Verify it compiles**

Run: `npx tsx --eval "import './examples/05-agent-conversation.js'" 2>&1 | head -5`
Expected: No syntax/import errors

- [ ] **Step 3: Commit**

```bash
git add examples/05-agent-conversation.ts
git commit -m "feat(examples): add 05-agent-conversation — chat, stream, history"
```

---

### Task 7: Example 06 — `examples/06-full-pipeline.ts`

**Files:**
- Create: `examples/06-full-pipeline.ts`

- [ ] **Step 1: Create 06-full-pipeline.ts using CLI create-from-ds shortcut**

This example uses the CLI `bkn create-from-ds` command which handles the full pipeline:
datasource → DataView creation → BKN creation → object type creation → build.

The CLI approach is preferred because the low-level API calls for creating object types
require internal knowledge of the payload structure that the CLI already encapsulates.

```typescript
/**
 * Example 06: Full Pipeline — from datasource to intelligent search
 *
 * Demonstrates: Datasource registration, BKN creation from datasource,
 * build + wait, semantic search, resource cleanup.
 *
 * DESTRUCTIVE: This example creates and deletes resources.
 *
 * Prerequisites:
 *   - A reachable MySQL database
 *   - Set environment variables: KWEAVER_TEST_DB_HOST, KWEAVER_TEST_DB_PORT,
 *     KWEAVER_TEST_DB_NAME, KWEAVER_TEST_DB_USER, KWEAVER_TEST_DB_PASS
 *
 * Run: npx tsx examples/06-full-pipeline.ts
 */
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { createClient, pp } from "./setup.js";

const exec = promisify(execFile);

async function runCli(args: string[]): Promise<{ stdout: string; stderr: string }> {
  const result = await exec("npx", ["tsx", "packages/typescript/src/cli.ts", ...args]);
  return result;
}

function requireEnv(name: string, fallback?: string): string {
  const v = process.env[name] ?? fallback;
  if (!v) throw new Error(`Missing env var: ${name}`);
  return v;
}

async function main() {
  // Require explicit opt-in for destructive operations
  if (process.env.RUN_DESTRUCTIVE !== "1") {
    console.log("This example creates and deletes resources.");
    console.log("Set RUN_DESTRUCTIVE=1 to run it.");
    return;
  }

  const dbHost = requireEnv("KWEAVER_TEST_DB_HOST");
  const dbPort = requireEnv("KWEAVER_TEST_DB_PORT", "3306");
  const dbName = requireEnv("KWEAVER_TEST_DB_NAME");
  const dbUser = requireEnv("KWEAVER_TEST_DB_USER");
  const dbPass = requireEnv("KWEAVER_TEST_DB_PASS");
  const dbType = requireEnv("KWEAVER_TEST_DB_TYPE", "mysql");
  const dsName = `example_pipeline_${Date.now()}`;
  const knName = `example_pipeline_${Date.now()}`;

  let dsId: string | undefined;
  let knId: string | undefined;

  try {
    // Step 1: Register datasource
    console.log("=== Step 1: Register Datasource ===");
    const dsResult = await runCli([
      "ds", "connect", dbType, dbHost, dbPort, dbName,
      "--account", dbUser, "--password", dbPass,
      "--name", dsName,
    ]);
    const dsParsed = JSON.parse(dsResult.stdout);
    dsId = String(dsParsed?.id ?? dsParsed?.ds_id ?? "");
    console.log(`Created datasource: ${dsName} (${dsId})\n`);

    // Step 2: Create BKN from datasource (creates DataViews, object types, etc.)
    console.log("=== Step 2: Create BKN from Datasource ===");
    const knResult = await runCli([
      "bkn", "create-from-ds", dsId,
      "--name", knName,
      "--no-build",
    ]);
    const knParsed = JSON.parse(knResult.stdout);
    knId = String(knParsed?.kn_id ?? knParsed?.id ?? "");
    console.log(`Created BKN: ${knName} (${knId})\n`);

    // Step 3: Build the knowledge network index
    console.log("=== Step 3: Build BKN ===");
    const client = createClient();
    console.log("Building... (this may take a while)");
    const buildStatus = await client.knowledgeNetworks.buildAndWait(knId, {
      timeout: 300_000,
      interval: 5_000,
    });
    console.log("Build complete:", buildStatus);

    // Step 4: Export the BKN to see what was created
    console.log("\n=== Step 4: Export BKN ===");
    const exportResult = await runCli(["bkn", "export", knId]);
    const exported = JSON.parse(exportResult.stdout);
    console.log("Exported schema:");
    pp(exported);

    // Step 5: Semantic search on the new BKN
    console.log("\n=== Step 5: Semantic Search ===");
    const searchResult = await client.bkn.semanticSearch(knId, "数据");
    console.log("Search results:");
    pp(searchResult);

  } finally {
    // Cleanup: delete created resources
    console.log("\n=== Cleanup ===");
    if (knId) {
      try {
        await runCli(["bkn", "delete", knId, "-y"]);
        console.log(`Deleted BKN: ${knId}`);
      } catch (e) {
        console.error(`Failed to delete BKN: ${(e as Error).message}`);
      }
    }
    if (dsId) {
      try {
        await runCli(["ds", "delete", dsId, "-y"]);
        console.log(`Deleted datasource: ${dsId}`);
      } catch (e) {
        console.error(`Failed to delete datasource: ${(e as Error).message}`);
      }
    }
  }
}

main().catch(console.error);
```

- [ ] **Step 2: Verify it compiles**

Run: `npx tsx --eval "import './examples/06-full-pipeline.js'" 2>&1 | head -5`
Expected: No syntax/import errors

- [ ] **Step 3: Commit**

```bash
git add examples/06-full-pipeline.ts
git commit -m "feat(examples): add 06-full-pipeline — datasource to search lifecycle"
```

---

### Task 8: README — `examples/README.md`

**Files:**
- Create: `examples/README.md`

- [ ] **Step 1: Create examples README**

```markdown
# KWeaver SDK Examples

End-to-end examples running against a real KWeaver instance. Each script is independent and demonstrates a progression of SDK capabilities.

## Prerequisites

- Node.js 22+
- `npm install` (from the repo root)
- `npx tsx packages/typescript/src/cli.ts auth login <your-platform-url>` — saves credentials to `~/.kweaver/`
- A KWeaver instance with at least one BKN containing data (for examples 01-05)

## Examples

| # | File | What you'll learn | API Layer |
|---|------|-------------------|-----------|
| 01 | [01-quick-start.ts](01-quick-start.ts) | Configure, discover BKNs, semantic search | Simple API |
| 02 | [02-explore-schema.ts](02-explore-schema.ts) | Object types, relations, actions, statistics | Client API |
| 03 | [03-query-and-traverse.ts](03-query-and-traverse.ts) | Instance queries, subgraph traversal, Context Loader | Client API |
| 04 | [04-actions.ts](04-actions.ts) | Action discovery, execution logs, polling | Client API |
| 05 | [05-agent-conversation.ts](05-agent-conversation.ts) | Agent chat (single + streaming), conversation history | Client API |
| 06 | [06-full-pipeline.ts](06-full-pipeline.ts) | Full datasource → BKN → build → search pipeline | Mixed |

## Running

```bash
npx tsx examples/01-quick-start.ts
```

## Notes

- **Examples 01-05 are read-only** — safe to run anytime against any instance
- **Example 06 is destructive** — creates and deletes resources (datasource, BKN). Requires `RUN_DESTRUCTIVE=1` and database env vars
- All examples dynamically discover available BKNs and agents at runtime — no hardcoded IDs
- Examples use two API styles:
  - **Simple API** (`import kweaver from "kweaver-sdk/kweaver"`) — minimal, opinionated
  - **Client API** (`new KWeaverClient()`) — full control over all resources
```

- [ ] **Step 2: Commit**

```bash
git add examples/README.md
git commit -m "docs(examples): add README with overview and running instructions"
```

---

### Task 9: Verify All Examples Compile

**Files:**
- All files in `examples/`

- [ ] **Step 1: Compile-check all examples**

Run: `for f in examples/0*.ts; do echo "--- $f ---"; npx tsx --eval "import './$f'" 2>&1 | head -3; done`
Expected: No import/syntax errors for any example

- [ ] **Step 2: Run example 01 against real instance (smoke test)**

Run: `npx tsx examples/01-quick-start.ts`
Expected: Lists BKNs and prints search results (or "No BKNs found" if empty instance)

- [ ] **Step 3: Run example 02 against real instance**

Run: `npx tsx examples/02-explore-schema.ts`
Expected: Prints object types, relation types, action types

- [ ] **Step 4: Final commit if any fixes needed**

```bash
git add examples/
git commit -m "fix(examples): address compilation/runtime issues from smoke tests"
```
