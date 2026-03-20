# Enhancement: Schema CRUD CLI + Agent Get + OT Properties + KN Search (TS)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 4 missing capabilities to the SDK — schema write CLI commands, agent detail CLI, object-type properties CLI, and TS kn_search — with full test coverage and updated skill docs.

**Architecture:** All 4 features are pure additions on top of existing SDK resource methods. Python Resource layer is already complete; work is primarily CLI commands, unit tests, and skill documentation. TS needs one new method on BknResource. No breaking changes.

**Tech Stack:** Python (Click CLI, pytest, httpx MockTransport), TypeScript (node:test, fetchTextOrThrow), Markdown (SKILL.md references)

**Branch:** `feature/enhancement` (sync with main first)

---

## File Map

| Feature | Files to Modify | Files to Create |
|---------|-----------------|-----------------|
| F1: Schema CRUD CLI | `packages/python/src/kweaver/cli/kn.py` | — |
| F1: Schema CRUD tests | `packages/python/tests/unit/test_cli.py` | — |
| F1: Schema CRUD resource tests | `packages/python/tests/unit/test_object_types.py` | — |
| F3: Agent get CLI | `packages/python/src/kweaver/cli/agent.py` | — |
| F3: Agent get CLI tests | `packages/python/tests/unit/test_cli.py` | — |
| FB: OT properties CLI | `packages/python/src/kweaver/cli/kn.py` | — |
| FB: OT properties CLI tests | `packages/python/tests/unit/test_cli.py` | — |
| F6: TS kn_search | `packages/typescript/src/resources/bkn.ts` | — |
| F6: TS kn_search tests | `packages/typescript/test/context-loader.test.ts` or new file | — |
| Skill docs | `skills/kweaver-core/references/bkn.md`, `skills/kweaver-core/references/agent.md`, `skills/kweaver-core/SKILL.md` | — |

---

## Task 1: Sync branch with main

**Files:** (git operations only)

- [ ] **Step 1: Checkout and sync branch**

```bash
git checkout feature/enhancement
git merge main --no-edit
```

- [ ] **Step 2: Verify clean state**

```bash
git status
```

- [ ] **Step 3: Run existing tests to confirm green baseline**

```bash
cd packages/python && python -m pytest tests/unit/ -v --tb=short
```

Expected: All existing tests pass.

---

## Task 2: Feature 1 — Object Type CRUD CLI commands

**Files:**
- Modify: `packages/python/src/kweaver/cli/kn.py` (add commands under `object_type_group`)
- Test: `packages/python/tests/unit/test_cli.py`

### Step 2a: Write failing tests for `bkn object-type get`

- [ ] **Step 2a.1: Add test**

Append to `packages/python/tests/unit/test_cli.py`, in the KN subcommands section:

```python
def test_object_type_get(runner):
    with patch("kweaver.cli.kn.make_client") as mock_make:
        client = _mock_client()
        mock_ot = MagicMock()
        mock_ot.model_dump.return_value = {
            "id": "ot1", "name": "products", "kn_id": "kn1",
            "primary_keys": ["id"], "display_key": "name",
        }
        client.object_types.get.return_value = mock_ot
        mock_make.return_value = client
        result = runner.invoke(cli, ["bkn", "object-type", "get", "kn1", "ot1"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "ot1"
        client.object_types.get.assert_called_once_with("kn1", "ot1")
```

- [ ] **Step 2a.2: Run test to verify it fails**

Run: `cd packages/python && python -m pytest tests/unit/test_cli.py::test_object_type_get -v`
Expected: FAIL (no such command "get" in object-type group)

- [ ] **Step 2a.3: Implement `bkn object-type get`**

In `packages/python/src/kweaver/cli/kn.py`, after the existing `object_type_list` command:

```python
@object_type_group.command("get")
@click.argument("kn_id")
@click.argument("ot_id")
@handle_errors
def object_type_get(kn_id: str, ot_id: str) -> None:
    """Get object type details."""
    client = make_client()
    ot = client.object_types.get(kn_id, ot_id)
    pp(ot.model_dump())
```

- [ ] **Step 2a.4: Run test to verify it passes**

Run: `cd packages/python && python -m pytest tests/unit/test_cli.py::test_object_type_get -v`
Expected: PASS

### Step 2b: Write failing tests for `bkn object-type create`

- [ ] **Step 2b.1: Add test**

```python
def test_object_type_create(runner):
    with patch("kweaver.cli.kn.make_client") as mock_make:
        client = _mock_client()
        mock_ot = MagicMock()
        mock_ot.model_dump.return_value = {"id": "ot1", "name": "products"}
        client.object_types.create.return_value = mock_ot
        mock_make.return_value = client
        result = runner.invoke(cli, [
            "bkn", "object-type", "create", "kn1",
            "--name", "products",
            "--dataview-id", "dv1",
            "--primary-key", "id",
            "--display-key", "name",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "products"
        client.object_types.create.assert_called_once_with(
            "kn1", name="products", dataview_id="dv1",
            primary_key="id", display_key="name", properties=None,
        )


def test_object_type_create_with_properties(runner):
    with patch("kweaver.cli.kn.make_client") as mock_make:
        client = _mock_client()
        mock_ot = MagicMock()
        mock_ot.model_dump.return_value = {"id": "ot1", "name": "products"}
        client.object_types.create.return_value = mock_ot
        mock_make.return_value = client
        prop_json = '{"name":"age","type":"integer","indexed":true}'
        result = runner.invoke(cli, [
            "bkn", "object-type", "create", "kn1",
            "--name", "products",
            "--dataview-id", "dv1",
            "--primary-key", "id",
            "--display-key", "name",
            "--property", prop_json,
        ])
        assert result.exit_code == 0
        call_kwargs = client.object_types.create.call_args[1]
        assert len(call_kwargs["properties"]) == 1
        assert call_kwargs["properties"][0].name == "age"
```

- [ ] **Step 2b.2: Run tests to verify they fail**

Run: `cd packages/python && python -m pytest tests/unit/test_cli.py::test_object_type_create tests/unit/test_cli.py::test_object_type_create_with_properties -v`
Expected: FAIL

- [ ] **Step 2b.3: Implement `bkn object-type create`**

```python
@object_type_group.command("create")
@click.argument("kn_id")
@click.option("--name", required=True, help="Object type name.")
@click.option("--dataview-id", required=True, help="Data view ID.")
@click.option("--primary-key", required=True, help="Primary key field name.")
@click.option("--display-key", required=True, help="Display key field name.")
@click.option("--property", "properties_json", multiple=True, help="Property JSON (repeatable).")
@handle_errors
def object_type_create(
    kn_id: str, name: str, dataview_id: str, primary_key: str,
    display_key: str, properties_json: tuple[str, ...],
) -> None:
    """Create an object type."""
    from kweaver.types import Property

    properties = None
    if properties_json:
        properties = [Property(**json.loads(p)) for p in properties_json]
    client = make_client()
    ot = client.object_types.create(
        kn_id, name=name, dataview_id=dataview_id,
        primary_key=primary_key, display_key=display_key, properties=properties,
    )
    pp(ot.model_dump())
```

**Important:** `kn.py` does NOT have `import json`. Add it to the imports at the top of the file:

```python
import json
```

Add this right after `import time` in the existing imports block.

- [ ] **Step 2b.4: Run tests to verify they pass**

Run: `cd packages/python && python -m pytest tests/unit/test_cli.py::test_object_type_create tests/unit/test_cli.py::test_object_type_create_with_properties -v`
Expected: PASS

### Step 2c: Write failing tests for `bkn object-type update`

- [ ] **Step 2c.1: Add test**

```python
def test_object_type_update(runner):
    with patch("kweaver.cli.kn.make_client") as mock_make:
        client = _mock_client()
        mock_ot = MagicMock()
        mock_ot.model_dump.return_value = {"id": "ot1", "name": "new-name"}
        client.object_types.update.return_value = mock_ot
        mock_make.return_value = client
        result = runner.invoke(cli, [
            "bkn", "object-type", "update", "kn1", "ot1",
            "--name", "new-name",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "new-name"
        client.object_types.update.assert_called_once_with("kn1", "ot1", name="new-name")
```

- [ ] **Step 2c.2: Run test to verify it fails**

Run: `cd packages/python && python -m pytest tests/unit/test_cli.py::test_object_type_update -v`
Expected: FAIL

- [ ] **Step 2c.3: Implement `bkn object-type update`**

```python
@object_type_group.command("update")
@click.argument("kn_id")
@click.argument("ot_id")
@click.option("--name", default=None, help="New name.")
@click.option("--display-key", default=None, help="New display key.")
@handle_errors
def object_type_update(kn_id: str, ot_id: str, name: str | None, display_key: str | None) -> None:
    """Update an object type."""
    kwargs: dict[str, Any] = {}
    if name is not None:
        kwargs["name"] = name
    if display_key is not None:
        kwargs["display_key"] = display_key
    if not kwargs:
        error_exit("No update fields provided. Use --name or --display-key.")
    client = make_client()
    ot = client.object_types.update(kn_id, ot_id, **kwargs)
    pp(ot.model_dump())
```

- [ ] **Step 2c.4: Run test to verify it passes**

Run: `cd packages/python && python -m pytest tests/unit/test_cli.py::test_object_type_update -v`
Expected: PASS

### Step 2d: Write failing tests for `bkn object-type delete`

- [ ] **Step 2c.5: Add error-path test for update with no flags**

```python
def test_object_type_update_no_fields(runner):
    with patch("kweaver.cli.kn.make_client") as mock_make:
        client = _mock_client()
        mock_make.return_value = client
        result = runner.invoke(cli, [
            "bkn", "object-type", "update", "kn1", "ot1",
        ])
        assert result.exit_code != 0
        client.object_types.update.assert_not_called()
```

- [ ] **Step 2d.1: Add test**

```python
def test_object_type_delete(runner):
    with patch("kweaver.cli.kn.make_client") as mock_make:
        client = _mock_client()
        mock_make.return_value = client
        result = runner.invoke(cli, [
            "bkn", "object-type", "delete", "kn1", "ot1", "--yes",
        ])
        assert result.exit_code == 0
        client.object_types.delete.assert_called_once_with("kn1", "ot1")
        assert "Deleted" in result.output


def test_object_type_delete_aborted(runner):
    with patch("kweaver.cli.kn.make_client") as mock_make:
        client = _mock_client()
        mock_make.return_value = client
        result = runner.invoke(cli, [
            "bkn", "object-type", "delete", "kn1", "ot1",
        ], input="n\n")
        assert result.exit_code != 0
        client.object_types.delete.assert_not_called()
```

- [ ] **Step 2d.2: Run tests to verify they fail**

Run: `cd packages/python && python -m pytest tests/unit/test_cli.py::test_object_type_delete tests/unit/test_cli.py::test_object_type_delete_aborted -v`
Expected: FAIL

- [ ] **Step 2d.3: Implement `bkn object-type delete`**

```python
@object_type_group.command("delete")
@click.argument("kn_id")
@click.argument("ot_ids")
@click.option("--yes", "-y", is_flag=True, default=False, help="Skip confirmation.")
@handle_errors
def object_type_delete(kn_id: str, ot_ids: str, yes: bool) -> None:
    """Delete object type(s). Pass comma-separated IDs for batch delete."""
    if not yes:
        click.confirm(f"Delete object type(s) {ot_ids}?", abort=True)
    client = make_client()
    client.object_types.delete(kn_id, ot_ids)
    click.echo(f"Deleted {ot_ids}")
```

- [ ] **Step 2d.4: Run tests to verify they pass**

Run: `cd packages/python && python -m pytest tests/unit/test_cli.py::test_object_type_delete tests/unit/test_cli.py::test_object_type_delete_aborted -v`
Expected: PASS

- [ ] **Step 2e: Commit Feature 1a — Object Type CRUD CLI**

```bash
git add packages/python/src/kweaver/cli/kn.py packages/python/tests/unit/test_cli.py
git commit -m "feat(cli): add object-type get/create/update/delete commands"
```

---

## Task 3: Feature 1 — Relation Type CRUD CLI commands

**Files:**
- Modify: `packages/python/src/kweaver/cli/kn.py` (add commands under `relation_type_group`)
- Test: `packages/python/tests/unit/test_cli.py`

### Step 3a: Write failing tests for `bkn relation-type get/create/update/delete`

- [ ] **Step 3a.1: Add tests**

```python
def test_relation_type_get(runner):
    with patch("kweaver.cli.kn.make_client") as mock_make:
        client = _mock_client()
        mock_rt = MagicMock()
        mock_rt.model_dump.return_value = {
            "id": "rt1", "name": "has_order", "kn_id": "kn1",
            "source_ot_id": "ot1", "target_ot_id": "ot2",
        }
        client.relation_types.get.return_value = mock_rt
        mock_make.return_value = client
        result = runner.invoke(cli, ["bkn", "relation-type", "get", "kn1", "rt1"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "rt1"
        client.relation_types.get.assert_called_once_with("kn1", "rt1")


def test_relation_type_create(runner):
    with patch("kweaver.cli.kn.make_client") as mock_make:
        client = _mock_client()
        mock_rt = MagicMock()
        mock_rt.model_dump.return_value = {"id": "rt1", "name": "has_order"}
        client.relation_types.create.return_value = mock_rt
        mock_make.return_value = client
        result = runner.invoke(cli, [
            "bkn", "relation-type", "create", "kn1",
            "--name", "has_order",
            "--source", "ot1",
            "--target", "ot2",
            "--mapping", "user_id:id",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "has_order"
        call_kwargs = client.relation_types.create.call_args[1]
        assert call_kwargs["source_ot_id"] == "ot1"
        assert call_kwargs["target_ot_id"] == "ot2"
        assert call_kwargs["mappings"] == [("user_id", "id")]


def test_relation_type_create_no_mapping(runner):
    with patch("kweaver.cli.kn.make_client") as mock_make:
        client = _mock_client()
        mock_rt = MagicMock()
        mock_rt.model_dump.return_value = {"id": "rt1", "name": "linked_to"}
        client.relation_types.create.return_value = mock_rt
        mock_make.return_value = client
        result = runner.invoke(cli, [
            "bkn", "relation-type", "create", "kn1",
            "--name", "linked_to",
            "--source", "ot1",
            "--target", "ot2",
        ])
        assert result.exit_code == 0
        call_kwargs = client.relation_types.create.call_args[1]
        assert call_kwargs["mappings"] is None


def test_relation_type_update(runner):
    with patch("kweaver.cli.kn.make_client") as mock_make:
        client = _mock_client()
        mock_rt = MagicMock()
        mock_rt.model_dump.return_value = {"id": "rt1", "name": "new-name"}
        client.relation_types.update.return_value = mock_rt
        mock_make.return_value = client
        result = runner.invoke(cli, [
            "bkn", "relation-type", "update", "kn1", "rt1",
            "--name", "new-name",
        ])
        assert result.exit_code == 0
        client.relation_types.update.assert_called_once_with("kn1", "rt1", name="new-name")


def test_relation_type_delete(runner):
    with patch("kweaver.cli.kn.make_client") as mock_make:
        client = _mock_client()
        mock_make.return_value = client
        result = runner.invoke(cli, [
            "bkn", "relation-type", "delete", "kn1", "rt1", "--yes",
        ])
        assert result.exit_code == 0
        client.relation_types.delete.assert_called_once_with("kn1", "rt1")
        assert "Deleted" in result.output


def test_relation_type_delete_aborted(runner):
    with patch("kweaver.cli.kn.make_client") as mock_make:
        client = _mock_client()
        mock_make.return_value = client
        result = runner.invoke(cli, [
            "bkn", "relation-type", "delete", "kn1", "rt1",
        ], input="n\n")
        assert result.exit_code != 0
        client.relation_types.delete.assert_not_called()


def test_relation_type_update_no_fields(runner):
    with patch("kweaver.cli.kn.make_client") as mock_make:
        client = _mock_client()
        mock_make.return_value = client
        result = runner.invoke(cli, [
            "bkn", "relation-type", "update", "kn1", "rt1",
        ])
        assert result.exit_code != 0
        client.relation_types.update.assert_not_called()


def test_relation_type_create_invalid_mapping(runner):
    with patch("kweaver.cli.kn.make_client") as mock_make:
        client = _mock_client()
        mock_make.return_value = client
        result = runner.invoke(cli, [
            "bkn", "relation-type", "create", "kn1",
            "--name", "bad",
            "--source", "ot1",
            "--target", "ot2",
            "--mapping", "no_colon_here",
        ])
        assert result.exit_code != 0
```

- [ ] **Step 3a.2: Run tests to verify they fail**

Run: `cd packages/python && python -m pytest tests/unit/test_cli.py -k "relation_type_get or relation_type_create or relation_type_update or relation_type_delete" -v`
Expected: FAIL

- [ ] **Step 3a.3: Implement all relation-type commands**

In `packages/python/src/kweaver/cli/kn.py`, after the existing `relation_type_list` command:

```python
@relation_type_group.command("get")
@click.argument("kn_id")
@click.argument("rt_id")
@handle_errors
def relation_type_get(kn_id: str, rt_id: str) -> None:
    """Get relation type details."""
    client = make_client()
    rt = client.relation_types.get(kn_id, rt_id)
    pp(rt.model_dump())


@relation_type_group.command("create")
@click.argument("kn_id")
@click.option("--name", required=True, help="Relation type name.")
@click.option("--source", "source_ot_id", required=True, help="Source object type ID.")
@click.option("--target", "target_ot_id", required=True, help="Target object type ID.")
@click.option("--mapping", "mappings_raw", multiple=True, help="Field mapping as src_prop:tgt_prop (repeatable).")
@handle_errors
def relation_type_create(
    kn_id: str, name: str, source_ot_id: str, target_ot_id: str,
    mappings_raw: tuple[str, ...],
) -> None:
    """Create a relation type."""
    mappings = None
    if mappings_raw:
        mappings = []
        for m in mappings_raw:
            parts = m.split(":", 1)
            if len(parts) != 2:
                error_exit(f"Invalid mapping format: {m!r}. Expected 'source_prop:target_prop'.")
            mappings.append((parts[0], parts[1]))
    client = make_client()
    rt = client.relation_types.create(
        kn_id, name=name, source_ot_id=source_ot_id,
        target_ot_id=target_ot_id, mappings=mappings,
    )
    pp(rt.model_dump())


@relation_type_group.command("update")
@click.argument("kn_id")
@click.argument("rt_id")
@click.option("--name", default=None, help="New name.")
@handle_errors
def relation_type_update(kn_id: str, rt_id: str, name: str | None) -> None:
    """Update a relation type."""
    kwargs: dict[str, Any] = {}
    if name is not None:
        kwargs["name"] = name
    if not kwargs:
        error_exit("No update fields provided. Use --name.")
    client = make_client()
    rt = client.relation_types.update(kn_id, rt_id, **kwargs)
    pp(rt.model_dump())


@relation_type_group.command("delete")
@click.argument("kn_id")
@click.argument("rt_ids")
@click.option("--yes", "-y", is_flag=True, default=False, help="Skip confirmation.")
@handle_errors
def relation_type_delete(kn_id: str, rt_ids: str, yes: bool) -> None:
    """Delete relation type(s). Pass comma-separated IDs for batch delete."""
    if not yes:
        click.confirm(f"Delete relation type(s) {rt_ids}?", abort=True)
    client = make_client()
    client.relation_types.delete(kn_id, rt_ids)
    click.echo(f"Deleted {rt_ids}")
```

- [ ] **Step 3a.4: Run tests to verify they pass**

Run: `cd packages/python && python -m pytest tests/unit/test_cli.py -k "relation_type_get or relation_type_create or relation_type_update or relation_type_delete" -v`
Expected: PASS

- [ ] **Step 3b: Commit Feature 1b — Relation Type CRUD CLI**

```bash
git add packages/python/src/kweaver/cli/kn.py packages/python/tests/unit/test_cli.py
git commit -m "feat(cli): add relation-type get/create/update/delete commands"
```

---

## Task 4: Feature 3 — Agent Get CLI command

**Files:**
- Modify: `packages/python/src/kweaver/cli/agent.py`
- Test: `packages/python/tests/unit/test_cli.py`

- [ ] **Step 4a: Add tests**

```python
def test_agent_get(runner):
    with patch("kweaver.cli.agent.make_client") as mock_make:
        client = _mock_client()
        mock_agent = MagicMock()
        mock_agent.id = "a1"
        mock_agent.name = "assistant"
        mock_agent.description = "test agent"
        mock_agent.status = "published"
        mock_agent.kn_ids = ["kn1"]
        mock_agent.model_dump.return_value = {
            "id": "a1", "name": "assistant", "description": "test agent",
            "status": "published", "kn_ids": ["kn1"],
        }
        client.agents.get.return_value = mock_agent
        mock_make.return_value = client
        result = runner.invoke(cli, ["agent", "get", "a1"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "a1"
        assert data["name"] == "assistant"
        client.agents.get.assert_called_once_with("a1")


def test_agent_get_verbose(runner):
    with patch("kweaver.cli.agent.make_client") as mock_make:
        client = _mock_client()
        mock_agent = MagicMock()
        mock_agent.model_dump.return_value = {
            "id": "a1", "name": "assistant", "system_prompt": "你是专家",
            "capabilities": ["search"], "model_config_data": {"name": "gpt"},
        }
        client.agents.get.return_value = mock_agent
        mock_make.return_value = client
        result = runner.invoke(cli, ["agent", "get", "a1", "--verbose"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "system_prompt" in data
```

- [ ] **Step 4b: Run tests to verify they fail**

Run: `cd packages/python && python -m pytest tests/unit/test_cli.py::test_agent_get tests/unit/test_cli.py::test_agent_get_verbose -v`
Expected: FAIL

- [ ] **Step 4c: Implement `agent get`**

In `packages/python/src/kweaver/cli/agent.py`, after `list_agents`:

```python
@agent_group.command("get")
@click.argument("agent_id")
@click.option("--verbose", "-v", is_flag=True, help="Show full JSON response.")
@handle_errors
def get_agent(agent_id: str, verbose: bool) -> None:
    """Get agent details."""
    client = make_client()
    agent = client.agents.get(agent_id)
    if verbose:
        pp(agent.model_dump())
    else:
        simplified = {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description or "",
            "status": agent.status,
            "kn_ids": agent.kn_ids,
        }
        pp(simplified)
```

- [ ] **Step 4d: Run tests to verify they pass**

Run: `cd packages/python && python -m pytest tests/unit/test_cli.py::test_agent_get tests/unit/test_cli.py::test_agent_get_verbose -v`
Expected: PASS

- [ ] **Step 4e: Commit Feature 3**

```bash
git add packages/python/src/kweaver/cli/agent.py packages/python/tests/unit/test_cli.py
git commit -m "feat(cli): add agent get command"
```

---

## Task 5: Feature B — Object Type Properties CLI command

**Files:**
- Modify: `packages/python/src/kweaver/cli/kn.py` (add under `object_type_group`)
- Test: `packages/python/tests/unit/test_cli.py`

- [ ] **Step 5a: Add tests**

```python
def test_object_type_properties(runner):
    with patch("kweaver.cli.kn.make_client") as mock_make:
        client = _mock_client()
        client.query.object_type_properties.return_value = {
            "properties": [
                {"name": "id", "type": "integer"},
                {"name": "name", "type": "varchar"},
            ],
        }
        mock_make.return_value = client
        result = runner.invoke(cli, ["bkn", "object-type", "properties", "kn1", "ot1"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "properties" in data
        client.query.object_type_properties.assert_called_once_with("kn1", "ot1")
```

- [ ] **Step 5b: Run test to verify it fails**

Run: `cd packages/python && python -m pytest tests/unit/test_cli.py::test_object_type_properties -v`
Expected: FAIL

- [ ] **Step 5c: Implement `bkn object-type properties`**

In `packages/python/src/kweaver/cli/kn.py`, add under `object_type_group`:

```python
@object_type_group.command("properties")
@click.argument("kn_id")
@click.argument("ot_id")
@handle_errors
def object_type_properties(kn_id: str, ot_id: str) -> None:
    """Query object type property definitions and statistics."""
    client = make_client()
    data = client.query.object_type_properties(kn_id, ot_id)
    pp(data)
```

- [ ] **Step 5d: Run test to verify it passes**

Run: `cd packages/python && python -m pytest tests/unit/test_cli.py::test_object_type_properties -v`
Expected: PASS

- [ ] **Step 5e: Commit Feature B**

```bash
git add packages/python/src/kweaver/cli/kn.py packages/python/tests/unit/test_cli.py
git commit -m "feat(cli): add object-type properties command"
```

---

## Task 6: Feature 6 — TypeScript BknResource.knSearch()

**Files:**
- Modify: `packages/typescript/src/resources/bkn.ts`
- Test: new or extend existing TS tests

- [ ] **Step 6a: Add knSearch method to BknResource**

In `packages/typescript/src/resources/bkn.ts`, add import and method:

Add to imports:
```typescript
import { knSearch as knSearchApi } from "../api/context-loader.js";
```

Note: `knSearch` in `api/context-loader.ts` uses the MCP protocol. For a direct API call (non-MCP), we need to call `agent-retrieval` directly. Check if there's a direct endpoint wrapper. If `knSearch` from context-loader works (it calls MCP tool `kn_search`), that's fine. But a cleaner approach is a direct HTTP call to `/api/agent-retrieval/in/v1/kn/kn_search`.

Add method to `BknResource`:

```typescript
/**
 * Search KN schema — finds matching object types, relation types, and action types.
 * Calls agent-retrieval directly (not via MCP).
 */
async knSearch(
  knId: string,
  query: string,
  opts: { onlySchema?: boolean } = {}
): Promise<{
  object_types?: unknown[];
  relation_types?: unknown[];
  action_types?: unknown[];
  nodes?: unknown[];
}> {
  const { baseUrl, accessToken, businessDomain } = this.ctx.base();
  const url = `${baseUrl}/api/agent-retrieval/in/v1/kn/kn_search`;
  const body: Record<string, unknown> = { kn_id: knId, query };
  if (opts.onlySchema) {
    body.only_schema = true;
  }
  const { body: respBody } = await fetchTextOrThrow(url, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      authorization: `Bearer ${accessToken}`,
      token: accessToken,
      "x-business-domain": businessDomain,
    },
    body: JSON.stringify(body),
  });
  return JSON.parse(respBody) as {
    object_types?: unknown[];
    relation_types?: unknown[];
    action_types?: unknown[];
    nodes?: unknown[];
  };
}
```

- [ ] **Step 6b: Add unit test**

Create or extend test file. Following existing TS test patterns (using `node:test` and `node:assert`), add a test that mocks the HTTP call and verifies the knSearch method sends correct request body and parses response.

The test approach depends on existing TS test infrastructure. Check `packages/typescript/test/` for patterns. If using `node:test` with mock fetch, follow that pattern.

- [ ] **Step 6c: Run TS tests**

```bash
cd packages/typescript && npm test
```

Expected: PASS

- [ ] **Step 6d: Commit Feature 6**

```bash
git add packages/typescript/src/resources/bkn.ts packages/typescript/test/
git commit -m "feat(ts): add BknResource.knSearch for schema search"
```

---

## Task 7: Update Skill Documentation

**Files:**
- Modify: `skills/kweaver-core/SKILL.md`
- Modify: `skills/kweaver-core/references/bkn.md`
- Modify: `skills/kweaver-core/references/agent.md`

- [ ] **Step 7a: Update SKILL.md command overview**

In `skills/kweaver-core/SKILL.md`, update the `bkn` row in the command table:

```markdown
| `bkn` | 知识网络管理与查询（list/get/create/update/delete/export/stats；object-type CRUD/properties、relation-type CRUD、subgraph、action-type、action-log） |
| `agent` | Agent 管理与对话（list、get、chat、sessions、history） |
```

- [ ] **Step 7b: Update bkn.md — add Schema CRUD section**

In `skills/kweaver-core/references/bkn.md`, update the "Schema 列表" section to "Schema 管理":

```markdown
### Schema 管理（ontology-manager）

| 命令 | 说明 |
|------|------|
| `kweaver bkn object-type list <kn-id>` | 列出对象类 |
| `kweaver bkn object-type get <kn-id> <ot-id>` | 查看对象类详情 |
| `kweaver bkn object-type create <kn-id> --name <name> --dataview-id <dv-id> --primary-key <pk> --display-key <dk> [--property '<json>']...` | 创建对象类 |
| `kweaver bkn object-type update <kn-id> <ot-id> [--name <name>] [--display-key <dk>]` | 更新对象类 |
| `kweaver bkn object-type delete <kn-id> <ot-ids> [--yes]` | 删除对象类 |
| `kweaver bkn object-type properties <kn-id> <ot-id>` | 查询属性定义与统计 |
| `kweaver bkn relation-type list <kn-id>` | 列出关系类 |
| `kweaver bkn relation-type get <kn-id> <rt-id>` | 查看关系类详情 |
| `kweaver bkn relation-type create <kn-id> --name <name> --source <ot-id> --target <ot-id> [--mapping src:tgt]...` | 创建关系类 |
| `kweaver bkn relation-type update <kn-id> <rt-id> [--name <name>]` | 更新关系类 |
| `kweaver bkn relation-type delete <kn-id> <rt-ids> [--yes]` | 删除关系类 |
| `kweaver bkn action-type list <kn-id>` | 列出行动类 |
```

- [ ] **Step 7c: Update agent.md — add get command**

In `skills/kweaver-core/references/agent.md`, add `get` to the CLI 命令总览 table:

```markdown
| `kweaver agent get <agent-id> [--verbose]` | 查看 Agent 详情（名称、描述、状态、绑定 KN） |
```

Add usage example:

```markdown
### 查看 Agent 详情

\`\`\`bash
# 查看 Agent 基本信息
kweaver agent get <agent-id>

# 查看完整信息（含 system_prompt、capabilities、model 配置）
kweaver agent get <agent-id> --verbose
\`\`\`
```

Update 默认策略:

```markdown
1. 先用 `kweaver agent list` 查看可用 Agent
2. 用 `kweaver agent get <id>` 查看 Agent 详情和绑定的知识网络
3. 首轮：`kweaver agent chat <agent-id> -m "..."` （不传 conversation-id）
...
```

- [ ] **Step 7d: Commit skill docs**

```bash
git add skills/kweaver-core/
git commit -m "docs(skill): update skill references for new CLI commands"
```

---

## Task 8: Add SDK Resource-level Unit Tests (补充)

Supplement resource-layer tests for update/delete/get operations that don't have dedicated tests yet.

**Files:**
- Modify: `packages/python/tests/unit/test_object_types.py`
- Modify: `packages/python/tests/unit/test_relation_types.py`
- Modify: `packages/python/tests/unit/test_query.py`

- [ ] **Step 8a: Add object_types resource tests for get/update/delete**

Append to `packages/python/tests/unit/test_object_types.py`:

```python
def test_get_object_type(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_OT_RESPONSE)

    client = make_client(handler, capture)
    ot = client.object_types.get("kn_01", "ot_01")
    assert ot.id == "ot_01"
    assert ot.name == "产品"
    assert "/knowledge-networks/kn_01/object-types/ot_01" in capture.last_url()


def test_update_object_type(capture: RequestCapture):
    updated = {**_OT_RESPONSE, "name": "新产品"}

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=updated)

    client = make_client(handler, capture)
    ot = client.object_types.update("kn_01", "ot_01", name="新产品")
    assert ot.name == "新产品"
    body = capture.last_body()
    assert body["name"] == "新产品"


def test_delete_object_type(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    client = make_client(handler, capture)
    client.object_types.delete("kn_01", "ot_01")
    assert "/object-types/ot_01" in capture.last_url()


def test_delete_multiple_object_types(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    client = make_client(handler, capture)
    client.object_types.delete("kn_01", ["ot_01", "ot_02"])
    assert "/object-types/ot_01,ot_02" in capture.last_url()
```

- [ ] **Step 8b: Add relation_types resource tests for get/update/delete**

Append to `packages/python/tests/unit/test_relation_types.py`:

```python
def test_get_relation_type(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_RT_RESPONSE)

    client = make_client(handler, capture)
    rt = client.relation_types.get("kn_01", "rt_01")
    assert rt.id == "rt_01"
    assert rt.name == "产品_库存"
    assert "/relation-types/rt_01" in capture.last_url()


def test_update_relation_type(capture: RequestCapture):
    updated = {**_RT_RESPONSE, "name": "新关系"}

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=updated)

    client = make_client(handler, capture)
    rt = client.relation_types.update("kn_01", "rt_01", name="新关系")
    assert rt.name == "新关系"


def test_delete_relation_type(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    client = make_client(handler, capture)
    client.relation_types.delete("kn_01", "rt_01")
    assert "/relation-types/rt_01" in capture.last_url()


def test_delete_multiple_relation_types(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    client = make_client(handler, capture)
    client.relation_types.delete("kn_01", ["rt_01", "rt_02"])
    assert "/relation-types/rt_01,rt_02" in capture.last_url()
```

- [ ] **Step 8c: Add query resource test for kn_search**

Append to `packages/python/tests/unit/test_query.py`:

```python
def test_kn_search(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "object_types": [{"id": "ot_01", "name": "产品"}],
            "relation_types": [],
            "action_types": [],
        })

    client = make_client(handler, capture)
    result = client.query.kn_search("kn_01", "产品")
    assert result.object_types is not None
    assert len(result.object_types) == 1
    body = capture.last_body()
    assert body["kn_id"] == "kn_01"
    assert body["query"] == "产品"


def test_kn_search_only_schema(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "object_types": [],
            "relation_types": [],
            "action_types": [],
        })

    client = make_client(handler, capture)
    client.query.kn_search("kn_01", "产品", only_schema=True)
    body = capture.last_body()
    assert body["only_schema"] is True


def test_object_type_properties(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "properties": [{"name": "id", "type": "integer"}],
        })

    client = make_client(handler, capture)
    result = client.query.object_type_properties("kn_01", "ot_01")
    assert "properties" in result
    assert capture.last_headers()["x-http-method-override"] == "GET"
```

- [ ] **Step 8d: Run all resource tests**

```bash
cd packages/python && python -m pytest tests/unit/test_object_types.py tests/unit/test_relation_types.py tests/unit/test_query.py -v
```

Expected: All PASS

- [ ] **Step 8e: Commit supplementary tests**

```bash
git add packages/python/tests/unit/
git commit -m "test: add resource-level tests for OT/RT CRUD and query operations"
```

---

## Task 9: Full Test Suite Verification

- [ ] **Step 9a: Run full Python unit test suite**

```bash
cd packages/python && python -m pytest tests/unit/ -v --tb=short
```

Expected: All tests pass, no regressions.

- [ ] **Step 9b: Run TS test suite**

```bash
cd packages/typescript && npm test
```

Expected: All tests pass.

- [ ] **Step 9c: Verify CLI help output**

```bash
cd packages/python && python -m kweaver bkn object-type --help
cd packages/python && python -m kweaver bkn relation-type --help
cd packages/python && python -m kweaver agent --help
```

Verify: new commands appear in help output.
