# Fix #19: Server-Side Filtering + Polling Backoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix performance and correctness issues across Python and TypeScript SDK — add server-side keyword filtering to bulk-fetch-then-filter patterns, add exponential backoff to all polling loops, and increase inadequate timeouts.

**Architecture:** Seven targeted fixes following existing patterns (`datasources.create()` for keyword filtering, `jobs.wait()` for exponential backoff). Each fix is TDD: write a failing test that asserts the correct behavior, then modify the implementation to pass it.

**Tech Stack:** Python (pytest, httpx MockTransport, unittest.mock.patch), TypeScript (node:test, globalThis.fetch mock)

---

## File Map

| Fix | Files to Modify | Test Files |
|-----|----------------|------------|
| 1. dataviews.find_by_table keyword + timeout + backoff | `packages/python/src/kweaver/resources/dataviews.py` | `packages/python/tests/unit/test_dataviews.py` |
| 2. object_types.create keyword filter | `packages/python/src/kweaver/resources/object_types.py` | `packages/python/tests/unit/test_object_types.py` |
| 3. relation_types.create keyword filter | `packages/python/src/kweaver/resources/relation_types.py` | `packages/python/tests/unit/test_relation_types.py` |
| 4. dataflows.poll backoff (Python) | `packages/python/src/kweaver/resources/dataflows.py` | `packages/python/tests/unit/test_dataflows.py` |
| 5. pollDataflowResults backoff (TS) | `packages/typescript/src/api/dataflow.ts` | `packages/typescript/test/dataflow.test.ts` |
| 6. bkn.ts polling backoff + DRY | `packages/typescript/src/commands/bkn.ts` | `packages/typescript/test/bkn-push-pull.test.ts` |
| 7. datasources.list_tables secondary query | `packages/python/src/kweaver/resources/datasources.py` | `packages/python/tests/unit/test_datasources.py` |

---

### Task 1: `dataviews.find_by_table` — keyword, timeout 30s, exponential backoff

**Files:**
- Modify: `packages/python/src/kweaver/resources/dataviews.py:24-56`
- Test: `packages/python/tests/unit/test_dataviews.py`

**Reference:** TS `findDataView` already does this correctly (keyword + 30s + backoff). Python `jobs.wait()` has backoff pattern.

- [ ] **Step 1: Write failing test — keyword param is passed to server**

```python
# In test_dataviews.py

def test_find_by_table_passes_keyword_param(capture: RequestCapture):
    """find_by_table must send keyword=<table_name> to narrow server results."""
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "entries": [{"id": "dv_01", "name": "products", "type": "atomic",
                         "query_type": "SQL", "fields": [], "data_source_id": "ds_01"}],
        })

    client = make_client(handler, capture)
    client.dataviews.find_by_table("ds_01", "products", wait=False)

    url = str(capture.requests[-1].url)
    assert "keyword=products" in url
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/python && python -m pytest tests/unit/test_dataviews.py::test_find_by_table_passes_keyword_param -v`
Expected: FAIL — `keyword=products` not in URL

- [ ] **Step 3: Write failing test — default timeout is 30s**

```python
def test_find_by_table_default_timeout_is_30s():
    """Default timeout should be 30 seconds, not 10."""
    import inspect
    from kweaver.resources.dataviews import DataViewsResource
    sig = inspect.signature(DataViewsResource.find_by_table)
    assert sig.parameters["timeout"].default == 30
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd packages/python && python -m pytest tests/unit/test_dataviews.py::test_find_by_table_default_timeout_is_30s -v`
Expected: FAIL — default is 10, not 30

- [ ] **Step 5: Write failing test — exponential backoff**

```python
def test_find_by_table_uses_exponential_backoff(capture: RequestCapture):
    """Polling should use exponential backoff (1s, 2s, 4s, ...) capped at 5s."""
    call_count = 0

    def handler(req: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count < 4:
            return httpx.Response(200, json={"entries": []})
        return httpx.Response(200, json={
            "entries": [{"id": "dv_01", "name": "tbl", "type": "atomic",
                         "query_type": "SQL", "fields": [], "data_source_id": "ds_01"}],
        })

    client = make_client(handler, capture)
    sleep_calls = []
    with patch("kweaver.resources.dataviews.time.sleep", side_effect=lambda s: sleep_calls.append(s)):
        with patch("kweaver.resources.dataviews.time.monotonic") as mock_mono:
            # Ensure we never hit deadline
            mock_mono.return_value = 0.0
            client.dataviews.find_by_table("ds_01", "tbl", wait=True)

    assert call_count == 4
    # Backoff: 1s, 2s, 4s (capped at 5s)
    assert sleep_calls == [1.0, 2.0, 4.0]
```

- [ ] **Step 6: Run test to verify it fails**

Run: `cd packages/python && python -m pytest tests/unit/test_dataviews.py::test_find_by_table_uses_exponential_backoff -v`
Expected: FAIL — current implementation uses fixed `time.sleep(5)`

- [ ] **Step 7: Implement the fix**

In `dataviews.py`, modify `find_by_table`:

```python
def find_by_table(
    self,
    datasource_id: str,
    table_name: str,
    *,
    wait: bool = True,
    timeout: float = 30,
) -> DataView | None:
    deadline = time.monotonic() + timeout
    attempt = 0
    while True:
        data = self._http.get(
            "/api/mdl-data-model/v1/data-views",
            params={"data_source_id": datasource_id, "keyword": table_name, "limit": -1},
        )
        items = data if isinstance(data, list) else (data.get("entries") or data.get("data") or [])
        logger.debug(
            "find_by_table attempt=%d ds=%s table=%r found=%d",
            attempt + 1, datasource_id, table_name, len(items),
        )
        for d in items:
            if d.get("name") == table_name:
                return _parse_single_dataview(d)
        if not wait or time.monotonic() >= deadline:
            return None
        delay = min(5.0, 1.0 * 2 ** attempt)
        time.sleep(delay)
        attempt += 1
```

- [ ] **Step 8: Run all dataview tests**

Run: `cd packages/python && python -m pytest tests/unit/test_dataviews.py -v`
Expected: ALL PASS

- [ ] **Step 9: Commit**

```bash
git add packages/python/src/kweaver/resources/dataviews.py packages/python/tests/unit/test_dataviews.py
git commit -m "fix(dataviews): add keyword filter, 30s timeout, exponential backoff to find_by_table

Closes part of #19"
```

---

### Task 2: `object_types.create` — keyword filter on Existed fallback

**Files:**
- Modify: `packages/python/src/kweaver/resources/object_types.py:78-88`
- Test: `packages/python/tests/unit/test_object_types.py`

**Reference:** `datasources.create()` L91 already does `self.list(keyword=name)`.

- [ ] **Step 1: Write failing test — Existed fallback passes keyword**

```python
def test_create_existed_fallback_passes_keyword(capture: RequestCapture):
    """When OT already exists, list() should filter by keyword instead of fetching all."""
    call_count = 0

    def handler(req: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if req.method == "POST":
            return httpx.Response(409, json={
                "error_code": "Existed",
                "message": "Object type already exists",
            })
        # GET (list) — return matching OT
        return httpx.Response(200, json={
            "entries": [_OT_RESPONSE],
        })

    client = make_client(handler, capture)
    ot = client.object_types.create(
        "kn_01", name="产品", dataview_id="dv_01",
        primary_keys=["material_number"], display_key="product_name",
    )

    assert ot.id == "ot_01"
    # Verify the GET request includes keyword filter
    get_reqs = [r for r in capture.requests if r.method == "GET" and "object-types" in str(r.url) and "?" in str(r.url)]
    assert get_reqs, "Expected a filtered list request"
    url = str(get_reqs[0].url)
    assert "keyword" in url, f"Expected keyword param in URL: {url}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/python && python -m pytest tests/unit/test_object_types.py::test_create_existed_fallback_passes_keyword -v`
Expected: FAIL — current `list()` doesn't support keyword, and `create()` calls `self.list(kn_id)` without it

- [ ] **Step 3: Implement the fix**

In `object_types.py`:

1. Add `keyword` parameter to `list()`:

```python
def list(self, kn_id: str, *, branch: str = "main", keyword: str | None = None) -> list[ObjectType]:
    params: dict[str, Any] = {"limit": -1, "branch": branch}
    if keyword:
        params["keyword"] = keyword
    data = self._http.get(
        f"{_PREFIX}/knowledge-networks/{kn_id}/object-types",
        params=params,
    )
    items = data if isinstance(data, list) else (data.get("entries") or data.get("data") or [])
    return [_parse_object_type(d, kn_id) for d in items]
```

2. Change the `create()` fallback (L80) from `self.list(kn_id)` to `self.list(kn_id, keyword=name)`:

```python
existing = self.list(kn_id, keyword=name)
```

- [ ] **Step 4: Run all object_types tests**

Run: `cd packages/python && python -m pytest tests/unit/test_object_types.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add packages/python/src/kweaver/resources/object_types.py packages/python/tests/unit/test_object_types.py
git commit -m "fix(object_types): use keyword filter in Existed fallback instead of full scan"
```

---

### Task 3: `relation_types.create` — keyword filter on Existed fallback

**Files:**
- Modify: `packages/python/src/kweaver/resources/relation_types.py:78-84`
- Test: `packages/python/tests/unit/test_relation_types.py`

Identical pattern to Task 2.

- [ ] **Step 1: Write failing test — Existed fallback passes keyword**

```python
def test_create_existed_fallback_passes_keyword(capture: RequestCapture):
    """When RT already exists, list() should filter by keyword instead of fetching all."""
    def handler(req: httpx.Request) -> httpx.Response:
        if req.method == "POST":
            return httpx.Response(409, json={
                "error_code": "Existed",
                "message": "Relation type already exists",
            })
        return httpx.Response(200, json={
            "entries": [_RT_RESPONSE],
        })

    client = make_client(handler, capture)
    rt = client.relation_types.create(
        "kn_01", name="产品_库存",
        source_ot_id="ot_01", target_ot_id="ot_02",
        mappings=[("material_number", "material_code")],
    )

    assert rt.id == "rt_01"
    get_reqs = [r for r in capture.requests if r.method == "GET" and "relation-types" in str(r.url) and "?" in str(r.url)]
    assert get_reqs, "Expected a filtered list request"
    url = str(get_reqs[0].url)
    assert "keyword" in url, f"Expected keyword param in URL: {url}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/python && python -m pytest tests/unit/test_relation_types.py::test_create_existed_fallback_passes_keyword -v`
Expected: FAIL

- [ ] **Step 3: Implement the fix**

In `relation_types.py`:

1. Add `keyword` parameter to `list()`:

```python
def list(self, kn_id: str, *, branch: str = "main", keyword: str | None = None) -> list[RelationType]:
    params: dict[str, Any] = {"limit": -1, "branch": branch}
    if keyword:
        params["keyword"] = keyword
    data = self._http.get(
        f"{_PREFIX}/knowledge-networks/{kn_id}/relation-types",
        params=params,
    )
    items = data if isinstance(data, list) else (data.get("entries") or data.get("data") or [])
    return [_parse_relation_type(d, kn_id) for d in items]
```

2. Change the `create()` fallback (L80) from `self.list(kn_id)` to `self.list(kn_id, keyword=name)`:

```python
existing = self.list(kn_id, keyword=name)
```

- [ ] **Step 4: Run all relation_types tests**

Run: `cd packages/python && python -m pytest tests/unit/test_relation_types.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add packages/python/src/kweaver/resources/relation_types.py packages/python/tests/unit/test_relation_types.py
git commit -m "fix(relation_types): use keyword filter in Existed fallback instead of full scan"
```

---

### Task 4: `dataflows.poll` — exponential backoff (Python)

**Files:**
- Modify: `packages/python/src/kweaver/resources/dataflows.py:68-102`
- Test: `packages/python/tests/unit/test_dataflows.py`

**Reference:** `jobs.wait()` pattern: `current_interval = min(current_interval * 2, _MAX_BACKOFF)`

- [ ] **Step 1: Write failing test — poll uses exponential backoff**

```python
def test_poll_uses_exponential_backoff(capture: RequestCapture):
    """Poll should use exponential backoff instead of fixed interval."""
    call_count = 0

    def handler(req: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count < 5:
            return httpx.Response(200, json={"results": []})
        return httpx.Response(200, json={"results": [{"status": "success"}]})

    client = make_client(handler, capture)
    sleep_calls = []
    with patch("kweaver.resources.dataflows.time.sleep", side_effect=lambda s: sleep_calls.append(s)):
        with patch("kweaver.resources.dataflows.time.monotonic") as mock_mono:
            mock_mono.return_value = 0.0
            result = client.dataflows.poll("dag_001", interval=3.0, timeout=900.0)

    assert result.status == "success"
    # Backoff: 3, 6, 12, 24 (doubling from initial interval, capped at 30)
    assert sleep_calls == [3.0, 6.0, 12.0, 24.0]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/python && python -m pytest tests/unit/test_dataflows.py::test_poll_uses_exponential_backoff -v`
Expected: FAIL — all sleeps are currently fixed at 3.0

- [ ] **Step 3: Implement the fix**

In `dataflows.py`, modify `poll`:

```python
def poll(
    self,
    dag_id: str,
    *,
    interval: float = 3.0,
    timeout: float = 900.0,
) -> DataflowResult:
    deadline = time.monotonic() + timeout
    current_interval = interval

    while True:
        data = self._http.get(f"{_BASE}/dag/{dag_id}/results")
        results = data.get("results", []) if isinstance(data, dict) else []

        if results:
            latest = results[0]
            status = latest.get("status", "")
            reason = latest.get("reason")

            if status in ("success", "completed"):
                return DataflowResult(status=status, reason=reason)
            if status in ("failed", "error"):
                msg = f"Dataflow run {status}"
                if reason:
                    msg += f": {reason}"
                raise KWeaverError(msg, status_code=None, error_code=None)

        if time.monotonic() + current_interval > deadline:
            raise TimeoutError(
                f"Dataflow polling timed out after {timeout}s for DAG {dag_id}"
            )
        time.sleep(current_interval)
        current_interval = min(current_interval * 2, 30.0)
```

- [ ] **Step 4: Run all dataflow tests**

Run: `cd packages/python && python -m pytest tests/unit/test_dataflows.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add packages/python/src/kweaver/resources/dataflows.py packages/python/tests/unit/test_dataflows.py
git commit -m "fix(dataflows): add exponential backoff to poll (Python)"
```

---

### Task 5: `pollDataflowResults` — exponential backoff (TypeScript)

**Files:**
- Modify: `packages/typescript/src/api/dataflow.ts:131-178`
- Test: `packages/typescript/test/dataflow.test.ts`

- [ ] **Step 1: Write failing test — poll uses exponential backoff**

Add `_delayFn` injection parameter to `PollDataflowOptions` interface for testability (same pattern as Task 6's `pollWithBackoff`):

```typescript
test("pollDataflowResults uses exponential backoff between polls", async () => {
  const originalFetch = globalThis.fetch;
  const sleepDurations: number[] = [];
  let callCount = 0;

  try {
    globalThis.fetch = async () => {
      callCount++;
      if (callCount < 4) {
        return new Response(JSON.stringify({ results: [] }), { status: 200 });
      }
      return new Response(
        JSON.stringify({ results: [{ status: "success" }] }),
        { status: 200 }
      );
    };

    const result = await pollDataflowResults({
      ...COMMON_OPTS,
      dagId: "dag-backoff",
      interval: 3,
      timeout: 900,
      _delayFn: async (ms: number) => { sleepDurations.push(ms); },
    });
    assert.equal(result.status, "success");
    // Backoff: 3000, 6000, 12000 (doubling, capped at 30000)
    assert.deepEqual(sleepDurations, [3000, 6000, 12000]);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/typescript && npx tsx --test test/dataflow.test.ts`
Expected: FAIL — all sleeps are fixed at `interval * 1000`

- [ ] **Step 3: Implement the fix**

In `dataflow.ts`:

1. Add `_delayFn` to `PollDataflowOptions`:

```typescript
  /** Test injection: override delay function. */
  _delayFn?: (ms: number) => Promise<void>;
```

2. Modify `pollDataflowResults`:

```typescript
export async function pollDataflowResults(options: PollDataflowOptions): Promise<DataflowResult> {
  const {
    baseUrl,
    accessToken,
    businessDomain = "bd_public",
    dagId,
    interval = 3,
    timeout = 900,
    _delayFn = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms)),
  } = options;

  const base = baseUrl.replace(/\/+$/, "");
  const url = `${base}/api/automation/v1/dag/${encodeURIComponent(dagId)}/results`;

  const deadlineMs = Date.now() + timeout * 1000;
  let currentInterval = interval;

  while (Date.now() < deadlineMs) {
    const response = await fetch(url, {
      method: "GET",
      headers: buildHeaders(accessToken, businessDomain),
    });

    const responseBody = await response.text();
    if (!response.ok) {
      throw new HttpError(response.status, response.statusText, responseBody);
    }

    const parsed = JSON.parse(responseBody) as { results?: DataflowResult[] };
    const results = parsed.results ?? [];
    const latest = results[0];

    if (latest) {
      if (latest.status === "success" || latest.status === "completed") {
        return latest;
      }
      if (latest.status === "failed" || latest.status === "error") {
        const reason = latest.reason ? `: ${latest.reason}` : "";
        throw new Error(`Dataflow run ${latest.status}${reason}`);
      }
    }

    if (currentInterval > 0) {
      await _delayFn(currentInterval * 1000);
    }
    currentInterval = Math.min(currentInterval * 2, 30);
  }

  throw new Error(`Dataflow polling timed out after ${timeout}s for DAG ${dagId}`);
}
```

- [ ] **Step 4: Run all dataflow tests**

Run: `cd packages/typescript && npx tsx --test test/dataflow.test.ts`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add packages/typescript/src/api/dataflow.ts packages/typescript/test/dataflow.test.ts
git commit -m "fix(dataflow): add exponential backoff to pollDataflowResults (TypeScript)"
```

---

### Task 6: `bkn.ts` — extract polling helper + add backoff

**Files:**
- Modify: `packages/typescript/src/commands/bkn.ts`
- Test: `packages/typescript/test/bkn-push-pull.test.ts`

Three near-identical polling loops (L2031-2045, L2638-2652, L2835-2860) should be extracted into a shared helper with exponential backoff.

- [ ] **Step 1: Write failing test — polling helper uses backoff**

```typescript
// In bkn-push-pull.test.ts (or a new test file if cleaner)
import { pollWithBackoff } from "../src/commands/bkn.js";

test("pollWithBackoff uses exponential backoff", async () => {
  const sleepDurations: number[] = [];
  let callCount = 0;

  const result = await pollWithBackoff({
    fn: async () => {
      callCount++;
      if (callCount < 3) return { done: false, value: undefined };
      return { done: true, value: "completed" };
    },
    interval: 2000,
    timeout: 60000,
    _sleep: async (ms: number) => { sleepDurations.push(ms); },
  });

  assert.equal(result, "completed");
  // Backoff: 2000, 4000 (doubling, capped at 15000)
  assert.deepEqual(sleepDurations, [2000, 4000]);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/typescript && npx tsx --test test/bkn-push-pull.test.ts`
Expected: FAIL — `pollWithBackoff` doesn't exist yet

- [ ] **Step 3: Implement `pollWithBackoff` helper and refactor the 3 polling sites**

Add to `bkn.ts` (exported for testing):

```typescript
export interface PollOptions<T> {
  fn: () => Promise<{ done: boolean; value: T }>;
  interval: number;     // initial interval ms
  timeout: number;      // total budget ms
  maxInterval?: number; // cap (default 15000)
  _sleep?: (ms: number) => Promise<void>; // test injection
}

export async function pollWithBackoff<T>(opts: PollOptions<T>): Promise<T> {
  const { fn, timeout, maxInterval = 15000, _sleep = (ms) => new Promise(r => setTimeout(r, ms)) } = opts;
  let currentInterval = opts.interval;
  const deadline = Date.now() + timeout;

  while (Date.now() < deadline) {
    const result = await fn();
    if (result.done) return result.value;
    await _sleep(currentInterval);
    currentInterval = Math.min(currentInterval * 2, maxInterval);
  }

  throw new Error(`Polling timed out after ${timeout}ms`);
}
```

Then replace each of the 3 polling sites with a call to `pollWithBackoff`:

**Site 1 (L2031-2045):** Action execution polling — `fn` calls `actionExecutionGet()`, checks `extractStatus(lastBody)` against `TERMINAL_STATUSES`, returns `{ done: true, value: lastBody }` when terminal.

**Site 2 (L2638-2652):** Build status after `bkn push --build` — `fn` calls `getBuildStatus()`, parses JSON, checks `state` against `["completed", "failed", "success"]`, returns `{ done: true, value: state }` when terminal.

**Site 3 (L2835-2860):** Standalone build wait — same as Site 2 but also extracts `state_detail`. `fn` returns `{ done: true, value: { state, detail } }` when terminal.

- [ ] **Step 4: Run all bkn tests**

Run: `cd packages/typescript && npx tsx --test test/bkn-push-pull.test.ts`
Expected: ALL PASS

- [ ] **Step 5: Run full TS test suite**

Run: `cd packages/typescript && npx tsx --test test/*.test.ts`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add packages/typescript/src/commands/bkn.ts packages/typescript/test/bkn-push-pull.test.ts
git commit -m "fix(bkn): extract pollWithBackoff helper, add exponential backoff to 3 polling sites"
```

---

### Task 7: `datasources.list_tables` — pass keyword to secondary column query

**Files:**
- Modify: `packages/python/src/kweaver/resources/datasources.py:178-181`
- Test: `packages/python/tests/unit/test_datasources.py`

The secondary per-table column fetch (L181) hardcodes `params={"limit": -1}` without passing the `keyword` that was provided to `list_tables`. This is a minor issue since the secondary query fetches columns for a specific table by ID, not a list query — but the `limit: -1` without keyword is inconsistent. On closer inspection, L179-181 fetches columns for a **specific table by table_id**, so `keyword` is not applicable here. The real concern from the issue scan was the initial fetch, which already correctly passes `keyword` (L151-152).

**Re-evaluation:** This item is a false positive from the initial scan. The secondary query is a `GET /metadata/table/{table_id}` endpoint — it fetches columns for one specific table, not a search. `keyword` doesn't apply. **Skip this task.**

---

### Task 8: Final verification

- [ ] **Step 1: Run full Python test suite**

Run: `cd packages/python && python -m pytest tests/unit/ -v`
Expected: ALL PASS

- [ ] **Step 2: Run full TypeScript test suite**

Run: `cd packages/typescript && npx tsx --test test/*.test.ts`
Expected: ALL PASS

- [ ] **Step 3: Final commit and push**

```bash
git push -u origin fix/19-find-perf-polling-backoff
```
