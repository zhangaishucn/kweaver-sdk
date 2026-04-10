# Python Dataflow CLI Design

Last updated: 2026-04-10

## Summary

Add a Python `dataflow` CLI command group under `packages/python` with the same user-facing command forms and output behavior as the existing TypeScript implementation.

This work must not replace the existing Python `resources/dataflows.py` lifecycle API. Instead, it adds a new resource layer for the document-oriented dataflow CLI workflow and wires a parallel Python CLI surface on top of it.

## Goals

- Match the TypeScript `dataflow` CLI command set:
  - `dataflow list`
  - `dataflow run <dag_id> --file <path>`
  - `dataflow run <dag_id> --url <remote-url> --name <filename>`
  - `dataflow runs <dag_id> [--since <date-like>]`
  - `dataflow logs <dag_id> <instance_id> [--detail]`
- Keep the new Python API/resource layer separate from the old lifecycle-style `dataflows.py`.
- Keep output semantics aligned with TypeScript:
  - `list` / `runs` use terminal tables
  - `run` prints only `dag_instance_id`
  - `logs` defaults to summary blocks
  - `logs --detail` prints indented pretty JSON payloads
- Avoid adding new third-party runtime dependencies for table rendering.

## Non-goals

- Do not migrate or rename the existing `resources/dataflows.py`.
- Do not redesign the Python CLI architecture beyond what is needed for `dataflow`.
- Do not add interactive polling or follow mode for logs.
- Do not introduce a general-purpose formatting framework.

## Architecture

### CLI layer

Add a new Click command group:

- `packages/python/src/kweaver/cli/dataflow.py`

Responsibilities:

- Define the `dataflow` command group and 4 subcommands.
- Validate CLI arguments and mutual exclusivity rules.
- Resolve local files for `run --file`.
- Parse `--since` into a local natural-day range.
- Implement the two-request fetch strategy for `runs --since`.
- Render `list` and `runs` as terminal tables.
- Render `logs` in summary or detail mode.

### Resource layer

Add a new resource module, separate from the existing lifecycle API:

- `packages/python/src/kweaver/resources/dataflow_v2.py`

Responsibilities:

- Encapsulate the document-style automation HTTP endpoints.
- Expose small, CLI-oriented methods:
  - `list_dataflows()`
  - `run_dataflow_with_file(...)`
  - `run_dataflow_with_remote_url(...)`
  - `list_dataflow_runs(...)`
  - `get_dataflow_logs_page(...)`

This resource coexists with:

- `packages/python/src/kweaver/resources/dataflows.py`

The old resource remains unchanged in purpose.

### Client wiring

Expose the new resource from the Python client in a clearly separate name so callers do not confuse it with the old lifecycle API.

Recommended property:

- `client.dataflow_v2`

This mirrors the TypeScript split between old and new APIs without overloading one object with unrelated semantics.

### Formatting helper

Add a small helper module for CLI-only table rendering:

- `packages/python/src/kweaver/cli/_formatting.py`

Responsibilities:

- Render a list of row dictionaries as a left-aligned table.
- Convert `None` to empty strings.
- Stay intentionally small and dependency-free.

No wrapping or advanced terminal features are required for the first version.

## Command contract

### `kweaver dataflow list`

Fetch all dataflow DAGs and print a table with these columns:

- `ID`
- `Title`
- `Status`
- `Trigger`
- `Creator`
- `Updated At`
- `Version ID`

Backend request:

- `GET /api/automation/v2/dags?type=data-flow&page=0&limit=-1`

The CLI does not expose pagination for this command.

### `kweaver dataflow run <dag_id>`

Accepted source forms:

- `--file <path>`
- `--url <remote-url> --name <filename>`

Rules:

- `--file` and `--url` are mutually exclusive.
- `--url` requires `--name`.
- A local file path must exist and be readable before the request is made.

Backend behavior:

- `--file`: multipart upload to the dataflow trigger endpoint
- `--url --name`: JSON body with remote source metadata

Success output:

- print only `dag_instance_id`

### `kweaver dataflow runs <dag_id> [--since <date-like>]`

Default behavior when `--since` is absent or invalid:

- request only the most recent 20 runs
- fixed query parameters:
  - `page=0`
  - `limit=20`
  - `sortBy=started_at`
  - `order=desc`

Behavior when `--since` is valid:

- parse the value with Python date parsing logic
- if parsing succeeds, convert it to the local natural day:
  - `start_time` = `00:00:00`
  - `end_time` = `23:59:59`
- first request:
  - `page=0`
  - `limit=20`
  - `sortBy=started_at`
  - `order=desc`
  - `start_time=<unix_sec>`
  - `end_time=<unix_sec>`
- if `total <= 20`, stop
- if `total > 20`, issue a second request for the remaining results

Second request behavior:

- `page=1`
- `limit=<total - 20>`
- same `sortBy`, `order`, `start_time`, `end_time`

Output table columns:

- `ID`
- `Status`
- `Started At`
- `Ended At`
- `Source Name`
- `Content Type`
- `Size`
- `Reason`

### `kweaver dataflow logs <dag_id> <instance_id> [--detail]`

The CLI does not expose pagination flags. It fetches all logs internally.

Internal fetch strategy:

- request `limit=100`
- increment `page` until:
  - the response is empty, or
  - fetched item count reaches `total`

Default output is a summary block per log item:

```text
[0] 0 @trigger/dataflow-doc
Status: success
Started At: 1775616541
Updated At: 1775616541
Duration: 0
```

`--detail` appends formatted payloads:

```text
    input:
        {
            "foo": "bar"
        }

    output:
        {
            "_type": "file",
            "name": "demo.pdf"
        }
```

Formatting rules:

- use `json.dumps(value, indent=4, ensure_ascii=False)`
- prepend 4 spaces for the `input:` / `output:` labels
- prepend 8 spaces for each JSON line

## HTTP endpoints

The new Python resource should align with the current TypeScript implementation:

- list DAGs:
  - `GET /api/automation/v2/dags?type=data-flow&page=0&limit=-1`
- trigger with file:
  - `POST /api/automation/v2/dataflow-doc/trigger/{dag_id}`
- trigger with remote URL:
  - `POST /api/automation/v2/dataflow-doc/trigger/{dag_id}`
- list run records:
  - `GET /api/automation/v2/dag/{dag_id}/results`
- get run logs page:
  - `GET /api/automation/v2/dag/{dag_id}/result/{instance_id}?page=<n>&limit=<n>`

## Dependency decision

Do not add a new runtime dependency for table rendering.

Reasoning:

- the Python package already has `click` but no table library
- only 2 commands need table formatting
- a small local formatter is sufficient and keeps package entropy lower

## Error handling

- CLI argument shape errors should come from Click.
- `run --file` must fail early if the path does not exist or is unreadable.
- `--since` parse failure should not raise; it should silently fall back to the default recent-20 behavior.
- empty `list`, `runs`, or `logs` results should not raise synthetic errors.
- HTTP and auth errors should continue to use the Python CLI’s existing error handling path.

## Testing

### Unit tests: resource layer

Add tests for:

- list DAGs endpoint and query string
- file-trigger request shape
- remote-trigger request shape
- runs query parameter propagation
- logs page endpoint and page/limit propagation

### Unit tests: CLI layer

Add tests for:

- `dataflow list` table output
- `dataflow run --file` success path
- `dataflow run --url --name` success path
- invalid `run` argument combinations
- `dataflow runs` default recent-20 behavior
- `dataflow runs --since` natural-day conversion and two-request merge
- invalid `--since` fallback behavior
- `dataflow logs` summary output
- `dataflow logs --detail` detail output
- `dataflow logs` internal pagination with `limit=100`

### Documentation

Update:

- `packages/python/README.md`
- `packages/python/README.zh.md`

The Python CLI help text must also include the new command group and options.

## File plan

Expected touched areas:

- `packages/python/src/kweaver/cli/dataflow.py`
- `packages/python/src/kweaver/cli/_formatting.py`
- `packages/python/src/kweaver/resources/dataflow_v2.py`
- `packages/python/src/kweaver/_client.py`
- Python CLI entry wiring files
- `packages/python/tests/unit/` for CLI and resource tests
- `packages/python/README.md`
- `packages/python/README.zh.md`

## Acceptance criteria

- Python CLI exposes the same 4 `dataflow` subcommands as TypeScript.
- Python CLI output shape matches TypeScript for `list`, `run`, `runs`, and `logs`.
- Old Python `dataflows.py` lifecycle API remains available and behaviorally unchanged.
- No new runtime dependency is added for table rendering.
- Unit tests cover the new resource and CLI behavior.
